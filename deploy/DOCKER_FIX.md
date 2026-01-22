# Docker Hub 镜像拉取 403 错误解决方案

## 问题描述

```
failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0:
failed to create LLB definition: unexpected status code [manifests 3.11-slim]: 403 Forbidden
```

这是 Docker Hub 在国内网络环境的访问限制问题。

---

## 🚀 解决方案

### 方案 1：配置 Docker 镜像加速器（推荐）

**macOS (Docker Desktop):**

1. 打开 Docker Desktop
2. 点击设置 (Settings/Preferences)
3. 选择 "Docker Engine"
4. 在配置文件中添加：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://docker.anyhub.us.kg",
    "https://dockerhub.jobcher.com"
  ]
}
```

5. 点击 "Apply & Restart"

**Linux 系统:**

```bash
# 编辑 Docker 配置
sudo vim /etc/docker/daemon.json

# 添加以下内容
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live"
  ]
}

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
docker info | grep -A 10 "Registry Mirrors"
```

**Windows (Docker Desktop):**

1. 右键点击任务栏 Docker 图标
2. 选择 "Settings"
3. 选择 "Docker Engine"
4. 添加上面的 registry-mirrors 配置
5. 点击 "Apply & Restart"

---

### 方案 2：使用 Alpine 版本镜像

Alpine 镜像更小且通常更容易拉取：

```bash
# 使用 Alpine 版本的 Dockerfile
docker build -f deploy/Dockerfile.alpine -t aigc-backend:latest .
```

修改 `deploy/docker-compose.yml`:

```yaml
backend:
  build:
    context: ..
    dockerfile: deploy/Dockerfile.alpine  # 改用 alpine 版本
```

---

### 方案 3：手动拉取镜像

如果某个镜像一直拉取失败，可以尝试手动拉取：

```bash
# 尝试从不同源拉取
docker pull docker.m.daocloud.io/library/python:3.11-slim
docker pull docker.m.daocloud.io/library/nginx:alpine

# 重新标记镜像
docker tag docker.m.daocloud.io/library/python:3.11-slim python:3.11-slim
docker tag docker.m.daocloud.io/library/nginx:alpine nginx:alpine
```

---

### 方案 4：使用代理（如果有）

```bash
# 配置 Docker 使用代理
sudo mkdir -p /etc/systemd/system/docker.service.d

sudo vim /etc/systemd/system/docker.service.d/http-proxy.conf
```

添加内容：

```ini
[Service]
Environment="HTTP_PROXY=http://your-proxy:port"
Environment="HTTPS_PROXY=http://your-proxy:port"
Environment="NO_PROXY=localhost,127.0.0.1"
```

重启 Docker：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 🔍 验证配置

配置镜像加速后，验证是否生效：

```bash
# 查看 Docker 信息
docker info

# 测试拉取镜像
docker pull python:3.11-slim
docker pull nginx:alpine
```

---

## 📝 其他建议

1. **更新 Docker 版本**：旧版本可能有更多限制
2. **使用国内镜像源**：如阿里云、腾讯云等提供的镜像加速服务
3. **定时清理缓存**：`docker system prune -a`

---

## 💡 快速修复脚本

创建 `fix-docker.sh`:

```bash
#!/bin/bash
echo "配置 Docker 镜像加速..."

# macOS/Linux 配置
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "请手动在 Docker Desktop 中配置镜像加速器"
    echo "详见: deploy/DOCKER_FIX.md"
else
    # Linux
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live"
  ]
}
EOF
    sudo systemctl restart docker
    echo "✅ Docker 配置已更新，请重新构建镜像"
fi
```
