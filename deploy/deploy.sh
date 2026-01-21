#!/bin/bash
# 一键部署前后端服务

set -e

# ============================================
# 路径检测：自动适配运行位置
# ============================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 检查是在项目根目录还是 deploy 目录运行
if [ "$(basename "$SCRIPT_DIR")" = "deploy" ]; then
    # 从 deploy 目录运行
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    IN_DEPLOY_DIR=true
else
    # 从项目根目录运行
    PROJECT_ROOT="$SCRIPT_DIR"
    IN_DEPLOY_DIR=false
fi

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${GREEN}AIGC 应用一键部署脚本${NC}"
    echo ""
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo "命令:"
    echo "  dev     启动开发环境（默认）"
    echo "  prod    启动生产环境"
    echo "  build   构建镜像（不启动）"
    echo "  stop    停止所有服务"
    echo "  restart 重启所有服务"
    echo "  logs    查看日志"
    echo "  status  查看服务状态"
    echo "  clean   清理所有容器和镜像"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -f, --frontend 仅构建/启动前端"
    echo "  -b, --backend  仅构建/启动后端"
    echo ""
    echo "示例:"
    echo "  $0 dev                    # 启动开发环境"
    echo "  $0 prod                   # 启动生产环境"
    echo "  $0 build -f               # 仅构建前端"
    echo "  $0 dev -b                 # 仅启动后端开发环境"
}

# 检查环境变量
check_env() {
    local env_file="$1"

    if [ ! -f "$env_file" ]; then
        echo -e "${RED}❌ 错误: 环境变量文件不存在: $env_file${NC}"
        echo -e "${YELLOW}请先创建 .env 文件：${NC}"
        echo -e "  cp deploy/.env.example deploy/.env"
        echo -e "  # 然后编辑 deploy/.env 填写必要的配置"
        exit 1
    fi

    # 检查必需的 API Key
    if ! grep -q "^ANTHROPIC_API_KEY=" "$env_file" || grep -q "^ANTHROPIC_API_KEY=$" "$env_file"; then
        echo -e "${RED}❌ 错误: ANTHROPIC_API_KEY 未设置${NC}"
        echo -e "${YELLOW}请在 $env_file 中设置 ANTHROPIC_API_KEY${NC}"
        exit 1
    fi
}

# 创建必要的目录
create_dirs() {
    echo -e "${BLUE}创建必要的目录...${NC}"
    mkdir -p data work_dir logs
}

# 构建镜像
build_images() {
    local frontend_only="$1"
    local backend_only="$2"

    # 切换到项目根目录
    cd "$PROJECT_ROOT"

    if [ "$backend_only" != "true" ]; then
        echo -e "${GREEN}构建前端镜像...${NC}"
        ./deploy/build-frontend.sh
    fi

    if [ "$frontend_only" != "true" ]; then
        echo -e "${GREEN}构建后端镜像...${NC}"
        ./deploy/build.sh
    fi
}

# 启动服务
start_services() {
    local compose_file="$1"
    local frontend_only="$2"
    local backend_only="$3"

    create_dirs

    echo -e "${GREEN}启动服务...${NC}"

    # 切换到 deploy 目录
    if [ "$IN_DEPLOY_DIR" = true ]; then
        # 已经在 deploy 目录
        :
    else
        cd deploy
    fi

    if [ "$frontend_only" = "true" ]; then
        docker-compose -f "$compose_file" up -d frontend
    elif [ "$backend_only" = "true" ]; then
        docker-compose -f "$compose_file" up -d backend
    else
        docker-compose -f "$compose_file" up -d
    fi

    echo -e "${GREEN}✅ 服务已启动！${NC}"
    echo -e "${YELLOW}前端地址: http://localhost:3000${NC}"
    echo -e "${YELLOW}后端地址: http://localhost:8000${NC}"
    echo -e "${YELLOW}API 文档: http://localhost:8000/docs${NC}"
}

# 停止服务
stop_services() {
    local compose_file="$1"

    echo -e "${YELLOW}停止服务...${NC}"

    # 切换到 deploy 目录
    if [ "$IN_DEPLOY_DIR" = true ]; then
        :
    else
        cd deploy
    fi

    docker-compose -f "$compose_file" down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart_services() {
    local compose_file="$1"

    echo -e "${YELLOW}重启服务...${NC}"
    stop_services "$compose_file"
    start_services "$compose_file" false false
}

# 查看日志
show_logs() {
    local compose_file="$1"
    shift

    # 切换到 deploy 目录
    if [ "$IN_DEPLOY_DIR" = true ]; then
        :
    else
        cd deploy
    fi

    docker-compose -f "$compose_file" logs -f "$@"
}

# 查看状态
show_status() {
    local compose_file="$1"

    echo -e "${GREEN}服务状态：${NC}"

    # 切换到 deploy 目录
    if [ "$IN_DEPLOY_DIR" = true ]; then
        :
    else
        cd deploy
    fi

    docker-compose -f "$compose_file" ps
}

# 清理资源
clean_resources() {
    echo -e "${RED}警告: 此操作将删除所有容器和镜像${NC}"
    read -p "确定要继续吗? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}清理资源...${NC}"

        # 切换到 deploy 目录
        if [ "$IN_DEPLOY_DIR" = true ]; then
            :
        else
            cd deploy
        fi

        # 停止并删除容器
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

        # 删除镜像
        docker rmi aigc-frontend:latest 2>/dev/null || true
        docker rmi aigc-backend:latest 2>/dev/null || true

        echo -e "${GREEN}✅ 清理完成${NC}"
    else
        echo -e "${YELLOW}已取消${NC}"
    fi
}

# 解析命令行参数
FRONTEND_ONLY=false
BACKEND_ONLY=false
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--frontend)
            FRONTEND_ONLY=true
            shift
            ;;
        -b|--backend)
            BACKEND_ONLY=true
            shift
            ;;
        dev|prod|build|stop|restart|logs|status|clean)
            COMMAND="$1"
            shift
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 如果没有指定命令，默认为 dev
if [ -z "$COMMAND" ]; then
    COMMAND="dev"
fi

# 根据 IN_DEPLOY_DIR 决定 .env 路径
if [ "$IN_DEPLOY_DIR" = true ]; then
    ENV_FILE=".env"
else
    ENV_FILE="deploy/.env"
fi

# 根据命令执行相应操作
case $COMMAND in
    dev)
        echo -e "${GREEN}启动开发环境...${NC}"
        check_env "$ENV_FILE"
        start_services "docker-compose.yml" "$FRONTEND_ONLY" "$BACKEND_ONLY"
        ;;
    prod)
        echo -e "${GREEN}启动生产环境...${NC}"
        check_env "$ENV_FILE"
        start_services "docker-compose.prod.yml" "$FRONTEND_ONLY" "$BACKEND_ONLY"
        ;;
    build)
        build_images "$FRONTEND_ONLY" "$BACKEND_ONLY"
        ;;
    stop)
        stop_services "docker-compose.yml"
        ;;
    restart)
        restart_services "docker-compose.yml"
        ;;
    logs)
        show_logs "docker-compose.yml" "$@"
        ;;
    status)
        show_status "docker-compose.yml"
        ;;
    clean)
        clean_resources
        ;;
    *)
        echo -e "${RED}未知命令: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
