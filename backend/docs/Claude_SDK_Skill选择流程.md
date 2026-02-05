# Claude SDK Skill 选择和使用完整流程

## 概览

Claude SDK 选择和使用 Skill 是一个多步骤的过程，涉及配置、加载、发现和调用。本文档详细说明了这个完整流程。

---

## 第一部分：Skill 配置层（你的代码）

### 1.1 配置优先级

```
Request > Session > User > Scenario > Global
```

查看 [configuration_manager.py](services/configuration_manager.py:94-387) 的 `merge_agent_config()` 方法。

### 1.2 核心配置参数

#### 参数1：`setting_sources`（开关）

**作用**：控制是否从文件系统加载 Skills

**值**：
- `None` 或 `[]`：不加载任何 Skills（默认，最安全）
- `["project"]`：只加载项目级 Skills（`.claude/skills/`）
- `["user"]`：只加载用户级 Skills（`~/.claude/skills/`）
- `["user", "project"]`：加载两种 Skills

**代码位置**：[agent_service.py:569-572](services/agent_service.py#L569-L572)

```python
options_dict["setting_sources"] = agent_config.setting_sources
# setting_sources 可能是 None（不加载 skill）或 ["project"]（加载项目 skill）
```

#### 参数2：`enabled_skill_ids`（过滤器）

**作用**：指定允许使用哪些具体的 Skill IDs

**值**：
- `None`：允许所有已加载的 Skills
- `["data-analysis", "water_network_beijing"]`：只允许这两个 Skills

**代码位置**：[agent_service.py:697-713](services/agent_service.py#L697-L713)

```python
if agent_config and agent_config.enabled_skill_ids:
    final_prompt = options_dict.get('system_prompt', '')
    if final_prompt:
        skill_instruction = f"""

## 可用技能限制

你只能使用以下指定的技能：
{chr(10).join(f"- {skill_id}" for skill_id in agent_config.enabled_skill_ids)}

**重要**：
- 不要使用其他技能，即使它们在你的技能列表中可用
- 只使用上述明确列出的技能
- 如果用户请求需要使用其他技能，请告知用户当前场景只支持上述技能
"""
        options_dict['system_prompt'] = final_prompt + skill_instruction
```

#### 参数3：`allowed_tools`（工具白名单）

**作用**：控制 Claude 可以使用哪些工具类别

**必须包含**：
- `"Skill"`：允许 Claude 调用 Skills
- 其他工具：`"Read"`, `"Write"`, `"Bash"` 等

**代码位置**：[agent_service.py:563](services/agent_service.py#L563)

```python
options_dict = {
    "allowed_tools": agent_config.allowed_tools or self.default_options.allowed_tools,
    # allowed_tools 必须包含 "Skill" 才能使用 Skills
}
```

---

## 第二部分：SDK 内部流程（Claude Agent SDK）

### 2.1 Skill 加载阶段

当调用 `ClaudeAgentOptions(setting_sources=["project"], ...)` 时：

```python
# 步骤1：SDK 扫描文件系统
skills_dir = cwd / ".claude/skills/"
skill_files = glob(skills_dir / "*/SKILL.md")

# 步骤2：解析每个 SKILL.md
for skill_file in skill_files:
    # 读取 SKILL.md
    content = read_file(skill_file)

    # 解析 frontmatter (YAML)
    frontmatter, markdown = parse_frontmatter(content)

    # 提取元数据
    skill_id = skill_file.parent.name  # 目录名
    skill_name = frontmatter.get('name', skill_id)
    skill_description = frontmatter.get('description', '')

    # 存储到内存
    loaded_skills[skill_id] = {
        'name': skill_name,
        'description': skill_description,
        'content': markdown
    }
```

**示例 Skill 结构**：
```
.claude/skills/data-analysis/
└── SKILL.md
```

**SKILL.md 格式**：
```yaml
---
name: data-analysis
description: Perform data analysis tasks including statistical analysis, visualization, and insight generation
category: Analysis
allowed-tools: []
---

# Data Analysis Skill

You are an expert data analyst...
```

### 2.2 Skill 发现阶段

**何时发生**：首次创建 `ClaudeAgentOptions` 实例时

**发现内容**：
- Skill ID（目录名）
- Skill 名称
- Skill 描述
- Skill 分类

**不加载**：
- 完整的 Skill 内容（按需加载）

### 2.3 Skill 调用决策（AI 层）

这是最关键的部分：**Claude 如何决定使用哪个 Skill**

#### 决策流程

```
1. 用户发送请求
   "分析这个CSV文件的销售额趋势"

2. Claude 检查可用 Skills
   - 遍历所有已加载的 Skills
   - 读取每个 Skill 的 description

3. 语义匹配
   - 比较 user_prompt 与 skill_description
   - 找到最相关的 Skill

4. 如果 enabled_skill_ids 有限制
   - 只在允许的 Skill IDs 中选择
   - 跳过不在白名单中的 Skills

5. 命中 Skill
   - data-analysis description: "Perform data analysis tasks..."
   - 匹配成功！

6. 加载完整 Skill 内容
   - 读取 data-analysis/SKILL.md 的完整内容
   - 附加到 system_prompt
```

#### 具体示例

**用户请求**：
```
"分析这个数据并生成报告"
```

**可用 Skills**：
1. `data-analysis` - "Perform data analysis tasks including statistical analysis, visualization, and insight generation"
2. `water_network_beijing` - "专为北京市水网系统设计的智能数据分析技能"
3. `pptx` - "Presentation creation, editing, and analysis"

**匹配结果**：
- `data-analysis`: 95% 相关度 ✅
- `water_network_beijing`: 30% 相关度（特定领域）
- `pptx`: 10% 相关度（不相关）

**如果配置了 `enabled_skill_ids=["data-analysis"]`**：
- 只使用 `data-analysis`
- 忽略其他 Skills，即使相关

---

## 第三部分：完整调用链路

### 3.1 从用户请求到 Skill 执行

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户发送请求                                                   │
│    POST /api/v1/agent/query/stream                               │
│    { "prompt": "分析这个CSV数据" }                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Endpoint 获取配置 (endpoints.py)                              │
│    - 获取 user_config                                            │
│    - 获取 scenario_config                                        │
│    - 合并配置 (优先级: Request > Session > User > Scenario)      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ConfigurationManager 合并配置                                │
│    (configuration_manager.py:94-387)                            │
│                                                                  │
│    merged = {                                                    │
│      "system_prompt": "...",                                    │
│      "allowed_tools": ["Skill", "Read", "Write", ...],          │
│      "setting_sources": ["project"],  # 🔑 启用 Skill 加载       │
│      "enabled_skill_ids": ["data-analysis"],  # 🔑 限制 Skills  │
│      "cwd": "/path/to/project",                                 │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. AgentService 创建 ClaudeAgentOptions                         │
│    (agent_service.py:528-738)                                   │
│                                                                  │
│    options = ClaudeAgentOptions(**merged)                       │
│    # SDK 在这里开始加载 Skills                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. SDK 加载 Skills (Claude Agent SDK 内部)                      │
│                                                                  │
│    if setting_sources == ["project"]:                           │
│      skills_dir = cwd / ".claude/skills/"                       │
│      for skill_dir in skills_dir.iterdir():                     │
│        skill_md = skill_dir / "SKILL.md"                        │
│        if skill_md.exists():                                    │
│          # 解析 frontmatter 和 content                          │
│          skills[skill_dir.name] = parse_skill(skill_md)         │
│                                                                  │
│    # 发现的所有 Skills:                                          │
│    # - data-analysis                                            │
│    # - water_network_beijing                                    │
│    # - pptx                                                     │
│    # - ...                                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. 附加 Skill 限制指令到 system_prompt                          │
│    (agent_service.py:697-713)                                   │
│                                                                  │
│    if enabled_skill_ids:                                        │
│      system_prompt += """                                       │
│                                                                  │
│      ## 可用技能限制                                              │
│                                                                  │
│      你只能使用以下指定的技能：                                     │
│      - data-analysis                                            │
│                                                                  │
│      **重要**：不要使用其他技能                                     │
│      """                                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Claude 调用 query() 函数                                     │
│    (agent_service.py:822)                                       │
│                                                                  │
│    async for sdk_message in query(                              │
│      prompt="分析这个CSV数据",                                    │
│      options=options  # 包含已加载的 Skills                      │
│    ):                                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. AI 决策层 (Claude Model)                                     │
│                                                                  │
│    # Claude 分析请求                                             │
│    user_request = "分析这个CSV数据"                               │
│                                                                  │
│    # Claude 检查可用 Skills                                      │
│    available_skills = {                                         │
│      "data-analysis": "Perform data analysis tasks...",         │
│      "water_network_beijing": "专为北京市水网系统...",           │
│      "pptx": "Presentation creation...",                        │
│    }                                                             │
│                                                                  │
│    # Claude 语义匹配                                             │
│    best_match = semantic_search(                                │
│      query=user_request,                                        │
│      candidates=available_skills                                │
│    )                                                             │
│    # 结果: data-analysis (匹配度 95%)                            │
│                                                                  │
│    # 检查 enabled_skill_ids 限制                                 │
│    if "data-analysis" in enabled_skill_ids:  # ✅ 允许           │
│      # 加载完整 Skill 内容                                       │
│      skill_content = load_skill("data-analysis/SKILL.md")       │
│                                                                  │
│      # 附加到 system prompt                                     │
│      full_system_prompt = base_system_prompt + "\n\n" + skill_content  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. 执行 Skill (Claude Model + Skill Prompt)                     │
│                                                                  │
│    # Claude 现在有了 Skill 指导                                  │
│    # 它会按照 Skill 的说明来处理请求                             │
│                                                                  │
│    例如 data-analysis Skill 会：                                │
│    1. 读取 CSV 文件                                             │
│    2. 执行统计分析                                              │
│    3. 生成可视化图表                                            │
│    4. 提取洞察和结论                                             │
│    5. 生成分析报告                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. 返回结果给用户                                               │
│     (endpoints.py:183-200)                                      │
│                                                                  │
│     async for msg in agent_service.query_once(...):             │
│       yield f"data: {msg.model_dump_json()}\n\n"               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第四部分：实战示例

### 4.1 配置示例1：不使用任何 Skills

```python
# configuration_manager.py
merged = {
    "setting_sources": None,  # 不加载 Skills
    "enabled_skill_ids": None,
    "allowed_tools": ["Read", "Write", "Bash"],  # 不包含 "Skill"
}
```

**结果**：Claude 不会加载或使用任何 Skills

### 4.2 配置示例2：使用所有项目 Skills

```python
merged = {
    "setting_sources": ["project"],  # 加载项目 Skills
    "enabled_skill_ids": None,  # 不限制，允许所有
    "allowed_tools": ["Skill", "Read", "Write", "Bash"],  # 包含 "Skill"
}
```

**结果**：
- 加载 `.claude/skills/` 下所有 Skills
- Claude 根据请求自动选择最相关的 Skill

### 4.3 配置示例3：只使用特定 Skills

```python
merged = {
    "setting_sources": ["project"],
    "enabled_skill_ids": ["data-analysis", "pptx"],  # 🔑 只允许这两个
    "allowed_tools": ["Skill", "Read", "Write", "Bash"],
}
```

**结果**：
- 加载所有 Skills（用于发现）
- 但只使用 `data-analysis` 和 `pptx`
- 即使 `water_network_beijing` 更相关，也不会使用

### 4.4 配置示例4：场景配置 Skills

```python
# database: business_scenarios table
{
    "id": 1,
    "name": "数据分析场景",
    "skills": ["data-analysis", "joyagent_skill"],
}
```

**结果**：
- 用户使用此场景时，只能用这两个 Skills
- 优先级：User > Scenario
- 如果用户配置了 `custom_skills`，会覆盖场景配置

---

## 第五部分：Skill 选择的关键因素

### 5.1 技能描述 (Description)

最重要！Claude 根据描述来决定是否使用 Skill。

**好的描述**：
```yaml
---
description: Perform data analysis tasks including statistical analysis, visualization, and insight generation. Use when the user asks to analyze data, create charts, or generate reports from datasets.
---
```

**不好的描述**：
```yaml
---
description: A skill for data
---
```

### 5.2 技能内容 (Content)

当 Skill 被选中后，完整内容会附加到 system prompt。

**关键要素**：
- 清晰的任务范围
- 具体的工作流程
- 工具使用指导
- 输出格式要求

### 5.3 enabled_skill_ids 过滤

**作用**：即使 Skill 更相关，也不在白名单中就不能用

**使用场景**：
- 场景限制：数据分析场景只能用 data-analysis
- 用户权限：普通用户不能使用 admin_skills
- 成本控制：限制使用昂贵的 Skills

---

## 第六部分：调试和监控

### 6.1 日志关键点

**配置合并日志**：
```
[ConfigManager] ========== Final merged config (with sources) ==========
  - setting_sources: ['project'] (skills: ENABLED) [SOURCE: USER]
  - enabled_skill_ids: ['data-analysis', 'pptx'] [SOURCE: USER]
  - allowed_tools: 12 tools - ['Skill', 'Read', 'Write', ...] [SOURCE: USER]
[ConfigManager] ==========================================================
```

**Skill 加载日志**：
```
[AgentService] Final ClaudeAgentOptions configuration:
  - setting_sources: ['project'] (skills: ENABLED)
  - enabled_skill_ids: ['data-analysis', 'pptx'] (specific skills to use)
  - allowed_tools: 12 tools - ['Skill', 'Read', 'Write', ...]
```

### 6.2 测试 Skill 是否生效

**方法1：询问 Claude**
```
"What Skills are available?"
```

**方法2：直接调用**
```
"分析这个CSV文件"  # 应该触发 data-analysis Skill
```

**方法3：检查日志**
```
grep "skill" logs/app.log | grep "enabled"
```

---

## 第七部分：常见问题和解决方案

### 7.1 Skill 没有被加载

**症状**：Claude 说没有可用的 Skills

**原因**：
1. `setting_sources` 是 `None`
2. `"Skill"` 不在 `allowed_tools` 中
3. `.claude/skills/` 目录不存在或路径错误

**解决**：
```python
merged = {
    "setting_sources": ["project"],
    "allowed_tools": ["Skill", ...],  # 必须包含 "Skill"
    "cwd": "/path/to/project",  # 必须包含 .claude/skills/
}
```

### 7.2 Skill 被加载但没有被使用

**症状**：Skill 存在，但 Claude 不使用

**原因**：
1. 描述不够具体
2. `enabled_skill_ids` 限制了其他 Skills
3. 请求与 Skill 不匹配

**解决**：
1. 改进 Skill 描述
2. 检查 `enabled_skill_ids` 配置
3. 测试更明确的请求

### 7.3 错误的 Skill 被选中

**症状**：Claude 使用了不相关的 Skill

**原因**：
1. Skill 描述太宽泛
2. 没有配置 `enabled_skill_ids`

**解决**：
1. 使用 `enabled_skill_ids` 限制可用 Skills
2. 改进 Skill 描述，更具体

---

## 总结

Claude SDK 选择 Skill 的完整流程：

```
1. 配置层 (你的代码)
   ├─ setting_sources: ["project"]  # 启用 Skill 加载
   ├─ enabled_skill_ids: [...]      # 过滤可用 Skills
   └─ allowed_tools: ["Skill"]      # 允许使用 Skill 工具

2. SDK 层 (Claude Agent SDK)
   ├─ 扫描 .claude/skills/
   ├─ 解析 SKILL.md
   ├─ 提取元数据 (name, description)
   └─ 存储到内存

3. AI 层 (Claude Model)
   ├─ 接收用户请求
   ├─ 检查可用 Skills
   ├─ 语义匹配 (request vs description)
   ├─ 检查 enabled_skill_ids 限制
   ├─ 加载完整 Skill 内容
   └─ 附加到 system prompt

4. 执行层 (Claude + Skill)
   ├─ 按照 Skill 指导工作
   ├─ 调用相关工具
   └─ 生成结果
```

**关键要点**：
- `setting_sources` 是开关：控制是否加载 Skills
- `enabled_skill_ids` 是过滤器：控制可以使用哪些 Skills
- `description` 是关键：决定 Claude 是否选择该 Skill
- `"Skill"` 必须在 `allowed_tools` 中：否则无法调用
