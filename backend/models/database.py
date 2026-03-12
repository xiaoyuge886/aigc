"""
SQLAlchemy database models for session persistence
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy import (
    String, DateTime, Integer, Text, Boolean, JSON, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from passlib.context import CryptContext


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class RoleDB(Base):
    """Role table for user roles"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Role permissions

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    users: Mapped[list["UserDB"]] = relationship(
        "UserDB", back_populates="role"
    )

    def __repr__(self):
        return f"<RoleDB(name={self.name})>"


class UserDB(Base):
    """User table for authentication and authorization"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # User profile
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Foreign key to role
    role_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    role: Mapped[Optional["RoleDB"]] = relationship("RoleDB", back_populates="users")
    sessions: Mapped[list["SessionDB"]] = relationship(
        "SessionDB", back_populates="user", cascade="all, delete-orphan"
    )

    def verify_password(self, plain_password: str) -> bool:
        """Verify password"""
        # Truncate to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')[:72]
        return pwd_context.verify(password_bytes, self.hashed_password)

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """Hash password"""
        # Truncate to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')[:72]
        return pwd_context.hash(password_bytes)

    def __repr__(self):
        return f"<UserDB(id={self.id}, username={self.username})>"


class SessionDB(Base):
    """Session table for storing conversation sessions"""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)

    # User relationship
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    # Session configuration
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    allowed_tools: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    permission_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_turns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Session metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Relationships
    user: Mapped[Optional["UserDB"]] = relationship(
        "UserDB", back_populates="sessions"
    )
    messages: Mapped[list["MessageDB"]] = relationship(
        "MessageDB", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SessionDB(session_id={self.session_id}, model={self.model})>"


class MessageDB(Base):
    """Message table for storing conversation history"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True
    )

    # Message type and content
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    message_type: Mapped[str] = mapped_column(String(50))  # "text", "tool_use", "tool_result", etc.
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional metadata (renamed to avoid SQLAlchemy reserved word)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # ResultMessage info for AI messages (stores ResultMessage fields)
    result_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Conversation pairing fields
    conversation_turn_id: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True,
        comment="Unique ID for pairing user question with AI response in the same turn"
    )
    parent_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="Reference to parent message (e.g., AI message references user message)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    turn_number: Mapped[int] = mapped_column(Integer, default=1, index=True)

    # Relationships
    session: Mapped["SessionDB"] = relationship("SessionDB", back_populates="messages")
    parent_message: Mapped[Optional["MessageDB"]] = relationship(
        "MessageDB", remote_side=[id], backref="child_messages"
    )

    def __repr__(self):
        return f"<MessageDB(role={self.role}, type={self.message_type}, turn_id={self.conversation_turn_id})>"


class UserConfigDB(Base):
    """User configuration table for platform customization"""
    __tablename__ = "user_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Agent configuration
    default_system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_allowed_tools: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    default_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    permission_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_turns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Working directory isolation
    work_dir: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Custom tools and skills
    custom_tools: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # MCP server configs
    custom_skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Skill names list
    
    # Business scenario association (使用整数ID)
    associated_scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("business_scenarios.id"), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", backref="user_config")
    associated_scenario: Mapped[Optional["BusinessScenarioDB"]] = relationship(
        "BusinessScenarioDB", foreign_keys=[associated_scenario_id]
    )

    def __repr__(self):
        return f"<UserConfigDB(user_id={self.user_id})>"


class BusinessScenarioDB(Base):
    """Business scenario template table"""
    __tablename__ = "business_scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 移除 scenario_id 字符串字段，统一使用整数 id

    # Scenario metadata
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # 分类：如 "技术开发", "数据分析", "商业助手" 等
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Meta 信息：tags, capabilities, keywords 等（类似 skill 的 meta 信息）

    # Scenario configuration
    system_prompt: Mapped[str] = mapped_column(Text)
    allowed_tools: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    recommended_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    custom_tools: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # MCP server configs
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Skill names list
    workflow: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Workflow definition
    # 高优先级参数
    permission_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_turns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    work_dir: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Ownership and visibility
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 是否是系统默认场景

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped[Optional["UserDB"]] = relationship("UserDB", foreign_keys=[created_by])

    def __repr__(self):
        return f"<BusinessScenarioDB(id={self.id}, name={self.name})>"


class SystemPromptDB(Base):
    """System prompt template table"""
    __tablename__ = "system_prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 移除 prompt_id 字符串字段，统一使用整数 id

    # Prompt metadata
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # 分类：如 "default", "analysis", "coding" 等

    # Prompt content
    content: Mapped[str] = mapped_column(Text)  # 系统提示词内容

    # Usage metadata
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # 使用次数
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # 是否为默认提示词

    # Ownership and visibility
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped[Optional["UserDB"]] = relationship("UserDB", foreign_keys=[created_by])

    def __repr__(self):
        return f"<SystemPromptDB(id={self.id}, name={self.name})>"


