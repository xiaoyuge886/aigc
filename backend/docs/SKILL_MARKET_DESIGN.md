# Skill Market 实现方案

## 📋 概述

参考 https://github.com/coreyhaines31/marketingskills 的设计思想，构建一个**在线技能市场**，支持：
- 技能上传和分享
- 技能浏览和安装
- 版本管理和更新
- 评价和统计系统

## 🎯 核心功能

### 1. 技能仓库 (Skill Repository)
- 技能包管理（类似 npm 包）
- 支持 GitHub 仓库集成
- 版本控制 (语义化版本)
- 技能依赖管理

### 2. 技能市场 (Skill Market)
- 技能浏览和搜索
- 分类和标签系统
- 技能详情页
- 评分和评论

### 3. 技能安装系统
- 一键安装到用户环境
- 自动依赖解析
- 技能启用/禁用
- 技能更新和卸载

## 📊 数据库设计

### 新增数据表

#### 1. `skill_packages` - 技能包表
```sql
CREATE TABLE skill_packages (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,           -- 技能包名称 (如: marketing-skills)
    identifier VARCHAR(200) UNIQUE NOT NULL,      -- 唯一标识 (如: coreyhaines31/marketing-skills)
    display_name VARCHAR(200),                    -- 显示名称
    description TEXT,                             -- 描述
    long_description TEXT,                        -- 详细描述 (Markdown)
    author_id INTEGER,                            -- 作者ID (外键到 users)
    category VARCHAR(50),                         -- 分类 (data-analysis, marketing, productivity, etc.)
    tags JSON,                                    -- 标签数组 ["seo", "cro", "analytics"]

    -- 版本信息
    current_version VARCHAR(20),                  -- 当前版本 (如: 1.0.0)
    repository_url VARCHAR(500),                  -- Git 仓库URL
    homepage_url VARCHAR(500),                    -- 主页URL
    documentation_url VARCHAR(500),               -- 文档URL

    -- 统计信息
    download_count INTEGER DEFAULT 0,             -- 下载次数
    install_count INTEGER DEFAULT 0,              -- 安装次数
    rating_average FLOAT DEFAULT 0,               -- 平均评分
    rating_count INTEGER DEFAULT 0,               -- 评分人数

    -- 状态
    is_featured BOOLEAN DEFAULT FALSE,            -- 是否精选
    is_official BOOLEAN DEFAULT FALSE,            -- 是否官方
    is_active BOOLEAN DEFAULT TRUE,               -- 是否激活
    visibility VARCHAR(20) DEFAULT 'public',      -- 可见性: public/private/unlisted

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,                        -- 首次发布时间

    FOREIGN KEY (author_id) REFERENCES users(id)
);
CREATE INDEX idx_skill_packages_name ON skill_packages(name);
CREATE INDEX idx_skill_packages_category ON skill_packages(category);
CREATE INDEX idx_skill_packages_author ON skill_packages(author_id);
```

#### 2. `skill_package_versions` - 技能包版本表
```sql
CREATE TABLE skill_package_versions (
    id INTEGER PRIMARY KEY,
    package_id INTEGER NOT NULL,                  -- 技能包ID (外键)
    version VARCHAR(20) NOT NULL,                 -- 版本号 (如: 1.0.0)
    changelog TEXT,                               -- 更新日志
    download_url VARCHAR(500),                    -- 下载URL (可以是 .tar.gz, .zip, 或 git tag)
    file_size INTEGER,                            -- 文件大小 (字节)
    checksum VARCHAR(64),                         -- SHA256 校验和
    min_agent_version VARCHAR(20),                -- 最小代理版本要求
    max_agent_version VARCHAR(20),                -- 最大代理版本要求

    -- 依赖管理
    dependencies JSON,                            -- 依赖其他技能包 [{"name": "base-skills", "version": ">=1.0.0"}]

    -- 安装信息
    install_command TEXT,                         -- 安装命令
    uninstall_command TEXT,                       -- 卸载命令

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
    UNIQUE(package_id, version)
);
CREATE INDEX idx_skill_versions_package ON skill_package_versions(package_id);
```

