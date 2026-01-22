# 前后端 Docker 部署指南

## 📋 概述

本目录包含完整的前后端 Docker 部署配置，包括：

**后端服务：**
- `Dockerfile`：后端多阶段构建配置（FastAPI + Python 3.11）
- 包含 Claude Code CLI 集成

**前端服务：**
- `Dockerfile.frontend`：前端多阶段构建配置（React + Nginx）
- `nginx.conf`：Nginx 反向代理配置

**服务编排：**
- `docker-compose.yml`：开发环境配置
- `docker-compose.prod.yml`：生产环境配置

**部署脚本：**
- `deploy.sh`：一键部署脚本（推荐）
- `build.sh`：构建后端镜像
- `build-frontend.sh`：构建前端镜像
- `run.sh`：快速启动后端容器

**配置文件：**
- `.env.example`：环境变量示例
- `.dockerignore`：构建忽略文件

---

## 🚀 快速开始

### 方法 1：使用一键部署脚本（推荐）

```bash
# 1. 创建环境变量文件
cd deploy
cp .env.example .env

# 2. 编辑 .env 文件，填写 ANTHROPIC_API_KEY
vim .env

# 3. 一键部署
./deploy.sh dev

# 其他命令
./deploy.sh prod              # 生产环境
./deploy.sh logs              # 查看日志
./deploy.sh status            # 查看状态
./deploy.sh stop              # 停止服务
./deploy.sh restart           # 重启服务
./deploy.sh clean             # 清理所有资源
./deploy.sh --help            # 查看帮助
```

### 方法 2：使用 Docker Compose

```bash
# 1. 创建环境变量文件
cd deploy
cp .env.example .env

# 2. 编辑 .env 文件
vim .env

# 3. 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法 3：手动构建和运行

```bash
# 构建后端镜像
./deploy/build.sh

# 构建前端镜像
./deploy/build-frontend.sh

# 运行后端
docker run -d \
  --name aigc-backend \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  aigc-backend:latest

# 运行前端
docker run -d \
  --name aigc-frontend \
  -p 3000:80 \
  --link aigc-backend:backend \
  aigc-frontend:latest
```

---

## 🔧 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
# 必需
ANTHROPIC_API_KEY=your-api-key-here

# 可选
FRONTEND_PORT=3000          # 前端端口
BACKEND_PORT=8000           # 后端端口
DEBUG=false                 # 调试模式
DEFAULT_MODEL=sonnet        # 默认模型
MAX_TURNS=20                # 最大对话轮数
DATABASE_URL=sqlite:///./data/aigc.db  # 数据库连接
```

完整配置项见 [`.env.example`](.env.example)

### 数据持久化

以下目录会自动创建并持久化：

```
deploy/
├── data/           # 数据库文件
├── work_dir/       # 工作目录（生成的文件）
└── logs/           # 日志文件
```

---

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | http://localhost:3000 | Web 界面 |
| **后端 API** | http://localhost:8000 | API 根路径 |
| **API 文档** | http://localhost:8000/docs | Swagger UI |
| **健康检查** | http://localhost:8000/health | 后端健康状态 |

---

## 📦 镜像特点

### 后端镜像（aigc-backend）

**多阶段构建：**
- **构建阶段**：安装所有依赖（Node.js、Python 包、Claude CLI）
- **运行阶段**：只包含运行时必需文件，减小镜像体积

**包含组件：**
- Python 3.11 Slim
- Node.js 18+
- Claude Code CLI（全局安装）
- 所有 Python 依赖

**优化措施：**
- 使用 slim 基础镜像
- 多阶段构建减小体积
- 清理 apt 缓存
- 健康检查（30s 间隔）

### 前端镜像（aigc-frontend）

**多阶段构建：**
- **构建阶段**：使用 Node.js 构建 React 应用（Vite）
- **运行阶段**：使用 Nginx Alpine 托管静态文件

**包含组件：**
- Nginx Alpine
- 优化的 React 构建产物

**Nginx 配置：**
- Gzip 压缩
- 静态资源缓存（1年）
- API 反向代理
- WebSocket/SSE 支持
- SPA 路由支持

---