class ConversationTurnConfigDB(Base):
    """Conversation turn configuration log table
    
    Records the configuration used for each conversation turn,
    including the source of each configuration item (Request/Session/Scenario/User/Global).
    This is used for logging and auditing in the admin dashboard.
    """
    __tablename__ = "conversation_turn_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_turn_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True,
        comment="Unique ID for this conversation turn"
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Final merged configuration (what was actually used)
    final_config: Mapped[dict] = mapped_column(
        JSON, nullable=False,
        comment="Final merged configuration that was used for this turn"
    )
    
    # Configuration sources (which level provided each config item)
    config_sources: Mapped[dict] = mapped_column(
        JSON, nullable=False,
        comment="Source of each configuration item: REQUEST, SESSION, SCENARIO, USER, or GLOBAL"
    )
    
    # Configuration details (使用整数ID)
    scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("business_scenarios.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="Scenario ID used (if any)"
    )
    scenario_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="Scenario name used (if any)"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session: Mapped["SessionDB"] = relationship("SessionDB")
    user: Mapped[Optional["UserDB"]] = relationship("UserDB")
    
    def __repr__(self):
        return f"<ConversationTurnConfigDB(turn_id={self.conversation_turn_id}, scenario={self.scenario_id})>"


class SkillDB(Base):
    """技能表 - 极简设计

    设计理念：
    1. 技能存储在文件系统（.claude/skills/）
    2. 数据库只存：名称、路径、状态、作者、使用次数
    3. 通过 status 区分使用场景：
       - draft: 草稿（用户创建，正在编辑）
       - testing: 调试中（技能市场在线调试）
       - published: 已发布（AI 对话可加载）
       - official: 官方技能（系统预设）
       - archived: 归档
    """
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True,
        comment="技能名称（同目录名）"
    )

    # 文件路径（核心字段）
    skill_path: Mapped[str] = mapped_column(
        String(500), unique=True, index=True,
        comment="技能目录路径，如：.claude/skills/{name}/"
    )

    # 简短描述（可选，用于列表展示）
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="简短描述（用于列表展示）"
    )

    # 来源标识
    source: Mapped[str] = mapped_column(
        String(50), default='conversation', index=True,
        comment="来源：github(GitHub拉取) | conversation(对话生成) | upload(手动上传) | official(官方预设)"
    )

    # ==================== 核心状态标识 ====================
    status: Mapped[str] = mapped_column(
        String(20), default='draft', index=True,
        comment="状态：draft(草稿) | testing(调试中) | published(已发布) | official(官方) | archived(归档)"
    )

    # 所有权（NULL 表示官方技能）
    author_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="创建者 ID（NULL 表示官方技能）"
    )

    # 使用统计
    usage_count: Mapped[int] = mapped_column(Integer, default=0, comment="使用次数")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator: Mapped[Optional["UserDB"]] = relationship("UserDB", foreign_keys=[author_id])

    def __repr__(self):
        return f"<SkillDB(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_official(self) -> bool:
        """是否为官方技能"""
        return self.author_id is None or self.status == 'official'

    @property
    def can_load_in_chat(self) -> bool:
        """是否可在 AI 对话中加载"""
        return self.status in ('published', 'official')

    @property
    def can_debug_online(self) -> bool:
        """是否可在线调试"""
        return self.status in ('draft', 'testing')

    def get_skill_dir(self) -> Path:
        """获取技能目录路径"""
        from pathlib import Path
        return Path(self.skill_path)

    def get_skill_file_path(self) -> Path:
        """获取 SKILL.md 文件路径"""
        return self.get_skill_dir() / "SKILL.md"

    def get_skill_content(self) -> str:
        """读取 SKILL.md 内容"""
        try:
            return self.get_skill_file_path().read_text(encoding='utf-8')
        except FileNotFoundError:
            return f"# 技能文件未找到\n\n技能路径：{self.skill_path}"

    def is_available(self) -> bool:
        """检查技能是否可用（目录和 SKILL.md 都存在）"""
        return self.get_skill_file_path().exists()


