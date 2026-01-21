#!/bin/bash
# 构建后端 Docker 镜像

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始构建后端 Docker 镜像...${NC}"

# 获取项目根目录（deploy 的父目录）
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 镜像名称和标签
IMAGE_NAME="aigc-backend"
IMAGE_TAG="${1:-latest}"

echo -e "${YELLOW}项目根目录: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}镜像名称: $IMAGE_NAME:$IMAGE_TAG${NC}"

# 构建镜像
docker build \
    -f deploy/Dockerfile \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    .

echo -e "${GREEN}✅ 构建完成！${NC}"
echo -e "${YELLOW}使用以下命令运行容器：${NC}"
echo -e "  docker run -d -p 8000:8000 -e ANTHROPIC_API_KEY=your-key $IMAGE_NAME:$IMAGE_TAG"
echo -e "或使用 docker-compose："
echo -e "  cd deploy && docker-compose up -d"
