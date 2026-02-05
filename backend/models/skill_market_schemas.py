"""
Skill Market API Schemas
技能市场 API 数据传输对象
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# =========================================================================
# Enums - 枚举类型
# =========================================================================

class SourceType(str, Enum):
    """技能来源类型"""
    UPLOAD = "upload"
    GITHUB = "github"
    URL = "url"
    BUILTIN = "builtin"


class VisibilityType(str, Enum):
    """可见性类型"""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class SkillType(str, Enum):
    """技能类型"""
    MARKDOWN = "markdown"
    JSON = "json"


# =========================================================================
# Skill Package Schemas - 技能包 Schema
# =========================================================================

class SkillPackageBase(BaseModel):
    """技能包基础 Schema"""
    name: str = Field(..., description="技能包名称", min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=200)
    description: Optional[str] = Field(None, description="简短描述")
    long_description: Optional[str] = Field(None, description="详细描述 (Markdown)")
    category: Optional[str] = Field(None, description="分类", max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    repository_url: Optional[HttpUrl] = Field(None, description="仓库URL")
    homepage_url: Optional[HttpUrl] = Field(None, description="主页URL")
    documentation_url: Optional[HttpUrl] = Field(None, description="文档URL")


class SkillPackageCreate(SkillPackageBase):
    """创建技能包"""
    identifier: str = Field(..., description="唯一标识 (如: username/skill-name)", max_length=200)
    author_name: Optional[str] = Field(None, description="作者名称", max_length=100)
    author_email: Optional[str] = Field(None, description="作者邮箱", max_length=255)
    source_type: SourceType = Field(default=SourceType.UPLOAD, description="来源类型")
    source_location: Optional[str] = Field(None, description="源位置")
    visibility: VisibilityType = Field(default=VisibilityType.PUBLIC, description="可见性")


class SkillPackageUpdate(BaseModel):
    """更新技能包"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_url: Optional[HttpUrl] = None
    homepage_url: Optional[HttpUrl] = None
    documentation_url: Optional[HttpUrl] = None
    visibility: Optional[VisibilityType] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class SkillPackageResponse(SkillPackageBase):
    """技能包响应"""
    id: int
    identifier: str
    current_version: Optional[str] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    source_type: str
    visibility: str

    # 统计信息
    download_count: int = 0
    install_count: int = 0
    view_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0

    # 状态
    is_featured: bool = False
    is_official: bool = False
    is_active: bool = True

    # 时间戳
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    # 用户相关信息（需要时填充）
    is_installed: bool = False
    has_update: bool = False

    class Config:
        from_attributes = True


class SkillPackageDetail(SkillPackageResponse):
    """技能包详情"""
    versions: List['SkillPackageVersionResponse'] = []
    items: List['SkillItemResponse'] = []
    reviews: List['SkillReviewResponse'] = []

    # 最新版本信息
    latest_version: Optional['SkillPackageVersionResponse'] = None


# =========================================================================
# Skill Package Version Schemas - 技能包版本 Schema
# =========================================================================

class SkillPackageVersionBase(BaseModel):
    """技能包版本基础 Schema"""
    version: str = Field(..., description="版本号 (如: 1.0.0)", min_length=1, max_length=20)
    changelog: Optional[str] = Field(None, description="更新日志 (Markdown)")
    min_agent_version: Optional[str] = Field(None, description="最小代理版本", max_length=20)
    max_agent_version: Optional[str] = Field(None, description="最大代理版本", max_length=20)
    dependencies: Optional[Dict[str, str]] = Field(default_factory=dict, description="依赖关系")


class SkillPackageVersionCreate(SkillPackageVersionBase):
    """创建技能包版本"""
    download_url: Optional[str] = Field(None, description="下载URL")
    file_size: Optional[int] = Field(None, description="文件大小 (字节)", ge=0)
    checksum: Optional[str] = Field(None, description="SHA256校验和", max_length=64)


class SkillPackageVersionResponse(SkillPackageVersionBase):
    """技能包版本响应"""
    id: int
    package_id: int
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# Skill Item Schemas - 技能项 Schema
# =========================================================================

class SkillItemBase(BaseModel):
    """技能项基础 Schema"""
    name: str = Field(..., description="技能名称", min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=200)
    description: Optional[str] = Field(None, description="技能描述")
    category: Optional[str] = Field(None, description="分类", max_length=50)
    skill_content: str = Field(..., description="技能内容 (Markdown/JSON)")
    skill_type: SkillType = Field(default=SkillType.MARKDOWN, description="技能类型")
    trigger_keywords: Optional[List[str]] = Field(default_factory=list, description="触发关键词")


class SkillItemCreate(SkillItemBase):
    """创建技能项"""
    package_id: Optional[int] = Field(None, description="所属技能包ID")
    package_version_id: Optional[int] = Field(None, description="所属版本ID")


