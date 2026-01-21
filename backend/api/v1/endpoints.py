"""
FastAPI routes for Agent API
"""
import asyncio
import json
import re
from typing import AsyncIterator, Optional, Dict, List, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from datetime import datetime


def format_utc_timestamp(dt: datetime) -> str:
    """
    格式化 UTC 时间戳，确保包含时区信息
    
    数据库存储的是 UTC 时间（使用 datetime.utcnow()），
    但 naive datetime 的 isoformat() 不包含时区标记。
    前端需要明确的时区信息才能正确转换为本地时间。
    """
    timestamp_str = dt.isoformat()
    # 如果时间戳没有时区信息（naive datetime），添加 'Z' 表示 UTC
    if not timestamp_str.endswith('Z') and '+' not in timestamp_str and timestamp_str.count('-') <= 2:
        timestamp_str = timestamp_str + 'Z'
    return timestamp_str


def clean_message_text(text: str) -> str:
    """
    清理消息文本，移除本地文件路径等内部信息
    
    注意：保留 URL 链接（如 MinIO 链接），因为用户需要看到和访问这些链接
    文件信息也会通过文件事件单独传递
    """
    if not text:
        return text
    
    cleaned = text
    
    # 移除本地文件路径（work_dir/reports/...）
    # 但保留 URL 链接，因为用户需要访问这些链接
    cleaned = re.sub(r'work_dir/reports/[^\s\n\)\]]+\.[a-zA-Z0-9]+', '', cleaned)

    # 注释掉的清理规则已移除，保留所有用户生成的内容
    # 包括本地文件路径和 MinIO URL（用户需要访问这些链接）

    # 移除包含本地文件路径的完整行（如果整行只有文件路径）
    # 但保留包含 URL 的行，因为 URL 通常与其他文本一起出现
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        trimmed = line.strip()
        # 跳过空行
        if not trimmed:
            filtered_lines.append(line)
            continue
        # 只过滤掉只包含本地文件路径的行（不包含 URL）
        if re.match(r'^work_dir/reports/.+\.(md|txt|html|pdf|docx?|xlsx?|pptx?)$', trimmed, re.IGNORECASE):
            continue
        # 保留所有其他行，包括 MinIO URL
        filtered_lines.append(line)
    cleaned = '\n'.join(filtered_lines)
    
    # 移除多余的空行
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()

from services.agent_service import get_agent_service, AgentService
from services.session_manager import get_session_manager, SessionManager
from models.schemas import (
    AgentRequest,
    AgentResponse,
    AssistantMessage,
    ContentBlock,
    ErrorResponse,
    ResultInfo,
    SessionCreateRequest,
    SessionResponse,
    StreamChunk,
    SystemMessage,
    UserMessage,
    ConversationHistoryResponse,
    HistoryMessage,
    MessageResultInfo,
    ToolCallInfo,
    FrontendLogRequest,
    FrontendLogResponse,
    FileEventInfo,
    DataFlowNode,
    DataFlowResponse,
)
from services.database import get_database_service, DatabaseService
from sqlalchemy import select
from models.database import UserScenarioConfigDB, MessageDB
from services.configuration_manager import ConfigurationManager
from services.file_upload_service import FileUploadService
from services.prompt_composer import PromptComposer
from services.file_reference_parser import FileReferenceParser
from services.file_intent_detector import FileIntentDetector
from services.file_search_service import FileSearchService
from services.file_content_loader import FileContentLoader
from services.feedback_collector import FeedbackCollector
from api.v1.auth import get_current_user_optional
from models.database import UserDB


router = APIRouter(tags=["agent"])


