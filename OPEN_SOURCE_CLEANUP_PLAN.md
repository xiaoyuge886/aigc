# 开源整理计划

> 项目开源到 GitHub 前的代码整理清单
> **原则**：只清理和整理，不改变任何功能

## 📋 整理计划概览

本次整理分为 6 个阶段，预计需要 2-3 小时完成：

| 阶段 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| 🔐 阶段1 | 敏感信息清理 | 🔴 极高 | 30分钟 |
| 🗂️ 阶段2 | 目录结构优化 | 🟡 中 | 30分钟 |
| 🧹 阶段3 | 临时文件清理 | 🟡 中 | 20分钟 |
| 📝 阶段4 | 文档完善 | 🟢 低 | 30分钟 |
| ⚙️ 阶段5 | 配置文件规范化 | 🟡 中 | 20分钟 |
| ✅ 阶段6 | 最终检查 | 🔴 极高 | 20分钟 |

---

## 🔐 阶段1：敏感信息清理（极高优先级）

### 1.1 检查并清理所有 .env 文件

**需要检查的文件：**
- [ ] `/frontend/aigc-frontend/.env`
- [ ] `/deploy/.env`
- [ ] `/backend/.env`

**操作步骤：**
```bash
# 1. 检查 .env 文件内容
cat frontend/aigc-frontend/.env
cat deploy/.env
cat backend/.env

# 2. 如果存在真实的 API Key 或密钥，替换为示例值
# 3. 确保 .gitignore 包含所有 .env 文件

# 4. 只保留 .env.example 文件作为模板
```

**需要保留的示例文件：**
- ✅ `/backend/.env.example` - 已存在
- ✅ `/deploy/.env.example` - 已存在
- ➕ 需要创建 `/frontend/aigc-frontend/.env.example`

### 1.2 检查代码中的硬编码密钥

**搜索关键词：**
```bash
# 在 Python 代码中搜索
grep -r "sk-ant-" backend/
grep -r "API_KEY" backend/
grep -r "SECRET" backend/
grep -r "PASSWORD" backend/
grep -r "TOKEN" backend/

# 在前端代码中搜索
grep -r "sk-ant-" frontend/
grep -r "api_key" frontend/
grep -r "secret" frontend/
grep -r "password" frontend/
```

### 1.3 数据库文件检查

**需要清理的文件：**
```bash
# 检查是否有数据库文件包含了敏感数据
find backend/data -name "*.db" -o -name "*.sqlite*"
find data -name "*.db" -o -name "*.sqlite*"

# 确保以下目录在 .gitignore 中：
# - backend/data/*.db
# - data/
```

### 1.4 日志文件清理

**需要确认：**
```bash
# 确认 logs/ 目录在 .gitignore 中
# - logs/

# 清理可能存在的日志文件
find /Users/hehe/pycharm_projects/aigc -name "*.log" -type f
```

---

## 🗂️ 阶段2：目录结构优化（中优先级）

### 2.1 清理冗余的虚拟环境目录

**发现问题：**
- ❌ 存在两个虚拟环境：`.venv/` 和 `venv/`
- ✅ 应该只保留一个（推荐 `.venv/`）

**操作步骤：**
```bash
# 1. 确认两个虚拟环境都是本地创建的
ls -la .venv/
ls -la venv/

# 2. 删除多余的 venv/ 目录
rm -rf venv/

# 3. 确保 .gitignore 包含：
# .venv/
# venv/
```

### 2.2 修复 work_dir 嵌套问题

**发现问题：**
- ❌ 存在 `/work_dir/work_dir/` 嵌套结构
- ✅ 应该扁平化为 `/work_dir/`

**操作步骤：**
```bash
# 1. 检查嵌套目录内容
ls -la work_dir/work_dir/

# 2. 如果有文件，移动到上级目录
mv work_dir/work_dir/* work_dir/
rmdir work_dir/work_dir/

# 3. 确保 .gitignore 包含：
# work_dir
```

### 2.3 清理 deploy 目录的运行时文件

