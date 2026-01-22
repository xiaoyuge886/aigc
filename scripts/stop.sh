#!/bin/bash

# AIGC 应用停止脚本
# 停止所有运行中的服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录（脚本所在目录的父目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}        停止 AIGC 应用服务${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

STOPPED=false

# ========================================
# 停止后端服务
# ========================================
echo -e "${YELLOW}检查后端服务...${NC}"

# 方法1: 通过 PID 文件
if [ -f "$SCRIPT_DIR/scripts/backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/scripts/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        sleep 1
        if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 后端服务已停止${NC}"
            STOPPED=true
        fi
    fi
    rm -f "$SCRIPT_DIR/scripts/backend.pid"
fi

# 方法2: 通过进程名
BACKEND_PIDS=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}停止后端服务...${NC}"
    echo "$BACKEND_PIDS" | xargs kill 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ 后端服务已停止${NC}"
    STOPPED=true
else
    echo -e "${GREEN}✓ 后端服务未运行${NC}"
fi

echo ""

# ========================================
# 停止前端服务
# ========================================
echo -e "${YELLOW}检查前端服务...${NC}"

# 方法1: 通过 PID 文件
if [ -f "$SCRIPT_DIR/scripts/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/scripts/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        sleep 1
        if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 前端服务已停止${NC}"
            STOPPED=true
        fi
    fi
    rm -f "$SCRIPT_DIR/scripts/frontend.pid"
fi

# 方法2: 通过进程名
FRONTEND_PIDS=$(ps aux | grep "vite.*aigc-frontend" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}停止前端服务...${NC}"
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ 前端服务已停止${NC}"
    STOPPED=true
else
    echo -e "${GREEN}✓ 前端服务未运行${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════${NC}"

if [ "$STOPPED" = true ]; then
    echo -e "${GREEN}所有服务已停止${NC}"
else
    echo -e "${YELLOW}没有运行中的服务${NC}"
fi

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""
