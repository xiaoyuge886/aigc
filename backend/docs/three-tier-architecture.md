# 三级架构设计：Subject - Scenario - Skill

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Subject (业务领域/主题)                    │
│                     最高层级：业务分类                        │
│  例如：数据分析、内容创作、技术开发、客户服务、财务管理...     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Scenario (应用场景)                        │
│                   中间层级：具体使用场景                      │
│  例如：财务报表分析、销售趋势分析、技术文档写作...            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Skill (原子技能)                         │
│                    底层层级：可复用能力单元                   │
│  例如：data-analysis、echarts-chart、pptx、sql-query...      │
└─────────────────────────────────────────────────────────────┘
```

---

## 层级定义与职责

### Level 1: Subject (业务领域/主题)

**定义**：最高层级的业务分类，代表一个完整的业务领域

**特征**：
- 抽象程度最高
- 不包含具体配置
- 只用于分类和组织
- 一个 Subject 包含多个相关的 Scenarios

**数据模型**：
```sql
CREATE TABLE business_subjects (
    id INT PRIMARY KEY,
    name VARCHAR(200) UNIQUE,          -- 例如："数据分析"、"内容创作"
    code VARCHAR(50) UNIQUE,           -- 例如："data-analysis"、"content-creation"
    description TEXT,
    icon VARCHAR(500),                 -- 图标 URL
    color VARCHAR(20),                 -- 主题色
    order_index INT DEFAULT 0,         -- 显示顺序

    -- 元数据
    metadata JSON,                     -- tags, capabilities, keywords

    -- 统计
    scenario_count INT DEFAULT 0,      -- 包含的场景数量

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,

    created_at DATETIME,
    updated_at DATETIME
);
```

**示例 Subjects**：
1. **数据分析** (data-analysis)
   - 描述：处理、分析、可视化数据的各种场景

2. **内容创作** (content-creation)
   - 描述：文档写作、内容生成、编辑优化

3. **技术开发** (tech-development)
   - 描述：代码开发、调试、技术方案设计

4. **商业智能** (business-intelligence)
   - 描述：商业决策支持、市场分析、竞品分析

5. **客户服务** (customer-service)
   - 描述：客户咨询、问题解答、服务支持

---

### Level 2: Scenario (应用场景)

**定义**：Subject 下的具体使用场景，是可配置的 Agent 模板

**特征**：
- 中等抽象程度
- 包含完整的 Agent 配置
- 可直接使用，也可作为自定义 Agent 的基础
- 一个 Scenario 属于一个 Subject，包含多个 Skills

**数据模型**（扩展现有的 BusinessScenarioDB）：
```sql
CREATE TABLE business_scenarios (
    id INT PRIMARY KEY,

    -- 关联 Subject
    subject_id INT,                    -- 所属的业务领域

    -- Scenario 元数据
    name VARCHAR(200),                 -- 例如："财务报表分析"、"销售趋势分析"
    code VARCHAR(50) UNIQUE,           -- 唯一标识码
    description TEXT,
    thumbnail VARCHAR(500),            -- 预览图

    -- Scenario 配置（完整的 Agent 配置）
    system_prompt TEXT,
    allowed_tools JSON,                -- ["Read", "Write", "Bash", "Skill"]
    enabled_skill_ids JSON,            -- [1, 5, 8] (Skill IDs)
    custom_tools JSON,                 -- MCP server configs
    workflow JSON,                     -- 工作流定义

    -- Agent 行为参数
    recommended_model VARCHAR(50),     -- "claude-sonnet-4-5"
    temperature FLOAT DEFAULT 0.7,
    max_turns INT DEFAULT 50,

    -- 高优先级参数
    permission_mode VARCHAR(50),       -- "restricted", "flexible"
    work_dir VARCHAR(500),

    -- 元数据
    metadata JSON,                     -- tags, capabilities, examples

    -- 统计
    usage_count INT DEFAULT 0,
    rating_avg FLOAT DEFAULT 0,
    rating_count INT DEFAULT 0,

    -- 所有权
    created_by INT,
    is_public BOOLEAN DEFAULT FALSE,
    is_official BOOLEAN DEFAULT FALSE, -- 官方模板

    created_at DATETIME,
    updated_at DATETIME,

    FOREIGN KEY (subject_id) REFERENCES business_subjects(id)
);
```

**示例 Scenarios**：

#### Subject: 数据分析
1. **财务报表分析**
   - Skills: [data-analysis, echarts-chart, pptx, excel-export]
   - Workflow: 读取数据 → 分析 → 生成图表 → 导出报告

2. **销售趋势分析**
   - Skills: [data-analysis, smart-query-analyzer, echarts-chart]
   - Workflow: SQL查询 → 趋势分析 → 预测 → 可视化

3. **客户行为分析**
   - Skills: [data-analysis, joyagent-skill, minio-uploader]
   - Workflow: 数据加载 → 分群分析 → 行为洞察 → 报告

#### Subject: 内容创作
1. **技术文档写作**
   - Skills: [docs-management, meta-agent, markdown-editor]
   - Workflow: 需求分析 → 大纲生成 → 内容撰写 → 格式化

2. **营销文案生成**
   - Skills: [meta-agent, creative-writing, seo-optimizer]
   - Workflow: 产品分析 → 角色设定 → 文案生成 → SEO优化

3. **学术论文辅助**
   - Skills: [docs-management, scientific-critical-thinking, citation-manager]
   - Workflow: 文献检索 → 论文阅读 → 观点提取 → 写作辅助

---

### Level 3: Skill (原子技能)

**定义**：最小的可复用能力单元，提供特定功能的 prompt 和工具配置

**特征**：
- 最小抽象程度（原子化）
- 高度可复用
- 不绑定具体场景
- 可组合使用
- 包含具体的执行逻辑和工具使用指导

**数据模型**（现有的 SkillDB，无需修改）：
```sql
CREATE TABLE skills (
    id INT PRIMARY KEY,

    -- Skill 元数据
    name VARCHAR(200),                 -- 例如："data-analysis"
    code VARCHAR(50) UNIQUE,           -- 唯一标识（用于 SDK 加载）
    description TEXT,
    category VARCHAR(50),              -- 分类：analysis, coding, research...

    -- Skill 内容
    skill_content TEXT,                -- SKILL.md 内容（prompt）
    skill_config JSON,                 -- skill.json（工具配置）

    -- 依赖关系
    dependencies JSON,                 -- 依赖的其他 skills

    -- 元数据
    metadata JSON,                     -- tags, capabilities, examples

    -- 统计
    usage_count INT DEFAULT 0,
    install_count INT DEFAULT 0,
    rating_avg FLOAT DEFAULT 0,
    rating_count INT DEFAULT 0,

    -- 所有权
    created_by INT,
    is_public BOOLEAN DEFAULT FALSE,
    is_official BOOLEAN DEFAULT FALSE, -- 官方技能

    created_at DATETIME,
    updated_at DATETIME
);
```

**示例 Skills**：

1. **data-analysis** (数据分析)
   - 描述：数据加载、清洗、统计分析、洞察提取
   - 工具：Pandas, NumPy, Read, Write

2. **echarts-chart** (图表生成)
   - 描述：使用 ECharts 生成各种数据可视化图表
   - 工具：ECharts 配置生成

3. **pptx** (PPT制作)
   - 描述：创建、编辑 PowerPoint 演示文稿
   - 工具：python-pptx

4. **smart-query-analyzer** (智能SQL查询)
   - 描述：自然语言转 SQL，数据检索
   - 工具：agent-sql-pro

5. **docs-management** (文档管理)
   - 描述：文档索引、搜索、检索
   - 工具：docs-management skill

6. **meta-agent** (元代理)
   - 描述：任务规划、多工具协调
   - 工具：全工具集

---

## 三级关系图

```
Subject: 数据分析 (ID: 1)
│
├─ Scenario: 财务报表分析 (ID: 1)
│  ├─ Skill: data-analysis (ID: 1)
│  ├─ Skill: echarts-chart (ID: 2)
│  ├─ Skill: pptx (ID: 3)
│  └─ Skill: excel-export (ID: 4)
│
├─ Scenario: 销售趋势分析 (ID: 2)
│  ├─ Skill: data-analysis (ID: 1)           ← 复用
│  ├─ Skill: smart-query-analyzer (ID: 5)
│  └─ Skill: echarts-chart (ID: 2)           ← 复用
│
└─ Scenario: 客户行为分析 (ID: 3)
   ├─ Skill: data-analysis (ID: 1)           ← 复用
   ├─ Skill: joyagent-skill (ID: 6)
   └─ Skill: minio-uploader (ID: 7)