class UserFileRelationshipDB(Base):
    """User file relationship table
    
    Stores the relationship between users, sessions, conversation turns, and uploaded files.
    Works with docs-management index system:
    - doc_id references an entry in docs-management index
    - File metadata is redundantly stored here for fast queries
    - Supports various query scenarios (by user, session, turn, etc.)
    """
    __tablename__ = "user_file_relationships"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True,
        comment="User who uploaded the file"
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), 
        nullable=True, index=True,  # 允许 NULL，可延迟绑定
        comment="Session where the file was uploaded (can be NULL initially, bound later)"
    )
    conversation_turn_id: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,  # 不允许 NULL，提前生成
        comment="Conversation turn when the file was uploaded (generated early, required)"
    )
    
    # Reference to docs-management index
    doc_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True,
        comment="Reference to docs-management index entry (e.g., user-upload-{user_id}-{file_hash})"
    )
    
    # File metadata (redundant storage for fast queries)
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Original file name"
    )
    file_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="File MIME type (e.g., application/pdf, image/png)"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="File size in bytes"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True,
        comment="Whether this file relationship is active (soft delete)"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True,
        comment="When the file was uploaded"
    )
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB")
    session: Mapped["SessionDB"] = relationship("SessionDB")
    
    def __repr__(self):
        return f"<UserFileRelationshipDB(user_id={self.user_id}, doc_id={self.doc_id}, file_name={self.file_name})>"


# =========================================================================
# Phase 1 & Phase 2: 场景配置相关模型
# =========================================================================

class SystemDefaultConfigDB(Base):
    """系统默认配置表"""
    __tablename__ = "system_default_config"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    config_value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemDefaultConfigDB(config_key={self.config_key})>"


class UserScenarioConfigDB(Base):
    """用户场景配置表（支持多场景）"""
    __tablename__ = "user_scenario_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # 场景配置（JSON数组，支持多选）
    scenario_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON数组，存储用户选择的场景ID列表，NULL表示使用默认场景"
    )
    
    # 用户自定义prompt
    user_custom_prompt: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="用户自定义prompt和规则"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB")
    
    def __repr__(self):
        return f"<UserScenarioConfigDB(user_id={self.user_id})>"


class SessionScenarioConfigDB(Base):
    """会话场景配置表（会话级覆盖）"""
    __tablename__ = "session_scenario_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # 场景配置（JSON数组，支持多选）
    scenario_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON数组，存储会话选择的场景ID列表，NULL表示使用用户配置或默认"
    )
    
    # 会话级自定义prompt
    session_custom_prompt: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="会话级自定义prompt，覆盖用户配置"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session: Mapped["SessionDB"] = relationship("SessionDB")
    
    def __repr__(self):
        return f"<SessionScenarioConfigDB(session_id={self.session_id})>"


# =========================================================================
# Phase 3: 自我进化机制 - 数据库模型
# =========================================================================


# =========================================================================
# Phase 3: 自我进化机制 - 数据库模型
# =========================================================================

class UserFeedbackDB(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=True, index=True
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    conversation_turn_id: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True,
        comment="对话轮次ID，用于关联用户问题和AI回答"
    )
    
    # 反馈类型和内容
    feedback_type: Mapped[str] = mapped_column(
        String(50), index=True,
        comment="反馈类型：like, dislike, correct, regenerate, implicit_retry, implicit_modify"
    )
    feedback_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="反馈数据：原因、修正内容、隐式反馈的上下文等"
    )
    
    # 反馈上下文
    user_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assistant_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenario_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="使用的场景ID列表（JSON数组）"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user: Mapped[Optional["UserDB"]] = relationship("UserDB")
    session: Mapped[Optional["SessionDB"]] = relationship("SessionDB")
    message: Mapped[Optional["MessageDB"]] = relationship("MessageDB")
    
    def __repr__(self):
        return f"<UserFeedbackDB(id={self.id}, type={self.feedback_type}, user_id={self.user_id})>"


