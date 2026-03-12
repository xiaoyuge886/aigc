"""
Platform configuration models (Pydantic)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class UserConfigCreate(BaseModel):
    """Create user configuration request"""
    default_system_prompt: Optional[str] = Field(None, description="Default system prompt")
    default_allowed_tools: Optional[List[str]] = Field(None, description="Default allowed tools list")
    default_model: Optional[str] = Field(None, description="Default model")
    permission_mode: Optional[str] = Field(None, description="Permission mode")
    max_turns: Optional[int] = Field(None, description="Maximum turns")
    work_dir: Optional[str] = Field(None, description="Working directory path")
    custom_tools: Optional[Dict[str, Any]] = Field(None, description="Custom MCP server configs")
    custom_skills: Optional[List[str]] = Field(None, description="Custom skill names list")
    associated_scenario_id: Optional[int] = Field(None, description="Associated business scenario ID (integer)")


class UserConfigUpdate(BaseModel):
    """Update user configuration request"""
    default_system_prompt: Optional[str] = None
    default_allowed_tools: Optional[List[str]] = None
    default_model: Optional[str] = None
    permission_mode: Optional[str] = None
    max_turns: Optional[int] = None
    work_dir: Optional[str] = None
    custom_tools: Optional[Dict[str, Any]] = None
    custom_skills: Optional[List[str]] = None
    associated_scenario_id: Optional[int] = None


class UserConfigResponse(BaseModel):
    """User configuration response"""
    user_id: int
    default_system_prompt: Optional[str] = None
    default_allowed_tools: Optional[List[str]] = None
    default_model: Optional[str] = None
    permission_mode: Optional[str] = None
    max_turns: Optional[int] = None
    work_dir: Optional[str] = None
    custom_tools: Optional[Dict[str, Any]] = None
    custom_skills: Optional[List[str]] = None
    associated_scenario_id: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BusinessScenarioCreate(BaseModel):
    """Create business scenario request"""
    # 移除 scenario_id 字段，使用自增整数 id
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    category: Optional[str] = Field(None, description="Scenario category (e.g., '技术开发', '数据分析', '商业助手')")
    meta: Optional[Dict[str, Any]] = Field(None, description="Scenario meta information (tags, capabilities, keywords, etc.)")
    system_prompt: str = Field(..., description="System prompt for this scenario")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tools list")
    recommended_model: Optional[str] = Field(None, description="Recommended model")
    custom_tools: Optional[Dict[str, Any]] = Field(None, description="Custom MCP server configs")
    skills: Optional[List[str]] = Field(None, description="Skill names list (specific skill IDs to enable)")
    workflow: Optional[Dict[str, Any]] = Field(None, description="Workflow definition")
    # 高优先级参数
    permission_mode: Optional[str] = Field(None, description="Permission mode (acceptEdits, plan, bypassPermissions, etc.)")
    max_turns: Optional[int] = Field(None, description="Maximum conversation turns")
    work_dir: Optional[str] = Field(None, description="Working directory path")
    is_public: bool = Field(False, description="Whether scenario is public")
    is_default: bool = Field(False, description="Whether scenario is system default (admin only)")


class BusinessScenarioUpdate(BaseModel):
    """Update business scenario request"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    recommended_model: Optional[str] = None
    custom_tools: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    workflow: Optional[Dict[str, Any]] = None
    permission_mode: Optional[str] = None
    max_turns: Optional[int] = None
    work_dir: Optional[str] = None
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None


class BusinessScenarioResponse(BaseModel):
    """Business scenario response"""
    id: int  # 使用整数ID作为业务标识
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    system_prompt: str
    allowed_tools: Optional[List[str]] = None
    recommended_model: Optional[str] = None
    custom_tools: Optional[Dict[str, Any]] = None
    skills: Optional[List[str]] = None
    workflow: Optional[Dict[str, Any]] = None
    permission_mode: Optional[str] = None
    max_turns: Optional[int] = None
    work_dir: Optional[str] = None
    created_by: Optional[int] = None
    is_public: bool
    is_default: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AgentConfig(BaseModel):
    """Merged agent configuration"""
    system_prompt: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    model: Optional[str] = None
    permission_mode: Optional[str] = None
    max_turns: Optional[int] = None
    cwd: Optional[str] = None
    custom_tools: Optional[Dict[str, Any]] = None
    setting_sources: Optional[List[str]] = None
    enabled_skill_ids: Optional[List[str]] = None  # 指定要启用的技能ID列表（用于精细控制）
    add_dirs: Optional[List[str]] = None  # 额外的可访问目录（用于调试技能时只加载单个技能）
    # 新增： 插件配置
    sdk_plugins: Optional[List[Dict[str, str]]] = None  # SDK plugins 参数： [{"type": "local", "path": "..."}]
    plugin_ids: Optional[List[int]] = None  # 请求级指定的插件ID列表


# =========================================================================
# System Prompt Models
# =========================================================================

class SystemPromptCreate(BaseModel):
    """Create system prompt request"""
    # 移除 prompt_id 字段，使用自增整数 id
    name: str = Field(..., description="Prompt name")
    description: Optional[str] = Field(None, description="Prompt description")
    category: Optional[str] = Field(None, description="Prompt category")
    content: str = Field(..., description="Prompt content")
    is_default: bool = Field(False, description="Whether prompt is default")
    is_public: bool = Field(False, description="Whether prompt is public")


