# 两套技能存储系统的关系与区别

## 🔍 发现：系统中存在两套技能存储系统

### 系统 1：老系统 - `skills` 表（SkillDB）

**位置**：
- 模型：`backend/models/database.py` 第 353-387 行
- API：`backend/api/v1/platform.py` 第 1558-1850+ 行
- 路径：`/api/v1/skills`（注意：不是 `/skills/market`）

**表结构**：
```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),                    -- 技能名称
    description TEXT,                     -- 描述
    category VARCHAR(50),                 -- 分类
    skill_content TEXT,                   -- SKILL.md 内容
    skill_config JSON,                    -- skill.json 配置
    usage_count INTEGER DEFAULT 0,        -- 使用次数
    is_default BOOLEAN DEFAULT FALSE,     -- 是否默认技能
    created_by INTEGER,                   -- 创建者
    is_public BOOLEAN DEFAULT FALSE,      -- 是否公开
    created_at DATETIME,
    updated_at DATETIME
);
```

**API 端点**：
```python
# 简单的 CRUD
POST   /api/v1/skills         # 创建技能（管理员）
GET    /api/v1/skills         # 列表
GET    /api/v1/skills/{id}    # 详情
PUT    /api/v1/skills/{id}    # 更新
DELETE /api/v1/skills/{id}    # 删除
```

**使用场景**：
- 管理员预定义的系统技能
- 配置到 `business_scenarios` 表中
- 通过 `scenario.skills` 字段引用

---

### 系统 2：新系统 - `skill_market` 相关表

**位置**：
- 模型：`backend/models/skill_market.py`
- API：`backend/api/skill_market.py`
- 路径：`/api/v1/skills/market`

**表结构**（6 张表）：
```sql
-- 1. 技能包主表
CREATE TABLE skill_packages (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),                    -- 包名
    identifier VARCHAR(200),               -- 唯一标识
    display_name VARCHAR(200),
    description TEXT,
    long_description TEXT,
    author_id INTEGER,
    category VARCHAR(50),
    tags JSON,
    current_version VARCHAR(20),
    download_count INTEGER DEFAULT 0,
    install_count INTEGER DEFAULT 0,
    rating_average FLOAT DEFAULT 0.0,
    is_featured BOOLEAN,
    is_official BOOLEAN,
    is_active BOOLEAN,
    visibility VARCHAR(20),                -- public/private/unlisted
    source_type VARCHAR(50),               -- upload/github/url
    created_at DATETIME
);

-- 2. 版本管理
CREATE TABLE skill_package_versions (
    id INTEGER PRIMARY KEY,
    package_id INTEGER,
    version VARCHAR(20),
    changelog TEXT,
    download_url VARCHAR(500),
    dependencies JSON,
    created_at DATETIME
);

-- 3. 单个技能项
CREATE TABLE skill_items (
    id INTEGER PRIMARY KEY,
    package_id INTEGER,
    package_version_id INTEGER,
    name VARCHAR(100),                     -- 技能名称
    display_name VARCHAR(200),
    description TEXT,
    skill_content TEXT,                    -- 技能内容
    skill_type VARCHAR(20),                -- markdown/json
    trigger_keywords JSON,
    use_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at DATETIME
);

-- 4. 用户安装记录
CREATE TABLE user_installed_skills (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    package_id INTEGER,
    version_id INTEGER,
    installed_version VARCHAR(20),
    install_path VARCHAR(500),
    is_enabled BOOLEAN,
    custom_config JSON,
    has_update BOOLEAN,
    installed_at DATETIME
);

-- 5. 评价系统
CREATE TABLE skill_reviews (
    id INTEGER PRIMARY KEY,
    package_id INTEGER,
    user_id INTEGER,
    rating INTEGER,
    title VARCHAR(200),
    content TEXT,
    helpful_count INTEGER DEFAULT 0,
    created_at DATETIME
);

-- 6. 使用日志
CREATE TABLE skill_usage_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_id VARCHAR(36),
    skill_name VARCHAR(100),
    skill_id INTEGER,
    success BOOLEAN,
    error_message TEXT,
    execution_time_ms INTEGER,
    user_query TEXT,
    agent_response TEXT,
    used_at DATETIME
);
```

**API 端点**：
```python
# 技能市场
GET    /api/v1/skills/market              # 市场列表
GET    /api/v1/skills/market/{id}         # 市场详情
POST   /api/v1/skills/market              # 创建技能包
PUT    /api/v1/skills/market/{id}         # 更新技能包

# 安装管理
POST   /api/v1/skills/market/{id}/install # 安装
DELETE /api/v1/skills/market/{id}/install # 卸载
GET    /api/v1/skills/installed           # 已安装列表
PUT    /api/v1/skills/installed/{id}      # 更新设置

# 技能项
GET    /api/v1/skills/items/{id}          # 技能项详情
GET    /api/v1/skills/items/name/{name}   # 按名称获取

# 使用日志
GET    /api/v1/skills/logs                # 使用日志
POST   /api/v1/skills/debug               # 调试

# 统计
GET    /api/v1/skills/stats               # 市场统计
```

