# 动态 Agent 组合系统设计

## 核心场景

### 用户输入需求
```
用户: "我需要一个能分析销售数据并生成月度PPT报告的助手"
```

### 系统应该能够
1. **理解需求** → AI 分析用户意图
2. **匹配技能** → 推荐相关 Skills
3. **推荐场景** → 找到最匹配的 Template（如果有）
4. **动态组合** → 生成完整的 Agent 配置
5. **可视化预览** → 展示组合结果
6. **一键使用** → 立即开始对话或保存为 Agent

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  1. 用户输入需求                                             │
│     "我需要分析销售数据并生成月度PPT报告"                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. AI 需求分析引擎                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 输入：用户需求 + 可用的 Templates + 可用的 Skills      │   │
│  │                                                       │   │
│  │ 处理：                                                │   │
│  │  - 意图识别（分析数据、生成报告、导出PPT）            │   │
│  │  - 实体提取（销售数据、月度报告）                     │   │
│  │  - 能力映射（数据分析 → data-analysis）              │   │
│  │                                                       │   │
│  │ 输出：                                                │   │
│  │  - 推荐的 Templates（如果存在高度匹配的）             │   │
│  │  - 推荐的 Skills（带置信度分数）                     │   │
│  │  - 建议的 workflow（工作流程）                       │   │
│  │  - 推荐的配置参数                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. 智能匹配引擎                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Template 匹配：                                       │   │
│  │  - 语义搜索（需求 vs template.description）           │   │
│  │  - 标签匹配（需求关键词 vs template.tags）            │   │
│  │  - 技能重叠度（推荐 skills vs template.skills）       │   │
│  │                                                       │   │
│  │ Skill 匹配：                                          │   │
│  │  - 语义搜索（需求 vs skill.description）              │   │
│  │  - 类别匹配（数据分析 → analysis category）           │   │
│  │  - 协同过滤（其他用户常用的组合）                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 动态配置生成器                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 生成完整配置：                                         │   │
│  │  - system_prompt: 基于 template + skills 生成         │   │
│  │  - allowed_tools: 从 skills 聚合所需工具             │   │
│  │  - enabled_skill_ids: 选中的 skill ids               │   │
│  │  - workflow: 基于需求生成工作流步骤                   │   │
│  │  - parameters: temperature, max_turns 等             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 用户确认与调整                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 可视化展示：                                           │   │
│  │  ✅ 推荐的 Template: "销售趋势分析" (92% 匹配)         │   │
│  │  ✅ 推荐的 Skills:                                    │   │
│  │     - data-analysis (95%)                             │   │
│  │     - echarts-chart (88%)                             │   │
│  │     - pptx (82%)                                      │   │
│  │     - sql-query (75%)  [可选]                         │   │
│  │  ✅ 工作流预览:                                       │   │
│  │     1. 读取销售数据                                    │   │
│  │     2. 执行统计分析                                    │   │
│  │     3. 生成可视化图表                                  │   │
│  │     4. 创建 PPT 报告                                   │   │
│  │                                                       │   │
│  │ 用户操作：                                             │   │
│  │  - 添加/移除 Skills                                    │   │
│  │  - 调整 workflow 顺序                                  │   │
│  │  - 修改参数                                            │   │
│  │  - 预览对话效果                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  6. 创建并使用                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 选项 A: 立即开始对话                                   │   │
│  │  - 临时使用，不保存                                    │   │
│  │                                                       │   │
│  │ 选项 B: 保存为自定义 Agent                             │   │
│  │  - 输入名称: "我的销售报告助手"                        │   │
│  │  - 保存到 user_agents 表                              │   │
│  │  - 可以反复使用                                        │   │
│  │                                                       │   │
│  │ 选项 C: 发布到 Template Market                        │   │
│  │  - 分享给其他用户                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## API 设计

### 核心端点