## 🛠️ 开发环境 vs 生产环境

### 开发环境（docker-compose.yml）

```bash
./deploy.sh dev
# 或
docker-compose up -d
```

**特点：**
- 端口：前端 3000，后端 8000
- 无资源限制
- 容易调试
- 重启策略：unless-stopped

### 生产环境（docker-compose.prod.yml）

```bash
./deploy.sh prod
# 或
docker-compose -f docker-compose.prod.yml up -d
```

**特点：**
- 端口：前端 80/443，后端 8000
- 资源限制（2 CPU, 4GB RAM）
- 日志轮转（10MB x 3）
- 重启策略：always
- 日志级别：INFO

---

## 🔍 验证部署

### 健康检查

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000/health

# 检查服务状态
docker-compose ps
```

### 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 仅查看后端
docker-compose logs -f backend

# 仅查看前端
docker-compose logs -f frontend
```

### 进入容器

```bash
# 进入后端容器
docker exec -it aigc-backend bash

# 进入前端容器
docker exec -it aigc-frontend sh

# 验证 Claude CLI
docker exec aigc-backend claude --version
```

---

## 🐛 故障排查

### 1. 容器无法启动

```bash
# 查看详细日志
docker logs aigc-backend
docker logs aigc-frontend

# 检查环境变量
docker exec aigc-backend env | grep ANTHROPIC
```

### 2. 前端无法访问后端 API

```bash
# 检查网络连接
docker exec aigc-frontend ping backend

# 检查 nginx 配置
docker exec aigc-frontend cat /etc/nginx/conf.d/default.conf
```

### 3. Claude CLI 不可用

```bash
# 检查 CLI 是否安装
docker exec aigc-backend which claude

# 检查版本
docker exec aigc-backend claude --version
```

### 4. 数据库权限问题

```bash
# 确保数据目录有写权限
chmod -R 777 deploy/data/
```

### 5. 端口冲突

修改 `.env` 文件中的端口配置：

```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

---

## 🔄 更新和升级

### 更新代码

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
./deploy/build.sh
./deploy/build-frontend.sh

# 3. 重启服务
./deploy.sh restart
```

### 完全重新部署

```bash
# 1. 停止并清理
./deploy.sh clean

# 2. 重新构建
./deploy.sh build

# 3. 启动服务
./deploy.sh dev
```

---

## 📊 监控和维护

### 资源使用情况

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
du -sh deploy/data deploy/work_dir deploy/logs
```

### 日志管理

```bash
# 清理日志
docker-compose logs --tail=0 -f

# 手动清理
rm -rf deploy/logs/*.log
```

### 数据备份

```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz deploy/data/ deploy/work_dir/

# 恢复数据
tar -xzf backup-20250116.tar.gz
```

---

## 🔐 安全建议

1. **API 密钥安全**
   - 不要将 `.env` 文件提交到版本控制
   - 使用 Docker secrets 管理敏感信息
   - 定期轮换 API 密钥

2. **网络安全**
   - 生产环境使用 HTTPS
   - 配置防火墙规则
   - 限制 API 访问来源

3. **数据安全**
   - 定期备份数据库
   - 使用强密码
   - 启用访问日志

4. **更新维护**
   - 及时更新依赖包
   - 定期更新基础镜像
   - 关注安全漏洞公告

---

## 📝 高级配置

### 使用 PostgreSQL 替代 SQLite

修改 `docker-compose.yml`，添加数据库服务：

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: aigc
      POSTGRES_USER: aigc
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
    networks:
      - aigc-network

  backend:
    environment:
      - DATABASE_URL=postgresql://aigc:${DB_PASSWORD}@postgres:5432/aigc
```

### 配置 HTTPS

使用 Let's Encrypt 和 Certbot：

```bash
# 1. 安装 certbot
apt-get install certbot python3-certbot-nginx

# 2. 获取证书
certbot --nginx -d yourdomain.com

# 3. 自动续期
certbot renew --dry-run
```

---

## 📖 参考文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Nginx 配置指南](https://nginx.org/en/docs/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)

---

**文档版本**：v2.0
**最后更新**：2026-01-16
**维护者**：AIGC Team