**使用场景**：
- 用户从市场安装技能包
- 技能包包含多个技能项
- 支持版本管理、评价、分享
- 详细的统计和日志

---

## 🔑 核心区别对比

| 维度 | 老系统 (skills) | 新系统 (skill_market) |
|------|----------------|---------------------|
| **设计理念** | 简单存储 | 完整市场生态 |
| **表数量** | 1 张 | 6 张 |
| **层级结构** | 扁平（单个技能） | 分层（包 → 版本 → 技能项） |
| **权限模型** | 管理员创建 | 用户可创建 |
| **版本管理** | ❌ 无 | ✅ 完整 |
| **评价系统** | ❌ 无 | ✅ 有 |
| **安装机制** | ❌ 无 | ✅ 有 |
| **使用日志** | ❌ 只有计数 | ✅ 详细日志 |
| **分享功能** | ❌ 无 | ✅ public/private/unlisted |
| **来源管理** | ❌ 无 | ✅ upload/github/url |
| **依赖管理** | ❌ 无 | ✅ 有 |

---

## 📊 数据关系图

```
┌─────────────────────────────────────────────────────┐
│           老系统：skills 表                           │
│  ┌─────────────────────────────────────────────┐   │
│  │ id: 1                                        │   │
│  │ name: "data-analysis"                       │   │
│  │ skill_content: "..."                        │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  用途：                                             │
│  - 管理员预定义系统技能                            │
│  - 配置到 business_scenarios.skills                │
└─────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────┐
│        新系统：skill_market 表体系                   │
│                                                     │
│  skill_packages (技能包)                            │
│  ┌─────────────────────────────────────────────┐   │
│  │ id: 10                                       │   │
│  │ name: "marketing-skills"                    │   │
│  │ identifier: "user/marketing-skills"          │   │
│  │                                             │   │
│  │ skill_package_versions (版本)                │   │
│  │ ┌──────────────────────────────────────┐   │   │
│  │ │ id: 100, version: "1.0.0"            │   │   │
│  │ │                                     │   │   │
│  │ │ skill_items (技能项)                 │   │   │
│  │ │ ┌─────────────────────────────────┐ │   │   │
│  │ │ │ id: 1000                        │ │   │   │
│  │ │ │ name: "seo-optimization"        │ │   │   │
│  │ │ │ skill_content: "..."            │ │   │   │
│  │ │ └─────────────────────────────────┘ │   │   │
│  │ │                                     │   │   │
│  │ │ ┌─────────────────────────────────┐ │   │   │
│  │ │ │ id: 1001                        │ │   │   │
│  │ │ │ name: "cro-optimization"        │ │   │   │
│  │ │ │ skill_content: "..."            │ │   │   │
│  │ │ └─────────────────────────────────┘ │   │   │
│  │ └──────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  user_installed_skills (用户安装记录)               │
│  skill_reviews (评价)                               │
│  skill_usage_logs (使用日志)                         │
└─────────────────────────────────────────────────────┘
```

---

## 🤔 它们的关系

### 1. **独立系统，无直接关联**

```python
# 老系统：直接使用 skills 表
from models.database import SkillDB

scenario = BusinessScenarioDB(
    ...
    skills = ["data-analysis", "pptx"]  # 引用技能名称
)

# 新系统：通过安装使用
from models.skill_market import SkillPackageDB, UserInstalledSkillDB

# 用户安装技能包
installed = UserInstalledSkillDB(
    user_id = 1,
    package_id = 10,  # marketing-skills
    is_enabled = True
)
```

### 2. **可能的混淆点**

**API 路径冲突**：
```python
# 老系统
GET /api/v1/skills          # 列表（从 skills 表）
GET /api/v1/skills/{id}     # 详情（从 skills 表）

# 新系统
GET /api/v1/skills/market            # 市场列表（从 skill_packages 表）
GET /api/v1/skills/market/{id}       # 市场详情（从 skill_packages 表）
GET /api/v1/skills/installed         # 已安装列表
```

**路径前缀相同**，可能造成混淆！

---

## 💡 使用建议

### 场景 1：系统预定义技能（使用老系统）

**适用情况**：
- 官方提供的基础技能
- 不需要版本管理
- 管理员维护

**示例**：
```python
# 1. 管理员创建技能
POST /api/v1/skills
{
    "name": "data-analysis",
    "description": "数据分析技能",
    "category": "analysis",
    "skill_content": "# Data Analysis\n...",
    "is_public": True,
    "is_default": True
}

# 2. 配置到场景
scenario = BusinessScenarioDB(
    name = "数据分析场景",
    skills = ["data-analysis", "echarts-chart", "pptx"]
)
```

### 场景 2：用户自定义技能市场（使用新系统）

**适用情况**：
- 用户创建和分享技能
- 需要版本管理
- 需要评价和统计
- 社区驱动

