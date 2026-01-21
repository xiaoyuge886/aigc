# 贡献指南

感谢您考虑为 AIGC 智能 Agent 平台做出贡献！

## 🚀 快速开始

### 开发环境设置

详见 [README.md](README.md) 中的"快速开始"部分。

```bash
# 1. 克隆项目
git clone https://github.com/your-org/aigc-platform.git
cd aigc-platform

# 2. 设置后端环境
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 设置前端环境
cd ../frontend/aigc-frontend
npm install

# 4. 启动开发服务器
# 后端: cd backend && python main.py
# 前端: npm run dev
```

## 📝 代码风格

### Python
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 行长度不超过 120 字符
- 使用类型注解（Type Hints）

### TypeScript/React
- 使用 ESLint 配置
- 使用 2 空格缩进
- 遵循 React 最佳实践
- 组件使用函数式组件 + Hooks

## 🎯 提交规范

使用 Conventional Commits 规范：

- `feat:` 新功能
- `fix:` 问题修复
- `docs:` 文档更新
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构（不改变功能）
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建/工具链相关

### 提交示例

```bash
# 新功能
git commit -m "feat: 添加技能星系可视化组件"

# 问题修复
git commit -m "fix: 修复场景匹配器的缓存问题"

# 文档更新
git commit -m "docs: 更新部署文档"

# 重构
git commit -m "refactor: 优化 agent_service 的代码结构"
```

## 🔄 Pull Request 流程

### 1. Fork 并克隆

```bash
# 1. Fork 项目到你的 GitHub 账号
# 2. 克隆你的 fork
git clone https://github.com/your-username/aigc-platform.git
cd aigc-platform

# 3. 添加上游仓库
git remote add upstream https://github.com/original-org/aigc-platform.git
```

### 2. 创建特性分支

```bash
# 从 main 分支创建新分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### 3. 进行开发

```bash
# 进行你的更改...
# 确保遵循代码风格
# 运行测试（如果有）
# 更新相关文档
```

### 4. 提交更改

```bash
git add .
git commit -m "feat: 描述你的更改"
```

### 5. 推送到你的 fork

```bash
git push origin feature/your-feature-name
```

### 6. 创建 Pull Request

- 访问 GitHub 上的原始仓库
- 点击 "New Pull Request"
- 选择你的特性分支
- 填写 PR 模板
- 等待审查

## ✅ 代码审查清单

在提交 PR 之前，请确保：

- [ ] 代码符合项目的代码风格规范
- [ ] 包含适当的单元测试（如果适用）
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交信息遵循规范
- [ ] PR 描述清晰说明了更改内容
- [ ] 没有合并冲突

## 🐛 问题报告

使用 GitHub Issues 报告问题时，请提供：

### 必需信息
- 详细的问题描述
- 复现步骤
- 预期行为 vs 实际行为

### 可选但有帮助的信息
- 环境信息（OS、Python 版本、Node 版本）
- 相关日志或截图
- 最小化复现代码

### 问题报告模板

```markdown
### 问题描述
简要描述遇到的问题

### 复现步骤
1. 步骤 1
2. 步骤 2
3. ...

### 预期行为
描述你期望发生什么

### 实际行为
描述实际发生了什么

### 环境信息
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.11.5]
- Node: [e.g. 18.18.0]

### 相关日志
```
粘贴相关日志
```

### 截图
如果有界面问题，请提供截图
```

## 💡 功能建议

欢迎提出新的功能建议！在创建 Issue 之前：

1. 搜索现有的 Issues，避免重复
2. 清晰描述功能的使用场景
3. 说明为什么这个功能有价值
4. 如果可能，提供实现思路

## 🎨 技能开发

如果你想为项目贡献新的技能（Skill）：

### 技能目录结构

```
.claude/skills/your-skill/
├── skill.md           # 技能说明文档
├── guidance.py        # 执行逻辑（可选）
└── tests/            # 测试用例（可选）
```

### 技能开发指南

详见 [技能开发文档](develop_doc/docs/v0.8/v0.8-feat-doc.md)。

## 📜 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

## 🤝 行为准则

- 尊重不同的观点和经验
- 使用包容性的语言
- 优雅地接受建设性批评
- 专注于对社区最有利的事情
- 对其他社区成员表示同理心

## 📞 联系方式

如有任何问题，欢迎：
- 创建 [GitHub Issue](https://github.com/your-org/aigc-platform/issues)
- 参与 [GitHub Discussions](https://github.com/your-org/aigc-platform/discussions)

---

**再次感谢你的贡献！** 🎉