```python
# 1. AI 分析需求
POST /api/v1/agents/analyze-requirement
Request:
{
    "requirement": "我需要分析销售数据并生成月度PPT报告",
    "preferences": {
        "include_charts": true,
        "export_format": "pptx",
        "complexity": "intermediate"
    }
}

Response:
{
    "analysis": {
        "intent": ["数据分析", "报告生成", "可视化"],
        "entities": ["销售数据", "月度", "PPT"]
    },

    # 推荐的 Templates
    "recommended_templates": [
        {
            "id": 5,
            "name": "销售趋势分析",
            "match_score": 0.92,
            "reason": "该模板专用于销售数据分析，包含数据查询、分析和可视化功能"
        },
        {
            "id": 1,
            "name": "财务报表分析",
            "match_score": 0.75,
            "reason": "虽然主要用于财务数据，但可以适配销售数据分析"
        }
    ],

    # 推荐的 Skills
    "recommended_skills": [
        {
            "id": 1,
            "name": "data-analysis",
            "category": "analysis",
            "confidence": 0.95,
            "reason": "核心数据分析能力，用于处理销售数据"
        },
        {
            "id": 2,
            "name": "echarts-chart",
            "category": "visualization",
            "confidence": 0.88,
            "reason": "生成可视化图表，展示销售趋势"
        },
        {
            "id": 3,
            "name": "pptx",
            "category": "export",
            "confidence": 0.82,
            "reason": "导出为PPT格式，生成月度报告"
        },
        {
            "id": 5,
            "name": "smart-query-analyzer",
            "category": "database",
            "confidence": 0.75,
            "reason": "可选：如果数据在数据库中，可用此技能进行SQL查询",
            "optional": true
        }
    ],

    # 建议的工作流
    "suggested_workflow": {
        "steps": [
            {
                "order": 1,
                "name": "数据获取",
                "skill": "smart-query-analyzer",
                "description": "从数据库查询销售数据"
            },
            {
                "order": 2,
                "name": "数据分析",
                "skill": "data-analysis",
                "description": "执行统计分析，计算关键指标"
            },
            {
                "order": 3,
                "name": "可视化",
                "skill": "echarts-chart",
                "description": "生成销售趋势图表"
            },
            {
                "order": 4,
                "name": "报告生成",
                "skill": "pptx",
                "description": "创建PPT报告，整合数据和图表"
            }
        ]
    },

    # 推荐的配置参数
    "suggested_config": {
        "temperature": 0.7,
        "max_turns": 50,
        "allowed_tools": ["Read", "Write", "Bash", "Skill"],
        "recommended_model": "claude-sonnet-4-5"
    }
}

# 2. 基于 AI 推荐创建 Agent
POST /api/v1/agents/from-ai-recommendation
Request:
{
    "name": "我的销售报告助手",
    "description": "自动分析销售数据并生成月度PPT报告",

    # 选择 Template 作为基础（可选）
    "template_id": 5,

    # 选择 Skills（从 AI 推荐中选）
    "selected_skills": [1, 2, 3],  # data-analysis, echarts-chart, pptx

    # 自定义工作流（可选，默认使用 AI 建议的）
    "workflow": {
        "steps": [...]
    },

    # 配置参数
    "config": {
        "temperature": 0.7,
        "max_turns": 50
    },

    # 选项
    "save_as_agent": true,        # 是否保存为 Agent
    "start_conversation": false   # 是否立即开始对话
}

Response:
{
    "agent_id": 123,
    "agent": {
        "id": 123,
        "name": "我的销售报告助手",
        "description": "自动分析销售数据并生成月度PPT报告",
        "config": {...}
    },
    "preview_url": "/agents/123/preview"
}

# 3. 预览 Agent（测试效果）
POST /api/v1/agents/{id}/preview
Request:
{
    "test_prompt": "帮我分析上个月的销售数据并生成报告"
}

Response:
{
    "conversation_id": "xyz",
    "response_preview": "好的，我将帮您分析上个月的销售数据...",
    "estimated_tokens": 1500,
    "estimated_time": "30s"
}
```

---

## AI 需求分析引擎实现

### 方案 1: 使用 Claude 分析