class UserPreferencesCacheDB(Base):
    """用户偏好缓存表"""
    __tablename__ = "user_preferences_cache"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # 缓存数据
    data_summary_hash: Mapped[str] = mapped_column(
        String(64), index=True,
        comment="数据摘要的hash值，用于判断是否需要重新分析"
    )
    preferences: Mapped[dict] = mapped_column(
        JSON,
        comment="用户偏好（JSON格式）：常用场景、回答风格、问题类型模式等"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB")
    
    def __repr__(self):
        return f"<UserPreferencesCacheDB(user_id={self.user_id})>"


class SessionPreferencesDB(Base):
    """会话偏好表"""
    __tablename__ = "session_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), unique=True, index=True
    )

    # 会话偏好
    preferences: Mapped[dict] = mapped_column(
        JSON,
        comment="会话偏好（JSON格式）：临时偏好、会话上下文偏好等"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session: Mapped["SessionDB"] = relationship("SessionDB")

    def __repr__(self):
        return f"<SessionPreferencesDB(session_id={self.session_id})>"


# =========================================================================
# Phase 4: 能力包系统 - 数据库模型
# =========================================================================

class CapabilityPackageDB(Base):
    """能力包表 - 打包 skill、tools、MCP 为可独立管理的单元

    设计理念：
    1. 将 skill、tools、MCP 打包成能力包
    2. 用户直接绑定能力包，实现细粒度权限控制
    3. 支持请求级能力注入
    """
    __tablename__ = "capability_packages"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True,
        comment="能力包标识符，如 data-analysis-pack"
    )
    display_name: Mapped[str] = mapped_column(
        String(200),
        comment="显示名称，如 数据分析工具包"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="能力包描述"
    )
    version: Mapped[str] = mapped_column(
        String(20), default="1.0.0",
        comment="版本号"
    )

    # 所有权
    author_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="创建者ID（NULL表示系统预设）"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True,
        comment="是否公开（所有用户可见）"
    )
    is_official: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否官方能力包"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="分类：analysis/development/automation 等"
    )

    # 能力定义
    skills: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="技能列表：{\"skills\": [\"data-analysis\", \"echarts_chart\"]}"
    )
    allowed_tools: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="允许的工具：[\"Read\", \"Write\", \"Bash\"]"
    )
    mcp_servers: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="MCP服务器配置：{\"server_name\": {...}}"
    )
    custom_prompt_extension: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="系统提示词扩展"
    )

    # 插件路径（用于SDK加载）
    plugin_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="插件目录路径，用于SDK plugins参数"
    )

    # 元数据
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="标签：[\"data\", \"chart\", \"report\"]"
    )

    # 统计
    usage_count: Mapped[int] = mapped_column(Integer, default=0, comment="使用次数")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author: Mapped[Optional["UserDB"]] = relationship("UserDB", foreign_keys=[author_id])
    user_bindings: Mapped[List["UserCapabilityBindingDB"]] = relationship(
        "UserCapabilityBindingDB", back_populates="package", cascade="all, delete-orphan"
    )
    user_bindings: Mapped[list["UserCapabilityBindingDB"]] = relationship(
        "UserCapabilityBindingDB", back_populates="package", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CapabilityPackageDB(id={self.id}, name={self.name})>"

    @property
    def skill_list(self) -> list:
        """获取技能名称列表"""
        if not self.skills:
            return []
        if isinstance(self.skills, dict):
            return self.skills.get("skills", [])
        return self.skills if isinstance(self.skills, list) else []

    @property
    def tool_list(self) -> list:
        """获取工具名称列表"""
        if not self.allowed_tools:
            return []
        if isinstance(self.allowed_tools, list):
            return self.allowed_tools
        if isinstance(self.allowed_tools, dict):
            return self.allowed_tools.get("tools", [])
        return []


class UserCapabilityBindingDB(Base):
    """用户能力绑定表 - 核心权限控制

    设计理念：
    1. 用户只能使用已绑定的能力包
    2. 请求时系统自动校验 plugin_ids 是否在绑定范围内
    3. 后台管理员配置绑定关系
    """
    __tablename__ = "user_capability_bindings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True,
        comment="用户ID"
    )
    package_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("capability_packages.id", ondelete="CASCADE"), index=True,
        comment="能力包ID"
    )

    # 绑定状态
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True,
        comment="是否启用"
    )

    # 授权信息
    granted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow,
        comment="授权时间"
    )
    granted_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        comment="授权管理员ID"
    )

    # 使用统计
    usage_count: Mapped[int] = mapped_column(Integer, default=0, comment="使用次数")
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", foreign_keys=[user_id])
    package: Mapped["CapabilityPackageDB"] = relationship(
        "CapabilityPackageDB", back_populates="user_bindings"
    )
    granted_by_user: Mapped[Optional["UserDB"]] = relationship("UserDB", foreign_keys=[granted_by])

    # 唯一约束
    __table_args__ = (
        UniqueConstraint("user_id", "package_id", name="uq_user_package"),
    )

    def __repr__(self):
        return f"<UserCapabilityBindingDB(user_id={self.user_id}, package_id={self.package_id})>"


class UserBehaviorStatsDB(Base):
    """用户行为统计表（轻量级聚合数据）"""
    __tablename__ = "user_behavior_stats"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    
    # 统计信息（轻量级聚合数据）
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_feedback: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 场景使用统计（JSON格式）
    scenario_usage: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="场景使用统计：{scenario_id: count}"
    )
    
    # 问题类型统计（JSON格式）
    question_types: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="问题类型统计：{type: count}"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB")
    
    def __repr__(self):
        return f"<UserBehaviorStatsDB(user_id={self.user_id}, sessions={self.total_sessions})>"