**示例**：
```python
# 1. 用户发布技能包
POST /api/v1/skills/market
{
    "name": "my-marketing-skills",
    "identifier": "user123/marketing-skills",
    "description": "营销技能包",
    "category": "marketing",
    "tags": ["seo", "cro", "analytics"]
}

# 2. 其他用户安装
POST /api/v1/skills/market/10/install

# 3. 使用时动态加载
user_skills = await get_user_installed_skills(user_id)
await dynamic_skill_loader.sync_skills(user_skills)
```

---

## 🔄 迁移建议

### 选项 A：保持两套系统（推荐）

**理由**：
- 老系统：系统核心技能，稳定可靠
- 新系统：用户扩展技能，灵活丰富

**分工**：
```
skills 表（老系统）
    ↓ 提供核心技能
系统稳定性 + 基础功能

skill_market 表（新系统）
    ↓ 提供扩展技能
社区生态 + 个性化
```

### 选项 B：统一到新系统（复杂）

**迁移步骤**：
1. 将 `skills` 表的数据迁移到 `skill_packages`
2. 为每个 skill 创建一个 package
3. 更新 `business_scenarios.skills` 引用
4. 废弃老的 API

**风险**：工作量大，可能破坏现有功能

### 选项 C：API 层统一（推荐）

**实现**：
```python
# 统一的技能查询 API
@router.get("/skills/unified")
async def list_unified_skills(
    current_user: UserDB = Depends(get_current_user)
):
    """返回所有可用技能（系统 + 已安装的市场技能）"""

    # 1. 获取系统技能（从 skills 表）
    system_skills = await get_system_skills()

    # 2. 获取用户安装的市场技能（从 skill_items 表）
    installed_skills = await get_user_installed_skills(current_user.id)

    # 3. 合并返回
    return {
        "system_skills": system_skills,
        "installed_market_skills": installed_skills,
        "all_skills": system_skills + installed_skills
    }
```

---

## 🎯 当前实际使用情况

### 在代码中的使用

**老系统**（platform.py）：
```python
# 配置管理器中使用
scenario.skills = ["data-analysis", "pptx"]  # 字符串数组，引用 skills.name
```

**新系统**（skill_market.py）：
```python
# 用户安装后通过 session 使用
installed = UserInstalledSkillDB(user_id=1, package_id=10)
# 使用时需要动态加载到文件系统
```

### Agent SDK 集成

**当前问题**：
- Agent SDK 从文件系统（`.claude/skills/`）加载
- `skills` 表的数据没有自动同步到文件系统
- `skill_items` 表的数据也没有同步

**需要实现**：
```python
class UnifiedSkillLoader:
    """统一的技能加载器"""

    async def load_all_skills(self, user_id: int):
        """加载所有可用技能"""

        # 1. 从 skills 表加载系统技能
        system_skills = await self.load_system_skills()

        # 2. 从 skill_items 表加载用户安装的市场技能
        market_skills = await self.load_market_skills(user_id)

        # 3. 生成 .claude/skills/ 目录结构
        for skill in system_skills + market_skills:
            self.write_skill_to_filesystem(skill)

        return [s.name for s in system_skills + market_skills]
```

---

## 📋 总结

### 关键区别

| 特性 | 老系统 (skills) | 新系统 (skill_market) |
|------|----------------|---------------------|
| **复杂度** | 简单（1 表） | 复杂（6 表） |
| **创建者** | 仅管理员 | 所有用户 |
| **版本管理** | ❌ | ✅ |
| **分享功能** | ❌ | ✅ |
| **评价系统** | ❌ | ✅ |
| **使用统计** | 简单计数 | 详细日志 |
| **适用场景** | 系统核心技能 | 用户自定义技能 |

### 使用建议

1. **保持两套系统共存**
2. **老系统**：用于系统预定义的核心技能
3. **新系统**：用于用户扩展和社区分享
4. **API 层统一**：提供统一的查询接口
5. **动态加载**：实现 UnifiedSkillLoader，将两者都加载到文件系统

### 当前问题

⚠️ **两套系统没有打通！**
- 老系统的技能在 `skills` 表
- 新系统的技能在 `skill_items` 表
- Agent SDK 只能从文件系统加载
- **缺少同步机制**

需要实现：将两套系统的技能都动态加载到 `.claude/skills/` 目录。

---

## 🚀 下一步行动

### 立即做

1. **统一技能查询 API**
   - 创建 `/api/v1/skills/unified` 端点
   - 返回系统技能 + 用户安装的市场技能

2. **实现统一加载器**
   - `UnifiedSkillLoader` 类
   - 从两个表读取技能
   - 统一生成 `.claude/skills/` 结构

### 长期规划

3. **评估是否需要迁移**
   - 如果两套系统长期共存，需要在 API 层统一
   - 如果决定统一，需要数据迁移方案

4. **文档说明**
   - 明确告诉用户什么时候用哪个系统
   - 提供清晰的使用指南

要我帮你实现统一的技能加载器吗？这样可以打通两套系统，让 Agent 能够使用所有技能（系统 + 市场）。