class SkillItemUpdate(BaseModel):
    """更新技能项"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    skill_content: Optional[str] = None
    trigger_keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SkillItemResponse(SkillItemBase):
    """技能项响应"""
    id: int
    package_id: Optional[int] = None
    package_version_id: Optional[int] = None

    # 使用统计
    use_count: int = 0
    success_count: int = 0
    error_count: int = 0

    # 状态
    is_builtin: bool = False
    is_active: bool = True

    # 时间戳
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# User Installed Skill Schemas - 用户安装技能 Schema
# =========================================================================

class UserInstalledSkillBase(BaseModel):
    """用户安装技能基础 Schema"""
    package_id: int = Field(..., description="技能包ID")
    version_id: int = Field(..., description="版本ID")
    installed_version: str = Field(..., description="安装版本")


class UserInstalledSkillCreate(UserInstalledSkillBase):
    """创建用户安装技能"""
    install_path: Optional[str] = Field(None, description="安装路径")
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义配置")


class UserInstalledSkillUpdate(BaseModel):
    """更新用户安装技能"""
    is_enabled: Optional[bool] = None
    custom_config: Optional[Dict[str, Any]] = None


class UserInstalledSkillResponse(BaseModel):
    """用户安装技能响应"""
    id: int
    user_id: int
    package_id: int
    version_id: int

    installed_version: str
    install_path: Optional[str] = None
    is_enabled: bool = True
    custom_config: Optional[Dict[str, Any]] = None

    has_update: bool = False
    last_check_at: Optional[datetime] = None

    installed_at: datetime
    updated_at: datetime

    # 关联信息
    package: Optional[SkillPackageResponse] = None
    version: Optional[SkillPackageVersionResponse] = None

    class Config:
        from_attributes = True


# =========================================================================
# Review Schemas - 评价 Schema
# =========================================================================

class SkillReviewBase(BaseModel):
    """技能评价基础 Schema"""
    rating: int = Field(..., description="评分 1-5", ge=1, le=5)
    title: Optional[str] = Field(None, description="评价标题", max_length=200)
    content: Optional[str] = Field(None, description="评价内容")


class SkillReviewCreate(SkillReviewBase):
    """创建技能评价"""
    package_id: int = Field(..., description="技能包ID")


class SkillReviewUpdate(BaseModel):
    """更新技能评价"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None


class SkillReviewResponse(SkillReviewBase):
    """技能评价响应"""
    id: int
    package_id: int
    user_id: int
    helpful_count: int = 0
    created_at: datetime
    updated_at: datetime

    # 用户信息（需要时填充）
    user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# =========================================================================
# Usage Log Schemas - 使用日志 Schema
# =========================================================================

class SkillUsageLogCreate(BaseModel):
    """创建技能使用日志"""
    skill_name: str = Field(..., description="技能名称")
    skill_id: Optional[int] = Field(None, description="技能ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    success: Optional[bool] = Field(None, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time_ms: Optional[int] = Field(None, description="执行时间(毫秒)", ge=0)
    user_query: Optional[str] = Field(None, description="用户查询内容")
    agent_response: Optional[str] = Field(None, description="Agent响应内容")


class SkillUsageLogResponse(BaseModel):
    """技能使用日志响应"""
    id: int
    user_id: int
    session_id: Optional[str] = None
    skill_name: str
    skill_id: Optional[int] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    user_query: Optional[str] = None
    agent_response: Optional[str] = None
    used_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# Market Query Schemas - 市场查询 Schema
# =========================================================================

class SkillMarketQuery(BaseModel):
    """技能市场查询参数"""
    category: Optional[str] = Field(None, description="按分类筛选")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort: Optional[str] = Field("popular", description="排序方式: popular/latest/rated/featured/installed")
    tags: Optional[List[str]] = Field(None, description="按标签筛选")
    author: Optional[str] = Field(None, description="按作者筛选")
    visibility: Optional[VisibilityType] = Field(None, description="可见性")
    is_featured: Optional[bool] = Field(None, description="是否只看精选")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class SkillMarketListResponse(BaseModel):
    """技能市场列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    items: List[SkillPackageResponse] = Field(default_factory=list, description="技能包列表")


# =========================================================================
# Debug/Test Schemas - 调试/测试 Schema
# =========================================================================

class SkillDebugRequest(BaseModel):
    """技能调试请求"""
    skill_name: str = Field(..., description="技能名称")
    query: str = Field(..., description="测试查询内容")
    session_id: Optional[str] = Field(None, description="会话ID (可选)")


class SkillDebugResponse(BaseModel):
    """技能调试响应"""
    skill_name: str
    skill_content: str
    user_query: str
    agent_response: str
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None
    usage_log_id: Optional[int] = None


# =========================================================================
# Statistics Schemas - 统计 Schema
# =========================================================================

class SkillStatisticsResponse(BaseModel):
    """技能统计响应"""
    total_packages: int = 0
    total_downloads: int = 0
    total_installs: int = 0
    total_reviews: int = 0
    average_rating: float = 0.0
    category_counts: Dict[str, int] = Field(default_factory=dict)
    popular_skills: List[SkillPackageResponse] = Field(default_factory=list)


# 更新前向引用
SkillPackageDetail.model_rebuild()