Subject: 内容创作 (ID: 2)
│
├─ Scenario: 技术文档写作 (ID: 4)
│  ├─ Skill: docs-management (ID: 8)
│  ├─ Skill: meta-agent (ID: 9)
│  └─ Skill: markdown-editor (ID: 10)
│
└─ Scenario: 营销文案生成 (ID: 5)
   ├─ Skill: meta-agent (ID: 9)              ← 复用
   ├─ Skill: creative-writing (ID: 11)
   └─ Skill: seo-optimizer (ID: 12)
```

---

## 组合关系 vs 继承关系

### Scenario 和 Skill 的关系：**组合关系**
```
Scenario = base_config + [Skill_1, Skill_2, ...] + workflow
```

**特点**：
- Scenario 是一个"配置模板"
- Scenario 可以包含多个 Skills
- Skills 可以被多个 Scenarios 复用
- 移除一个 Skill 不会影响 Scenario 的其他部分

### User Agent 和 Scenario 的关系：**继承 + 扩展**
```
UserAgent = Scenario基础配置 + 用户自定义覆盖 + 自选Skills
```

**特点**：
- User Agent 基于 Scenario 创建
- 用户可以：
  - 选择一个 Scenario 作为起点
  - 添加/移除 Skills
  - 调整配置参数
  - 自定义工作流

---

## API 设计

### Subject APIs
```python
GET  /api/v1/subjects                    # 获取所有业务领域
GET  /api/v1/subjects/{id}               # 获取领域详情（含 Scenarios）
GET  /api/v1/subjects/{id}/scenarios     # 获取领域下的所有场景
```

### Scenario APIs
```python
GET  /api/v1/scenarios                   # 获取所有场景（支持按 subject 过滤）
GET  /api/v1/scenarios/{id}              # 获取场景详情
POST /api/v1/scenarios                   # 创建场景（管理员）
PUT  /api/v1/scenarios/{id}              # 更新场景
```

### Skill APIs
```python
GET  /api/v1/skills                      # 获取所有技能
GET  /api/v1/skills/{id}                 # 获取技能详情
GET  /api/v1/skills/market               # 技能市场
POST /api/v1/skills/{id}/install         # 安装技能
```

### User Agent APIs
```python
POST /api/v1/agents                      # 创建自定义 Agent
GET  /api/v1/agents                      # 获取用户的 Agents
GET  /api/v1/agents/{id}                 # 获取 Agent 详情
PUT  /api/v1/agents/{id}                 # 更新 Agent
POST /api/v1/agents/{id}/chat            # 使用 Agent 对话
```

---

## 使用示例

### 示例1：用户基于 Scenario 创建 Agent
```python
POST /api/v1/agents
{
    "name": "我的财务分析助手",
    "scenario_id": 1,                    # 基于场景创建
    "skill_ids": [1, 2, 3],              # 选择技能（可选，默认使用场景的）
    "custom_config": {
        "temperature": 0.5,
        "max_turns": 100
    }
}
```

### 示例2：用户从零创建 Agent
```python
POST /api/v1/agents
{
    "name": "自定义数据分析助手",
    "subject_id": 1,                     # 选择业务领域（用于分类）
    "skill_ids": [1, 5, 7],              # 手动选择技能
    "system_prompt": "你是一个专业的数据分析师...",
    "allowed_tools": ["Read", "Write", "Skill"]
}
```

### 示例3：AI 辅助创建 Agent
```python
POST /api/v1/agents/ai-create
{
    "requirement": "我需要一个能分析销售数据并生成月度报告的助手",
    "preferences": {
        "include_charts": true,
        "export_to_ppt": true
    }
}

