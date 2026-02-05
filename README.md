# AIGC 智能 Agent 平台

> 基于 Claude AI 的智能对话与任务执行平台，支持自定义技能生态和场景化 AI 解决方案

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-green.svg)](https://reactjs.org/)

---

## 🎯 项目简介

AIGC 智能 Agent 平台是一个强大的 AI 应用框架，通过集成 Claude AI 模型和丰富的技能生态系统，为用户提供智能化、场景化的 AI 解决方案。平台采用前后端分离架构，支持多租户、会话管理、技能扩展等企业级特性。

### 核心特性

- **🤖 Claude AI 深度集成** - 基于最新的 Claude API，支持 Sonnet、Opus、Haiku 等多种模型
- **🧠 技能星系（Skill Galaxy）** - 可视化技能生态，以脑图形式展示和管理 AI 能力
- **🎨 场景化智能匹配** - 根据用户需求自动匹配最合适的 AI 场景，提供精准服务
- **🔌 丰富的技能插件** - 内置 15+ 专业技能，涵盖数据分析、代码开发、文档管理等多个领域
- **⚙️ 自定义场景配置** - 管理员可灵活配置 AI 行为、工具权限、系统提示词等
- **👥 多用户会话管理** - 支持多用户、多会话，提供完整的对话历史和反馈机制

---

## 先睹为快

![AIGC 平台首页](http://yiqixueba.top:19000/agentic/index.png)

![AIGC 平台对话](http://yiqixueba.top:19000/agentic/chat.png)

---


## 🎬 视频演示

观看完整的功能演示视频：

[![AIGC 平台演示](https://img.shields.io/badge/视频演示-B站-FF69B4.svg)](https://www.bilibili.com/video/BV16cr2BYEdc/)

**[📺 点击观看完整演示视频](https://www.bilibili.com/video/BV16cr2BYEdc/)**

---

## ✨ 技能

### 🌟 内置技能

#### 数据分析与可视化
- **data-analysis** - 数据清洗、统计分析、洞察生成
- **echarts_chart** - ECharts 图表生成专家
- **smart_query_analyzer** - 智能问数分析，自动生成 SQL

#### 开发工具
- **agent-sql-pro** - SQL 查询优化与数据库设计专家
- **frontend-design** - UI/UX 设计转前端代码
- **pptx** - PowerPoint 演示文稿生成与编辑

#### 效率工具
- **meta_agent** - 综合智能代理，自主决策与反思
- **x_agent_skill** - 跨域分析助手，商业智能专家
- **joyagent_skill** - SOP 驱动的智能分析助手
- **todo-master** - 专业的任务规划与管理
- **planning_first** - 强制先规划后执行的思考框架

#### 基础设施
- **minio_uploader** - MinIO 文件上传工具
- **whodb** - 多数据库操作（PostgreSQL、MySQL、MongoDB 等）
- **docs-management** - Claude 官方文档管理与解析



---

## 🎭 场景化 AI 解决方案

平台支持**自定义场景**（Custom Scenarios），让 AI 能够适应不同的业务需求：

### 场景匹配引擎

通过 [ScenarioMatcher](backend/services/scenario_matcher.py) 实现：

1. **智能分析** - 使用 Claude 模型分析用户意图
2. **自动匹配** - 从可用场景中选择最合适的
3. **上下文注入** - 自动加载场景专属的配置和提示词

### 场景配置项

每个场景可以独立配置：

- 🎯 **系统提示词** - 定义 AI 的角色和行为准则
- 🔧 **工具权限** - 控制可用的工具和技能
- ⚙️ **模型参数** - 选择使用的 Claude 模型（Sonnet/Opus/Haiku）
- 🎨 **UI 主题** - 自定义前端展示样式
- 📊 **数据源** - 关联特定的数据库或知识库

### 预置场景

平台内置多个常用场景：

| 场景名称 | 描述 | 适用模型 |
|---------|------|----------|
| **通用助手** | 全能型 AI 助手，支持日常对话和任务执行 | Sonnet |
| **代码专家** | 代码开发、调试、优化和文档生成 | Opus |
| **数据分析师** | 数据查询、分析和可视化 | Sonnet |
| **文档创作者** - | 技术文档、报告、PPT 生成 | Sonnet |
| **行业研究员** | 深度行业研究和市场分析 | Opus |

---

## 🏗️ 技术架构

### 前端架构（React + TypeScript）

```
frontend/aigc-frontend/
├── components/
│   ├── ChatInterface.tsx          # 主聊天界面
│   ├── SkillGalaxy.tsx            # 技能星系可视化
│   ├── ScenarioSelector.tsx       # 场景选择器
│   ├── AdminDashboard.tsx         # 管理员控制台
│   ├── ScenarioEditor.tsx         # 场景编辑器
│   └── SessionHistory.tsx         # 会话历史
├── services/
│   └── api.ts                     # API 客户端
└── App.tsx                        # 应用入口
```

**核心技术栈：**
- React 18 + TypeScript
- Vite 构建工具
- TailwindCSS 样式框架
- Zustand 状态管理
- React Query 数据请求

### 后端架构（FastAPI + Python）

```
backend/
├── api/v1/
│   ├── endpoints.py               # API 路由
│   ├── platform.py               # 场景配置 API
│   └── auth.py                   # 用户认证
├── services/
│   ├── agent_service.py          # Agent 核心服务
│   ├── scenario_matcher.py       # 场景匹配引擎
│   ├── scenario_provider.py      # 场景数据提供
│   ├── configuration_manager.py  # 配置管理
│   └── database.py               # 数据库服务
├── models/
│   ├── platform.py               # 场景模型
│   └── database.py               # 数据模型
└── main.py                       # 应用入口
```

**核心技术栈：**
- FastAPI Web 框架
- SQLAlchemy ORM
- Claude Agent SDK
- SQLite / PostgreSQL 数据库
- Pydantic 数据验证

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose（可选）

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/your-org/aigc-platform.git
cd aigc-platform

# 2. 安装后端依赖
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 ANTHROPIC_API_KEY

# 4. 启动后端服务
cd backend
python main.py

# 5. 安装前端依赖（新终端）
cd frontend/aigc-frontend
npm install

# 6. 启动前端服务
npm run dev
```

访问 http://localhost:5173 开始使用

### Docker 部署（推荐）

```bash
# 使用一键部署脚本
cd deploy
cp .env.example .env
# 编辑 .env 文件
./deploy.sh dev
```

详细部署指南请参考 [部署文档](deploy/README.md)

---

## 📖 核心功能使用指南

### 1. 技能星系使用

```typescript
// 在聊天界面中启用技能
import { SkillGalaxy } from './components/SkillGalaxy';

<SkillGalaxy
  onSkillSelect={(skill) => console.log('选中技能:', skill)}
  activeSkills={['data-analysis', 'echarts_chart']}
/>
```

### 2. 创建自定义场景

通过管理员控制台创建场景：

```python
# backend/services/scenario_provider.py
scenario = {
    "name": "金融分析助手",
    "description": "专注于金融数据分析和投资建议",
    "system_prompt": "你是一位专业的金融分析师...",
    "model": "sonnet",
    "tools": ["data-analysis", "echarts_chart"],
    "max_turns": 30,
    "permission_mode": "autoConfirm"
}
```

### 3. API 调用示例

```bash
# 创建会话
curl -X POST http://localhost:8000/api/v1/session/create \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": 1}'

# 发送消息
curl -X POST http://localhost:8000/api/v1/session/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "xxx",
    "prompt": "分析2024年A股市场趋势",
    "enable_skills": ["data-analysis", "echarts_chart"]
  }'
```

---

## 🎯 应用场景

### 企业级应用

- **📊 智能数据分析** - 快速生成数据报告和可视化图表
- **💻 代码开发助手** - 代码生成、重构、调试和文档编写
- **📝 文档自动生成** - 技术文档、API 文档、用户手册
- **🎨 UI/UX 设计** - 设计稿转前端代码、样式生成

### 行业解决方案

- **💰 金融行业** - 市场分析、风险评估、投资建议
- **🏥 医疗健康** - 医疗文献分析、诊断辅助
- **🏭 制造业** - 生产数据分析、质量检测
- **🌾 农业** - 农业数据分析、种植建议

---

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `ANTHROPIC_API_KEY` | Claude API 密钥 | - | ✅ |
| `DEFAULT_MODEL` | 默认模型 | `sonnet` | ❌ |
| `MAX_TURNS` | 最大对话轮数 | `20` | ❌ |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./data/aigc.db` | ❌ |
| `FRONTEND_PORT` | 前端端口 | `3000` | ❌ |
| `BACKEND_PORT` | 后端端口 | `8000` | ❌ |

### 技能配置

技能定义在 `.claude/skills/` 目录下，每个技能包含：

```
.claude/skills/your-skill/
├── skill.md           # 技能说明文档
├── guidance.py        # 执行逻辑
└── tests/            # 测试用例
```

详细开发指南请参考 [技能开发文档](devolop_doc/docs/v0.8/v0.8-feat-doc.md)

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下流程：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- **代码风格**：遵循 PEP 8 (Python) 和 ESLint (TypeScript)
- **提交信息**：使用 Conventional Commits 规范
- **测试要求**：新功能需要包含单元测试
- **文档更新**：更新相关文档和示例

---

## 📚 相关文档

- [部署指南](deploy/README.md) - Docker 部署详细说明
- [API 文档](http://localhost:8000/docs) - Swagger UI 自动生成
- [开发文档](devolop_doc/docs/) - 架构设计和开发指南
- [技能开发教程](devolop_doc/docs/v0.8/) - 如何开发自定义技能
- [故障排查](deploy/DOCKER_FIX.md) - 常见问题解决
- [黄金走势报告设计示例](http://yiqixueba.top:19000/agentic/%E9%BB%84%E9%87%91%E8%B5%B0%E5%8A%BF%E6%8A%A5%E5%91%8A_Apple%E8%AE%BE%E8%AE%A1.html) - Apple 设计风格的报告生成示例

---

## 📄 开源协议

本项目采用 MIT 协议开源。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude AI 模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [React](https://reactjs.org/) - 用户界面库
- [Vite](https://vitejs.dev/) - 下一代前端构建工具

---

## 📮 联系我们

- **Issues**: [GitHub Issues](https://github.com/your-org/aigc-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/aigc-platform/discussions)
- **Email**: support@aigc-platform.dev

---

<div align="center">

**Made with ❤️ by the AIGC Team**

[⬆ 返回顶部](#aigc-智能-agent-平台)

</div>
