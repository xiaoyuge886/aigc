"""
Configuration management for the Agent Server
"""
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Configuration
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Agent Configuration
    default_model: str = Field(default="sonnet", description="Default Claude model")
    max_turns: int = Field(default=100, description="Maximum conversation turns")
    permission_mode: str = Field(default="acceptEdits", description="Permission mode")
    enable_security_control: bool = Field(default=True, description="Enable runtime security control (protects sensitive files and dangerous commands)")

    # Tools Configuration
    default_allowed_tools: str = Field(
        default="Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,TodoWrite,mcp__custom_tools__sqlite_query,mcp__custom_tools__sqlite_get_tables,mcp__custom_tools__sqlite_get_schema,mcp__custom_tools__sqlite_test_connection,mcp__custom_tools__enhanced_todo_write,mcp__custom_tools__todo_statistics",
        description="Comma-separated list of allowed tools"
    )

    # ============================================================================
    # Working Directory Configuration
    # ============================================================================

    # Production working directory (生产环境工作目录)
    # 用于对话环境的文件操作
    work_dir: Path = Field(
        default=Path(__file__).parent.parent.parent / "work_dir",
        description="Production working directory (用于对话环境)"
    )

    # Debug working directory (调试环境工作目录)
    # 用于调试环境的文件操作
    debug_work_dir: Path = Field(
        default=Path(__file__).parent.parent.parent / "debug_work_dir",
        description="Debug working directory (用于调试环境)"
    )

    # ============================================================================
    # Setting Sources Configuration (技能加载来源)
    # ============================================================================

    # Production setting sources (生产环境技能来源)
    # 用于对话环境的技能加载
    setting_sources: List[str] = Field(
        default=["project"],
        description="Production skill loading sources (用于对话环境)"
    )

    # Debug setting sources (调试环境技能来源)
    # 用于调试环境的技能加载
    debug_setting_sources: List[str] = Field(
        default=["project"],
        description="Debug skill loading sources (用于调试环境)"
    )

    # ============================================================================
    # Online Debug Feature (在线调试功能 - 面向用户)
    # ============================================================================

    # Online debug max turns (在线调试最大对话轮次)
    # 用户在测试技能时的轮次限制（通常比生产环境小，节省成本）
    online_debug_max_turns: int = Field(
        default=10,
        description="Online debug maximum conversation turns (for user skill testing)"
    )

    @field_validator('work_dir', mode='after')
    @classmethod
    def validate_work_dir(cls, v: Path) -> Path:
        """
        验证工作目录
        - 强制使用项目根目录下的 work_dir
        - 如果目录不存在，自动创建
        """
        import logging
        logger = logging.getLogger(__name__)

        # 确保路径是绝对路径
        if not v.is_absolute():
            v = v.resolve()

        # 强制目录必须是 work_dir
        if v.name != "work_dir":
            logger.warning(f"工作目录名称必须是 'work_dir'，当前是 '{v.name}'，强制修正")
            v = v.parent / "work_dir"

        # 自动创建目录（如果不存在）
        try:
            v.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 工作目录已准备就绪: {v}")
        except Exception as e:
            logger.error(f"❌ 无法创建工作目录 {v}: {e}")
            # 如果创建失败，回退到临时目录
            import tempfile
            v = Path(tempfile.gettempdir()) / "aigc_work_dir"
            v.mkdir(exist_ok=True)
            logger.warning(f"⚠️ 使用临时目录作为工作目录: {v}")

        return v

    @field_validator('debug_work_dir', mode='after')
    @classmethod
    def validate_debug_work_dir(cls, v: Path) -> Path:
        """
        验证调试环境工作目录
        - 强制使用项目根目录下的 debug_work_dir
        - 如果目录不存在，自动创建
        """
        import logging
        logger = logging.getLogger(__name__)

        # 确保路径是绝对路径
        if not v.is_absolute():
            v = v.resolve()

        # 强制目录名称必须是 debug_work_dir
        if v.name != "debug_work_dir":
            logger.warning(f"调试工作目录名称必须是 'debug_work_dir'，当前是 '{v.name}'，强制修正")
            v = v.parent / "debug_work_dir"

        # 自动创建目录（如果不存在）
        try:
            v.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 调试环境工作目录已准备就绪: {v}")
        except Exception as e:
            logger.error(f"❌ 无法创建调试工作目录 {v}: {e}")
            # 如果创建失败，回退到临时目录
            import tempfile
            v = Path(tempfile.gettempdir()) / "aigc_debug_work_dir"
            v.mkdir(exist_ok=True)
            logger.warning(f"⚠️ 使用临时目录作为调试工作目录: {v}")

        return v

    # Session Configuration
    session_timeout_seconds: int = Field(default=3600, description="Session timeout")
    max_concurrent_sessions: int = Field(default=100, description="Max concurrent sessions")

    # JWT Configuration
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=10080, description="JWT token expiry in minutes (7 days)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def allowed_tools_list(self) -> List[str]:
        """Parse comma-separated tools into a list"""
        return [tool.strip() for tool in self.default_allowed_tools.split(",") if tool.strip()]

    def get_agent_options(self) -> dict:
        """Get Claude Agent SDK options for production environment (对话环境)"""
        return {
            "allowed_tools": self.allowed_tools_list,
            "permission_mode": self.permission_mode,
            "max_turns": self.max_turns,
            "model": self.default_model,
            "cwd": str(self.work_dir),
            "setting_sources": self.setting_sources,
        }

    def get_debug_agent_options(self) -> dict:
        """Get Claude Agent SDK options for debug environment (调试环境)"""
        return {
            "allowed_tools": self.allowed_tools_list,
            "permission_mode": self.permission_mode,
            "max_turns": self.online_debug_max_turns,
            "model": self.default_model,
            "cwd": str(self.debug_work_dir),
            "setting_sources": self.debug_setting_sources,
        }


# Global settings instance
settings = Settings()