```python
class AgentCompositionEngine:
    """Agent 组合引擎"""

    async def analyze_requirement(
        self,
        requirement: str,
        preferences: Optional[dict] = None
    ) -> dict:
        """分析用户需求，推荐配置"""

        # 1. 获取可用的 Templates 和 Skills
        templates = await self.get_available_templates()
        skills = await self.get_available_skills()

        # 2. 构建 AI Prompt
        prompt = self._build_analysis_prompt(
            requirement=requirement,
            templates=templates,
            skills=skills,
            preferences=preferences
        )

        # 3. 调用 Claude 分析
        analysis = await self._call_claude(prompt)

        # 4. 解析和验证结果
        result = self._parse_analysis_result(analysis)

        return result

    def _build_analysis_prompt(
        self,
        requirement: str,
        templates: List[dict],
        skills: List[dict],
        preferences: Optional[dict]
    ) -> str:
        """构建分析 Prompt"""

        prompt = f"""
你是一个智能 Agent 配置专家。用户想要创建一个 Agent，请分析需求并推荐配置。

## 用户需求
{requirement}

## 用户偏好
{json.dumps(preferences, ensure_ascii=False) if preferences else "无"}

## 可用的 Agent Templates
{self._format_templates(templates)}

## 可用的 Skills
{self._format_skills(skills)}

## 你的任务

请分析用户需求，返回 JSON 格式的推荐配置：

```json
{{
    "analysis": {{
        "intent": ["意图1", "意图2", "意图3"],
        "entities": ["实体1", "实体2"],
        "complexity": "beginner|intermediate|advanced"
    }},

    "recommended_templates": [
        {{
            "id": 1,
            "name": "模板名称",
            "match_score": 0.95,
            "reason": "推荐理由（1-2句话）"
        }}
    ],

    "recommended_skills": [
        {{
            "id": 1,
            "name": "skill_name",
            "confidence": 0.95,
            "reason": "推荐理由",
            "optional": false
        }}
    ],

    "suggested_workflow": {{
        "steps": [
            {{
                "order": 1,
                "name": "步骤名称",
                "skill": "skill_name",
                "description": "步骤描述"
            }}
        ]
    }},

    "suggested_config": {{
        "temperature": 0.7,
        "max_turns": 50,
        "allowed_tools": ["Read", "Write", "Bash", "Skill"],
        "recommended_model": "claude-sonnet-4-5"
    }}
}}
```

## 注意事项

1. **匹配分数**：
   - 0.9-1.0: 高度匹配
   - 0.7-0.9: 中度匹配，可能需要调整
   - <0.7: 低匹配，不推荐

2. **Skills 选择**：
   - 优先选择匹配度最高的技能
   - 避免功能重复
   - 考虑技能之间的协同性
   - 标注可选技能（optional: true）

3. **Workflow 设计**：
   - 步骤顺序要合理
   - 每个步骤要明确指定使用的技能
   - 考虑数据流转

4. **复杂度评估**：
   - beginner: 1-2 个 skills, 简单工作流
   - intermediate: 3-4 个 skills, 中等工作流
   - advanced: 5+ skills, 复杂工作流

请返回纯 JSON，不要有其他文字。
"""
        return prompt

    def _format_templates(self, templates: List[dict]) -> str:
        """格式化 Templates 列表"""
        result = []
        for t in templates:
            result.append(f"""
- ID: {t['id']}
  名称: {t['name']}
  分类: {t['category']}
  描述: {t['description']}
  包含技能: {', '.join(t.get('skill_names', []))}
""")
        return '\n'.join(result)

    def _format_skills(self, skills: List[dict]) -> str:
        """格式化 Skills 列表"""
        result = []
        for s in skills:
            result.append(f"""
- ID: {s['id']}
  名称: {s['name']}
  分类: {s['category']}
  描述: {s['description']}
  标签: {', '.join(s.get('tags', []))}
""")
        return '\n'.join(result)

    async def _call_claude(self, prompt: str) -> str:
        """调用 Claude API"""
        from claude_agent_sdk import query
        from claude_agent_sdk import ClaudeAgentOptions

        options = ClaudeAgentOptions(
            system_prompt="你是一个专业的AI配置专家，擅长分析需求并推荐技术方案。",
            temperature=0.3  # 降低温度，获得更确定的结果
        )

        response = ""
        async for msg in query(prompt=prompt, options=options):
            if msg.content:
                response += msg.content

        return response

    def _parse_analysis_result(self, analysis: str) -> dict:
        """解析分析结果"""
        import json
        import re

        # 提取 JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', analysis, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = analysis.strip()

        # 解析 JSON
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ValueError(f"AI 返回的格式不正确: {e}")

        # 验证结果
        self._validate_analysis_result(result)

        return result

    def _validate_analysis_result(self, result: dict):
        """验证分析结果"""
        required_fields = [
            'analysis',
            'recommended_templates',
            'recommended_skills',
            'suggested_workflow',
            'suggested_config'
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(f"缺少必需字段: {field}")
```