**需要清理的目录：**
```bash
# 这些目录应该在 .gitignore 中
deploy/data/
deploy/logs/
deploy/work_dir/

# 检查是否有不应该提交的文件
ls -la deploy/data/
ls -la deploy/logs/
ls -la deploy/work_dir/
```

### 2.4 目录命名规范化

**需要确认的命名：**
- ❌ `devolop_doc/` - 拼写错误（应为 `develop_doc/` 或 `dev_docs/`）
- ✅ 建议保持现状，避免破坏现有引用
- ➕ 或者创建软链接 `development_doc/` -> `devolop_doc/`

**推荐操作：**
```bash
# 暂时保持现状，在 README 中说明
# 如果一定要改，需要全局搜索替换所有引用
```

---

## 🧹 阶段3：临时文件清理（中优先级）

### 3.1 清理备份文件

**查找所有备份文件：**
```bash
# 查找 .bak, .backup, .old, .tmp 文件
find /Users/hehe/pycharm_projects/aigc -name "*.bak" -o -name "*.backup" -o -name "*.old" -o -name "*.tmp" | grep -v node_modules
```

**已发现的备份文件：**
- [ ] `frontend/aigc-frontend/App.tsx.bak`
- [ ] `frontend/aigc-frontend/ChatInterface.tsx.bak`
- [ ] `frontend/aigc-frontend/components/ChatInterface.tsx.bak`
- [ ] `frontend/aigc-frontend/components/Editor.tsx.bak`
- [ ] `frontend/aigc-frontend/components/SessionHistory.tsx.bak`

**操作步骤：**
```bash
# 删除所有 .bak 文件
find . -name "*.bak" -type f -delete

# 更新 .gitignore，添加：
# *.bak
# *.backup
```

### 3.2 清理 Python 缓存

**操作步骤：**
```bash
# 清理 __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 清理 .pyc 文件
find . -name "*.pyc" -delete

# 清理 .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
```

### 3.3 清理 IDE 临时文件

**操作步骤：**
```bash
# 清理 .DS_Store (macOS)
find . -name ".DS_Store" -delete

# 清理 .swp, .swo (vim)
find . -name "*.swp" -delete
find . -name "*.swo" -delete

# 确保 .gitignore 包含：
# .DS_Store
# Thumbs.db
# *.swp
# *.swo
```

### 3.4 清理前端的构建产物

**需要确认在 .gitignore 中：**
```
frontend/aigc-frontend/node_modules/
frontend/aigc-frontend/dist/
frontend/aigc-frontend/.next/
```

**检查是否有遗漏：**
```bash
ls -la frontend/aigc-frontend/dist/
ls -la frontend/aigc-frontend/.next/
```

---

## 📝 阶段4：文档完善（低优先级）

### 4.1 根目录文档检查

**已存在的文档：**
- ✅ `README.md` - 主文档
- ✅ `LICENSE` - 需要确认是否存在
- ❓ `CONTRIBUTING.md` - 贡献指南（建议添加）
- ❓ `CHANGELOG.md` - 变更日志（建议添加）

### 4.2 LICENSE 文件

**操作步骤：**
```bash
# 1. 检查是否已有 LICENSE 文件
ls -la LICENSE

# 2. 如果没有，创建 MIT License
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 AIGC Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### 4.3 CONTRIBUTING.md 贡献指南

**创建文件：**
```bash
cat > CONTRIBUTING.md << 'EOF'
# 贡献指南

感谢您考虑为 AIGC 智能 Agent 平台做出贡献！

## 开发环境设置

详见 [README.md](README.md) 中的"快速开始"部分。

## 代码风格

### Python
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 行长度不超过 120 字符

### TypeScript/React
- 使用 ESLint 配置
- 使用 2 空格缩进
- 遵循 React 最佳实践

## 提交规范

使用 Conventional Commits 规范：
- `feat:` 新功能
- `fix:` 问题修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链相关

示例：
```
feat: 添加技能星系可视化组件
fix: 修复场景匹配器的缓存问题
docs: 更新部署文档
```

## Pull Request 流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 代码审查

