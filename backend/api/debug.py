"""
Debug API - 调试和诊断接口
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
import platform
import sys
from datetime import datetime
from typing import Optional, AsyncIterator
from pydantic import BaseModel

from models.schemas import HealthResponse

router = APIRouter(
    prefix="/api/v1/debug",
    tags=["debug"]
)


# Request models
class SkillDebugStreamRequest(BaseModel):
    skill_name: str
    skill_content: str
    test_query: str
    session_id: Optional[str] = None


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


@router.post("/skill/stream")
async def debug_skill_stream(request: SkillDebugStreamRequest):
    """
    调试技能（流式响应，支持多轮对话）

    使用指定的技能内容处理测试查询，返回流式响应
    用于调试和测试技能

    多轮对话支持：
        - 首次查询：session_id=null 或不提供，创建新会话
        - 后续查询：传入返回的 session_id，继续对话
    """
    from services.agent_service import AgentService
    from services.session_manager import SessionManager, get_session_manager
    from services.database import DatabaseService, get_database_service
    from models.schemas import StreamChunk, ContentBlock
    from models.database import MessageDB
    import uuid

    async def event_generator() -> AsyncIterator[str]:
        session_mgr = get_session_manager()
        agent_service = AgentService()
        db_service = get_database_service()

        session_id = request.session_id
        conversation_turn_id = uuid.uuid4().hex[:16]

        try:
            # 构造技能 system_prompt（增强强调）
            system_prompt = f"""# CRITICAL: You MUST follow this skill's instructions EXACTLY

## Skill: {request.skill_name}

{request.skill_content}

---

⚠️ IMPORTANT: You MUST follow ALL instructions above, especially:
- Output in the specified format (e.g., [CHART_START]...[CHART_END])
- Use the Write tool to save files as instructed
- Do NOT skip any required output format or tool usage"""

            logger.info(f"[debug_skill_stream] Testing skill: {request.skill_name}")
            logger.info(f"[debug_skill_stream] Query: {request.test_query}")
            logger.info(f"[debug_skill_stream] Session ID: {session_id or 'new session'}")

            # 如果没有 session_id，创建新会话
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f"[debug_skill_stream] Created new session: {session_id}")

            # 保存用户消息
            user_message_id = await session_mgr.save_message(
                session_id=session_id,
                role="user",
                message_type="text",
                content=request.test_query,
                conversation_turn_id=conversation_turn_id,
            )
            logger.info(f"[debug_skill_stream] Saved user message: {user_message_id}")

            # 使用 query_in_session 进行多轮对话
            message_count = 0
            tool_use_index_map = {}
            pending_tool_input_deltas = {}

            # 创建 AgentConfig 传递 system_prompt
            from models.platform import AgentConfig
            from core.config import settings

            agent_config = AgentConfig(
                system_prompt=system_prompt,
                model="sonnet"
            )

            # 临时禁用安全控制（调试模式需要绕过 can_use_tool 的流式模式要求）
            original_security_control = getattr(settings, 'enable_security_control', False)
            settings.enable_security_control = False
            logger.info(f"[debug_skill_stream] Temporarily disabled security control for debug mode")

            try:
                async for msg in agent_service.query_in_session(
                    prompt=request.test_query,
                    session_id=session_id,
                    agent_config=agent_config,
                    include_partial_messages=True,
                ):
                    message_count += 1

                    # 处理消息类型
                    if isinstance(msg, ContentBlock) and msg.type == "text_delta":
                        # 处理增量流式文本片段
                        chunk = StreamChunk(type="text_delta", data=msg)
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    elif isinstance(msg, ContentBlock) and msg.type == "tool_input_delta":
                        # 处理工具输入增量
                        # 从 tool_use_id 中获取 index（agent_service.py 将 index 存储在 tool_use_id 中）
                        index = int(msg.tool_use_id) if msg.tool_use_id and msg.tool_use_id.isdigit() else None
                        if index is None:
                            index = 0  # 默认值

                        if index not in pending_tool_input_deltas:
                            pending_tool_input_deltas[index] = []

                        pending_tool_input_deltas[index].append(msg)
                        chunk = StreamChunk(type="tool_input_delta", data={"index": index, "delta": msg.text})
                        yield f"data: {chunk.model_dump_json()}\n\n"
                    else:
                        chunk = StreamChunk(type="data", data=msg)
                        yield f"data: {chunk.model_dump_json()}\n\n"

                        # 处理 tool_use 消息，保存 tool_use_id
                        if isinstance(msg, ContentBlock) and msg.type == "tool_use" and hasattr(msg, 'id'):
                            tool_use_id = msg.id
                            # 从 tool_input 中获取 index（如果存在）
                            tool_input = getattr(msg, 'tool_input', None) or {}
                            index = tool_input.get('_index') if isinstance(tool_input, dict) else None
                            if index is not None:
                                tool_use_index_map[index] = tool_use_id
                                logger.info(f"[debug_skill_stream] Mapped tool_use index {index} -> {tool_use_id}")

                logger.info(f"[debug_skill_stream] Streamed {message_count} messages")

                # 返回结果（包含 session_id）
                result_chunk = StreamChunk(
                    type="result",
                    data={
                        "session_id": session_id,
                        "conversation_turn_id": conversation_turn_id,
                        "skill_name": request.skill_name
                    }
                )
                yield f"data: {result_chunk.model_dump_json()}\n\n"

                logger.info(f"[debug_skill_stream] Skill test completed")

            finally:
                # 恢复安全控制设置
                settings.enable_security_control = original_security_control
                logger.info(f"[debug_skill_stream] Restored security control to {original_security_control}")

        except Exception as e:
            logger.error(f"Error in skill debug stream: {e}", exc_info=True)
            error_chunk = StreamChunk(
                type="error",
                data={"error": str(e), "skill_name": request.skill_name}
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