class SystemPromptUpdate(BaseModel):
    """Update system prompt request"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None


class SystemPromptResponse(BaseModel):
    """System prompt response"""
    id: int  # 使用整数ID作为业务标识
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    content: str
    usage_count: int
    is_default: bool
    created_by: Optional[int] = None
    is_public: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# =========================================================================
# Skill Models
# =========================================================================

class SkillCreate(BaseModel):
    """Create skill request"""
    # 移除 skill_id 字段，使用自增整数 id
    name: str = Field(..., description="Skill name")
    description: Optional[str] = Field(None, description="Skill description")
    category: Optional[str] = Field(None, description="Skill category")
    skill_content: str = Field(..., description="Skill content (SKILL.md)")
    skill_config: Optional[Dict[str, Any]] = Field(None, description="Skill config (skill.json)")
    is_default: bool = Field(False, description="Whether skill is default")
    is_public: bool = Field(False, description="Whether skill is public")


class SkillUpdate(BaseModel):
    """Update skill request"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    skill_content: Optional[str] = None
    skill_config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None


class SkillResponse(BaseModel):
    """Skill response"""
    id: int  # 使用整数ID作为业务标识
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    skill_content: str
    skill_config: Optional[Dict[str, Any]] = None
    usage_count: int
    is_default: bool
    created_by: Optional[int] = None
    is_public: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ToolResponse(BaseModel):
    """Tool response"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    category: str  # standard, custom, user_defined
    tool_type: str  # builtin, mcp, skill
    mcp_server: Optional[str] = None
    is_enabled: bool = True
    is_public: bool = True
    usage_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserScenarioConfigUpdate(BaseModel):
    """Update user scenario configuration request"""
    scenario_ids: Optional[List[int]] = Field(None, description="List of scenario IDs (integers) to enable for the user")
    user_custom_prompt: Optional[str] = Field(None, description="User custom prompt")


# =========================================================================
# Capability Package Models (能力包) ⭐ 核心功能
# =========================================================================

class CapabilityPackageCreate(BaseModel):
    """Create capability package request"""
    name: str = Field(..., description="Package identifier (e.g., 'data-analysis-pack')")
    display_name: str = Field(..., description="Display name (e.g., '数据分析工具包')")
    description: Optional[str] = Field(None, description="Package description")
    version: Optional[str] = Field("1.0.0", description="Package version")
    category: Optional[str] = Field(None, description="Category: analysis/development/automation")
    is_public: bool = Field(False, description="Whether package is public")
    is_official: bool = Field(False, description="Whether package is official")

    # 能力定义
    skills: Optional[List[str]] = Field(None, description="Skill names: ['data-analysis', 'echarts_chart']")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tools: ['Read', 'Write', 'Bash']")
    mcp_servers: Optional[Dict[str, Any]] = Field(None, description="MCP server configs")
    custom_prompt_extension: Optional[str] = Field(None, description="System prompt extension")
    plugin_path: Optional[str] = Field(None, description="Plugin directory path for SDK loading")

    # 元数据
    icon_url: Optional[str] = Field(None, description="Icon URL")
    tags: Optional[List[str]] = Field(None, description="Tags")


class CapabilityPackageUpdate(BaseModel):
    """Update capability package request"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    is_official: Optional[bool] = None

    # 能力定义
    skills: Optional[List[str]] = None
    allowed_tools: Optional[List[str]] = None
    mcp_servers: Optional[Dict[str, Any]] = None
    custom_prompt_extension: Optional[str] = None
    plugin_path: Optional[str] = None

    # 元数据
    icon_url: Optional[str] = None
    tags: Optional[List[str]] = None


class CapabilityPackageResponse(BaseModel):
    """Capability package response"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    is_public: bool
    is_official: bool

    # 能力定义
    skills: Optional[List[str]] = None
    allowed_tools: Optional[List[str]] = None
    mcp_servers: Optional[Dict[str, Any]] = None
    custom_prompt_extension: Optional[str] = None
    plugin_path: Optional[str] = None

    # 元数据
    icon_url: Optional[str] = None
    tags: Optional[List[str]] = None

    # 统计
    usage_count: int = 0
    author_id: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# =========================================================================
# User Capability Binding Models (用户能力绑定) ⭐ 核心功能
# =========================================================================

class UserCapabilityBindingCreate(BaseModel):
    """Create user capability binding request (admin)"""
    user_id: int = Field(..., description="User ID")
    package_id: int = Field(..., description="Capability package ID")
    is_enabled: bool = Field(True, description="Whether binding is enabled")


class UserCapabilityBindingUpdate(BaseModel):
    """Update user capability binding request"""
    is_enabled: Optional[bool] = None


class UserCapabilityBindingResponse(BaseModel):
    """User capability binding response"""
    id: int
    user_id: int
    package_id: int
    package_name: Optional[str] = None  # 关联的能力包名称
    package_display_name: Optional[str] = None  # 关联的能力包显示名称
    is_enabled: bool
    granted_at: str
    granted_by: Optional[int] = None
    usage_count: int = 0
    last_used_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class UserPackagesResponse(BaseModel):
    """User's bound packages response"""
    user_id: int
    bindings: List[UserCapabilityBindingResponse]
    available_packages: List[CapabilityPackageResponse]  # 所有可用能力包（用于选择）


class ResolvePluginsResponse(BaseModel):
    """Resolved plugins configuration response"""
    skills: List[str] = []
    allowed_tools: List[str] = []
    mcp_servers: Dict[str, Any] = {}
    custom_prompt_extension: str = ""
    plugins: List[Dict[str, str]] = []  # SDK plugins 参数格式