所有 PR 需要通过：
- ✅ 代码风格检查
- ✅ 单元测试通过
- ✅ 文档更新完整
- ✅ 至少一位维护者审查通过

## 问题报告

使用 GitHub Issues 报告问题时，请提供：
- 详细的问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（OS、Python 版本等）
- 相关日志或截图

---

**再次感谢您的贡献！** 🎉
EOF
```

### 4.4 部署文档检查

**已存在的文档：**
- ✅ `deploy/README.md` - 已更新
- ✅ `deploy/DOCKER_FIX.md` - Docker 问题修复指南

**需要检查的内容：**
- [ ] 所有命令示例都经过验证
- [ ] 环境变量说明完整
- [ ] 常见问题覆盖全面

---

## ⚙️ 阶段5：配置文件规范化（中优先级）

### 5.1 .gitignore 完善性检查

**当前 .gitignore 包含：**
- ✅ Python 相关
- ✅ Node.js 相关
- ✅ IDE 相关
- ✅ 数据库文件
- ✅ 日志文件
- ✅ 环境变量

**需要添加：**
```gitignore
# 备份文件
*.bak
*.backup
*.old
*.tmp
*.temp

# 测试覆盖率
.coverage
htmlcov/
.pytest_cache/

# 构建产物
build/
dist/

# 临时工作目录
work_dir/
*/work_dir
```

### 5.2 .dockerignore 检查

**检查 `/deploy/.dockerignore`：**
```bash
cat deploy/.dockerignore
```

**应该包含的内容：**
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.git/
.gitignore
.venv/
venv/
node_modules/
logs/
*.log
data/*.db
work_dir/
.env
.env.local
```

### 5.3 前端配置文件检查

**检查 `/frontend/aigc-frontend/.env.example`：**
```bash
# 需要创建这个文件
cat > frontend/aigc-frontend/.env.example << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
EOF
```

---

## ✅ 阶段6：最终检查（极高优先级）

### 6.1 敏感信息最终扫描

**使用专业工具扫描：**
```bash
# 使用 truffleHog 扫描
# pip install truffleHog
trufflehog --regex --entropy=False /Users/hehe/pycharm_projects/aigc

# 或使用 git-secrets
# git secrets --scan
```

**手动搜索确认：**
```bash
# 搜索常见 API 密钥格式
grep -r "sk-ant-" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "gsk_" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "AIza" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "xoxb-" . --exclude-dir=node_modules --exclude-dir=.git

# 搜索敏感词
grep -ri "password.*=.*[^$]" . --exclude-dir=node_modules --exclude-dir=.git | grep -v ".example"
grep -ri "secret.*=.*[^$]" . --exclude-dir=node_modules --exclude-dir=.git | grep -v ".example"
grep -ri "token.*=.*[^$]" . --exclude-dir=node_modules --exclude-dir=.git | grep -v ".example"
```

### 6.2 文件大小检查

**查找过大的文件：**
```bash
# 查找大于 10MB 的文件
find . -type f -size +10M -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.venv/*" -exec ls -lh {} \;
```

**需要特别注意：**
- 数据库文件（不应提交）
- 日志文件（不应提交）
- 模型文件（如 ML 模型，考虑使用 Git LFS）
- 构建产物（不应提交）

### 6.3 文件权限检查

**检查脚本文件是否可执行：**
```bash
# 查找 .sh 文件
find . -name "*.sh" -type f ! -executable

# 如果找到，添加执行权限
chmod +x deploy/*.sh
```

### 6.4 构建测试

**测试项目是否可以正常构建：**

**后端：**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --help  # 测试是否能正常启动
```

**前端：**
```bash
cd frontend/aigc-frontend
npm install
npm run build
```

**Docker：**
```bash
cd deploy
./deploy.sh build
```

### 6.5 Git 仓库检查

**检查 Git 配置：**
```bash
# 查看 Git 用户信息
git config user.name
git config user.email

# 检查 .gitattributes
cat .gitattributes

# 如果不存在，创建：
cat > .gitattributes << 'EOF'
# Auto detect text files and normalize line endings to LF
* text=auto