# AI 返回建议
{
    "suggested_scenario_id": 2,          # 推荐场景
    "suggested_skills": [1, 2, 3],       # 推荐技能
    "suggested_workflow": [...],         # 推荐工作流
    "reason": "根据您的需求，推荐使用'销售趋势分析'场景..."
}
```

---

## 数据库迁移

### 添加 Subject 表
```sql
-- 创建 business_subjects 表
CREATE TABLE business_subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(500),
    color VARCHAR(20),
    order_index INTEGER DEFAULT 0,
    metadata JSONB,
    scenario_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入初始数据
INSERT INTO business_subjects (name, code, description, icon, color, order_index) VALUES
('数据分析', 'data-analysis', '数据处理、分析、可视化相关的各种场景', '📊', '#3B82F6', 1),
('内容创作', 'content-creation', '文档写作、内容生成、编辑优化相关场景', '✍️', '#8B5CF6', 2),
('技术开发', 'tech-development', '代码开发、调试、技术方案设计相关场景', '💻', '#10B981', 3),
('商业智能', 'business-intelligence', '商业决策支持、市场分析相关场景', '🎯', '#F59E0B', 4),
('客户服务', 'customer-service', '客户咨询、问题解答、服务支持相关场景', '🤝', '#EC4899', 5);
```

### 修改 Scenario 表
```sql
-- 添加 subject_id 字段
ALTER TABLE business_scenarios
ADD COLUMN subject_id INTEGER REFERENCES business_subjects(id);

