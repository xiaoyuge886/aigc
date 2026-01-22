#!/bin/bash

# AIGC 应用重启脚本
# 停止现有服务并重新启动

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录（脚本所在目录的父目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}        重启 AIGC 应用服务${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

# ========================================
# 停止现有服务
# ========================================
echo -e "${YELLOW}[1/3] 停止现有服务...${NC}"

# 查找并停止后端服务
BACKEND_PIDS=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}发现运行中的后端服务，正在停止...${NC}"
    echo "$BACKEND_PIDS" | xargs kill 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ 后端服务已停止${NC}"
else
    echo -e "${GREEN}✓ 没有运行中的后端服务${NC}"
fi

# 查找并停止前端服务
FRONTEND_PIDS=$(ps aux | grep "vite" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}发现运行中的前端服务，正在停止...${NC}"
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ 前端服务已停止${NC}"
else
    echo -e "${GREEN}✓ 没有运行中的前端服务${NC}"
fi

# 清理 PID 文件
rm -f "$SCRIPT_DIR/scripts/backend.pid" "$SCRIPT_DIR/scripts/frontend.pid"

echo ""

# ========================================
# 等待端口释放
# ========================================
echo -e "${YELLOW}[2/3] 等待端口释放...${NC}"

# 检查端口 8000
for i in {1..10}; do
    if ! lsof -i :8000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 端口 8000 已释放${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}警告: 端口 8000 仍被占用${NC}"
        lsof -i :8000 | grep -v COMMAND
    fi
    sleep 1
done

# 检查端口 5173
for i in {1..10}; do
    if ! lsof -i :5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 端口 5173 已释放${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}警告: 端口 5173 仍被占用${NC}"
        lsof -i :5173 | grep -v COMMAND
    fi
    sleep 1
done

echo ""

# ========================================
# 重新启动服务
# ========================================
echo -e "${YELLOW}[3/3] 重新启动服务...${NC}"
echo ""

# 调用启动脚本
if [ -x "$SCRIPT_DIR/start.sh" ]; then
    exec "$SCRIPT_DIR/start.sh"
else
    echo -e "${YELLOW}start.sh 不可执行，尝试直接运行...${NC}"
    bash "$SCRIPT_DIR/start.sh"
fi
