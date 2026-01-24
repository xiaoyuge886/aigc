"""
Pydantic models for API requests and responses
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class FileAttachment(BaseModel):
    """File attachment model"""
    name: str = Field(..., description="File name")
    type: str = Field(..., description="File MIME type")
    data: str = Field(..., description="Base64 encoded file data")


class AgentRequest(BaseModel):
    """Request model for agent query"""

    prompt: str = Field(..., description="User prompt to send to the agent")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for continuing conversation"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt override"
    )
    allowed_tools: Optional[List[str]] = Field(
        default=None,
        description="Optional list of allowed tools for this request"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (sonnet, opus, haiku)"
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )
    incremental_stream: bool = Field(
        default=False,
        description="Whether to use incremental streaming (SSE mode with text deltas)"
    )
    attachments: Optional[List[FileAttachment]] = Field(
        default=None,
        description="Optional file attachments (base64 encoded)"
    )


class ToolDefinition(BaseModel):
    """Custom tool definition"""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="Input JSON schema")


class SessionCreateRequest(BaseModel):
    """Request to create a new session"""

    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    allowed_tools: Optional[List[str]] = Field(default=None, description="Allowed tools")
    model: Optional[str] = Field(default=None, description="Model to use")
    incremental_stream: bool = Field(
        default=False,
        description="Whether to enable incremental streaming for this session"
    )


class SessionResponse(BaseModel):
    """Response for session creation"""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: str = Field(..., description="ISO timestamp of creation")


class ContentBlock(BaseModel):
    """Content block in assistant message"""

    type: str = Field(..., description="Block type: text, thinking, tool_use, tool_result, file_created, file_uploaded")
    text: Optional[str] = Field(default=None, description="Text content")
    thinking: Optional[str] = Field(default=None, description="Thinking content")
    tool_name: Optional[str] = Field(default=None, description="Tool name used")
    tool_input: Optional[Dict[str, Any]] = Field(default=None, description="Tool input")
    tool_use_id: Optional[str] = Field(default=None, description="Tool use ID")
    is_error: Optional[bool] = Field(default=None, description="Whether tool result is error")
    
    # 文件事件相关字段（可选，向后兼容）
    file_path: Optional[str] = Field(default=None, description="File path for file_created event")
    file_url: Optional[str] = Field(default=None, description="File URL for file_uploaded event")
    file_name: Optional[str] = Field(default=None, description="File name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    file_type: Optional[str] = Field(default=None, description="File MIME type")
    conversation_turn_id: Optional[str] = Field(default=None, description="Conversation turn ID for file event")
    # 🔧 新增：文件内容字段（可选，用于直接推送文件内容到前端）
    file_content: Optional[str] = Field(default=None, description="File content (optional, for streaming file content to frontend)")


class AssistantMessage(BaseModel):
    """Message from assistant"""

    type: str = Field(default="assistant", description="Message type")
    content: List[ContentBlock] = Field(..., description="Content blocks")
    model: Optional[str] = Field(default=None, description="Model used")


class UserMessage(BaseModel):
    """Message from user (may contain tool results)"""

    type: str = Field(default="user", description="Message type")
    content: List[ContentBlock] = Field(..., description="Content blocks (may contain ToolResultBlock)")
    uuid: Optional[str] = Field(default=None, description="Message UUID")
    parent_tool_use_id: Optional[str] = Field(default=None, description="Parent tool use ID")


class SystemMessage(BaseModel):
    """System message"""

    type: str = Field(default="system", description="Message type")
    subtype: str = Field(..., description="System message subtype")
    data: Dict[str, Any] = Field(default_factory=dict, description="System message data")


class ResultInfo(BaseModel):
    """Final result information"""

    type: str = Field(default="result", description="Message type")
    subtype: str = Field(..., description="Result subtype: success, error")
    result: Optional[str] = Field(default=None, description="Final result text")
    is_error: bool = Field(..., description="Whether this is an error")
    duration_ms: int = Field(..., description="Total duration in milliseconds")
    num_turns: int = Field(..., description="Number of conversation turns")
    session_id: str = Field(..., description="Session identifier")
    total_cost_usd: Optional[float] = Field(default=None, description="Total cost in USD")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage information")
    duration_api_ms: Optional[int] = Field(default=None, description="API duration in milliseconds")


class AgentResponse(BaseModel):
    """Response from agent query"""

    session_id: str = Field(..., description="Session identifier")
    messages: List[Union[AssistantMessage, SystemMessage]] = Field(
        default_factory=list,
        description="Response messages"
    )
    result: Optional[ResultInfo] = Field(default=None, description="Final result info")


class StreamChunk(BaseModel):
    """Single chunk in streamed response"""

    type: str = Field(..., description="Chunk type")
    data: Any = Field(
        ...,
        description="Chunk data - can be any message type"
    )


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error info")
    error_type: Optional[str] = Field(default=None, description="Error type")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="1.0.0", description="API version")


class MessageResultInfo(BaseModel):
    """ResultMessage info for AI messages (matches frontend ResultInfo)"""

    subtype: Optional[str] = Field(default=None, description="Result subtype")
    duration_ms: Optional[int] = Field(default=None, description="Total duration in milliseconds")
    duration_api_ms: Optional[int] = Field(default=None, description="API duration in milliseconds")
    is_error: Optional[bool] = Field(default=None, description="Whether this is an error")
    num_turns: Optional[int] = Field(default=None, description="Number of conversation turns")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    total_cost_usd: Optional[float] = Field(default=None, description="Total cost in USD")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage information")


class ToolCallInfo(BaseModel):
    """Tool call information"""
    tool_use_id: str = Field(..., description="Tool use ID")
    tool_name: str = Field(..., description="Tool name")
    tool_input: Dict[str, Any] = Field(..., description="Tool input parameters")
    tool_output: Optional[str] = Field(default=None, description="Tool output/result")
    conversation_turn_id: Optional[str] = Field(default=None, description="Conversation turn ID for this tool call")


class HistoryMessage(BaseModel):
    """Message format for conversation history (matches frontend Message)"""

    id: str = Field(..., description="Message ID")
    text: str = Field(..., description="Message content")
    sender: str = Field(..., description="Message sender: 'user' or 'ai'")
    timestamp: str = Field(..., description="ISO timestamp")
    resultInfo: Optional[MessageResultInfo] = Field(default=None, description="ResultMessage info for AI messages")
    conversation_turn_id: Optional[str] = Field(
        default=None, description="ID for pairing user question with AI response"
    )
    parent_message_id: Optional[int] = Field(
        default=None, description="Parent message ID (for tool calls, etc.)"
    )
    tool_calls: List[ToolCallInfo] = Field(
        default_factory=list, description="Tool calls in this message"
    )


class FileEventInfo(BaseModel):
    """File event information for frontend library"""
    file_path: Optional[str] = Field(default=None, description="File path")
    file_url: Optional[str] = Field(default=None, description="File URL")
    file_name: Optional[str] = Field(default=None, description="File name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    file_type: Optional[str] = Field(default=None, description="File MIME type")
    conversation_turn_id: Optional[str] = Field(default=None, description="Conversation turn ID")
    created_at: str = Field(..., description="ISO timestamp")


class DataFlowNode(BaseModel):
    """数据链路节点"""
    node_id: str = Field(..., description="节点ID（message.id 或 tool_use_id）")
    node_type: str = Field(..., description="节点类型: user_message, assistant_message, tool_use, tool_result, file_event")
    node_name: str = Field(..., description="节点名称（工具名称、消息类型等）")
    timestamp: str = Field(..., description="时间戳 ISO格式")
    content_preview: Optional[str] = Field(default=None, description="内容预览（前100字符）")
    extra_data: Optional[Dict[str, Any]] = Field(default=None, description="额外数据（工具输入、文件信息等）")
    parent_node_id: Optional[str] = Field(default=None, description="父节点ID")
    children_node_ids: List[str] = Field(default_factory=list, description="子节点ID列表")


class DataFlowResponse(BaseModel):
    """数据链路响应"""
    conversation_turn_id: str = Field(..., description="对话轮次ID")
    session_id: str = Field(..., description="会话ID")
    nodes: List[DataFlowNode] = Field(..., description="所有节点")
    root_node_id: Optional[str] = Field(default=None, description="根节点ID（用户消息）")


class ConversationHistoryResponse(BaseModel):
    """Response for conversation history with pagination"""

    session_id: str = Field(..., description="Session identifier")
    messages: List[HistoryMessage] = Field(default_factory=list, description="List of messages (excluding file events)")
    file_events: List[FileEventInfo] = Field(default_factory=list, description="List of file events for library display")
    total: Optional[int] = Field(default=None, description="Total number of messages in the session")
    limit: Optional[int] = Field(default=None, description="Limit parameter used")
    offset: int = Field(default=0, description="Offset parameter used")
    has_more: bool = Field(default=False, description="Whether there are more messages to load")


class FrontendLogRequest(BaseModel):
    """Request model for frontend log submission"""
    level: str = Field(..., description="Log level (info, warn, error, debug, etc.)")
    message: str = Field(..., description="Log message")
    data: Optional[Any] = Field(default=None, description="Additional log data")
    timestamp: Optional[str] = Field(default=None, description="Client-side timestamp")
    source: Optional[str] = Field(default="frontend", description="Log source")


class FrontendLogResponse(BaseModel):
    """Response for frontend log submission"""
    success: bool = Field(..., description="Whether the log was successfully written")
    message: str = Field(..., description="Response message")


# User Log Schemas (for future ES migration - designed to be compatible with Elasticsearch)
class ConversationTurnDetail(BaseModel):
    """Conversation turn detail with all intermediate data for audit trail"""
    conversation_turn_id: str = Field(..., description="Unique conversation turn ID")
    session_id: str = Field(..., description="Session ID")
    created_at: str = Field(..., description="ISO timestamp")
    user_message: Optional[dict] = Field(None, description="User message content")
    assistant_messages: List[dict] = Field(default_factory=list, description="Assistant messages")
    tool_calls: List[dict] = Field(default_factory=list, description="Tool calls made during this turn")
    tool_results: List[dict] = Field(default_factory=list, description="Tool execution results")
    config_used: Optional[dict] = Field(None, description="Configuration used (from ConversationTurnConfigDB)")
    config_sources: Optional[dict] = Field(None, description="Configuration sources (Request/Session/User/Scenario/Global)")
    result_info: Optional[dict] = Field(None, description="ResultMessage info (cost, tokens, duration)")
    total_cost_usd: Optional[float] = Field(None, description="Total cost in USD")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")


class SessionLogDetail(BaseModel):
    """Session log detail with all conversation turns"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[int] = Field(None, description="User ID")
    created_at: str = Field(..., description="Session creation time (ISO)")
    last_activity: str = Field(..., description="Last activity time (ISO)")
    model: Optional[str] = Field(None, description="Model used")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    conversation_turns: List[ConversationTurnDetail] = Field(default_factory=list, description="All conversation turns")
    total_turns: int = Field(0, description="Total number of turns")
    total_cost_usd: float = Field(0.0, description="Total cost in USD")
    total_tokens: int = Field(0, description="Total tokens used")


class UserLogResponse(BaseModel):
    """User log response with all sessions and conversation details"""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    total_sessions: int = Field(..., description="Total number of sessions")
    total_conversation_turns: int = Field(..., description="Total number of conversation turns")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    sessions: List[SessionLogDetail] = Field(default_factory=list, description="List of sessions with details")
    limit: Optional[int] = Field(None, description="Limit used for pagination")
    offset: int = Field(0, description="Offset used for pagination")
    has_more: bool = Field(False, description="Whether there are more sessions to load")