#### 3. `skill_items` - 单个技能表
```sql
CREATE TABLE skill_items (
    id INTEGER PRIMARY KEY,
    package_version_id INTEGER,                   -- 所属包版本 (外键，可为NULL表示内置技能)
    name VARCHAR(100) UNIQUE NOT NULL,            -- 技能名称 (如: page-cro)
    display_name VARCHAR(200),                    -- 显示名称
    description TEXT,                             -- 描述
    category VARCHAR(50),                         -- 分类

    -- 技能内容
    skill_content TEXT NOT NULL,                  -- 技能定义内容 (Markdown/JSON)
    skill_type VARCHAR(20) DEFAULT 'markdown',    -- 技能类型: markdown/json
    trigger_keywords JSON,                        -- 触发关键词 ["cro", "landing page", "conversion"]

    -- 使用统计
    use_count INTEGER DEFAULT 0,                  -- 使用次数

    -- 状态
    is_builtin BOOLEAN DEFAULT FALSE,             -- 是否内置技能
    is_active BOOLEAN DEFAULT TRUE,               -- 是否激活

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (package_version_id) REFERENCES skill_package_versions(id) ON DELETE SET NULL
);
CREATE INDEX idx_skill_items_name ON skill_items(name);
CREATE INDEX idx_skill_items_package ON skill_items(package_version_id);
```

#### 4. `user_installed_skills` - 用户已安装技能表
```sql
CREATE TABLE user_installed_skills (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,                     -- 用户ID (外键)
    package_id INTEGER NOT NULL,                  -- 技能包ID (外键)
    version_id INTEGER NOT NULL,                  -- 版本ID (外键)

    -- 安装信息
    installed_version VARCHAR(20),                -- 安装的版本号
    install_path VARCHAR(500),                    -- 安装路径
    is_enabled BOOLEAN DEFAULT TRUE,              -- 是否启用

    -- 更新信息
    has_update BOOLEAN DEFAULT FALSE,             -- 是否有更新
    last_check_at DATETIME,                       -- 最后检查更新时间

    -- 时间戳
    installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES skill_package_versions(id) ON DELETE CASCADE,
    UNIQUE(user_id, package_id)
);
CREATE INDEX idx_user_installed_skills_user ON user_installed_skills(user_id);
CREATE INDEX idx_user_installed_skills_package ON user_installed_skills(package_id);
```

#### 5. `skill_reviews` - 技能评价表
```sql
CREATE TABLE skill_reviews (
    id INTEGER PRIMARY KEY,
    package_id INTEGER NOT NULL,                  -- 技能包ID (外键)
    user_id INTEGER NOT NULL,                     -- 用户ID (外键)

    -- 评价内容
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),  -- 评分 1-5
    title VARCHAR(200),                           -- 评价标题
    content TEXT,                                 -- 评价内容

    -- 统计
    helpful_count INTEGER DEFAULT 0,              -- 有用投票数

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(package_id, user_id)  -- 每个用户对每个包只能评价一次
);
CREATE INDEX idx_skill_reviews_package ON skill_reviews(package_id);
CREATE INDEX idx_skill_reviews_user ON skill_reviews(user_id);
```

#### 6. `skill_usage_logs` - 技能使用日志表
```sql
CREATE TABLE skill_usage_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,                     -- 用户ID (外键)
    session_id VARCHAR(36),                       -- 会话ID (外键到 sessions)
    skill_name VARCHAR(100) NOT NULL,             -- 使用的技能名称

    -- 使用信息
    success BOOLEAN,                              -- 是否成功
    error_message TEXT,                           -- 错误信息
    execution_time_ms INTEGER,                    -- 执行时间 (毫秒)

    -- 时间戳
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_skill_usage_logs_user ON skill_usage_logs(user_id);
CREATE INDEX idx_skill_usage_logs_skill ON skill_usage_logs(skill_name);
CREATE INDEX idx_skill_usage_logs_time ON skill_usage_logs(used_at);
```

