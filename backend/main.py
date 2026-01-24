"""
Main FastAPI application for Claude Agent Server
"""
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from loguru import logger
from dotenv import load_dotenv

# Load .env file to os.environ FIRST
# This makes ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL available to Claude Agent SDK
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
logger.info(f"Loaded environment variables from {env_path}")

from core.config import settings
from models.schemas import HealthResponse
from api.v1 import router
from services.session_manager import get_session_manager
from services.database import get_database_service


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 配置 uvicorn 访问日志过滤器，过滤掉 /api/v1/frontend/log 请求
import logging

class SuppressFrontendLogFilter(logging.Filter):
    """过滤掉 /api/v1/frontend/log 的访问日志"""
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/api/v1/frontend/log" not in message

# 获取 uvicorn.access logger 并添加过滤器
# 注意：这会在应用启动时配置，但 uvicorn 可能在应用加载前就配置了日志
# 所以在 lifespan 中也会再次配置以确保生效
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(SuppressFrontendLogFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # 确保 uvicorn.access logger 有过滤器（在应用启动时再次配置以确保生效）
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    # 检查是否已有过滤器，如果没有则添加
    has_filter = any(isinstance(f, SuppressFrontendLogFilter) for f in uvicorn_access_logger.filters)
    if not has_filter:
        uvicorn_access_logger.addFilter(SuppressFrontendLogFilter())
    
    # Startup
    logger.info("Starting Claude Agent Server...")

    # Initialize database
    db_service = get_database_service()
    await db_service.initialize()
    logger.info("Database initialized")

    # Register tools (自动注册工具到数据库)
    from services.tool_registry import auto_register_tools
    tools_result = await auto_register_tools(db_service)
    if tools_result and tools_result.get('success'):
        logger.info(f"Tools registered: {tools_result['total']} total ({tools_result['added']} new)")
    else:
        logger.warning("Tool registration skipped or failed")

    # Initialize session manager with database
    session_mgr = get_session_manager()
    session_mgr.db_service = db_service
    await session_mgr.start()
    logger.info(f"Session manager started (max sessions: {settings.max_concurrent_sessions})")
    
    # Initialize default system prompt from database
    from services.agent_service import get_agent_service, initialize_default_prompt
    agent_service = get_agent_service()
    await initialize_default_prompt(agent_service)
    
    # Initialize cron jobs (定时任务)
    from services.cron_jobs import CronJobs
    cron_jobs = CronJobs(db_service)
    # 注意：定时任务需要 agent_service，但为了避免启动时的依赖问题，
    # 定时任务会在后台循环中检查 agent_service 是否可用
    # 可以通过 API 手动触发批量分析
    # await cron_jobs.start()  # 可选：自动启动定时任务
    logger.info("Cron jobs initialized (can be started via API)")

    yield

    # Shutdown
    logger.info("Shutting down Claude Agent Server...")
    # Stop cron jobs if running
    try:
        await cron_jobs.stop()
    except Exception as e:
        logger.warning(f"Error stopping cron jobs: {e}")
    await session_mgr.stop()
    logger.info("Server shutdown complete")


# Create FastAPI application
# 禁用默认的 docs 和 redoc，我们将使用自定义路由
app = FastAPI(
    title="Claude Agent Server",
    description="通用 Agent 服务 API - 基于 Claude Agent SDK 和 FastAPI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # 禁用默认的 /docs，使用自定义路由
    redoc_url=None,  # 禁用默认的 /redoc
)

# Configure OpenAPI security scheme for Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add JWT Bearer security scheme
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["Bearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter JWT token obtained from /api/v1/auth/login endpoint. Format: Bearer <token>"
    }
    
    # Mark endpoints that use authentication with security requirement
    # This makes Swagger UI show the "Authorize" button and allow users to input token
    # The token will then be automatically added to all requests
    public_paths = [
        "/api/v1/auth/login",
        # "/api/v1/auth/register",  # 注册接口已禁用
        "/",
        "/health",
        "/api/v1/health",
        "/api/v1/agent/query",
        "/api/v1/agent/query/stream",
    ]
    
    # Track if any endpoint uses security (to ensure Authorize button appears)
    has_security = False
    
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if isinstance(operation, dict):
                # Exclude public endpoints
                if path not in public_paths:
                    # Add security requirement (optional - endpoints can work without it)
                    # Using empty list [] means the security is optional
                    if "security" not in operation:
                        operation["security"] = [{"Bearer": []}]
                        has_security = True
    
    # If no endpoints have security, add it to at least one endpoint to show Authorize button
    # We'll add it to /api/v1/sessions as an example
    if not has_security and "/api/v1/sessions" in openapi_schema.get("paths", {}):
        sessions_path = openapi_schema["paths"]["/api/v1/sessions"]
        if "get" in sessions_path:
            if "security" not in sessions_path["get"]:
                sessions_path["get"]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# # 挂载静态文件目录（Swagger UI 资源）
# static_dir = Path(__file__).parent / "static"
# if static_dir.exists():
#     app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
#
# # 自定义 Swagger UI 路由，使用本地资源
# from fastapi.responses import HTMLResponse
#
# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     """自定义 Swagger UI HTML，使用本地静态资源"""
#     html_file = static_dir / "swagger-ui" / "index.html"
#     if html_file.exists():
#         logger.info(f"使用本地 Swagger UI: {html_file}")
#         return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
#     # 如果本地文件不存在，回退到默认的 Swagger UI
#     logger.warning(f"本地 Swagger UI 文件不存在: {html_file}，使用默认版本")
#     from fastapi.openapi.docs import get_swagger_ui_html
#     return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": str(exc), "error_type": type(exc).__name__}
    )


# Include routers
app.include_router(router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Claude Agent Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Health check
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


if __name__ == "__main__":
    import uvicorn
    
    # 确保过滤器已配置（已在模块级别配置，这里再次确保）
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    has_filter = any(isinstance(f, SuppressFrontendLogFilter) for f in uvicorn_access_logger.filters)
    if not has_filter:
        uvicorn_access_logger.addFilter(SuppressFrontendLogFilter())

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
