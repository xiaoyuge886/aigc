#!/bin/bash
# 快速运行后端容器（开发环境）

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查环境变量
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量${NC}"
    echo -e "${YELLOW}请设置环境变量：${NC}"
    echo -e "  export ANTHROPIC_API_KEY=your-api-key"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 镜像名称
IMAGE_NAME="aigc-backend:latest"

# 检查镜像是否存在
if ! docker images | grep -q "aigc-backend.*latest"; then
    echo -e "${YELLOW}镜像不存在，开始构建...${NC}"
    ./deploy/build.sh
fi

# 创建必要的目录
mkdir -p data work_dir logs

echo -e "${GREEN}启动后端容器...${NC}"

# 停止并删除旧容器（如果存在）
docker stop aigc-backend 2>/dev/null || true
docker rm aigc-backend 2>/dev/null || true

# 运行容器
docker run -d \
    --name aigc-backend \
    -p 8000:8000 \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -e ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.anthropic.com}" \
    -e DEBUG="${DEBUG:-false}" \
    -v "$PROJECT_ROOT/data:/app/data" \
    -v "$PROJECT_ROOT/work_dir:/app/work_dir" \
    -v "$PROJECT_ROOT/logs:/app/logs" \
    "$IMAGE_NAME"

echo -e "${GREEN}✅ 容器已启动！${NC}"
echo -e "${YELLOW}查看日志: docker logs -f aigc-backend${NC}"
echo -e "${YELLOW}停止容器: docker stop aigc-backend${NC}"
echo -e "${YELLOW}健康检查: curl http://localhost:8000/health${NC}"