## 🔌 API 设计

### 1. 技能市场 API

#### GET /api/skills/market
**获取技能市场列表**
```json
// Query Parameters
{
  "category": "marketing",        // 可选：按分类筛选
  "search": "seo",               // 可选：搜索关键词
  "sort": "popular",             // 可选：排序方式 (popular/latest/rated/featured)
  "page": 1,
  "page_size": 20
}

// Response
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 1,
      "name": "marketing-skills",
      "identifier": "coreyhaines31/marketing-skills",
      "display_name": "Marketing Skills",
      "description": "Marketing skills for Claude Code...",
      "category": "marketing",
      "tags": ["seo", "cro", "analytics"],
      "current_version": "1.2.0",
      "author": {
        "id": 10,
        "username": "coreyhaines31",
        "avatar_url": "..."
      },
      "download_count": 1250,
      "rating_average": 4.8,
      "rating_count": 42,
      "is_featured": true,
      "published_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### GET /api/skills/market/{skill_id}
**获取技能详情**
```json
// Response
{
  "id": 1,
  "name": "marketing-skills",
  "identifier": "coreyhaines31/marketing-skills",
  "display_name": "Marketing Skills",
  "description": "Marketing skills for Claude Code...",
  "long_description": "# Marketing Skills\n\n...",
  "category": "marketing",
  "tags": ["seo", "cro", "analytics"],
  "current_version": "1.2.0",
  "repository_url": "https://github.com/coreyhaines31/marketingskills",
  "homepage_url": "https://example.com",
  "documentation_url": "https://docs.example.com",

  "author": {
    "id": 10,
    "username": "coreyhaines31",
    "avatar_url": "..."
  },

  "statistics": {
    "download_count": 1250,
    "install_count": 850,
    "rating_average": 4.8,
    "rating_count": 42
  },

  "versions": [
    {
      "version": "1.2.0",
      "changelog": "- Added new SEO skills\n- Fixed bugs",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],

  "reviews": {
    "total": 42,
    "average": 4.8,
    "items": [
      {
        "id": 1,
        "user": {
          "username": "john_doe",
          "avatar_url": "..."
        },
        "rating": 5,
        "title": "Amazing skills!",
        "content": "Helped me a lot with marketing...",
        "created_at": "2024-01-20T15:30:00Z"
      }
    ]
  },

  "is_installed": false,          // 当前用户是否已安装
  "has_update": false             // 是否有可用更新
}
```

#### POST /api/skills/market/{skill_id}/install
**安装技能包**
```json
// Request Body (可选)
{
  "version": "1.2.0"  // 可选：指定版本，默认安装最新版
}

// Response
{
  "id": 100,
  "package_id": 1,
  "version": "1.2.0",
  "status": "installed",
  "installed_skills": [
    "page-cro",
    "copywriting",
    "seo-audit"
  ]
}
```

#### POST /api/skills/market/{skill_id}/uninstall
**卸载技能包**
```json
// Response
{
  "status": "uninstalled"
}
```

#### POST /api/skills/market/{skill_id}/update
**更新技能包**
```json
// Response
{
  "status": "updated",
  "old_version": "1.1.0",
  "new_version": "1.2.0",
  "updated_skills": [...]
}
```

### 2. 技能管理 API (用户已安装技能)

#### GET /api/skills/installed
**获取用户已安装技能列表**
```json
// Response
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "package": {
        "id": 10,
        "name": "marketing-skills",
        "display_name": "Marketing Skills",
        "description": "...",
        "category": "marketing"
      },
      "installed_version": "1.2.0",
      "is_enabled": true,
      "has_update": false,
      "installed_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### PUT /api/skills/installed/{skill_id}
**更新已安装技能设置**
```json
// Request Body
{
  "is_enabled": false  // 启用/禁用
}

// Response
{
  "status": "updated"
}
```

### 3. 技能上传 API (创作者)

#### POST /api/skills/publish
**发布技能包**
```json
// Request Body (multipart/form-data)
{
  "name": "my-skills",
  "display_name": "My Custom Skills",
  "description": "My awesome skills",
  "long_description": "# My Skills\n\n...",
  "category": "productivity",
  "tags": ["automation", "productivity"],

  // 版本信息
  "version": "1.0.0",
  "changelog": "Initial release",

  // 仓库信息
  "repository_url": "https://github.com/user/my-skills",

  // 技能包文件
  "file": <binary>  // .tar.gz 或 .zip 文件
}

// Response
{
  "id": 20,
  "name": "my-skills",
  "identifier": "username/my-skills",
  "version": "1.0.0",
  "status": "published"
}
```

#### PUT /api/skills/{skill_id}
**更新技能包信息**
```json
// Request Body
{
  "description": "Updated description",
  "tags": ["new-tag"]
}

// Response
{
  "status": "updated"
}
```

#### POST /api/skills/{skill_id}/versions
**发布新版本**
```json
// Request Body (multipart/form-data)
{
  "version": "1.1.0",
  "changelog": "- Added new feature\n- Fixed bug",
  "file": <binary>
}

// Response
{
  "version_id": 105,
  "version": "1.1.0",
  "status": "published"
}
```

### 4. 评价和评论 API

#### POST /api/skills/{skill_id}/reviews
**添加评价**
```json
// Request Body
{
  "rating": 5,
  "title": "Amazing!",
  "content": "Very helpful..."
}

// Response
{
  "id": 50,
  "rating": 5,
  "title": "Amazing!",
  "content": "Very helpful...",
  "created_at": "2024-01-20T15:30:00Z"
}
```

#### GET /api/skills/{skill_id}/reviews
**获取评价列表**
```json
// Query Parameters
{
  "page": 1,
  "page_size": 10
}

// Response
{
  "total": 42,
  "items": [...]
}
```

## 🎨 前端界面设计

### 1. 技能市场页面

#### 技能市场首页
```
┌─────────────────────────────────────────────────────────────┐
│  🛒 Skill Market                           🔍 [搜索框]       │
├─────────────────────────────────────────────────────────────┤
│  分类: [全部] [营销] [数据分析] [SEO] [生产力] [开发工具]     │
│  排序: [热门] [最新] [评分最高] [精选]                        │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ 📦 Marketing    │  │ 📦 Data        │  │ 📦 SEO         │ │
│  │    Skills      │  │    Analysis    │  │    Tools      │ │
│  │                │  │                │  │                │ │
│  │ ⭐ 4.8 (42)    │  │ ⭐ 4.9 (128)   │  │ ⭐ 4.7 (35)    │ │
│  │ 📥 1.2k 下载   │  │ 📥 2.5k 下载   │  │ 📥 890 下载    │ │
│  │                │  │                │  │                │ │
│  │ Marketing      │  │ Advanced data  │  │ SEO and search │ │
│  │ skills for...  │  │ analysis...    │  │ optimization.. │ │
│  │                │  │                │  │                │ │
│  │    [安装]      │  │    [安装]      │  │    [安装]      │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ 📦 ...         │  │ 📦 ...         │  │ 📦 ...         │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 技能详情页
```
┌─────────────────────────────────────────────────────────────┐
│  🛒 Marketing Skills                                      ✅ │
├─────────────────────────────────────────────────────────────┤
│  作者: @coreyhaines31 | 分类: 营销                         │
│  ⭐ 4.8 (42 评价) | 📥 1,250 下载 | 📦 850 安装             │
│                                                             │
│  [安装] [更新] [卸载]                                       │
├─────────────────────────────────────────────────────────────┤
│  Marketing skills for Claude Code and AI agents.            │
│  CRO, copywriting, SEO, analytics, and growth engineering. │
├─────────────────────────────────────────────────────────────┤
│  📊 统计                                                    │
│  下载: 1,250 | 安装: 850 | 评分: 4.8/5.0                   │
├─────────────────────────────────────────────────────────────┤
│  📝 包含的技能                                              │
│  • page-cro - Landing page optimization                    │
│  • copywriting - Marketing copy generation                 │
│  • seo-audit - SEO auditing and analysis                   │
│  • analytics-tracking - Analytics setup                    │
│  • email-sequence - Email campaign creation                │
├─────────────────────────────────────────────────────────────┤
│  📚 版本历史                                                │
│  v1.2.0 (2024-01-15) - Added new SEO skills                │
│  v1.1.0 (2024-01-01) - Fixed bugs                          │
│  v1.0.0 (2023-12-15) - Initial release                     │
├─────────────────────────────────────────────────────────────┤
│  💬 评价 (42)                                               │
│  ⭐⭐⭐⭐⭐ Amazing skills! Helped me...                     │
│    - @john_doe (2天前)                                     │
└─────────────────────────────────────────────────────────────┘
```

### 2. 我的技能页面

```
┌─────────────────────────────────────────────────────────────┐
│  🎒 My Skills                                              │
├─────────────────────────────────────────────────────────────┤
│  [已安装] [已发布] [浏览全部]                               │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📦 Marketing Skills                      v1.2.0  ✅   │ │
│  │    Installed: 2024-01-15                              │ │
│  │    [启用] [更新] [卸载] [配置]                         │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📦 Data Analysis                        v2.1.0  🔄   │ │
│  │    Installed: 2024-01-10 | Update available: v2.2.0  │ │
│  │    [禁用] [更新到v2.2.0] [卸载] [配置]                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 实现步骤

### Phase 1: 数据模型和基础 API (1-2周)
- [ ] 创建数据库表
- [ ] 实现 SQLAlchemy 模型
- [ ] 实现基础 CRUD API
- [ ] 添加数据库迁移脚本

### Phase 2: 技能包管理 (1-2周)
- [ ] 实现技能包上传功能
- [ ] 实现技能包下载和安装
- [ ] 实现版本管理
- [ ] 添加依赖解析

### Phase 3: 市场界面 (1-2周)
- [ ] 构建技能市场页面
- [ ] 实现搜索和筛选
- [ ] 技能详情页
- [ ] 评价和评论系统

### Phase 4: 高级功能 (1-2周)
- [ ] 自动更新检测
- [ ] 技能使用统计
- [ ] 技能推荐算法
- [ ] 用户仪表板

### Phase 5: 安全和优化 (1周)
- [ ] 权限控制
- [ ] 文件上传安全
- [ ] 性能优化
- [ ] 缓存策略

## 🚀 快速开始示例

### 1. 创建数据库迁移
```python
# backend/models/skill_market.py
from sqlalchemy import ...
from models.database import Base

class SkillPackageDB(Base):
    __tablename__ = "skill_packages"
    # ... 实现模型
```

### 2. 实现 API 路由
```python
# backend/api/skill_market.py
from fastapi import APIRouter, Depends
from models.skill_market import *

router = APIRouter(prefix="/api/skills/market", tags=["skill-market"])

@router.get("/")
async def list_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    # ... 实现列表查询
    pass

@router.post("/{skill_id}/install")
async def install_skill(skill_id: int, current_user = Depends(get_current_user)):
    # ... 实现安装逻辑
    pass
```

### 3. 前端页面
```typescript
// frontend/src/pages/SkillMarket.tsx
export function SkillMarket() {
  const [skills, setSkills] = useState([]);

  useEffect(() => {
    fetch('/api/skills/market')
      .then(res => res.json())
      .then(data => setSkills(data.items));
  }, []);

  return (
    <div>
      <h1>Skill Market</h1>
      {skills.map(skill => (
        <SkillCard key={skill.id} skill={skill} />
      ))}
    </div>
  );
}
```

## 📚 参考资源

- [marketingskills](https://github.com/coreyhaines31/marketingskills) - 技能包结构参考
- [npm registry API](https://github.com/npm/registry) - 包管理API参考
- [VSCode Marketplace](https://marketplace.visualstudio.com/) - 市场UI参考
- [PyPI](https://pypi.org/) - Python包管理参考