@router.post("/agent/query", response_model=AgentResponse)
async def query_agent(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Execute a single stateless query (creates new session each time)

    This uses query_once() which creates a fresh Claude session for each request.
    No conversation context is preserved between calls.

    Best for:
        - Simple one-off questions
        - Batch processing of independent prompts
        - Code generation or analysis tasks
        - Automated scripts

    For multi-turn conversations, use /session endpoints instead.
    """
    try:
        messages = []
        result = None

        async for msg in agent_service.query_once(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            allowed_tools=request.allowed_tools,
            model=request.model,
        ):
            if isinstance(msg, (AssistantMessage, SystemMessage)):
                messages.append(msg)
            elif isinstance(msg, ResultInfo):
                result = msg

        return AgentResponse(
            session_id="single",
            messages=messages,
            result=result
        )

    except Exception as e:
        logger.error(f"Error in query_agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/agent/query/stream")
async def query_agent_stream(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Execute a streaming stateless query

    This uses query_once() with Server-Sent Events (SSE) for real-time responses.
    Each request creates a fresh session with no conversation context.

    Best for:
        - Real-time responses to one-off questions
        - Simple queries where you want to see Claude thinking
        - Batch processing with streaming output

    For multi-turn conversations, use /session/query/stream instead.

    Incremental Streaming:
        Set `incremental_stream=true` in request to enable text-level streaming.
        This sends each text fragment as it arrives (character-by-character or word-by-word).
    """
    async def event_generator() -> AsyncIterator[str]:
        try:
            async for msg in agent_service.query_once(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                allowed_tools=request.allowed_tools,
                model=request.model,
                include_partial_messages=request.incremental_stream,
            ):
                # 处理增量流式文本片段
                if isinstance(msg, ContentBlock) and msg.type == "text_delta":
                    chunk = StreamChunk(type="text_delta", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                else:
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(f"Error in query_agent_stream: {e}")
            error_chunk = StreamChunk(
                type="error",
                data=ErrorResponse(error=str(e))
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/session", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    agent_service: AgentService = Depends(get_agent_service),
    session_mgr: SessionManager = Depends(get_session_manager),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    Create a new agent session for multi-turn conversations

    This endpoint is optional. You can also start a conversation directly
    by calling POST /session/query or POST /session/query/stream with
    session_id=null.

    If you use this endpoint:
    1. Creates a session with specific configuration
    2. Returns a session_id for subsequent queries
    3. Use the session_id in POST /session/query or /session/query/stream

    The session_id can be used for subsequent queries via:
        - POST /session/query (with session_id in request body)
        - POST /session/query/stream (with session_id in request body)

    Incremental Streaming:
        Set `incremental_stream=true` to enable text-level streaming for
        all queries in this session. This setting cannot be changed after
        session creation.

    Authentication (Optional):
        - If JWT token provided: session is bound to the authenticated user
        - If no token: session is created as anonymous (user_id=None)

    Platform Configuration (Optional):
        - If user has custom configuration, it will be applied
        - Request-level parameters override user configuration
        - Configuration priority: Request > Session > User > Global

    Returns:
        SessionResponse with session_id and creation timestamp
    """
    try:
        # 获取用户 ID（如果有认证用户）
        user_id = current_user.id if current_user else None
        if current_user:
            logger.info(f"Creating session for authenticated user: {current_user.username}")
        else:
            logger.info("Creating anonymous session (no authentication)")

        # Platform configuration (optional, doesn't affect core logic)
        agent_config = None
        if user_id:
            try:
                config_manager = ConfigurationManager(db_service)
                user_config = await config_manager.get_user_config(user_id)
                
                # Build request config from request parameters
                request_config = {}
                if request.system_prompt:
                    request_config["system_prompt"] = request.system_prompt
                if request.allowed_tools:
                    request_config["allowed_tools"] = request.allowed_tools
                if request.model:
                    request_config["model"] = request.model
                
                # Build session config (from request, will be saved to session)
                session_config = request_config.copy()
                
                # Merge configurations
                agent_config, _ = config_manager.merge_agent_config(
                    request_config=request_config,
                    session_config=session_config,
                    user_config=user_config,
                )
                logger.debug(f"Applied platform configuration for user_id={user_id}")
            except Exception as e:
                logger.warning(f"Failed to load platform configuration for user_id={user_id}: {e}")
                # Continue with default configuration (backward compatible)

        # Create options (with platform config if available)
        options = agent_service.create_options(
            system_prompt=request.system_prompt,
            allowed_tools=request.allowed_tools,
            model=request.model,
            include_partial_messages=request.incremental_stream,
            agent_config=agent_config,  # Platform configuration (optional)
        )

        session = await session_mgr.create_session(
            options=options,
            user_id=user_id  # ← 绑定到用户
        )

        return SessionResponse(
            session_id=session.session_id,
            created_at=format_utc_timestamp(session.created_at)
        )

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/session/query", response_model=AgentResponse)
async def session_query(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Send a query in a session (supports both new and existing sessions)

    This uses query_in_session() for multi-turn conversations.
    Claude will remember the conversation context from previous queries
    in the same session.

    Args:
        request: AgentRequest with:
            - prompt: User prompt to send to Claude
            - session_id: Optional session identifier (None for first query in new session)
            - Other optional parameters (system_prompt, allowed_tools, model, etc.)

    Returns:
        AgentResponse with messages and result metadata

    Session Handling:
        - First query: Send session_id=null or omit it to create a new conversation
        - Subsequent queries: Send the session_id returned in the ResultMessage
          to continue the conversation
    """
    try:
        # Get session_id from request body (can be None for first query)
        session_id = request.session_id

        messages = []
        result = None

        async for msg in agent_service.query_in_session(
            prompt=request.prompt,
            session_id=session_id or "",  # Empty string for first query
            include_partial_messages=request.incremental_stream  # 传递增量流式参数
            # 匿名用户不传 user_id，使用默认 work_dir
        ):
            if isinstance(msg, (AssistantMessage, SystemMessage)):
                messages.append(msg)
            elif isinstance(msg, ResultInfo):
                result = msg

        return AgentResponse(
            session_id=session_id or "new",
            messages=messages,
            result=result
        )

    except Exception as e:
        logger.error(f"Error in session_query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/session/query/stream")
async def session_query_stream(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service),
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    core 再用
    Send a streaming query in a session (supports both new and existing sessions)

    This uses query_in_session() with Server-Sent Events (SSE) for real-time
    responses in a multi-turn conversation. Claude maintains context from
    previous messages in the session.

    Args:
        request: AgentRequest with:
            - prompt: User prompt to send to Claude
            - session_id: Optional session identifier (None for first query in new session)
            - Other optional parameters (system_prompt, allowed_tools, model, etc.)

    Returns:
        Server-Sent Events stream with real-time messages

    Session Handling:
        - First query: Send session_id=null or omit it to create a new conversation
        - Subsequent queries: Send the session_id returned in the ResultMessage
          to continue the conversation

    Incremental Streaming:
        If the session was created with `incremental_stream=true`, text deltas
        will be sent as type="text_delta" chunks for character-level streaming.

    Example:
        ```python
        # First query (create new session)
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "/api/v1/session/query/stream",
                json={"prompt": "Hello", "session_id": None}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        # Extract session_id from ResultMessage for next query

        # Second query (continue conversation)
        async with client.stream(
            "POST",
            "/api/v1/session/query/stream",
            json={"prompt": "How are you?", "session_id": "<previous_session_id>"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    # Process data
        ```
    """
    async def event_generator() -> AsyncIterator[str]:
        import uuid
        
        session_id = None
        user_message_saved = False
        user_message_id = None  # 保存用户消息的ID，用于设置parent_message_id
        assistant_message_id = None  # 保存AI消息的ID，用于设置tool_use的parent_message_id
        conversation_turn_id = None  # 同一轮对话的唯一ID
        session_created = False  # 标记会话是否已创建
        assistant_content = []  # 收集 AssistantMessage 的内容
        tool_calls = []  # 收集工具调用信息
        saved_tool_use_ids = set()  # 追踪已保存的 tool_use_id，确保同一ID只保存一次
        result_info_dict = None  # 保存 ResultMessage 信息
        tool_use_index_map = {}  # 🔧 维护 index -> tool_use_id 的映射，用于 tool_input_delta 事件
        pending_tool_input_deltas: Dict[int, List[ContentBlock]] = {}  # 🔧 缓存待处理的 tool_input_delta 事件，key 是 index，value 是 ContentBlock 列表
        
        try:
            # Get session_id from request body (can be None for first query)
            session_id = request.session_id
            logger.info(f"[session_query_stream] Starting query for session {session_id or 'new session'}")
            logger.info(f"[session_query_stream] incremental_stream={request.incremental_stream}")

            # ==================== 提前生成 conversation_turn_id ====================
            # conversation_turn_id 在请求开始时立即生成，不依赖任何外部服务
            # 这样可以确保文件上传时就有可用的 conversation_turn_id
            conversation_turn_id = uuid.uuid4().hex[:16]
            logger.info(f"[session_query_stream] ✅ Generated conversation_turn_id: {conversation_turn_id} (early generation)")
            
            # 保存用户消息（如果已有 session_id）
            if session_id:
                user_message_id = await session_mgr.save_message(
                    session_id=session_id,
                    role="user",
                    message_type="text",
                    content=request.prompt,
                    conversation_turn_id=conversation_turn_id,
                )
                user_message_saved = True

            # Load user configuration BEFORE creating the agent client
            # This ensures the correct system_prompt is used from the start
            agent_config = None
            if current_user:
                try:
                    config_manager = ConfigurationManager(db_service)
                    user_config = await config_manager.get_user_config(current_user.id)
                    
                    logger.info(f"[session_query_stream] Loading config for user_id={current_user.id}, username={current_user.username} (BEFORE query)")
                    logger.info(f"[session_query_stream] User config found: {user_config is not None}")
                    if user_config:
                        logger.info(f"[session_query_stream] User config - system_prompt: {user_config.default_system_prompt[:100] if user_config.default_system_prompt else None}...")
                    
                    # Build request config from request parameters
                    request_config = {}
                    if request.system_prompt:
                        request_config["system_prompt"] = request.system_prompt
                        logger.info(f"[session_query_stream] Request has system_prompt (will override user config)")
                    if request.allowed_tools:
                        request_config["allowed_tools"] = request.allowed_tools
                    if request.model:
                        request_config["model"] = request.model
                    
                    # Build session config
                    session_config = request_config.copy()
                    
                    # Load scenario config if user has associated scenario
                    # 优先级：请求参数 > 用户场景配置（UserScenarioConfigDB） > 用户配置关联的场景（UserConfigDB，向后兼容）
                    scenario_config = None
                    scenario_id = None
                    user_id = current_user.id if current_user else None
                    
                    # 方案1：从请求参数中获取 scenario_id（如果前端传递，优先级最高）
                    if hasattr(request, 'scenario_id') and request.scenario_id:
                        scenario_id = request.scenario_id
                        logger.info(f"[session_query_stream] Found scenario_id in request: {scenario_id}")
                    
                    # 方案2：从用户场景配置中获取场景列表（新方式，支持多场景）
                    # 如果用户配置了多个场景，根据用户输入智能匹配最合适的场景
                    user_scenario_ids = None
                    if not scenario_id and user_id:
                        try:
                            from models.database import UserScenarioConfigDB
                            async with db_service.async_session() as session:
                                stmt = select(UserScenarioConfigDB).where(
                                    UserScenarioConfigDB.user_id == user_id
                                )
                                result = await session.execute(stmt)
                                user_scenario_config = result.scalar_one_or_none()
                                
                                if user_scenario_config and user_scenario_config.scenario_ids:
                                    try:
                                        scenario_ids = json.loads(user_scenario_config.scenario_ids)
                                        if scenario_ids and len(scenario_ids) > 0:
                                            user_scenario_ids = scenario_ids
                                            logger.info(f"[session_query_stream] Found scenario_ids in UserScenarioConfigDB: {scenario_ids}")
                                            
                                            # 如果只有一个场景，直接使用
                                            if len(scenario_ids) == 1:
                                                scenario_id = scenario_ids[0]
                                                logger.info(f"[session_query_stream] Only one scenario configured, using: {scenario_id}")
                                            # 如果有多个场景，且用户提供了查询内容，进行智能匹配
                                            elif len(scenario_ids) > 1 and request.prompt:
                                                logger.info(f"[session_query_stream] Multiple scenarios configured ({len(scenario_ids)}), will use intelligent matching based on user query")
                                                # 场景匹配逻辑将在后面执行（在 system_prompt is None 时）
                                            # 如果有多个场景但没有用户查询，使用第一个（向后兼容）
                                            else:
                                                scenario_id = scenario_ids[0]
                                                logger.info(f"[session_query_stream] Multiple scenarios configured but no user query, using first: {scenario_id}")
                                    except json.JSONDecodeError:
                                        logger.warning(f"[session_query_stream] Failed to parse scenario_ids JSON: {user_scenario_config.scenario_ids}")
                        except Exception as e:
                            logger.warning(f"[session_query_stream] Failed to load UserScenarioConfigDB: {e}")
                    
                    # 方案3：从用户配置中获取关联的场景（旧方式，向后兼容）
                    if not scenario_id and user_config and user_config.associated_scenario_id:
                        scenario_id = user_config.associated_scenario_id
                        logger.info(f"[session_query_stream] Found associated_scenario_id in user config (backward compatibility): {scenario_id}")
                    
                    # 加载场景配置（如果还没有通过智能匹配加载）
                    matched_scenario_config = None  # 初始化变量
                    scenario_config = None  # 初始化场景配置变量
                    
                    # ========== 智能场景匹配（在 merge_agent_config 之前执行） ==========
                    # 如果用户配置了多个场景，且还没有选择场景，进行智能匹配
                    if request.prompt and user_scenario_ids and len(user_scenario_ids) > 1 and not scenario_id:
                        try:
                            from services.scenario_matcher import ScenarioMatcher
                            matcher = ScenarioMatcher(db_service, agent_service)
                            
                            # 只从用户配置的场景列表中进行匹配
                            logger.info(f"[session_query_stream] 🔍 开始智能匹配场景，从用户配置的 {len(user_scenario_ids)} 个场景中选择: {user_scenario_ids}")
                            
                            # 获取这些场景的详细信息
                            available_scenarios = []
                            for sid in user_scenario_ids:
                                try:
                                    scenario_info = await config_manager.get_business_scenario(sid)
                                    if scenario_info:
                                        available_scenarios.append({
                                            "id": scenario_info.id,  # 使用整数ID
                                            "name": scenario_info.name,
                                            "description": scenario_info.description or "",
                                            "category": scenario_info.category or "",
                                            "meta": getattr(scenario_info, 'meta', None) or {},
                                            "is_default": getattr(scenario_info, 'is_default', False),
                                        })
                                except Exception as e:
                                    logger.warning(f"[session_query_stream] Failed to load scenario {sid} for matching: {e}")
                            
                            if available_scenarios:
                                # 使用 ScenarioMatcher 的模型匹配能力，但只从用户配置的场景中选择
                                matched_scenario = await matcher._match_with_model(
                                    request.prompt,
                                    available_scenarios,
                                    agent_service
                                )
                                
                                if matched_scenario:
                                    scenario_id = matched_scenario.get("id")  # 使用整数ID
                                    scenario_name = matched_scenario.get("name", "未知场景")
                                    logger.info(
                                        f"[session_query_stream] ✅ 智能匹配到场景: "
                                        f"{scenario_name} "
                                        f"(id: {scenario_id})"
                                    )
                                    
                                    # 立即加载匹配的场景配置
                                    try:
                                        matched_scenario_config = await config_manager.get_business_scenario(scenario_id)
                                        if matched_scenario_config:
                                            scenario_config = matched_scenario_config  # 设置场景配置
                                            logger.info(
                                                f"[session_query_stream] ✅ 已加载智能匹配的场景配置: "
                                                f"{matched_scenario_config.name}"
                                            )
                                            # 打印详细报告
                                            logger.info("=" * 80)
                                            logger.info("📋 智能场景匹配详细报告")
                                            logger.info("=" * 80)
                                            logger.info(f"🎯 选中的场景名称: {matched_scenario_config.name}")
                                            logger.info(f"🆔 场景ID: {matched_scenario_config.id}")
                                            logger.info(f"📝 场景描述: {matched_scenario_config.description or '无描述'}")
                                            logger.info(f"🏷️  场景分类: {matched_scenario_config.category or '无分类'}")
                                            
                                            # 打印场景的 system_prompt
                                            if matched_scenario_config.system_prompt:
                                                prompt_preview = matched_scenario_config.system_prompt[:200] + "..." if len(matched_scenario_config.system_prompt) > 200 else matched_scenario_config.system_prompt
                                                logger.info(f"💬 场景 System Prompt (长度: {len(matched_scenario_config.system_prompt)}):")
                                                logger.info(f"   {prompt_preview}")
                                            else:
                                                logger.info("💬 场景 System Prompt: 无")
                                            
                                            # 打印 Skills
                                            if matched_scenario_config.skills:
                                                logger.info(f"🛠️  场景 Skills ({len(matched_scenario_config.skills)}个): {matched_scenario_config.skills}")
                                            else:
                                                logger.info("🛠️  场景 Skills: 无")
                                            
                                            # 打印 Custom Tools (MCP)
                                            if matched_scenario_config.custom_tools:
                                                logger.info(f"🔧 场景 Custom Tools (MCP): {matched_scenario_config.custom_tools}")
                                            else:
                                                logger.info("🔧 场景 Custom Tools (MCP): 无")
                                            
                                            # 打印 Allowed Tools
                                            if matched_scenario_config.allowed_tools:
                                                try:
                                                    # allowed_tools 是 JSON 字符串，需要解析
                                                    tools_list = json.loads(matched_scenario_config.allowed_tools) if isinstance(matched_scenario_config.allowed_tools, str) else matched_scenario_config.allowed_tools
                                                    logger.info(f"✅ 场景 Allowed Tools ({len(tools_list)}个): {tools_list}")
                                                except (json.JSONDecodeError, TypeError) as e:
                                                    logger.warning(f"⚠️  场景 Allowed Tools 解析失败: {e}, 原始值: {matched_scenario_config.allowed_tools}")
                                                    logger.info(f"✅ 场景 Allowed Tools (原始值): {matched_scenario_config.allowed_tools}")
                                            else:
                                                logger.info("✅ 场景 Allowed Tools: 无")
                                            
                                            logger.info("=" * 80)
                                    except Exception as e:
                                        logger.warning(f"[session_query_stream] 加载智能匹配场景配置失败: {e}")
                                else:
                                    # 如果模型没有匹配到，使用第一个场景（默认场景）
                                    scenario_id = user_scenario_ids[0]
                                    logger.info(f"[session_query_stream] 模型未匹配到场景，使用第一个场景: {scenario_id}")
                                    
                                    # 加载第一个场景的配置
                                    try:
                                        matched_scenario_config = await config_manager.get_business_scenario(scenario_id)
                                        if matched_scenario_config:
                                            scenario_config = matched_scenario_config
                                            logger.info(
                                                f"[session_query_stream] ✅ 已加载默认场景配置: "
                                                f"{matched_scenario_config.name}"
                                            )
                                    except Exception as e:
                                        logger.warning(f"[session_query_stream] 加载默认场景配置失败: {e}")
                        except Exception as e:
                            logger.warning(f"[session_query_stream] 智能场景匹配失败: {e}, 使用第一个场景", exc_info=True)
                            if user_scenario_ids:
                                scenario_id = user_scenario_ids[0]
                                # 加载第一个场景的配置
                                try:
                                    matched_scenario_config = await config_manager.get_business_scenario(scenario_id)
                                    if matched_scenario_config:
                                        scenario_config = matched_scenario_config
                                except Exception as e2:
                                    logger.warning(f"[session_query_stream] 加载默认场景配置失败: {e2}")
                    
                    # 如果已经有明确的 scenario_id，加载场景配置
                    if scenario_id and not scenario_config:
                        try:
                            scenario_config = await config_manager.get_business_scenario(scenario_id)
                            if scenario_config:
                                logger.info(f"[session_query_stream] ✅ Loaded scenario config: id={scenario_config.id}, name={scenario_config.name}")
                                logger.info(f"[session_query_stream] Scenario allowed_tools: {scenario_config.allowed_tools}")
                                logger.info(f"[session_query_stream] Scenario custom_tools: {scenario_config.custom_tools}")
                                logger.info(f"[session_query_stream] Scenario skills: {scenario_config.skills}")
                            else:
                                logger.warning(f"[session_query_stream] Scenario not found: id={scenario_id}")
                        except Exception as e:
                            logger.error(f"[session_query_stream] Failed to load scenario config: {e}", exc_info=True)
                    elif not scenario_id:
                        logger.info(f"[session_query_stream] No scenario_id provided (neither in request nor user config), will try auto-match if user_query provided")
                    
                    # Merge configurations（在智能匹配之后）
                    agent_config, config_sources = config_manager.merge_agent_config(
                        request_config=request_config,
                        session_config=session_config,
                        user_config=user_config,
                        scenario_config=scenario_config,  # 传递场景配置（可能来自智能匹配）
                    )
                    
                    # 如果 system_prompt 为 None，使用 prompt_composer 生成默认的 system_prompt
                    # 核心原则0：不改变现有问答逻辑，只是增强默认行为
                    if agent_config.system_prompt is None:
                        try:
                            prompt_composer = PromptComposer(db_service)
                            
                            # 如果没有通过用户配置场景匹配，尝试全局自动匹配
                            if request.prompt and not scenario_config and not scenario_id:
                                try:
                                    from services.scenario_matcher import ScenarioMatcher
                                    matcher = ScenarioMatcher(db_service, agent_service)
                                    matched_scenario = await matcher.match_scenario(
                                        request.prompt, 
                                        user_id,
                                        agent_service=agent_service
                                    )
                                    if matched_scenario:
                                        scenario_id = matched_scenario.get("id")  # 使用整数ID
                                        scenario_name = matched_scenario.get("name", "未知场景")
                                        logger.info(
                                            f"[session_query_stream] ✅ 自动匹配到场景: "
                                            f"{scenario_name} "
                                            f"(scenario_id: {scenario_id})"
                                        )
                                        
                                        # 立即加载匹配的场景配置
                                        try:
                                            matched_scenario_config = await config_manager.get_business_scenario(scenario_id)
                                            if matched_scenario_config:
                                                scenario_config = matched_scenario_config
                                                logger.info(
                                                    f"[session_query_stream] ✅ 已加载匹配场景配置: "
                                                    f"{matched_scenario_config.name}"
                                                )
                                                # 重新合并配置
                                                agent_config, config_sources = config_manager.merge_agent_config(
                                                    request_config=request_config,
                                                    session_config=session_config,
                                                    user_config=user_config,
                                                    scenario_config=scenario_config,
                                                )
                                        except Exception as e:
                                            logger.warning(f"[session_query_stream] 加载匹配场景配置失败: {e}")
                                except Exception as e:
                                    logger.warning(f"[session_query_stream] 场景匹配失败: {e}")
                            
                            # 如果匹配到场景并成功加载配置，打印详细报告
                            if scenario_config:
                                # ========== 场景匹配详细报告 ==========
                                logger.info("=" * 80)
                                logger.info("📋 场景匹配详细报告")
                                logger.info("=" * 80)
                                logger.info(f"🎯 选中的场景名称: {scenario_config.name}")
                                logger.info(f"🆔 场景ID: {scenario_config.id}")
                                logger.info(f"📝 场景描述: {scenario_config.description or '无描述'}")
                                logger.info(f"🏷️  场景分类: {scenario_config.category or '无分类'}")
                                
                                # 打印场景的 system_prompt
                                if scenario_config.system_prompt:
                                    prompt_preview = scenario_config.system_prompt[:200] + "..." if len(scenario_config.system_prompt) > 200 else scenario_config.system_prompt
                                    logger.info(f"💬 场景 System Prompt (长度: {len(scenario_config.system_prompt)}):")
                                    logger.info(f"   {prompt_preview}")
                                else:
                                    logger.info("💬 场景 System Prompt: 无")
                                
                                # 打印 Skills
                                if scenario_config.skills:
                                    logger.info(f"🛠️  场景 Skills ({len(scenario_config.skills)}个):")
                                    for skill in scenario_config.skills:
                                        logger.info(f"   - {skill}")
                                else:
                                    logger.info("🛠️  场景 Skills: 无")
                                
                                # 打印 MCP (custom_tools)
                                if scenario_config.custom_tools:
                                    logger.info(f"🔌 场景 MCP Tools (custom_tools):")
                                    tools_str = json.dumps(scenario_config.custom_tools, indent=2, ensure_ascii=False)
                                    # 如果太长，只显示前500字符
                                    if len(tools_str) > 500:
                                        tools_str = tools_str[:500] + "..."
                                    logger.info(f"   {tools_str}")
                                else:
                                    logger.info("🔌 场景 MCP Tools: 无")
                                
                                # 打印其他重要参数
                                logger.info("⚙️  其他场景参数:")
                                logger.info(f"   - allowed_tools: {scenario_config.allowed_tools or '无'}")
                                logger.info(f"   - recommended_model: {scenario_config.recommended_model or '无'}")
                                logger.info(f"   - permission_mode: {scenario_config.permission_mode or '无'}")
                                logger.info(f"   - max_turns: {scenario_config.max_turns or '无'}")
                                logger.info(f"   - work_dir: {scenario_config.work_dir or '无'}")
                                if scenario_config.workflow:
                                    logger.info(f"   - workflow: {json.dumps(scenario_config.workflow, ensure_ascii=False)[:200]}...")
                                else:
                                    logger.info(f"   - workflow: 无")
                                
                                # 打印合并后的配置来源
                                logger.info("📊 配置来源 (优先级从高到低):")
                                for key, source in config_sources.items():
                                    logger.info(f"   - {key}: {source}")
                                
                                # 打印最终应用的配置摘要
                                logger.info("✅ 最终应用的配置摘要:")
                                logger.info(f"   - system_prompt 长度: {len(agent_config.system_prompt) if agent_config.system_prompt else 0}")
                                logger.info(f"   - allowed_tools: {agent_config.allowed_tools or '无'}")
                                logger.info(f"   - model: {agent_config.model or '无'}")
                                logger.info(f"   - enabled_skill_ids: {agent_config.enabled_skill_ids or '无'}")
                                logger.info(f"   - custom_tools: {'有' if agent_config.custom_tools else '无'}")
                                logger.info("=" * 80)
                                # ========== 场景匹配详细报告结束 ==========
                            
                            # 组合 prompt
                            # 如果已经匹配到场景并加载了配置，则不再自动匹配（避免重复）
                            auto_match = not scenario_config
                            composed_prompt = await prompt_composer.compose_base_prompt(
                                user_id=user_id,
                                session_id=session_id,
                                user_query=request.prompt if request.prompt else None,
                                auto_match_scenario=auto_match,
                                agent_service=agent_service
                            )
                            if composed_prompt:
                                # 如果已经通过场景配置设置了 system_prompt，优先使用场景的 system_prompt
                                # 否则使用组合的 prompt（包含场景详情）
                                if scenario_config and scenario_config.system_prompt:
                                    # 场景有自己的 system_prompt，使用场景的 prompt + 组合 prompt 的场景列表
                                    agent_config.system_prompt = f"{scenario_config.system_prompt}\n\n{composed_prompt}"
                                    config_sources["system_prompt"] = "SCENARIO_WITH_COMPOSED"
                                    logger.info(f"[session_query_stream] ✅ 使用场景 system_prompt + 组合 prompt (length: {len(agent_config.system_prompt)})")
                                else:
                                    # 使用组合的 prompt
                                    agent_config.system_prompt = composed_prompt
                                    config_sources["system_prompt"] = "DEFAULT_COMPOSED"
                                    logger.info(f"[session_query_stream] ✅ Generated default system_prompt using PromptComposer (length: {len(composed_prompt)})")
                        except Exception as e:
                            logger.warning(f"[session_query_stream] Failed to generate default system_prompt using PromptComposer: {e}, will use AgentService default")
                            # 继续使用 AgentService 的默认值，不影响现有逻辑
                    
                    logger.info(f"[session_query_stream] ✅ Applied platform configuration for user_id={current_user.id} BEFORE query")
                    
                    # Save configuration log for this conversation turn
                    try:
                        final_config_dict = {
                            "system_prompt": agent_config.system_prompt,
                            "allowed_tools": agent_config.allowed_tools,
                            "model": agent_config.model,
                            "permission_mode": agent_config.permission_mode,
                            "max_turns": agent_config.max_turns,
                            "cwd": agent_config.cwd,
                            "setting_sources": agent_config.setting_sources,
                            "enabled_skill_ids": agent_config.enabled_skill_ids,
                            "custom_tools": agent_config.custom_tools,
                        }
                        
                        # Get scenario info
                        scenario_id_value = scenario_config.id if scenario_config else None  # 使用整数 id 而不是 scenario_id
                        scenario_name_value = scenario_config.name if scenario_config else None
                        
                        # Save to database (will update session_id later when session is created)
                        await db_service.save_conversation_turn_config(
                            conversation_turn_id=conversation_turn_id,
                            session_id=session_id or "",  # Will be updated when session is created
                            user_id=current_user.id,
                            final_config=final_config_dict,
                            config_sources=config_sources,
                            scenario_id=scenario_id_value,
                            scenario_name=scenario_name_value,
                        )
                        logger.info(f"[session_query_stream] ✅ Saved configuration log for conversation_turn_id={conversation_turn_id}")
                    except Exception as e:
                        logger.error(f"[session_query_stream] Failed to save configuration log: {e}", exc_info=True)
                        # Don't fail the request if config logging fails
                except Exception as e:
                    logger.error(f"[session_query_stream] ❌ Failed to load platform configuration for user_id={current_user.id}: {e}", exc_info=True)
                    # Continue with default configuration (backward compatible)

            # ==================== File Upload and Reference Processing ====================
            # 文件处理逻辑：如果失败，不影响核心对话功能，继续使用原始 prompt
            enhanced_prompt = request.prompt
            uploaded_doc_ids = []
            pending_file_events = []  # 存储待保存的文件事件（当 session_id 可用时保存）
            
            # 1. Process file uploads (if any) - 错误处理：失败不影响对话
            if request.attachments and current_user:
                try:
                    file_upload_service = FileUploadService(db_service)
                    for attachment in request.attachments:
                        try:
                            # 文件上传时 session_id 可以为 None（第一次对话时）
                            # conversation_turn_id 是必需的，已在请求开始时生成
                            result = await file_upload_service.save_file_from_base64(
                                base64_data=attachment.data,
                                file_name=attachment.name,
                                user_id=current_user.id,
                                session_id=session_id,  # 可以是 None
                                conversation_turn_id=conversation_turn_id,  # 必需
                            )
                            uploaded_doc_ids.append(result["doc_id"])
                            
                            if result.get("is_existing", False):
                                logger.info(f"[session_query_stream] ✅ File already exists: {result['file_name']} (doc_id: {result['doc_id']})")
                            else:
                                logger.info(f"[session_query_stream] ✅ Uploaded file: {result['file_name']} (doc_id: {result['doc_id']})")
                            
                            # Yield file event to frontend (无论文件是否已存在，都发送事件)
                            # Get file path for the event
                            file_content_loader = FileContentLoader(db_service)
                            file_path = file_content_loader.get_file_path(result['doc_id'], result['file_name'])
                            
                            # 使用 StreamChunk 格式保持一致性
                            file_event_data = {
                                    'type': 'file_uploaded',
                                    'doc_id': result['doc_id'],
                                    'file_name': result['file_name'],
                                    'file_type': result['file_type'],
                                    'file_size': result['file_size'],
                                'file_path': str(file_path),
                                    'conversation_turn_id': conversation_turn_id,
                                'is_existing': result.get("is_existing", False),
                            }
                            chunk = StreamChunk(type="file_uploaded", data=file_event_data)
                            logger.info(f"[session_query_stream] 📤 Sending file event to frontend: {result['file_name']} (doc_id: {result['doc_id']}, is_existing: {result.get('is_existing', False)}, file_path: {file_path})")
                            yield f"data: {chunk.model_dump_json()}\n\n"
                            
                            # 保存文件事件到数据库（用于对话历史恢复）
                            # 注意：此时 session_id 可能还是 None（第一次对话），需要延迟保存
                            if session_id:
                                try:
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type="file_uploaded",
                                        content=str(file_path),
                                        extra_data={
                                            "file_path": str(file_path),
                                            "file_url": result.get("file_url"),
                                            "file_name": result['file_name'],
                                            "file_size": result['file_size'],
                                            "file_type": result['file_type'],
                                            "doc_id": result['doc_id'],
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    logger.debug(f"[session_query_stream] ✅ Saved file_uploaded event to database: {result['file_name']}")
                                except Exception as e:
                                    logger.warning(f"[session_query_stream] Failed to save file_uploaded event to database: {e}")
                            else:
                                # session_id 还未创建，保存到待处理列表，稍后通过 deferred binding 保存
                                pending_file_events.append({
                                    "file_path": str(file_path),
                                    "file_url": result.get("file_url"),
                                    "file_name": result['file_name'],
                                    "file_size": result['file_size'],
                                    "file_type": result['file_type'],
                                    "doc_id": result['doc_id'],
                                })
                                logger.debug(f"[session_query_stream] ⏳ File event queued for later save: {result['file_name']}")
                        except Exception as e:
                            # 单个文件上传失败，尝试检查文件是否已存在
                            logger.warning(f"[session_query_stream] File upload failed for {attachment.name}, checking if file exists: {e}")
                            
                            # Try to find existing file by hash
                            try:
                                import hashlib
                                import base64 as b64
                                # Decode to get file hash
                                if ',' in attachment.data:
                                    base64_data = attachment.data.split(',')[1]
                                else:
                                    base64_data = attachment.data
                                file_data = b64.b64decode(base64_data)
                                file_hash = hashlib.sha256(file_data).hexdigest()[:16]
                                doc_id = f"user-upload-{current_user.id}-{file_hash}"
                                
                                # Check if file exists
                                relationship = await db_service.get_file_relationship(doc_id)
                                if relationship:
                                    uploaded_doc_ids.append(doc_id)
                                    logger.info(f"[session_query_stream] ✅ Found existing file: {relationship.file_name} (doc_id: {doc_id})")
                                    
                                    # Yield file event
                                    # Get file path for the event
                                    file_content_loader = FileContentLoader(db_service)
                                    file_path = file_content_loader.get_file_path(doc_id, relationship.file_name)
                                    
                                    # 使用 StreamChunk 格式保持一致性
                                    file_event_data = {
                                        'type': 'file_uploaded',
                                        'doc_id': doc_id,
                                        'file_name': relationship.file_name,
                                        'file_type': relationship.file_type,
                                        'file_size': relationship.file_size,
                                        'file_path': str(file_path),
                                        'conversation_turn_id': conversation_turn_id,
                                        'is_existing': True,
                                    }
                                    chunk = StreamChunk(type="file_uploaded", data=file_event_data)
                                    logger.info(f"[session_query_stream] 📤 Sending existing file event to frontend: {relationship.file_name} (doc_id: {doc_id}, file_path: {file_path})")
                                    yield f"data: {chunk.model_dump_json()}\n\n"
                                else:
                                    # File doesn't exist, send error
                                    logger.error(f"[session_query_stream] File upload failed and file doesn't exist: {attachment.name}")
                                    error_event_data = {
                                        'type': 'error',
                                        'data': {
                                            'type': 'error',
                                            'message': f'文件上传失败: {attachment.name}',
                                        }
                                    }
                                    yield f"data: {json.dumps(error_event_data)}\n\n"
                            except Exception as recovery_error:
                                logger.error(f"[session_query_stream] Failed to recover from upload error: {recovery_error}")
                                # Send error notification
                            error_event_data = {
                                'type': 'error',
                                'data': {
                                    'type': 'error',
                                    'message': f'文件上传失败: {attachment.name}',
                                }
                            }
                            yield f"data: {json.dumps(error_event_data)}\n\n"
                except Exception as e:
                    # 文件上传服务初始化失败，记录错误但继续对话
                    logger.error(f"[session_query_stream] Failed to process file uploads: {e}", exc_info=True)
                    # 不影响核心功能，继续使用原始 prompt
            
            # 2. Process file references and intents - 错误处理：失败不影响对话
            if current_user:
                try:
                    file_reference_parser = FileReferenceParser()
                    file_intent_detector = FileIntentDetector()
                    file_search_service = FileSearchService(db_service)
                    file_content_loader = FileContentLoader(db_service)
                    
                    # Parse explicit file references
                    explicit_refs = file_reference_parser.parse_references(enhanced_prompt)
                    
                    # Detect file intent
                    intent = file_intent_detector.detect_intent(enhanced_prompt)
                    
                    file_context = ""
                    
                    if explicit_refs:
                        # Process explicit file references
                        for ref in explicit_refs:
                            try:
                                if ref.type == "doc_id":
                                    # For explicit doc_id references, provide file path and summary instead of full content
                                    relationship = await db_service.get_file_relationship(ref.value)
                                    if relationship:
                                        file_path = file_content_loader.get_file_path(ref.value, relationship.file_name)
                                        file_context += f"\n\n文件：{relationship.file_name} (doc_id: {ref.value})\n"
                                        file_context += f"文件路径：{file_path}\n"
                                        if ref.section:
                                            file_context += f"章节：{ref.section}\n"
                                        
                                        # For small files, provide summary; for large files, just path
                                        if relationship.file_size < 10000:  # < 10KB
                                            try:
                                                summary = await file_content_loader.get_file_summary(
                                                    doc_id=ref.value,
                                                    max_lines=50,
                                                    user_id=current_user.id
                                                )
                                                file_context += f"文件预览：\n{summary}\n"
                                            except:
                                                file_context += "（如需查看完整内容，请使用 Read 工具读取上述路径）\n"
                                        else:
                                            file_context += f"文件大小：{relationship.file_size} 字节\n"
                                            file_context += "（文件较大，如需查看内容，请使用 Read 工具读取上述路径）\n"
                                    
                                    # Replace reference in prompt
                                    if ref.original_mention:
                                        enhanced_prompt = enhanced_prompt.replace(
                                            ref.original_mention,
                                            f"[文件: {relationship.file_name}]"
                                        )
                                elif ref.type == "mention":
                                    # @mention format - search by file name
                                    files = await file_search_service.search_by_file_name(
                                        user_id=current_user.id,
                                        session_id=session_id,
                                        file_name=ref.value,
                                        limit=1
                                    )
                                    if files:
                                        file = files[0]
                                        relationship = await db_service.get_file_relationship(file.doc_id)
                                        if relationship:
                                            file_path = file_content_loader.get_file_path(file.doc_id, relationship.file_name)
                                            file_context += f"\n\n文件：{relationship.file_name} (doc_id: {file.doc_id})\n"
                                            file_context += f"文件路径：{file_path}\n"
                                            
                                            # For small files, provide summary; for large files, just path
                                            if relationship.file_size < 10000:  # < 10KB
                                                try:
                                                    summary = await file_content_loader.get_file_summary(
                                                        doc_id=file.doc_id,
                                                        max_lines=50,
                                                        user_id=current_user.id
                                                    )
                                                    file_context += f"文件预览：\n{summary}\n"
                                                except:
                                                    file_context += "（如需查看完整内容，请使用 Read 工具读取上述路径）\n"
                                            else:
                                                file_context += f"文件大小：{relationship.file_size} 字节\n"
                                                file_context += "（文件较大，如需查看内容，请使用 Read 工具读取上述路径）\n"
                                        
                                        # Replace mention in prompt
                                        if ref.original_mention:
                                            enhanced_prompt = enhanced_prompt.replace(
                                                ref.original_mention,
                                                f"[文件: {relationship.file_name}]"
                                            )
                            except Exception as e:
                                # 单个文件引用处理失败，记录错误但继续处理其他引用
                                logger.error(f"[session_query_stream] Failed to process file reference {ref}: {e}", exc_info=True)
                                # 不影响核心功能，继续处理
                    
                    elif intent.needs_search:
                        # Process file query intent
                        if intent.type == "file_query":
                            # Search for files
                            files = await file_search_service.search_by_natural_language(
                                user_id=current_user.id,
                                session_id=session_id,
                                query=enhanced_prompt,
                                limit=5
                            )
                            if files:
                                file_list = "\n\n找到以下相关文件：\n"
                                for i, file in enumerate(files, 1):
                                    file_list += f"{i}. {file.doc_id} - {file.file_name} (上传于 {file.uploaded_at.isoformat() if file.uploaded_at else '未知'})\n"
                                file_context = file_list + "\n请回答用户，并询问用户要查看哪个文件。"
                        elif intent.type == "content_query":
                            # Priority 1: Check if files were uploaded in current turn
                            files = []
                            if uploaded_doc_ids:
                                # Use files uploaded in current turn
                                for doc_id in uploaded_doc_ids:
                                    relationship = await db_service.get_file_relationship(doc_id)
                                    if relationship:
                                        from services.file_search_service import FileInfo
                                        file_info = FileInfo(relationship)
                                        files.append(file_info)
                                logger.info(f"[session_query_stream] Found {len(files)} file(s) uploaded in current turn for content query")
                            
                            # Priority 2: Check files in current conversation turn
                            if not files and conversation_turn_id:
                                try:
                                    turn_files = await db_service.get_turn_files(
                                        conversation_turn_id=conversation_turn_id,
                                        user_id=current_user.id
                                    )
                                    if turn_files:
                                        from services.file_search_service import FileInfo
                                        files = [FileInfo(rel) for rel in turn_files]
                                        logger.info(f"[session_query_stream] Found {len(files)} file(s) in current conversation turn for content query")
                                except Exception as e:
                                    logger.debug(f"[session_query_stream] Failed to get turn files: {e}")
                            
                            # Priority 3: Search by natural language query
                            if not files:
                                files = await file_search_service.search_by_natural_language(
                                    user_id=current_user.id,
                                    session_id=session_id,
                                    query=enhanced_prompt,
                                    limit=1
                                )
                                if files:
                                    logger.info(f"[session_query_stream] Found {len(files)} file(s) via search for content query")
                            
                            if files:
                                file = files[0]
                                relationship = await db_service.get_file_relationship(file.doc_id)
                                if relationship:
                                    file_path = file_content_loader.get_file_path(file.doc_id, relationship.file_name)
                                    file_context = f"\n\n找到相关文件：{relationship.file_name} (doc_id: {file.doc_id})\n"
                                    file_context += f"文件路径：{file_path}\n"
                                    
                                    # Use query-based retrieval to get relevant content snippets
                                    # This is more efficient than loading entire file
                                    try:
                                        relevant_content = await file_content_loader.get_file_content_by_query(
                                            doc_id=file.doc_id,
                                            query=enhanced_prompt,  # Use user query to find relevant snippets
                                            user_id=current_user.id,
                                            max_length=5000,  # Limit content to avoid token overflow
                                        )
                                        file_context += f"\n文件相关内容（基于查询检索）：\n{relevant_content}\n"
                                        enhanced_prompt = f"用户询问关于文件 {relationship.file_name} 的内容：{enhanced_prompt}\n\n文件相关内容（基于查询检索）：\n{relevant_content}"
                                        logger.info(f"[session_query_stream] ✅ Used query-based retrieval for file {file.doc_id}, query: {enhanced_prompt[:100]}")
                                    except Exception as e:
                                        logger.warning(f"[session_query_stream] Query-based retrieval failed, falling back to summary: {e}")
                                        # Fallback to summary for small files
                                    if relationship.file_size < 10000:  # < 10KB
                                        try:
                                            summary = await file_content_loader.get_file_summary(
                                                doc_id=file.doc_id,
                                                    max_lines=100,
                                                user_id=current_user.id
                                            )
                                            file_context += f"文件预览：\n{summary}\n"
                                            enhanced_prompt = f"用户询问关于文件 {relationship.file_name} 的内容：{enhanced_prompt}\n\n文件预览：\n{summary}"
                                        except:
                                            file_context += "（如需查看完整内容，请使用 Read 工具读取上述路径）\n"
                                            enhanced_prompt = f"用户询问关于文件 {relationship.file_name} 的内容：{enhanced_prompt}\n\n文件路径：{file_path}"
                                    else:
                                        file_context += f"文件大小：{relationship.file_size} 字节\n"
                                        file_context += "（文件较大，如需查看内容，请使用 Read 工具读取上述路径）\n"
                                        enhanced_prompt = f"用户询问关于文件 {relationship.file_name} 的内容：{enhanced_prompt}\n\n文件路径：{file_path}"
                    
                    # Add file context to prompt
                    if file_context:
                        enhanced_prompt = enhanced_prompt + file_context
                        logger.info(f"[session_query_stream] ✅ Added file context to prompt (length: {len(file_context)} chars)")
                
                except Exception as e:
                    # 文件引用处理失败，记录错误但继续使用原始 prompt
                    logger.error(f"[session_query_stream] Failed to process file references: {e}", exc_info=True)
                    # 不影响核心功能，继续使用原始 prompt
                    enhanced_prompt = request.prompt
            
            # 3. If files were uploaded in this turn, provide file info and path (NOT full content)
            # This avoids loading large files into prompt, letting Claude use Read tool when needed
            if uploaded_doc_ids and current_user:
                try:
                    file_content_loader = FileContentLoader(db_service)
                    upload_context = "\n\n用户在当前对话中上传了以下文件：\n"
                    for doc_id in uploaded_doc_ids:
                        try:
                            relationship = await db_service.get_file_relationship(doc_id)
                            if relationship:
                                # Get file path
                                file_path = file_content_loader.get_file_path(doc_id, relationship.file_name)
                                
                                # For small text files (< 5KB), provide a summary
                                # For larger files, just provide path and let Claude use Read tool
                                if relationship.file_size < 5000 and relationship.file_type.startswith('text/'):
                                    try:
                                        summary = await file_content_loader.get_file_summary(
                                            doc_id=doc_id,
                                            max_lines=30,  # Only first 30 lines
                                            user_id=current_user.id
                                        )
                                        upload_context += f"\n文件：{relationship.file_name}\n"
                                        upload_context += f"文件路径：{file_path}\n"
                                        upload_context += f"文件大小：{relationship.file_size} 字节\n"
                                        upload_context += f"文件类型：{relationship.file_type}\n"
                                        upload_context += f"文件预览（前30行）：\n{summary}\n"
                                        upload_context += "---\n"
                                    except Exception as e:
                                        logger.warning(f"[session_query_stream] Failed to get file summary for {doc_id}: {e}")
                                        # Fallback to just path info
                                        upload_context += f"\n文件：{relationship.file_name}\n"
                                        upload_context += f"文件路径：{file_path}\n"
                                        upload_context += f"文件大小：{relationship.file_size} 字节\n"
                                        upload_context += f"文件类型：{relationship.file_type}\n"
                                        upload_context += "（如需查看文件内容，请使用 Read 工具读取上述路径）\n"
                                        upload_context += "---\n"
                                else:
                                    # For larger files or non-text files, just provide path
                                    upload_context += f"\n文件：{relationship.file_name}\n"
                                    upload_context += f"文件路径：{file_path}\n"
                                    upload_context += f"文件大小：{relationship.file_size} 字节\n"
                                    upload_context += f"文件类型：{relationship.file_type}\n"
                                    upload_context += "（如需查看文件内容，请使用 Read 工具读取上述路径）\n"
                                    upload_context += "---\n"
                        except Exception as e:
                            logger.error(f"[session_query_stream] Failed to process uploaded file {doc_id}: {e}", exc_info=True)
                            # If processing fails, at least mention the file
                            try:
                                relationship = await db_service.get_file_relationship(doc_id)
                                if relationship:
                                    upload_context += f"\n文件：{relationship.file_name} (doc_id: {doc_id}) - 文件信息获取失败\n"
                            except:
                                pass
                    
                    enhanced_prompt = enhanced_prompt + upload_context
                    logger.info(f"[session_query_stream] ✅ Added uploaded file info to prompt (files: {len(uploaded_doc_ids)}, NOT loading full content)")
                except Exception as e:
                    logger.error(f"[session_query_stream] Failed to process uploaded files: {e}", exc_info=True)
                    # Fallback: just mention files without details
                    upload_context = "\n\n用户在当前对话中上传了以下文件：\n"
                    for doc_id in uploaded_doc_ids:
                        try:
                            relationship = await db_service.get_file_relationship(doc_id)
                            if relationship:
                                upload_context += f"- {relationship.file_name} (doc_id: {doc_id})\n"
                        except:
                            pass
                    enhanced_prompt = enhanced_prompt + upload_context

            # 🚀 开始查询（在主 try 块内）
            async for msg in agent_service.query_in_session(
                prompt=enhanced_prompt,  # Use enhanced prompt with file context
                session_id=session_id or "",  # Empty string for first query
                include_partial_messages=request.incremental_stream,  # 传递增量流式参数
                session_manager=session_mgr,  # 传递 session_manager 用于检查消息记录
                agent_config=agent_config,  # 传递平台配置
                user_id=current_user.id if current_user else None,  # 传递 user_id 用于生成 work_dir
            ):
                # 处理 SystemMessage - 提取 session_id（第一次查询时）
                if isinstance(msg, SystemMessage) and msg.subtype == "init":
                    # 从 SystemMessage 的 data 中提取 session_id
                    if isinstance(msg.data, dict) and "session_id" in msg.data:
                        extracted_session_id = msg.data.get("session_id")
                        if extracted_session_id and not session_id:
                            session_id = extracted_session_id
                            logger.info(f"[session_query_stream] Extracted session_id from SystemMessage: {session_id}")
                            
                            # ==================== 延迟绑定 session_id ====================
                            # 当 session_id 可用时，批量更新 conversation_turn_id 相关的记录
                            if current_user:
                                try:
                                    updated_count = await db_service.update_session_id_for_turn(
                                        conversation_turn_id=conversation_turn_id,
                                        session_id=session_id,
                                        user_id=current_user.id
                                    )
                                    logger.info(
                                        f"[session_query_stream] ✅ Bound session_id={session_id} "
                                        f"to {updated_count} records for conversation_turn_id={conversation_turn_id}"
                                    )
                                    
                                    # 保存待处理的文件事件到数据库
                                    if pending_file_events:
                                        for file_event in pending_file_events:
                                            try:
                                                file_content_loader = FileContentLoader(db_service)
                                                file_path = file_content_loader.get_file_path(file_event['doc_id'], file_event['file_name'])
                                                await session_mgr.save_message(
                                                    session_id=session_id,
                                                    role="assistant",
                                                    message_type="file_uploaded",
                                                    content=str(file_path),
                                                    extra_data={
                                                        "file_path": str(file_path),
                                                        "file_url": file_event.get("file_url"),
                                                        "file_name": file_event['file_name'],
                                                        "file_size": file_event['file_size'],
                                                        "file_type": file_event['file_type'],
                                                        "doc_id": file_event['doc_id'],
                                                    },
                                                    conversation_turn_id=conversation_turn_id,
                                                )
                                                logger.debug(f"[session_query_stream] ✅ Saved queued file_uploaded event: {file_event['file_name']}")
                                            except Exception as e:
                                                logger.warning(f"[session_query_stream] Failed to save queued file event: {e}")
                                        logger.info(f"[session_query_stream] ✅ Saved {len(pending_file_events)} queued file events to database")
                                        pending_file_events.clear()
                                except Exception as e:
                                    logger.error(
                                        f"[session_query_stream] Failed to bind session_id: {e}", 
                                        exc_info=True
                                    )
                                    # 不影响核心功能，继续执行
                            
                            # 创建会话记录（如果还没有创建）
                            if not session_created:
                                try:
                                    # 从数据库检查会话是否已存在
                                    db_session = await db_service.get_session(session_id)
                                    if not db_session:
                                        # 创建新的会话记录，绑定到当前用户
                                        user_id = current_user.id if current_user else None
                                        
                                        # Note: conversation_turn_config 的 session_id 已在上面批量更新
                                        # 这里只需要创建会话记录
                                        await db_service.create_session(
                                            session_id=session_id,
                                            user_id=user_id,
                                            system_prompt=agent_config.system_prompt if agent_config else None,
                                            model=agent_config.model if agent_config else None,
                                            allowed_tools=agent_config.allowed_tools if agent_config else None,
                                            permission_mode=agent_config.permission_mode if agent_config else None,
                                            max_turns=agent_config.max_turns if agent_config else None,
                                        )
                                        logger.info(f"[session_query_stream] ✅ Created session record: {session_id} for user: {user_id}")
                                    else:
                                        logger.info(f"[session_query_stream] Session {session_id} already exists in database")
                                    
                                    session_created = True
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Failed to create session record: {e}", exc_info=True)
                                    # 不影响核心功能，继续执行
                            
                            # 更新已保存的用户消息的 session_id（如果有）
                            if user_message_saved and user_message_id:
                                try:
                                    # 用户消息的 session_id 应该已经正确设置（如果有 session_id）
                                    # 这里主要是确保 conversation_turn_id 正确关联
                                    pass  # 用户消息已在保存时设置了正确的 session_id
                                except Exception as e:
                                    logger.warning(f"[session_query_stream] Failed to update user message: {e}")
                                    
                            # 保存用户消息（如果还没有保存，现在有了 session_id）
                            if not user_message_saved:
                                try:
                                    user_message_id = await session_mgr.save_message(
                                        session_id=session_id,
                                        role="user",
                                        message_type="text",
                                        content=request.prompt,
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    user_message_saved = True
                                    logger.info(f"[session_query_stream] ✅ Saved user message with session_id={session_id}")
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Failed to save user message: {e}", exc_info=True)
                
                # 处理增量流式文本片段
                if isinstance(msg, ContentBlock) and msg.type == "text_delta":
                    # 🔧 修复：收集 text_delta 内容到 assistant_content，确保完整保存
                    if msg.text:
                        assistant_content.append(msg.text)
                    chunk = StreamChunk(type="text_delta", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                elif isinstance(msg, ContentBlock) and msg.type == "tool_start":
                    # 🔧 处理工具调用开始事件，维护 index -> tool_use_id 映射
                    logger.info(f"[session_query_stream] 🔍 Received tool_start: tool_use_id={msg.tool_use_id[:20]}..., tool_input={msg.tool_input}")
                    if msg.tool_input and isinstance(msg.tool_input, dict) and '_index' in msg.tool_input:
                        index = msg.tool_input.pop('_index')  # 移除临时添加的 index
                        tool_use_index_map[index] = msg.tool_use_id
                        logger.info(f"[session_query_stream] ✅ Mapped tool_use: index={index} -> tool_use_id={msg.tool_use_id[:20]}...")
                        
                        # 🔧 先发送 tool_start 事件，让前端建立映射
                        chunk = StreamChunk(type="data", data=msg)
                        chunk_json = chunk.model_dump_json()
                        logger.info(f"[session_query_stream] 📤 发送 tool_start 到前端: chunk_type={chunk.type}, data_type={msg.type}, tool_use_id={msg.tool_use_id[:20]}..., chunk_json_length={len(chunk_json)}")
                        yield f"data: {chunk_json}\n\n"
                        
                        # 🔧 然后处理并发送缓存的 tool_input_delta 事件（确保前端已处理 toolStart）
                        if index in pending_tool_input_deltas:
                            cached_deltas = pending_tool_input_deltas.pop(index)
                            logger.info(f"[session_query_stream] 🔄 Processing {len(cached_deltas)} cached tool_input_delta events for index={index} (after tool_start)")
                            for cached_delta in cached_deltas:
                                # 更新 tool_use_id
                                cached_delta.tool_use_id = msg.tool_use_id
                                chunk = StreamChunk(type="data", data=cached_delta)
                                chunk_json = chunk.model_dump_json()
                                logger.info(f"[session_query_stream] 📤 发送缓存的 tool_input_delta 到前端: chunk_type={chunk.type}, data_type={cached_delta.type}, tool_use_id={msg.tool_use_id[:20]}..., partial_json_length={len(cached_delta.text) if cached_delta.text else 0}, chunk_json_length={len(chunk_json)}")
                                yield f"data: {chunk_json}\n\n"
                    else:
                        logger.warning(f"[session_query_stream] ⚠️ tool_start: tool_input is None or missing _index, tool_input={msg.tool_input}")
                        # 即使没有 _index，也发送 tool_start 事件
                        chunk = StreamChunk(type="data", data=msg)
                        yield f"data: {chunk.model_dump_json()}\n\n"
                elif isinstance(msg, ContentBlock) and msg.type == "tool_input_delta":
                    # 🔧 处理工具调用的流式输入更新（input_json_delta）
                    # msg.tool_use_id 临时存储的是 index（字符串形式）
                    index = int(msg.tool_use_id) if msg.tool_use_id and msg.tool_use_id.isdigit() else None
                    logger.info(f"[session_query_stream] 🔍 Received tool_input_delta: index={index}, tool_use_id={msg.tool_use_id}, tool_use_index_map={list(tool_use_index_map.keys())}")
                    if index is not None and index in tool_use_index_map:
                        # 找到对应的 tool_use_id，更新 ContentBlock
                        actual_tool_use_id = tool_use_index_map[index]
                        msg.tool_use_id = actual_tool_use_id
                        logger.info(f"[session_query_stream] ✅ Found mapping: index={index} -> tool_use_id={actual_tool_use_id[:20]}..., sending to frontend")
                        chunk = StreamChunk(type="data", data=msg)
                        chunk_json = chunk.model_dump_json()
                        logger.info(f"[session_query_stream] 📤 发送 tool_input_delta 到前端: chunk_type={chunk.type}, data_type={msg.type}, tool_use_id={actual_tool_use_id[:20]}..., partial_json_length={len(msg.text) if msg.text else 0}, chunk_json_length={len(chunk_json)}")
                        yield f"data: {chunk_json}\n\n"
                    else:
                        # 🔧 如果找不到映射，缓存起来，等待 tool_start 事件建立映射
                        if index is not None:
                            if index not in pending_tool_input_deltas:
                                pending_tool_input_deltas[index] = []
                            pending_tool_input_deltas[index].append(msg)
                            logger.info(f"[session_query_stream] ⏳ Cached tool_input_delta: index={index}, waiting for tool_start (total cached: {len(pending_tool_input_deltas[index])})")
                        else:
                            logger.warning(f"[session_query_stream] ⚠️ tool_input_delta: invalid index={index}, tool_use_id={msg.tool_use_id}")
                elif isinstance(msg, ContentBlock) and msg.type == "tool_result":
                    # 处理工具结果，保存到数据库
                    if session_id and msg.tool_use_id:
                        try:
                            # 确保工具输出不为空（如果为 None，使用空字符串）
                            tool_output = msg.text if msg.text is not None else ""
                            await session_mgr.save_message(
                                session_id=session_id,
                                role="assistant",
                                message_type="tool_result",
                                content=tool_output,
                                extra_data={
                                    "tool_use_id": msg.tool_use_id,
                                    "is_error": msg.is_error or False,
                                },
                                conversation_turn_id=conversation_turn_id,
                            )
                            logger.info(
                                f"[session_query_stream] ✅ Saved tool_result: tool_use_id={msg.tool_use_id[:20]}..., "
                                f"content_length={len(tool_output) if tool_output else 0}, "
                                f"content_preview={tool_output[:100] if tool_output else '(empty)'}, "
                                f"conversation_turn_id={conversation_turn_id}"
                            )
                        except Exception as e:
                            logger.error(f"[session_query_stream] Error saving tool_result: {e}")
                    
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                elif isinstance(msg, AssistantMessage):
                    # 收集 AssistantMessage 的内容
                    text_content = ""
                    for block in msg.content:
                        if block.type == "text" and block.text:
                            text_content += block.text
                        elif block.type == "tool_use":
                            # 🔍 重要：保存工具调用到数据库（确保同一 tool_use_id 只保存一次）
                            if session_id and block.tool_use_id and block.tool_use_id not in saved_tool_use_ids:
                                try:
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type="tool_use",
                                        content="",  # tool_use 不需要 content
                                        extra_data={
                                            "tool_use_id": block.tool_use_id,
                                            "tool_name": block.tool_name,
                                            "tool_input": block.tool_input,
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                        parent_message_id=assistant_message_id,  # 关联到 assistant 消息
                                    )
                                    saved_tool_use_ids.add(block.tool_use_id)  # 标记为已保存
                                    logger.info(
                                        f"[session_query_stream] ✅ Saved tool_use: tool_use_id={block.tool_use_id[:20]}..., "
                                        f"tool_name={block.tool_name}, "
                                        f"conversation_turn_id={conversation_turn_id}"
                                    )
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Error saving tool_use: {e}", exc_info=True)
                            
                            # 收集工具调用信息（用于后续处理）
                            tool_calls.append({
                                "tool_use_id": block.tool_use_id,
                                "tool_name": block.tool_name,
                                "tool_input": block.tool_input,
                            })
                        elif block.type == "tool_result":
                            # 处理工具结果，保存到数据库
                            if session_id and block.tool_use_id:
                                try:
                                    # 确保工具输出不为空（如果为 None，使用空字符串）
                                    tool_output = block.text if block.text is not None else ""
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type="tool_result",
                                        content=tool_output,
                                        extra_data={
                                            "tool_use_id": block.tool_use_id,
                                            "is_error": block.is_error or False,
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    logger.info(
                                        f"[session_query_stream] ✅ Saved tool_result: tool_use_id={block.tool_use_id[:20]}..., "
                                        f"content_length={len(tool_output) if tool_output else 0}, "
                                        f"content_preview={tool_output[:100] if tool_output else '(empty)'}, "
                                        f"conversation_turn_id={conversation_turn_id}"
                                    )
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Error saving tool_result: {e}")
                        elif block.type in ["file_created", "file_uploaded"]:
                            # 处理文件事件，设置 conversation_turn_id 并单独推送
                            if not block.conversation_turn_id:
                                block.conversation_turn_id = conversation_turn_id
                            # 单独推送文件事件
                            chunk = StreamChunk(type="file_event", data=block)
                            yield f"data: {chunk.model_dump_json()}\n\n"
                            # 保存文件事件到数据库（可选）
                            if session_id:
                                try:
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type=block.type,
                                        content=block.file_url or block.file_path or "",
                                        extra_data={
                                            "file_path": block.file_path,
                                            "file_url": block.file_url,
                                            "file_name": block.file_name,
                                            "file_size": block.file_size,
                                            "file_type": block.file_type,
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    logger.debug(f"[session_query_stream] Saved {block.type} event")
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Error saving file event: {e}")

                    # 🔧 修复：不要再次 append text_content 到 assistant_content
                    # 因为 text_delta 已经收集了所有文本内容
                    # 如果再次 append，会导致内容重复
                    # assistant_content.append(text_content)  # ← 已删除，避免重复

                    # 发送完整的 AssistantMessage（包含文本内容和 tool_use 块）
                    # 前端会从 AssistantMessage 的 content 中提取 tool_use 块
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                elif isinstance(msg, ResultInfo):
                    # 保存 ResultMessage 信息
                    result_info_dict = {
                        "subtype": msg.subtype,
                        "duration_ms": msg.duration_ms,
                        "duration_api_ms": getattr(msg, 'duration_api_ms', None),
                        "is_error": msg.is_error,
                        "num_turns": msg.num_turns,
                        "session_id": msg.session_id or session_id,  # 使用提取的 session_id
                        "total_cost_usd": msg.total_cost_usd,
                        "usage": getattr(msg, 'usage', None),
                    }
                    # 更新 session_id（如果 ResultInfo 中有）
                    if msg.session_id:
                        session_id = msg.session_id
                    elif not session_id:
                        # 如果还没有 session_id，使用 ResultInfo 中的（可能是空字符串）
                        session_id = msg.session_id
                    
                    # 如果用户消息还没保存，现在保存（因为现在有了 session_id）
                    if not user_message_saved and session_id:
                        user_message_id = await session_mgr.save_message(
                            session_id=session_id,
                            role="user",
                            message_type="text",
                            content=request.prompt,
                            conversation_turn_id=conversation_turn_id,
                        )
                        user_message_saved = True
                    
                    # 保存 AI 消息（包含 result_info）
                    if session_id:
                        try:
                            full_text = "".join(assistant_content)
                            # 清理文本内容，移除文件路径和URL（文件信息已通过文件事件单独保存）
                            cleaned_text = clean_message_text(full_text)
                            
                            # 🔍 调试：记录保存前的状态
                            logger.info(
                                f"[session_query_stream] 🔍 Saving AI message: session_id={session_id}, "
                                f"turn_id={conversation_turn_id}, "
                                f"assistant_content_length={len(assistant_content)}, "
                                f"full_text_length={len(full_text)}, "
                                f"cleaned_text_length={len(cleaned_text)}, "
                                f"user_message_id={user_message_id}, "
                                f"tool_calls_count={len(tool_calls)}"
                            )
                            
                            assistant_message_id = await session_mgr.save_message(
                                session_id=session_id,
                                role="assistant",
                                message_type="text",
                                content=cleaned_text,
                                result_info=result_info_dict,
                                conversation_turn_id=conversation_turn_id,
                                parent_message_id=user_message_id,
                            )
                            
                            logger.info(
                                f"[session_query_stream] ✅ Saved AI message: message_id={assistant_message_id}, "
                                f"content_preview={cleaned_text[:100] if cleaned_text else '(empty)'}"
                            )
                            
                            # 保存工具调用（tool_use）
                            for tool_call in tool_calls:
                                try:
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type="tool_use",
                                        content=None,
                                        extra_data={
                                            "tool_use_id": tool_call["tool_use_id"],
                                            "tool_name": tool_call["tool_name"],
                                            "tool_input": tool_call["tool_input"],
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                        parent_message_id=assistant_message_id,
                                    )
                                except Exception as tool_error:
                                    logger.error(f"[session_query_stream] ❌ Failed to save tool_call: {tool_error}", exc_info=True)
                            
                            logger.info(f"[session_query_stream] ✅ Saved messages for session: {session_id}, turn_id: {conversation_turn_id}, ai_message_id: {assistant_message_id}, tool_calls: {len(tool_calls)}")
                        except Exception as e:
                            logger.error(f"[session_query_stream] ❌ Failed to save AI message: {e}", exc_info=True)
                    else:
                        logger.warning(f"[session_query_stream] ⚠️ Cannot save AI message: session_id is None, turn_id: {conversation_turn_id}")
                    
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                elif isinstance(msg, UserMessage):
                    # 处理 UserMessage（包含工具结果，可能包含文件事件）
                    for block in msg.content:
                        if block.type == "tool_result":
                            # 🔍 重要：处理 UserMessage 中的工具结果，保存到数据库
                            if session_id and block.tool_use_id:
                                try:
                                    # ContentBlock 中的工具结果存储在 text 字段中（不是 content 字段）
                                    # 因为 _convert_sdk_message 已经将 ToolResultBlock.content 格式化为 text
                                    tool_output = block.text if hasattr(block, 'text') and block.text is not None else ""
                                    
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type="tool_result",
                                        content=tool_output,
                                        extra_data={
                                            "tool_use_id": block.tool_use_id,
                                            "is_error": getattr(block, 'is_error', False) or False,
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    logger.info(
                                        f"[session_query_stream] ✅ Saved tool_result from UserMessage: tool_use_id={block.tool_use_id[:20]}..., "
                                        f"content_length={len(tool_output) if tool_output else 0}, "
                                        f"content_preview={tool_output[:100] if tool_output else '(empty)'}, "
                                        f"conversation_turn_id={conversation_turn_id}"
                                    )
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Error saving tool_result from UserMessage: {e}", exc_info=True)
                            
                            # 发送工具结果到前端
                            chunk = StreamChunk(type="data", data=block)
                            yield f"data: {chunk.model_dump_json()}\n\n"
                        elif block.type in ["file_created", "file_uploaded"]:
                            # 处理文件事件，设置 conversation_turn_id 并单独推送
                            if not block.conversation_turn_id:
                                block.conversation_turn_id = conversation_turn_id
                            # 单独推送文件事件
                            chunk = StreamChunk(type="file_event", data=block)
                            yield f"data: {chunk.model_dump_json()}\n\n"
                            # 保存文件事件到数据库（可选）
                            if session_id:
                                try:
                                    await session_mgr.save_message(
                                        session_id=session_id,
                                        role="assistant",
                                        message_type=block.type,
                                        content=block.file_url or block.file_path or "",
                                        extra_data={
                                            "file_path": block.file_path,
                                            "file_url": block.file_url,
                                            "file_name": block.file_name,
                                            "file_size": block.file_size,
                                            "file_type": block.file_type,
                                        },
                                        conversation_turn_id=conversation_turn_id,
                                    )
                                    logger.debug(f"[session_query_stream] Saved {block.type} event from UserMessage")
                                except Exception as e:
                                    logger.error(f"[session_query_stream] Error saving file event from UserMessage: {e}")
                    # 发送完整的 UserMessage
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                else:
                    chunk = StreamChunk(type="data", data=msg)
                    yield f"data: {chunk.model_dump_json()}\n\n"

            logger.info(f"[session_query_stream] Query completed for session {session_id or 'new session'}")

            # 发送流结束标记
            end_chunk = StreamChunk(type="end", data={"status": "completed"})
            yield f"data: {end_chunk.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(f"Error in session_query_stream: {e}")
            error_chunk = StreamChunk(
                type="error",
                data=ErrorResponse(error=str(e))
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    Delete an existing session
    
    Only the session owner can delete their session.
    """
    # 从数据库获取会话（验证用户权限）
    # 允许删除不活跃的会话
    db_session = await db_service.get_session(session_id, include_inactive=True)
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # 验证会话属于当前用户
    if current_user:
        if db_session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this session"
            )
    elif db_session.user_id is not None:
        # 会话已绑定用户，但当前请求未认证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to delete this session"
        )
    
    deleted = await session_mgr.remove_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return None


@router.get("/sessions")
async def list_sessions(
    limit: Optional[int] = None,
    offset: int = 0,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    List all active sessions for the current user with pagination
    
    If user is authenticated, returns only their sessions.
    If not authenticated, returns empty list.
    
    Query Parameters:
        limit: Maximum number of sessions to return (default: None, returns all)
        offset: Number of sessions to skip (default: 0)
    
    Returns:
        {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": bool,
            "sessions": [...]
        }
    """
    if not current_user:
        logger.warning("[list_sessions] No authenticated user, returning empty list")
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False,
            "sessions": []
        }
    
    logger.info(f"[list_sessions] Getting sessions for user: {current_user.id} ({current_user.username}), limit={limit}, offset={offset}")
    
    # 从数据库获取用户的会话（分页）
    from sqlalchemy import select, func
    from models.database import SessionDB
    
    async with db_service.async_session() as session:
        # 先获取总数（包括不活跃的会话，因为用户可能想查看历史）
        count_stmt = select(func.count(SessionDB.session_id)).where(
            SessionDB.user_id == current_user.id
        )
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar() or 0
        logger.info(f"[list_sessions] Total sessions count for user {current_user.id}: {total_count}")
        
        # 查找用户的所有会话（包括不活跃的），支持分页
        stmt = select(SessionDB).where(
            SessionDB.user_id == current_user.id
        ).order_by(SessionDB.last_activity.desc())
        
        if offset > 0:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        
        result = await session.execute(stmt)
        db_sessions = list(result.scalars().all())
        logger.info(f"[list_sessions] Found {len(db_sessions)} sessions (offset={offset}, limit={limit}) for user {current_user.id}, total={total_count}")
    
    sessions = [
        {
            "session_id": s.session_id,
            "created_at": format_utc_timestamp(s.created_at),
            "last_activity": format_utc_timestamp(s.last_activity),
            "is_connected": s.is_connected,
            "model": s.model,
        }
        for s in db_sessions
    ]
    
    # 计算是否有更多数据
    has_more = (offset + len(sessions)) < total_count if limit else False
    
    # 计算统计信息（只在第一页时计算，避免性能问题）
    # 统计信息基于所有会话，而不是当前页
    stats = None
    if offset == 0:  # 只在第一页计算统计信息
        total_messages = 0
        total_cost = 0.0
        
        # 获取所有会话的消息数和花费（基于所有会话，不是当前页）
        from models.database import MessageDB
        async with db_service.async_session() as session:
            # 获取用户的所有会话ID（用于统计）
            all_sessions_stmt = select(SessionDB.session_id).where(
                SessionDB.user_id == current_user.id
            )
            all_sessions_result = await session.execute(all_sessions_stmt)
            all_session_ids = [s[0] for s in all_sessions_result.all()]
            
            # 统计所有会话的消息数和花费
            for session_id in all_session_ids:
                msg_stmt = select(MessageDB).where(MessageDB.session_id == session_id)
                msg_result = await session.execute(msg_stmt)
                messages = list(msg_result.scalars().all())
                total_messages += len(messages)
                
                # 统计花费（从 AI 消息的 result_info 中提取）
                for msg in messages:
                    if msg.role == "assistant" and msg.result_info:
                        cost = msg.result_info.get("total_cost_usd")
                        if cost is not None:
                            total_cost += float(cost)
        
        stats = {
            "total_sessions": total_count,
            "total_messages": total_messages,
            "total_cost_usd": round(total_cost, 6)
        }
    
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
        "sessions": sessions,
        "stats": stats  # 只在第一页返回统计信息
    }


@router.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: Optional[int] = None,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    Get conversation history for a session

    Returns all messages exchanged in this session.
    Only accessible by the session owner.
    """
    try:
        # 从数据库获取会话（验证用户权限）
        # 允许查看不活跃的会话（用于查看历史记录）
        db_session = await db_service.get_session(session_id, include_inactive=True)
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # 验证会话属于当前用户
        if current_user:
            if db_session.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this session"
                )
        elif db_session.user_id is not None:
            # 会话已绑定用户，但当前请求未认证
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this session"
            )

        # Get history from database
        history = await session_mgr.get_session_history(session_id, limit)

        return {
            "session_id": session_id,
            "total_messages": len(history),
            "messages": history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    Get messages for a session with pagination

    Returns paginated list of messages.
    Only accessible by the session owner.
    """
    try:
        # 从数据库获取会话（验证用户权限）
        db_session = await db_service.get_session(session_id)
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # 验证会话属于当前用户
        if current_user:
            if db_session.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this session"
                )
        elif db_session.user_id is not None:
            # 会话已绑定用户，但当前请求未认证
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this session"
            )

        # Get messages from database
        history = await session_mgr.get_session_history(session_id, limit)

        # Apply offset
        if offset > 0:
            history = history[offset:]

        return {
            "session_id": session_id,
            "offset": offset,
            "limit": limit,
            "total": len(history),
            "messages": history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/session/{session_id}/conversation", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    Get conversation history in frontend-compatible format with pagination
    
    Returns messages in the format expected by the frontend.
    Only accessible by the session owner.
    
    Query Parameters:
        limit: Maximum number of messages to return (default: None, returns all)
        offset: Number of messages to skip (default: 0)
    
    Returns:
        ConversationHistoryResponse with paginated messages
    """
    try:
        # 从数据库获取会话（验证用户权限）
        # 允许查看不活跃的会话（用于查看历史记录）
        db_session = await db_service.get_session(session_id, include_inactive=True)
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # 验证会话属于当前用户
        if current_user:
            if db_session.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this session"
                )
        elif db_session.user_id is not None:
            # 会话已绑定用户，但当前请求未认证
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this session"
            )

        logger.info(f"[get_conversation_history] Getting messages for session {session_id}, limit={limit}, offset={offset}")
        
        # Get total count of messages (only visible messages: text, file_created, file_uploaded)
        # 计算可见消息总数（排除 tool_use 和 tool_result）
        async with db_service.async_session() as session:
            from sqlalchemy import func, and_
            visible_types = ["text", "file_created", "file_uploaded"]
            stmt = select(func.count(MessageDB.id)).where(
                and_(
                    MessageDB.session_id == session_id,
                    MessageDB.message_type.in_(visible_types)
                )
            )
            result = await session.execute(stmt)
            total_messages_count = result.scalar() or 0
        
        # 🔧 修复分页问题：先获取足够多的消息（包括 tool_use 和 tool_result），然后过滤后再分页
        # 因为 tool_use 和 tool_result 需要关联到 text 消息，所以不能只查询 text 消息
        # 策略：使用更大的 limit（估算：每个可见消息平均有 5-10 个 tool_use/tool_result）
        # 如果 limit 存在，使用 limit * 10 来确保获取足够的消息
        # 当 offset > 0 时，需要从开始获取到 offset + limit 的所有消息，以确保包含所有相关的 tool_use 和 tool_result
        fetch_limit = None
        fetch_offset = 0
        if limit:
            # 估算：每个可见消息平均有 5-10 个 tool_use/tool_result
            # 计算需要获取的消息范围：从开始到 offset + limit
            # 使用 (offset + limit) * 10 来确保获取足够的消息
            fetch_limit = (offset + limit) * 10
            fetch_offset = 0  # 总是从开始获取，以确保包含所有相关的 tool_use 和 tool_result
        
        # Get messages from database (with larger limit to include tool_use and tool_result)
        db_messages = await db_service.get_messages(session_id, limit=fetch_limit, offset=fetch_offset)
        
        logger.info(
            f"[get_conversation_history] Fetched {len(db_messages)} raw messages "
            f"(fetch_limit={fetch_limit}, fetch_offset={fetch_offset}, "
            f"requested_limit={limit}, requested_offset={offset})"
        )
        
        # Group messages by conversation_turn_id for pairing
        messages_by_turn: Dict[str, List] = {}
        tool_calls_by_parent: Dict[int, List] = {}  # tool_use messages by parent
        tool_results_by_tool_use: Dict[str, List] = {}  # tool_result messages by tool_use_id
        
        # First pass: collect all messages and group by turn
        for msg in db_messages:
            turn_id = msg.conversation_turn_id or "unknown"
            if turn_id not in messages_by_turn:
                messages_by_turn[turn_id] = []
            messages_by_turn[turn_id].append(msg)
            
            # Collect tool calls (tool_use messages)
            if msg.message_type == "tool_use" and msg.parent_message_id:
                if msg.parent_message_id not in tool_calls_by_parent:
                    tool_calls_by_parent[msg.parent_message_id] = []
                tool_calls_by_parent[msg.parent_message_id].append(msg)
            
            # Collect tool results (tool_result messages)
            if msg.message_type == "tool_result" and msg.extra_data:
                tool_use_id = msg.extra_data.get("tool_use_id")
                if tool_use_id:
                    if tool_use_id not in tool_results_by_tool_use:
                        tool_results_by_tool_use[tool_use_id] = []
                    tool_results_by_tool_use[tool_use_id].append(msg)
                    logger.info(
                        f"[get_conversation_history] 📦 Collected tool_result: tool_use_id={tool_use_id[:20]}..., "
                        f"content_length={len(msg.content) if msg.content else 0}, "
                        f"content_is_none={msg.content is None}, "
                        f"content_preview={str(msg.content)[:100] if msg.content else '(empty)'}, "
                        f"conversation_turn_id={msg.conversation_turn_id}"
                    )
        
        # Convert to frontend format, grouped by conversation turns
        messages: List[HistoryMessage] = []
        file_events: List[FileEventInfo] = []  # 单独收集文件事件，用于库标签页显示
        message_counter = {"user": 0, "assistant": 0}
        
        # Sort turns by the earliest message timestamp
        sorted_turns = sorted(
            messages_by_turn.items(),
            key=lambda x: min(m.created_at for m in x[1])
        )
        
        for turn_id, turn_messages in sorted_turns:
            # Sort messages within turn by created_at
            turn_messages.sort(key=lambda m: m.created_at)
            
            for msg in turn_messages:
                # Skip tool_use messages (they're included in tool_calls)
                if msg.message_type == "tool_use":
                    continue
                
                # Skip tool_result messages (they're included in tool_calls as output)
                # tool_result 消息不应该显示在对话中，它们只是工具执行的内部结果
                if msg.message_type == "tool_result":
                    continue
                
                # 收集文件事件消息（单独返回，不显示在对话框中）
                if msg.message_type in ["file_created", "file_uploaded"]:
                    # 从 extra_data 中提取文件信息
                    extra_data = msg.extra_data or {}
                    file_event = FileEventInfo(
                        file_path=extra_data.get("file_path"),
                        file_url=extra_data.get("file_url"),
                        file_name=extra_data.get("file_name"),
                        file_size=extra_data.get("file_size"),
                        file_type=extra_data.get("file_type"),
                        conversation_turn_id=msg.conversation_turn_id,
                        created_at=format_utc_timestamp(msg.created_at),
                    )
                    file_events.append(file_event)
                    continue
                
                # 过滤掉看起来像工具结果的消息（即使它们被错误地保存为 text 类型）
                # 这些消息通常没有 resultInfo，没有 tool_calls，且内容看起来像工具输出
                if msg.role == "assistant" and msg.message_type == "text":
                    # 检查是否是工具结果消息的特征：
                    # 1. 没有 resultInfo（正常的 AI 响应应该有 resultInfo）
                    # 2. 没有关联的 tool_calls（正常的 AI 响应如果有工具调用会有 tool_calls）
                    # 3. 内容看起来像工具输出（如 "Todos have been modified successfully"）
                    has_result_info = msg.result_info is not None
                    has_tool_calls = msg.id in tool_calls_by_parent
                    content = (msg.content or "").strip()
                    
                    # 如果消息没有 resultInfo 和 tool_calls，且内容看起来像工具输出，则跳过
                    # 注意：正常的 AI 响应即使没有工具调用，也应该有 resultInfo
                    if not has_result_info and not has_tool_calls and content:
                        # 检查内容是否匹配常见的工具输出模式
                        tool_result_patterns = [
                            "Todos have been modified successfully",
                            "File created successfully",
                            "Web search results",
                            "MinIO客户端初始化成功",
                            "🔧 配置信息:",
                            "🚀 MinIO客户端初始化成功",
                        ]
                        if any(pattern in content for pattern in tool_result_patterns):
                            logger.debug(f"[get_conversation_history] Skipping tool_result-like message: id={msg.id}, content_preview={content[:50]}")
                            continue
                
                # Generate message ID
                if msg.role == "user":
                    message_counter["user"] += 1
                    msg_id = f"user-{message_counter['user']}"
                    sender = "user"
                else:  # assistant
                    message_counter["assistant"] += 1
                    msg_id = f"ai-{message_counter['assistant']}"
                    sender = "ai"
                
                # Build message
                history_msg = HistoryMessage(
                    id=msg_id,
                    text=msg.content or "",
                    sender=sender,
                    timestamp=format_utc_timestamp(msg.created_at),
                    conversation_turn_id=msg.conversation_turn_id,
                    parent_message_id=msg.parent_message_id,
                )
                
                # Add resultInfo for AI messages if available
                if msg.role == "assistant" and msg.result_info:
                    history_msg.resultInfo = MessageResultInfo(**msg.result_info)
                
                # Add tool calls for assistant messages
                if msg.role == "assistant" and msg.id in tool_calls_by_parent:
                    # 🔧 修复：按创建时间降序排序 tool_calls，确保最新的在前
                    # 这样前端选择最后一个 TodoWrite 时，会得到最新的状态
                    sorted_tool_calls = sorted(
                        tool_calls_by_parent[msg.id],
                        key=lambda m: m.created_at,
                        reverse=True  # 降序：最新的在前
                    )
                    for tool_msg in sorted_tool_calls:
                        tool_use_id = tool_msg.extra_data.get("tool_use_id", "") if tool_msg.extra_data else ""
                        
                        # Find corresponding tool_result
                        tool_output = None
                        if tool_use_id and tool_use_id in tool_results_by_tool_use:
                            # Get the first tool_result for this tool_use_id
                            tool_result_msg = tool_results_by_tool_use[tool_use_id][0]
                            # 🔍 重要：即使 content 是空字符串，也视为有输出（工具已执行完成）
                            # 只有 content 为 None 时才表示工具未执行完成
                            tool_output = tool_result_msg.content
                            logger.info(
                                f"[get_conversation_history] ✅ Found tool_result: tool_use_id={tool_use_id[:20]}..., "
                                f"tool_name={tool_msg.extra_data.get('tool_name', '') if tool_msg.extra_data else ''}, "
                                f"content_type={type(tool_output).__name__}, "
                                f"content_length={len(tool_output) if tool_output else 0}, "
                                f"content_is_none={tool_output is None}, "
                                f"content_preview={str(tool_output)[:100] if tool_output else '(empty)'}, "
                                f"tool_result_turn_id={tool_result_msg.conversation_turn_id}, "
                                f"tool_use_turn_id={tool_msg.conversation_turn_id}"
                            )
                        else:
                            logger.warning(
                                f"[get_conversation_history] ❌ No tool_result found: tool_use_id={tool_use_id[:20] if tool_use_id else 'None'}..., "
                                f"tool_name={tool_msg.extra_data.get('tool_name', '') if tool_msg.extra_data else ''}, "
                                f"available_tool_use_ids={[k[:20] + '...' for k in list(tool_results_by_tool_use.keys())[:10]]}, "
                                f"total_tool_results={len(tool_results_by_tool_use)}"
                            )
                        
                        # 获取原始 tool_input
                        raw_tool_input = tool_msg.extra_data.get("tool_input", {}) if tool_msg.extra_data else {}
                        tool_name = tool_msg.extra_data.get("tool_name", "") if tool_msg.extra_data else ""
                        
                        # 🔧 修复：对于 TodoWrite 工具调用，清理已完成任务的 activeForm 字段
                        # activeForm 只在 in_progress 状态时才有意义，completed 状态应该清除
                        cleaned_tool_input = raw_tool_input
                        if tool_name == "TodoWrite" and isinstance(raw_tool_input, dict):
                            todos = raw_tool_input.get("todos", [])
                            if isinstance(todos, list) and len(todos) > 0:
                                cleaned_todos = []
                                for todo in todos:
                                    if isinstance(todo, dict):
                                        todo_status = todo.get("status", "pending")
                                        cleaned_todo = todo.copy()
                                        # 如果任务状态是 completed，清除 activeForm 字段
                                        if todo_status == "completed" and "activeForm" in cleaned_todo:
                                            del cleaned_todo["activeForm"]
                                        cleaned_todos.append(cleaned_todo)
                                    else:
                                        cleaned_todos.append(todo)
                                cleaned_tool_input = raw_tool_input.copy()
                                cleaned_tool_input["todos"] = cleaned_todos
                        
                        tool_info = ToolCallInfo(
                            tool_use_id=tool_use_id,
                            tool_name=tool_name,
                            tool_input=cleaned_tool_input,
                            tool_output=tool_output,  # 可能是 None、空字符串或实际内容
                            conversation_turn_id=tool_msg.conversation_turn_id,  # 使用工具调用消息本身的 conversation_turn_id
                        )
                        history_msg.tool_calls.append(tool_info)
                
                messages.append(history_msg)

        # 🔧 修复分页：对过滤后的消息进行分页
        # 如果指定了 limit 和 offset，只返回对应的可见消息
        if limit is not None:
            # 对过滤后的消息进行分页
            start_idx = offset
            end_idx = offset + limit
            paginated_messages = messages[start_idx:end_idx]
            logger.info(
                f"[get_conversation_history] Paginated messages: "
                f"total_filtered={len(messages)}, "
                f"offset={offset}, limit={limit}, "
                f"returned={len(paginated_messages)}"
            )
            messages = paginated_messages

        # 计算是否有更多数据
        # 注意：total_messages_count 是可见消息的总数（已排除 tool_use 和 tool_result）
        has_more = (offset + len(messages)) < total_messages_count if limit else False

        return ConversationHistoryResponse(
            session_id=session_id,
            messages=messages,
            file_events=file_events,
            total=total_messages_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/message/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    Delete a message by its ID
    """
    try:
        success = await db_service.delete_message(message_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/file/content")
async def get_file_content(
    file_path: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    读取文件内容

    所有文件必须在 aigc/work_dir 目录下

    Args:
        file_path: 文件路径（相对于 aigc/work_dir，例如：reports/file.md）

    Returns:
        文件内容（文本文件）或错误信息
    """
    import os
    from pathlib import Path
    from core.config import settings

    try:
        # 安全检查：防止路径遍历攻击
        file_path = os.path.normpath(file_path)
        if file_path.startswith('/') or file_path.startswith('..'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path: must be relative to work_dir"
            )

        # 构建完整路径：aigc/work_dir/file_path
        full_path = settings.work_dir / file_path

        logger.info(f"[get_file_content] Reading file: {full_path}")

        # 检查文件是否存在
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path} (in {settings.work_dir})"
            )

        # 检查是否为文件（不是目录）
        if not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a file"
            )

        # 读取文件内容
        try:
            content = full_path.read_text(encoding='utf-8')
            return {
                "file_path": file_path,
                "content": content,
                "size": full_path.stat().st_size
            }
        except UnicodeDecodeError:
            # 如果不是文本文件，返回错误
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a text file or encoding is not UTF-8"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
@router.get("/conversation/{conversation_turn_id}/dataflow", response_model=DataFlowResponse)
async def get_conversation_dataflow(
    conversation_turn_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
    db_service: DatabaseService = Depends(get_database_service),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
):
    """
    获取 conversation_turn_id 的完整数据链路
    
    返回该对话轮次的所有节点（用户消息、工具调用、工具结果、AI响应、文件事件等）
    以及它们之间的父子关系，用于前端可视化展示
    """
    try:
        # 查询该 conversation_turn_id 的所有消息
        from sqlalchemy import select
        from models.database import MessageDB
        
        logger.info(f"[get_conversation_dataflow] Querying messages for conversation_turn_id: {conversation_turn_id}")
        
        # 先验证权限：通过 conversation_turn_id 找到 session，然后验证用户权限
        # 这样可以确保用户只能访问自己的数据
        async with db_service.async_session() as session:
            # 先获取一条消息以找到 session_id
            stmt = select(MessageDB).where(
                MessageDB.conversation_turn_id == conversation_turn_id
            ).limit(1)
            result = await session.execute(stmt)
            first_message = result.scalar_one_or_none()
            
            if not first_message:
                logger.warning(f"[get_conversation_dataflow] No messages found for conversation_turn_id: {conversation_turn_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No messages found for conversation_turn_id: {conversation_turn_id}"
                )
            
            session_id = first_message.session_id
            
            # 验证权限（包含 inactive sessions，因为可能是历史数据）
            db_session = await db_service.get_session(session_id, include_inactive=True)
            if db_session is None:
                logger.warning(f"[get_conversation_dataflow] Session {session_id} not found for conversation_turn_id: {conversation_turn_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found"
                )
            
            # 验证用户权限：确保只能访问自己的会话
            if current_user:
                if db_session.user_id != current_user.id:
                    logger.warning(f"[get_conversation_dataflow] User {current_user.id} attempted to access session {session_id} owned by user {db_session.user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to access this session"
                    )
            elif db_session.user_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to access this session"
                )
            
            # 权限验证通过后，获取所有消息
            stmt = select(MessageDB).where(
                MessageDB.conversation_turn_id == conversation_turn_id
            ).order_by(MessageDB.created_at)
            result = await session.execute(stmt)
            messages = list(result.scalars().all())
        
        logger.info(f"[get_conversation_dataflow] Found {len(messages)} messages for conversation_turn_id: {conversation_turn_id} (user_id: {current_user.id if current_user else None})")
        
        # 构建节点映射
        nodes: List[DataFlowNode] = []
        node_map: Dict[str, DataFlowNode] = {}
        tool_use_id_to_node_id: Dict[str, str] = {}  # tool_use_id -> node_id
        
        # 🔍 去重逻辑：追踪已处理的节点，避免重复
        processed_tool_use_ids = set()  # 已处理的 tool_use_id（tool_use 和 tool_result）
        processed_assistant_messages = {}  # 已处理的 assistant_message (parent_message_id -> 最新消息)
        
        # 第一遍：创建所有节点（带去重逻辑）
        for msg in messages:
            node_id = str(msg.id)
            node_type = msg.message_type
            node_name = ""
            content_preview = None
            extra_data = msg.extra_data or {}
            
            # 根据消息类型设置节点名称和内容
            if msg.role == "user" and msg.message_type == "text":
                node_type = "user_message"
                node_name = "用户消息"
                content_preview = (msg.content or "")[:100] if msg.content else None
            elif msg.role == "assistant":
                if msg.message_type == "text":
                    node_type = "assistant_message"
                    node_name = "AI响应"
                    content_preview = (msg.content or "")[:100] if msg.content else None
                elif msg.message_type == "tool_use":
                    node_type = "tool_use"
                    node_name = extra_data.get("tool_name", "未知工具")
                    tool_use_id = extra_data.get("tool_use_id", "")
                    if tool_use_id:
                        tool_use_id_to_node_id[tool_use_id] = node_id
                    extra_data = {
                        "tool_use_id": tool_use_id,
                        "tool_name": node_name,
                        "tool_input": extra_data.get("tool_input", {}),
                    }
                elif msg.message_type == "tool_result":
                    node_type = "tool_result"
                    tool_use_id = extra_data.get("tool_use_id", "")
                    # 尝试从 tool_use_id_to_node_id 获取工具名称（在第二遍遍历时更新）
                    tool_use_node_id = tool_use_id_to_node_id.get(tool_use_id)
                    if tool_use_node_id:
                        node_name = f"工具结果 ({tool_use_id[:8]}...)"
                    else:
                        node_name = "工具结果"
                    content_preview = (msg.content or "")[:100] if msg.content else None
                elif msg.message_type in ["file_created", "file_uploaded"]:
                    node_type = "file_event"
                    node_name = "文件创建" if msg.message_type == "file_created" else "文件上传"
                    extra_data = {
                        "file_path": extra_data.get("file_path"),
                        "file_url": extra_data.get("file_url"),
                        "file_name": extra_data.get("file_name"),
                        "file_size": extra_data.get("file_size"),
                        "file_type": extra_data.get("file_type"),
                    }
            
            # 确定父节点ID
            parent_node_id = None
            if msg.parent_message_id:
                parent_node_id = str(msg.parent_message_id)
            elif msg.message_type == "tool_result":
                # tool_result 的父节点是对应的 tool_use
                tool_use_id = extra_data.get("tool_use_id", "")
                parent_node_id = tool_use_id_to_node_id.get(tool_use_id)
            
            node = DataFlowNode(
                node_id=node_id,
                node_type=node_type,
                node_name=node_name,
                timestamp=format_utc_timestamp(msg.created_at),
                content_preview=content_preview,
                extra_data=extra_data if extra_data else None,
                parent_node_id=parent_node_id,
                children_node_ids=[],
            )
            nodes.append(node)
            node_map[node_id] = node
        
        # 第二遍：建立父子关系和更新工具结果名称
        root_node_id = None
        for node in nodes:
            # 更新工具结果的名称（现在 node_map 已经完整）
            if node.node_type == "tool_result" and node.extra_data:
                tool_use_id = node.extra_data.get("tool_use_id", "")
                tool_use_node_id = tool_use_id_to_node_id.get(tool_use_id)
                if tool_use_node_id and tool_use_node_id in node_map:
                    tool_name = node_map[tool_use_node_id].node_name
                    node.node_name = f"{tool_name} 结果"
            
            # 建立父子关系
            if node.parent_node_id and node.parent_node_id in node_map:
                parent_node = node_map[node.parent_node_id]
                if node.node_id not in parent_node.children_node_ids:
                    parent_node.children_node_ids.append(node.node_id)
            elif node.node_type == "user_message":
                # 用户消息是根节点
                root_node_id = node.node_id
        
        return DataFlowResponse(
            conversation_turn_id=conversation_turn_id,
            session_id=session_id,
            nodes=nodes,
            root_node_id=root_node_id,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation dataflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )


