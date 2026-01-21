#!/bin/bash

# AIGC 应用启动脚本
# 同时启动后端和前端服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录（脚本所在目录的父目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend/aigc-frontend"

# PID 文件（放在 scripts 目录）
BACKEND_PID_FILE="$SCRIPT_DIR/scripts/backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/scripts/frontend.pid"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在关闭服务...${NC}"

    # 关闭后端
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}关闭后端服务 (PID: $BACKEND_PID)...${NC}"
            kill $BACKEND_PID 2>/dev/null
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    # 关闭前端
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}关闭前端服务 (PID: $FRONTEND_PID)...${NC}"
            kill $FRONTEND_PID 2>/dev/null
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # 清理可能遗留的进程
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "vite" 2>/dev/null

    echo -e "${GREEN}所有服务已关闭${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 检查目录是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}错误: 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}错误: 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi

# ========================================
# 启动后端服务
# ========================================
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}        启动 AIGC 应用服务${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

echo -e "${GREEN}[1/2]${NC} 启动后端服务..."
cd "$BACKEND_DIR"

# 检查虚拟环境（按优先级检查多个位置）
if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}激活虚拟环境 (backend 目录)...${NC}"
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}激活虚拟环境 (backend 目录)...${NC}"
    source venv/bin/activate
elif [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    echo -e "${YELLOW}激活虚拟环境 (项目根目录)...${NC}"
    source "$SCRIPT_DIR/.venv/bin/activate"
else
    echo -e "${RED}警告: 未找到虚拟环境，使用系统 Python${NC}"
fi

# 启动后端（后台运行）
if [ -f "main.py" ]; then
    # 确保 logs 目录存在
    mkdir -p ../logs
    # 设置数据库路径环境变量
    DB_PATH="../data/sessions.db" nohup python main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    echo -e "  日志文件: ${YELLOW}logs/backend.log${NC}"
else
    echo -e "${RED}错误: 找不到 main.py${NC}"
    exit 1
fi

# 等待后端启动
echo -e "${YELLOW}等待后端服务就绪...${NC}"
sleep 3

# 检查后端是否启动成功
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}错误: 后端服务启动失败${NC}"
    echo -e "${YELLOW}请检查 logs/backend.log 文件查看详细错误信息${NC}"
    cleanup
    exit 1
fi

echo ""

# ========================================
# 启动前端服务
# ========================================
echo -e "${GREEN}[2/2]${NC} 启动前端服务..."
cd "$FRONTEND_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}首次运行，正在安装依赖...${NC}"
    npm install
fi

# 启动前端（前台运行）
echo -e "${GREEN}✓ 前端服务启动中...${NC}"
echo ""

echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${GREEN}所有服务已成功启动！${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}后端服务:${NC}"
echo -e "  - 地址: ${YELLOW}http://localhost:8000${NC}"
echo -e "  - API文档: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  - 日志: ${YELLOW}logs/backend.log${NC}"
echo ""
echo -e "${GREEN}前端服务:${NC}"
echo -e "  - 地址: ${YELLOW}http://localhost:8888${NC}"
echo -e "  - 日志: ${YELLOW}logs/frontend.log${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

# 启动前端（阻塞）
mkdir -p ../../logs
npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"

# 等待前端进程
wait $FRONTEND_PID
