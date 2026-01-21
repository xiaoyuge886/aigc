#!/bin/bash
# 导出 Docker 镜像为 tar 文件

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 镜像名称
FRONTEND_IMAGE="xiaoyuge886/aigc-frontend:latest"
BACKEND_IMAGE="xiaoyuge886/aigc-backend:latest"

# 导出目录
EXPORT_DIR="./logs/exports"
mkdir -p "$EXPORT_DIR"

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}Docker 镜像导出工具${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""

# 检查镜像是否存在
echo -e "${YELLOW}检查镜像...${NC}"
if ! docker image inspect "$FRONTEND_IMAGE" &>/dev/null; then
    echo -e "${RED}错误: 前端镜像不存在: $FRONTEND_IMAGE${NC}"
    echo -e "${YELLOW}请先运行: docker-compose -f docker-compose.prod.yml build frontend${NC}"
    exit 1
fi

if ! docker image inspect "$BACKEND_IMAGE" &>/dev/null; then
    echo -e "${RED}错误: 后端镜像不存在: $BACKEND_IMAGE${NC}"
    echo -e "${YELLOW}请先运行: docker-compose -f docker-compose.prod.yml build backend${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 镜像检查通过${NC}"
echo ""

# 获取镜像大小
FRONTEND_SIZE=$(docker image inspect "$FRONTEND_IMAGE" --format='{{.Size}}' | awk '{print int($1/1024/1024) "MB"}')
BACKEND_SIZE=$(docker image inspect "$BACKEND_IMAGE" --format='{{.Size}}' | awk '{print int($1/1024/1024) "MB"}')

echo -e "${YELLOW}镜像信息:${NC}"
echo "  前端: $FRONTEND_IMAGE ($FRONTEND_SIZE)"
echo "  后端: $BACKEND_IMAGE ($BACKEND_SIZE)"
echo ""

# 导出前端镜像
echo -e "${YELLOW}导出前端镜像...${NC}"
docker save "$FRONTEND_IMAGE" -o "$EXPORT_DIR/aigc-frontend.tar"
echo -e "${GREEN}✓ 前端镜像已导出: $EXPORT_DIR/aigc-frontend.tar${NC}"

# # 导出后端镜像
# echo -e "${YELLOW}导出后端镜像...${NC}"
# docker save "$BACKEND_IMAGE" -o "$EXPORT_DIR/aigc-backend.tar"
# echo -e "${GREEN}✓ 后端镜像已导出: $EXPORT_DIR/aigc-backend.tar${NC}"

# 显示文件大小
echo ""
echo -e "${YELLOW}导出文件大小:${NC}"
ls -lh "$EXPORT_DIR"/aigc-*.tar | awk '{print "  " $9 " - " $5}'

echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}导出完成！${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo -e "${YELLOW}导入命令:${NC}"
echo "  docker load -i $EXPORT_DIR/aigc-frontend.tar"
echo "  docker load -i $EXPORT_DIR/aigc-backend.tar"
echo ""