---

## 前端交互流程

### 流程 1: 快速创建（自动模式）

```
┌────────────────────────────────────────────────────────┐
│  Step 1: 用户输入需求                                   │
│  ┌──────────────────────────────────────────────────┐ │
│  │  🤖 AI 智能创建                                    │ │
│  │  ┌────────────────────────────────────────────┐  │ │
│  │  │ "我需要分析销售数据并生成月度PPT报告"        │  │ │
│  │  │                                        │  │ │
│  │  └────────────────────────────────────────────┘  │ │
│  │                                     [分析需求]     │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 2: AI 展示推荐结果                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │  ✅ 推荐模板: "销售趋势分析" (匹配度 92%)          │ │
│  │                                                     │ │
│  │  ✅ 推荐技能:                                      │ │
│  │     ☑ data-analysis (95%)                         │ │
│  │     ☑ echarts-chart (88%)                         │ │
│  │     ☑ pptx (82%)                                  │ │
│  │     ☐ sql-query (75%) [可选]                      │ │
│  │                                                     │ │
│  │  ✅ 工作流:                                       │ │
│  │     1. 查询数据 → 2. 分析 → 3. 图表 → 4. PPT      │ │
│  │                                                     │ │
│  │  [调整配置] [立即使用] [保存为 Agent]             │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 3: 用户选择                                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │  - [立即使用] → 直接开始对话                      │ │
│  │  - [保存为 Agent] → 输入名称，保存                │ │
│  │  - [调整配置] → 进入编辑模式                      │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### 流程 2: 手动创建（专家模式）

```
┌────────────────────────────────────────────────────────┐
│  Step 1: 选择基础                                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │  选择创建方式：                                    │ │
│  │  ⚪ 从模板开始（推荐）                            │ │
│  │  ⚪ 从零开始（高级）                              │ │
│  │  ⚪ AI 辅助创建                                   │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 2: 选择 Skills（多选）                           │
│  ┌──────────────────────────────────────────────────┐ │
│  │  分类：                                           │ │
│  │  [数据分析] [可视化] [导出] [数据库]              │ │
│  │                                                     │ │
│  │  可用技能：                                        │ │
│  │  ☑ data-analysis      数据处理、分析、洞察        │ │
│  │  ☑ echarts-chart      ECharts 图表生成            │ │
│  │  ☑ pptx              PPT 制作和导出               │ │
│  │  ☐ smart-query       智能SQL查询                  │ │
│  │  ☐ excel-export      Excel 导出                  │ │
│  │                                                     │ │
│  │  已选择 (3): [data-analysis, echarts-chart, pptx] │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 3: 配置参数                                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Agent 名称: [我的销售报告助手____________]       │ │
│  │  描述:      [自动分析销售数据并生成报告________]  │ │
│  │                                                     │ │
│  │  Temperature:   [━━━━○━━━] 0.7                    │ │
│  │  Max Turns:     [50]                              │ │
│  │  Model:         [Claude Sonnet 4.5 ▼]            │ │
│  │                                                     │ │
│  │  允许的工具:                                       │ │
│  │  ☑ Read  ☑ Write  ☑ Bash  ☑ Skill               │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 4: 工作流配置（可选）                            │
│  ┌──────────────────────────────────────────────────┐ │
│  │  拖拽调整步骤顺序：                                │ │
│  │  ┌────────────────────────────────────────────┐  │ │
│  │  │ 1. [data-analysis] 数据分析      ↓  ↑      │  │ │
│  │  │ 2. [echarts-chart] 可视化       ↓  ↑      │  │ │
│  │  │ 3. [pptx] 导出报告              ↓  ↑      │  │ │
│  │  │                                        │  │ │
│  │  │  [添加步骤] [生成工作流]                 │  │ │
│  │  └────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│  Step 5: 预览并保存                                    │
│  ┌──────────────────────────────────────────────────┐ │
│  │  配置预览：                                        │ │
│  │  ✅ 名称: 我的销售报告助手                        │ │
│  │  ✅ 包含 3 个技能                                  │ │
│  │  ✅ 工作流: 3 个步骤                              │ │
│  │                                                     │ │
│  │  [预览对话效果] [保存 Agent] [取消]               │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 实际例子