# Explicitly declare text files
*.py text
*.tsx text
*.ts text
*.jsx text
*.js text
*.json text
*.md text
*.yml text
*.yaml text

# Declare files that will always have CRLF line endings on checkout
*.bat text eol=crlf

# Denote all files that are truly binary and should not be modified
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
EOF
```

### 6.6 创建开源前的最后一次 Commit

**操作步骤：**
```bash
# 1. 检查当前状态
git status

# 2. 添加所有更改
git add .

# 3. 创建 commit
git commit -m "chore: 开源前代码整理

- 清理敏感信息和临时文件
- 优化目录结构
- 完善文档和配置文件
- 更新 .gitignore 和 .dockerignore

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 📝 GitHub 开源准备清单

### 7.1 创建 GitHub 仓库

**仓库设置：**
- [ ] 仓库名称：`aigc-platform`（或其他名称）
- [ ] 描述：`基于 Claude AI 的智能对话与任务执行平台，支持自定义技能生态和场景化 AI 解决方案`
- [ ] 可见性：**Public**
- [ ] 许可证：MIT License
- [ ] .gitignore：Python
- [ ] 主分支：`main`

### 7.2 推送到 GitHub

```bash
# 1. 添加远程仓库
git remote add origin https://github.com/your-username/aigc-platform.git

# 2. 推送主分支
git push -u origin main

# 3. 设置分支保护（可选）
# 在 GitHub 设置中：
# Settings -> Branches -> Add rule
# - Branch name pattern: main
# - ✅ Require a pull request before merging
# - ✅ Require status checks to pass before merging
```

### 7.3 仓库美化

**需要添加的内容：**
- [ ] **Repository Topics**（标签）
  - claude-ai
  - ai-agent
  - fastapi
  - react
  - docker
  - skills
  - intelligent-assistant

- [ ] **About** 部分
  - Website:（如果有）
  - Documentation: README.md
  - License: MIT

- [ ] **Issue Templates**
  - Bug Report
  - Feature Request
  - Question

- [ ] **PR Template**
  - 描述更改内容
  - 关联的 Issue
  - 测试情况

---

## 📊 整理进度追踪

### 阶段1：敏感信息清理
- [ ] 1.1 检查并清理 .env 文件
- [ ] 1.2 检查代码中的硬编码密钥
- [ ] 1.3 数据库文件检查
- [ ] 1.4 日志文件清理

### 阶段2：目录结构优化
- [ ] 2.1 清理冗余的虚拟环境
- [ ] 2.2 修复 work_dir 嵌套
- [ ] 2.3 清理运行时文件
- [ ] 2.4 目录命名规范化

### 阶段3：临时文件清理
- [ ] 3.1 清理备份文件
- [ ] 3.2 清理 Python 缓存
- [ ] 3.3 清理 IDE 临时文件
- [ ] 3.4 清理前端构建产物

### 阶段4：文档完善
- [ ] 4.1 根目录文档检查
- [ ] 4.2 创建 LICENSE
- [ ] 4.3 创建 CONTRIBUTING.md
- [ ] 4.4 部署文档检查

### 阶段5：配置文件规范化
- [ ] 5.1 .gitignore 完善
- [ ] 5.2 .dockerignore 检查
- [ ] 5.3 前端配置文件检查

### 阶段6：最终检查
- [ ] 6.1 敏感信息最终扫描
- [ ] 6.2 文件大小检查
- [ ] 6.3 文件权限检查
- [ ] 6.4 构建测试
- [ ] 6.5 Git 仓库检查
- [ ] 6.6 最后一次 Commit

---

## ⚠️ 重要提醒

1. **不要改变功能** - 只清理和整理，不修改代码逻辑
2. **备份重要数据** - 清理前先备份整个项目
3. **逐步验证** - 每个阶段完成后测试构建
4. **保留历史** - 不要使用 `git rebase` 或 `git filter-branch`
5. **团队同步** - 如果有团队，先沟通确认

---

## 🚀 开始执行

建议按顺序执行每个阶段，完成一个阶段后再进入下一个。

**预计总时间：** 2-3 小时

**准备好了？让我们开始吧！** 🎉