@router.get("/files/session/{session_id}")
async def get_session_files(
    session_id: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    Get all files for a session (for @mention functionality)
    
    Returns a list of files uploaded in the session, suitable for
    displaying in a file selection dropdown when user types "@".
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify session belongs to current user
    db_session = await db_service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get session files
    file_search_service = FileSearchService(db_service)
    files = await file_search_service.get_session_files(
        session_id=session_id,
        user_id=current_user.id,
    )
    
    # Convert to response format
    return {
        "files": [
            {
                "doc_id": file.doc_id,
                "file_name": file.file_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "uploaded_at": format_utc_timestamp(file.uploaded_at) if file.uploaded_at else None,
            }
            for file in files
        ]
    }


@router.post("/frontend/log", response_model=FrontendLogResponse)
async def log_frontend(
    log_request: FrontendLogRequest,
    current_user: Optional[UserDB] = Depends(get_current_user_optional)
):
    """
    接收前端日志并写入到 logs/frontend.log 文件
    
    前端可以通过这个接口将 console 日志发送到后端，后端会将其写入日志文件
    """
    from pathlib import Path
    from datetime import datetime
    import json
    
    try:
        # 获取项目根目录
        # 方法：从 backend/api/v1/endpoints.py 向上4级到项目根目录
        # __file__ = /Users/hehe/pycharm_projects/aigc/backend/api/v1/endpoints.py
        # parent = backend/api/v1
        # parent.parent = backend/api
        # parent.parent.parent = backend
        # parent.parent.parent.parent = 项目根目录 (aigc)
        current_file = Path(__file__).resolve()  # 使用 resolve() 获取绝对路径
        project_root = current_file.parent.parent.parent.parent
        log_file_path = project_root / "logs" / "frontend.log"
        
        # 确保 logs 目录存在
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 格式化日志消息
        timestamp = log_request.timestamp or datetime.now().isoformat()
        level = log_request.level.upper()
        
        # 构建日志行
        log_parts = [
            f"[{timestamp}]",
            f"[{level}]",
            f"[{log_request.source}]",
            log_request.message
        ]
        
        # 如果有额外数据，添加到日志中
        if log_request.data is not None:
            try:
                data_str = json.dumps(log_request.data, ensure_ascii=False, indent=2)
                log_parts.append(f"\nData: {data_str}")
            except (TypeError, ValueError):
                log_parts.append(f"\nData: {str(log_request.data)}")
        
        log_line = " ".join(log_parts) + "\n"
        
        # 写入日志文件（追加模式）
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(log_line)
        
        return FrontendLogResponse(
            success=True,
            message="Log written successfully"
        )
        
    except Exception as e:
        # 不记录错误到 backend.log，仅返回错误响应
        return FrontendLogResponse(
            success=False,
            message=f"Error writing log: {str(e)}"
        )


# =========================================================================
# Phase 3: 反馈收集 API
# =========================================================================

@router.post("/feedback")
async def submit_feedback(
    message_id: Optional[int] = None,
    session_id: Optional[str] = None,
    conversation_turn_id: Optional[str] = None,
    feedback_type: str = "like",  # 'like' | 'dislike' | 'correct' | 'regenerate' | 'implicit_retry' | 'implicit_modify'
    feedback_data: Optional[Dict] = None,
    user_prompt: Optional[str] = None,
    assistant_response: Optional[str] = None,
    scenario_ids: Optional[List[str]] = None,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    提交用户反馈
    
    支持显式反馈（点赞/点踩/纠正/重新生成）和隐式反馈（重新提问、修改问题等）
    """
    try:
        feedback_collector = FeedbackCollector(db_service)
        
        user_id = current_user.id if current_user else None
        
        feedback = await feedback_collector.collect_feedback(
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            conversation_turn_id=conversation_turn_id,
            feedback_type=feedback_type,
            feedback_data=feedback_data,
            user_prompt=user_prompt,
            assistant_response=assistant_response,
            scenario_ids=scenario_ids
        )
        
        logger.info(
            f"[submit_feedback] 反馈提交成功: user_id={user_id}, "
            f"session_id={session_id}, type={feedback_type}"
        )
        
        return {
            "success": True,
            "feedback_id": feedback.id,
            "message": "反馈已提交"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.post("/feedback/implicit")
async def submit_implicit_feedback(
    session_id: Optional[str] = None,
    implicit_type: str = "retry",  # 'retry' | 'modify' | 'regenerate'
    original_prompt: Optional[str] = None,
    modified_prompt: Optional[str] = None,
    context: Optional[Dict] = None,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    提交隐式反馈（用户重新提问、修改问题等）
    """
    try:
        feedback_collector = FeedbackCollector(db_service)
        
        user_id = current_user.id if current_user else None
        
        feedback = await feedback_collector.collect_implicit_feedback(
            user_id=user_id,
            session_id=session_id,
            implicit_type=implicit_type,
            original_prompt=original_prompt,
            modified_prompt=modified_prompt,
            context=context
        )
        
        logger.info(
            f"[submit_implicit_feedback] 隐式反馈提交成功: user_id={user_id}, "
            f"session_id={session_id}, type={implicit_type}"
        )
        
        return {
            "success": True,
            "feedback_id": feedback.id,
            "message": "隐式反馈已提交"
        }
        
    except Exception as e:
        logger.error(f"Error submitting implicit feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit implicit feedback: {str(e)}"
        )