### 例子 1: 简单需求
```
用户输入: "我需要一个能分析CSV数据的助手"

AI 分析:
{
    "recommended_templates": [
        {"id": 1, "name": "数据分析基础", "match_score": 0.95}
    ],
    "recommended_skills": [
        {"id": 1, "name": "data-analysis", "confidence": 0.98}
    ],
    "complexity": "beginner"
}

用户操作: 一键使用
```

### 例子 2: 中等复杂度
```
用户输入: "我需要监控数据库性能并生成周报"

AI 分析:
{
    "recommended_templates": [],  // 没有完全匹配的模板
    "recommended_skills": [
        {"id": 5, "name": "agent-sql-pro", "confidence": 0.92},
        {"id": 1, "name": "data-analysis", "confidence": 0.85},
        {"id": 3, "name": "pptx", "confidence": 0.78}
    ],
    "suggested_workflow": {
        "steps": [
            {"order": 1, "skill": "agent-sql-pro", "description": "查询性能指标"},
            {"order": 2, "skill": "data-analysis", "description": "分析性能趋势"},
            {"order": 3, "skill": "pptx", "description": "生成周报"}
        ]
    },
    "complexity": "intermediate"
}

用户操作: 调整 workflow，保存为 Agent
```

### 例子 3: 高度定制
```
用户输入: "我需要一个能自动监控GitHub仓库、分析代码质量、生成技术文档、并发送到Slack的助手"

AI 分析:
{
    "recommended_templates": [],  // 没有匹配的模板
    "recommended_skills": [
        {"id": 10, "name": "code-reviewer", "confidence": 0.90},
        {"id": 8, "name": "docs-management", "confidence": 0.85},
        {"id": 12, "name": "slack-integration", "confidence": 0.80},
        {"id": 1, "name": "data-analysis", "confidence": 0.75}
    ],
    "suggested_workflow": {
        "steps": [
            {"order": 1, "skill": "github-api", "description": "监控仓库变化"},
            {"order": 2, "skill": "code-reviewer", "description": "分析代码质量"},
            {"order": 3, "skill": "docs-management", "description": "生成技术文档"},
            {"order": 4, "skill": "slack-integration", "description": "发送通知"}
        ]
    },
    "complexity": "advanced"
}

用户操作: 调整 skills 顺序，自定义 workflow，保存并分享
```

---

## 技术实现要点

### 1. Skill 依赖关系处理
```python
# skills 表添加 dependencies 字段
{
    "name": "advanced-analytics",
    "dependencies": ["data-analysis", "echarts-chart"],
    "description": "依赖基础分析技能，提供高级分析功能"
}

# AI 在推荐时自动处理依赖
if user_selects("advanced-analytics"):
    auto_add_dependencies(["data-analysis", "echarts-chart"])
```

### 2. Skill 兼容性检查
```python
# 检查 skills 是否兼容
def check_skills_compatibility(skills: List[int]) -> bool:
    """
    检查选中的 skills 是否兼容
    - 工具冲突
    - 功能重复
    - 已知不兼容组合
    """
    # 实现兼容性检查逻辑
    pass
```

### 3. 智能工作流生成
```python
# 基于 skills 自动生成 workflow
def generate_workflow(skills: List[dict]) -> dict:
    """
    根据 skills 的依赖关系和类型，
    自动生成合理的 workflow
    """
    # 实现工作流生成逻辑
    pass
```

---

## 总结

### 核心能力

✅ **智能需求分析** - AI 理解用户意图
✅ **自动匹配技能** - 推荐最相关的 Skills
✅ **模板推荐** - 找到最合适的 Template
✅ **动态组合** - 灵活组合 Skills
✅ **工作流生成** - 自动生成执行步骤
✅ **可视化调整** - 用户可以手动调整
✅ **一键创建** - 快速使用或保存为 Agent

### 用户体验

```
新手: 输入需求 → AI 推荐 → 一键使用
进阶: 输入需求 → AI 推荐 → 调整 → 保存
专家: 手动选择 Skills → 自定义配置 → 保存
```

这个系统让用户可以用自然语言描述需求，然后自动生成合适的 Agent 配置，大大降低了使用门槛！