-- 更新现有数据（根据 category 推断 subject_id）
UPDATE business_scenarios
SET subject_id = (
    CASE
        WHEN category IN ('analysis', 'data', 'statistics') THEN 1
        WHEN category IN ('writing', 'content', 'document') THEN 2
        WHEN category IN ('coding', 'development', 'tech') THEN 3
        WHEN category IN ('business', 'marketing', 'sales') THEN 4
        WHEN category IN ('service', 'support') THEN 5
        ELSE 1  -- 默认数据分析
    END
);
```

---

## 前端展示结构

```
首页
└─ 业务领域选择
   ├─ 📊 数据分析
   │  ├─ 财务报表分析 [官方模板]
   │  ├─ 销售趋势分析 [官方模板]
   │  ├─ 客户行为分析 [官方模板]
   │  └─ + 我的自定义场景...
   │
   ├─ ✍️ 内容创作
   │  ├─ 技术文档写作 [官方模板]
   │  ├─ 营销文案生成 [官方模板]
   │  └─ + 我的自定义场景...
   │
   └─ 💻 技术开发
      ├─ 代码审查助手 [官方模板]
      ├─ Bug 调试助手 [官方模板]
      └─ + 我的自定义场景...
```

---

## 总结

### 三级架构的核心价值

1. **Subject（业务领域）**
   - 作用：分类、组织、导航
   - 用户价值：快速找到相关的场景
   - 不包含配置，只用于分类

2. **Scenario（应用场景）**
   - 作用：开箱即用的 Agent 模板
   - 用户价值：一键使用，或作为自定义起点
   - 包含完整配置，可直接运行

3. **Skill（原子技能）**
   - 作用：可复用的能力单元
   - 用户价值：灵活组合，构建个性化 Agent
   - 最小单元，高度复用

### 关键区别

| 维度 | Subject | Scenario | Skill |
|------|---------|----------|-------|
| 抽象程度 | 最高（分类） | 中等（模板） | 最低（单元） |
| 是否可执行 | ❌ | ✅ | ⚠️（需组合） |
| 是否可复用 | ❌ | ✅ | ✅（高度复用） |
| 包含配置 | ❌ | ✅ 完整配置 | ✅ 部分配置 |
| 用户操作 | 浏览、选择 | 使用、自定义 | 安装、组合 |

这个三级架构使得系统既有**开箱即用的便利性**（Scenario），又有**无限的灵活性和可扩展性**（Skill 组合）。
