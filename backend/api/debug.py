"""
Debug API - 调试和诊断接口
"""
from fastapi import APIRouter
from loguru import logger
import platform
import sys
from datetime import datetime

from models.schemas import HealthResponse

router = APIRouter(
    prefix="/api/v1/debug",
    tags=["debug"]
)


@router.get("/system-info")
async def get_system_info():
    """
    获取系统信息
    """
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查（调试路由专用）
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.post("/clear-cache")
async def clear_cache():
    """
    清除缓存（如果实现了缓存机制）
    """
    # TODO: 实现缓存清理逻辑
    logger.info("Cache clear requested")
    return {
        "status": "success",
        "message": "Cache cleared (not implemented yet)"
    }


@router.get("/logs")
async def get_logs(
    level: str = "INFO",
    limit: int = 100
):
    """
    获取日志（简化版本，实际应该从日志文件读取）
    """
    # TODO: 实现从日志文件读取的功能
    logger.info(f"Logs requested: level={level}, limit={limit}")
    return {
        "status": "success",
        "logs": [],
        "message": "Log reading not implemented yet"
    }


@router.get("/stats")
async def get_stats():
    """
    获取系统统计信息
    """
    from services.session_manager import get_session_manager
    from services.database import get_database_service

    session_mgr = get_session_manager()
    db_service = get_database_service()

    return {
        "status": "success",
        "data": {
            "active_sessions": len(session_mgr.sessions),
            "database_connected": db_service is not None,
            "timestamp": datetime.now().isoformat()
        }
    }
