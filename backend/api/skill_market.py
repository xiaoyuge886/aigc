"""
Skill Market API Routes
技能市场 API 路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.skill_market_schemas import (
    SkillPackageCreate, SkillPackageUpdate, SkillPackageResponse, SkillPackageDetail,
    SkillPackageVersionCreate, SkillPackageVersionResponse,
    SkillItemCreate, SkillItemResponse,
    UserInstalledSkillCreate, UserInstalledSkillUpdate, UserInstalledSkillResponse,
    SkillReviewCreate, SkillReviewResponse,
    SkillMarketQuery, SkillMarketListResponse,
    SkillUsageLogCreate, SkillUsageLogResponse,
    SkillDebugRequest, SkillDebugResponse,
    SkillStatisticsResponse
)
from services.skill_market_service import SkillMarketService
from services.database import get_db
from services.auth import get_current_user, get_current_user_optional
from models.database import UserDB


# 创建路由
router = APIRouter(prefix="/skills", tags=["skill-market"])


# =========================================================================
# Dependencies - 依赖注入
# =========================================================================

async def get_skill_market_service(db: AsyncSession = Depends(get_db)) -> SkillMarketService:
    """获取技能市场服务"""
    return SkillMarketService(db)


# =========================================================================
# Skill Market - 技能市场
# =========================================================================

@router.get("/market")
async def query_skill_market(
    category: Optional[str] = Query(None, description="按分类筛选（暂不支持）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort: Optional[str] = Query("latest", description="排序方式: latest/popular"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_testing: bool = Query(False, description="是否包含调试中的技能"),
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    查询技能市场

    返回已发布（published/official）的技能列表，可选择包含调试中的技能

    - **search**: 搜索关键词（匹配名称、描述）
    - **sort**: 排序方式
        - latest: 按更新时间排序（默认）
        - popular: 按使用次数排序
    - **include_testing**: 是否显示调试中的技能
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（1-100）
    """
    try:
        from sqlalchemy import select, desc, or_
        from models.database import SkillDB

        # 构建查询
        stmt = select(SkillDB)

        # 搜索过滤
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    SkillDB.name.ilike(search_term),
                    SkillDB.description.ilike(search_term)
                )
            )

        # 状态过滤：默认只显示已发布的
        if include_testing and current_user:
            # 显示已发布的 + 当前用户调试中的
            stmt = stmt.where(
                or_(
                    SkillDB.status.in_(['published', 'official']),
                    SkillDB.status == 'testing'
                )
            )
        else:
            stmt = stmt.where(SkillDB.status.in_(['published', 'official']))

        # 排序
        if sort == "popular":
            stmt = stmt.order_by(desc(SkillDB.usage_count))
        else:  # latest
            stmt = stmt.order_by(desc(SkillDB.updated_at))

        # 分页
        stmt = stmt.limit(page_size).offset((page - 1) * page_size)

        # 执行查询
        result = await service.db.execute(stmt)
        skills = result.scalars().all()

        # 转换为响应格式
        return {
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "usage_count": s.usage_count,
                    "author_id": s.author_id,
                    "is_official": s.is_official,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                }
                for s in skills
            ],
            "total": len(skills),
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Error querying skill market: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-skills")
async def get_my_skills(
    status_filter: Optional[str] = Query(None, description="按状态筛选: testing/published"),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的技能列表

    返回当前用户创建的所有技能，包括调试中和已发布的

    - **status_filter**: 状态筛选（testing/published/draft/archived）
    """
    try:
        from sqlalchemy import select, desc
        from models.database import SkillDB

        # 构建查询：只查询当前用户的技能
        stmt = select(SkillDB).where(SkillDB.author_id == current_user.id)

        # 状态过滤
        if status_filter:
            stmt = stmt.where(SkillDB.status == status_filter)

        # 排序：按更新时间降序
        stmt = stmt.order_by(desc(SkillDB.updated_at))

        # 执行查询
        result = await db.execute(stmt)
        skills = result.scalars().all()

        # 转换为响应格式
        return {
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "usage_count": s.usage_count,
                    "skill_path": s.skill_path,
                    "is_official": s.is_official,
                    "can_debug_online": s.can_debug_online,
                    "can_load_in_chat": s.can_load_in_chat,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                }
                for s in skills
            ],
            "total": len(skills)
        }

    except Exception as e:
        logger.error(f"Error getting my skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{package_id}", response_model=SkillPackageDetail)
async def get_skill_package_detail(
    package_id: int,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    获取技能包详情

    返回技能包的完整信息，包括：
    - 基本信息
    - 版本列表
    - 包含的技能项
    - 用户评价
    """
    try:
        user_id = current_user.id if current_user else None
        detail = await service.get_skill_package_detail(package_id, user_id)

        if not detail:
            raise HTTPException(status_code=404, detail="Skill package not found")

        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill package detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market", response_model=SkillPackageResponse)
async def create_skill_package(
    package_data: SkillPackageCreate,
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    创建技能包（需要登录）

    上传新的技能包到市场
    """
    try:
        db_package = await service.create_skill_package(
            package_data,
            author_id=current_user.id
        )

        return SkillPackageResponse(**service._skill_package_to_dict(db_package))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating skill package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/market/{package_id}", response_model=SkillPackageResponse)
async def update_skill_package(
    package_id: int,
    update_data: SkillPackageUpdate,
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    更新技能包信息（需要登录且是作者）

    只有技能包的作者才能更新
    """
    try:
        # 检查权限
        db_package = await service.get_skill_package(package_id)
        if not db_package:
            raise HTTPException(status_code=404, detail="Skill package not found")

        if db_package.author_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this package")

        # 更新
        updated = await service.update_skill_package(package_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Skill package not found")

        return SkillPackageResponse(**service._skill_package_to_dict(updated))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating skill package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Skill Package Installation - 安装管理
# =========================================================================

@router.post("/market/{package_id}/install", response_model=UserInstalledSkillResponse)
async def install_skill_package(
    package_id: int,
    version_id: Optional[int] = Query(None, description="指定版本ID，不指定则安装最新版"),
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    安装技能包（需要登录）

    安装指定的技能包到用户环境
    """
    try:
        installed = await service.install_skill_package(
            current_user.id,
            package_id,
            version_id
        )

        return UserInstalledSkillResponse(
            id=installed.id,
            user_id=installed.user_id,
            package_id=installed.package_id,
            version_id=installed.version_id,
            installed_version=installed.installed_version,
            install_path=installed.install_path,
            is_enabled=installed.is_enabled,
            custom_config=installed.custom_config,
            has_update=installed.has_update,
            last_check_at=installed.last_check_at,
            installed_at=installed.installed_at,
            updated_at=installed.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error installing skill package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/market/{package_id}/install")
async def uninstall_skill_package(
    package_id: int,
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    卸载技能包（需要登录）

    从用户环境中移除技能包
    """
    try:
        success = await service.uninstall_skill_package(current_user.id, package_id)

        if not success:
            raise HTTPException(status_code=404, detail="Installed skill package not found")

        return {"status": "uninstalled", "package_id": package_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uninstalling skill package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/installed", response_model=List[UserInstalledSkillResponse])
async def list_installed_skills(
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    获取用户已安装的技能列表（需要登录）

    返回当前用户安装的所有技能包
    """
    try:
        installed = await service.list_user_installed_skills(current_user.id)

        return [
            UserInstalledSkillResponse(
                id=item.id,
                user_id=item.user_id,
                package_id=item.package_id,
                version_id=item.version_id,
                installed_version=item.installed_version,
                install_path=item.install_path,
                is_enabled=item.is_enabled,
                custom_config=item.custom_config,
                has_update=item.has_update,
                last_check_at=item.last_check_at,
                installed_at=item.installed_at,
                updated_at=item.updated_at
            )
            for item in installed
        ]

    except Exception as e:
        logger.error(f"Error listing installed skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/installed/{package_id}", response_model=dict)
async def update_installed_skill(
    package_id: int,
    update_data: UserInstalledSkillUpdate,
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    更新已安装技能的设置（需要登录）

    可以启用/禁用技能，或更新自定义配置
    """
    try:
        installed = await service.get_user_installed_skill(current_user.id, package_id)
        if not installed:
            raise HTTPException(status_code=404, detail="Skill package not installed")

        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(installed, field, value)

        await service.db.commit()
        await service.db.refresh(installed)

        return {"status": "updated", "package_id": package_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating installed skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Skill Items - 技能项管理
# =========================================================================

@router.get("/items/{item_id}", response_model=SkillItemResponse)
async def get_skill_item(
    item_id: int,
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    获取技能项详情

    返回单个技能的完整内容
    """
    try:
        item = await service.get_skill_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Skill item not found")

        return SkillItemResponse(**service._skill_item_to_dict(item))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/name/{skill_name}", response_model=SkillItemResponse)
async def get_skill_item_by_name(
    skill_name: str,
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    通过技能名称获取技能项

    用于调试和预览技能
    """
    try:
        item = await service.get_skill_item_by_name(skill_name)
        if not item:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

        return SkillItemResponse(**service._skill_item_to_dict(item))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill item by name: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Usage Logging - 使用日志
# =========================================================================

@router.get("/logs", response_model=List[SkillUsageLogResponse])
async def get_skill_usage_logs(
    skill_name: Optional[str] = Query(None, description="筛选特定技能"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    获取技能使用日志（需要登录）

    返回当前用户的技能使用历史，用于分析和调试
    """
    try:
        logs = await service.get_skill_usage_logs(
            current_user.id,
            skill_name=skill_name,
            limit=limit
        )

        return [
            SkillUsageLogResponse(
                id=log.id,
                user_id=log.user_id,
                session_id=log.session_id,
                skill_name=log.skill_name,
                skill_id=log.skill_id,
                success=log.success,
                error_message=log.error_message,
                execution_time_ms=log.execution_time_ms,
                user_query=log.user_query,
                agent_response=log.agent_response,
                used_at=log.used_at
            )
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Error getting skill usage logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Statistics - 统计信息
# =========================================================================

@router.get("/stats", response_model=SkillStatisticsResponse)
async def get_skill_statistics(
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    获取技能市场统计信息

    返回整体统计数据，包括：
    - 总技能包数
    - 总下载次数
    - 各分类的技能数量
    - 热门技能
    """
    try:
        from sqlalchemy import select, func, desc
        from models.skill_market import SkillPackageDB

        # 总技能包数
        total_packages_result = await service.db.execute(
            select(func.count()).select_from(SkillPackageDB).where(SkillPackageDB.is_active == True)
        )
        total_packages = total_packages_result.scalar() or 0

        # 总下载次数
        total_downloads_result = await service.db.execute(
            select(func.sum(SkillPackageDB.download_count)).where(SkillPackageDB.is_active == True)
        )
        total_downloads = total_downloads_result.scalar() or 0

        # 总安装次数
        total_installs_result = await service.db.execute(
            select(func.sum(SkillPackageDB.install_count)).where(SkillPackageDB.is_active == True)
        )
        total_installs = total_installs_result.scalar() or 0

        # 平均评分
        avg_rating_result = await service.db.execute(
            select(func.avg(SkillPackageDB.rating_average)).where(SkillPackageDB.is_active == True)
        )
        average_rating = avg_rating_result.scalar() or 0.0

        # 分类统计
        category_count_result = await service.db.execute(
            select(SkillPackageDB.category, func.count())
            .where(SkillPackageDB.is_active == True)
            .group_by(SkillPackageDB.category)
        )
        category_counts = dict(category_count_result.all())

        # 热门技能（前5个）
        popular_result = await service.db.execute(
            select(SkillPackageDB)
            .where(SkillPackageDB.is_active == True)
            .order_by(desc(SkillPackageDB.download_count))
            .limit(5)
        )
        popular_skills = [service._skill_package_to_dict(pkg) for pkg in popular_result.scalars().all()]

        return SkillStatisticsResponse(
            total_packages=total_packages,
            total_downloads=total_downloads,
            total_installs=total_installs,
            total_reviews=0,  # TODO: 实现评价统计
            average_rating=round(average_rating, 2),
            category_counts=category_counts,
            popular_skills=[SkillPackageResponse(**pkg) for pkg in popular_skills]
        )

    except Exception as e:
        logger.error(f"Error getting skill statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Debug/Test - 调试和测试
# =========================================================================

@router.post("/debug", response_model=SkillDebugResponse)
async def debug_skill(
    debug_request: SkillDebugRequest,
    current_user: UserDB = Depends(get_current_user),
    service: SkillMarketService = Depends(get_skill_market_service)
):
    """
    调试技能（需要登录）

    使用指定的技能处理测试查询，用于优化和调试技能
    """
    try:
        import time
        from services.agent_service import process_agent_message
        from services.skill_loader import load_skill_content

        # 获取技能内容
        skill_item = await service.get_skill_item_by_name(debug_request.skill_name)
        if not skill_item:
            raise HTTPException(status_code=404, detail=f"Skill '{debug_request.skill_name}' not found")

        skill_content = skill_item.skill_content

        # 记录开始时间
        start_time = time.time()

        # 使用技能处理查询
        # TODO: 这里需要集成实际的 Agent 处理逻辑
        # 暂时返回模拟数据
        execution_time_ms = int((time.time() - start_time) * 1000)

        # 记录使用日志
        log_data = SkillUsageLogCreate(
            skill_name=debug_request.skill_name,
            skill_id=skill_item.id,
            session_id=debug_request.session_id,
            success=True,
            execution_time_ms=execution_time_ms,
            user_query=debug_request.query,
            agent_response="[Simulated response - integration pending]"
        )

        await service.log_skill_usage(current_user.id, log_data)

        return SkillDebugResponse(
            skill_name=debug_request.skill_name,
            skill_content=skill_content[:500] + "..." if len(skill_content) > 500 else skill_content,
            user_query=debug_request.query,
            agent_response="[Simulated response - Agent service integration pending]",
            execution_time_ms=execution_time_ms,
            success=True,
            usage_log_id=log_data.skill_id  # 临时使用
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error debugging skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# Delete Skill - 删除技能
# =========================================================================

@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除技能

    只有技能的创建者或管理员可以删除技能

    - **skill_id**: 技能ID
    """
    try:
        from sqlalchemy import select
        from models.database import SkillDB
        from pathlib import Path
        import shutil

        # 查询技能
        stmt = select(SkillDB).where(SkillDB.id == skill_id)
        result = await db.execute(stmt)
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(status_code=404, detail="技能不存在")

        # 权限检查：只有创建者或管理员可以删除
        if skill.author_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="您没有权限删除此技能")

        # 删除本地文件
        if skill.skill_path:
            skill_path = Path(skill.skill_path)
            if skill_path.exists():
                try:
                    shutil.rmtree(skill_path)
                    logger.info(f"Deleted skill directory: {skill_path}")
                except Exception as e:
                    logger.error(f"Failed to delete skill directory {skill_path}: {e}")
                    # 继续删除数据库记录，即使文件删除失败

        # 删除数据库记录
        await db.delete(skill)
        await db.commit()

        logger.info(f"Skill deleted: {skill_id} by user {current_user.id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/files")
async def get_skill_files(
    skill_id: int,
    current_user: UserDB = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取技能的文件树结构和内容
    
    返回技能目录下的所有文件，用于调试界面显示
    """
    from sqlalchemy import select
    from models.database import SkillDB
    from pathlib import Path
    
    try:
        # 查询技能
        stmt = select(SkillDB).where(SkillDB.id == skill_id)
        result = await db.execute(stmt)
        skill = result.scalar_one_or_none()
        
        if not skill:
            raise HTTPException(status_code=404, detail="技能不存在")
        
        # 构建技能目录的完整路径
        # skill_path 是相对路径，需要从项目根目录解析
        project_root = Path(__file__).parent.parent.parent  # backend/.. -> project root
        skill_full_path = project_root / skill.skill_path
        
        if not skill_full_path.exists():
            # 尝试使用 backend/.claude/debug_skills 目录
            debug_skills_dir = Path(__file__).parent.parent / ".claude" / "debug_skills"
            skill_full_path = debug_skills_dir / skill.name
        
        if not skill_full_path.exists():
            raise HTTPException(status_code=404, detail=f"技能目录不存在: {skill_full_path}")
        
        # 递归读取文件树
        def build_file_tree(directory: Path, base_path: Path) -> dict:
            """递归构建文件树"""
            tree = {
                "name": directory.name,
                "type": "folder",
                "path": str(directory.relative_to(base_path)),
                "children": []
            }
            
            try:
                for item in sorted(directory.iterdir()):
                    # 跳过隐藏文件和 __pycache__
                    if item.name.startswith('.') or item.name == '__pycache__':
                        continue
                    
                    if item.is_dir():
                        tree["children"].append(build_file_tree(item, base_path))
                    elif item.is_file():
                        # 读取文件内容
                        try:
                            content = item.read_text(encoding='utf-8', errors='ignore')
                        except Exception as e:
                            logger.warning(f"Failed to read file {item}: {e}")
                            content = f"# Error reading file: {str(e)}\n"
                        
                        tree["children"].append({
                            "name": item.name,
                            "type": "file",
                            "path": str(item.relative_to(base_path)),
                            "content": content
                        })
            except PermissionError:
                logger.warning(f"Permission denied accessing {directory}")
            
            return tree
        
        # 构建文件树
        file_tree = build_file_tree(skill_full_path, skill_full_path.parent)

        return {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "file_tree": file_tree
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_skill_zip(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传技能 ZIP 文件（需要登录）

    支持上传技能的 ZIP 压缩包，自动解压到调试目录
    """
    import zipfile
    import io
    import shutil
    from sqlalchemy import select
    from models.database import SkillDB

    try:
        # 验证文件类型
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="只支持 ZIP 格式的文件")

        # 验证文件大小（最大 50MB）
        MAX_SIZE = 50 * 1024 * 1024
        content = await file.read()

        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

        # 读取 ZIP 文件
        zip_file = zipfile.ZipFile(io.BytesIO(content))

        # 提取技能名称（使用 ZIP 文件名或根目录名）
        skill_name = file.filename.replace('.zip', '')

        # 检查 ZIP 结构，找到包含 SKILL.md 或 skill.md 的根目录
        root_dir = None
        extracted_files = []

        for file_info in zip_file.filelist:
            extracted_files.append(file_info.filename)

            # 跳过 __MACOSX 和其他隐藏文件
            if file_info.filename.startswith('__MACOSX/') or file_info.filename.startswith('.'):
                continue

            # 查找 SKILL.md 或 skill.md
            if file_info.filename.endswith('SKILL.md') or file_info.filename.endswith('skill.md'):
                # 获取技能根目录（SKILL.md 的父目录）
                parts = file_info.filename.split('/')
                if len(parts) >= 2:
                    potential_root = '/'.join(parts[:-1])
                    if not root_dir or len(potential_root) < len(root_dir):
                        root_dir = potential_root
                elif len(parts) == 1:
                    # SKILL.md 在根目录
                    root_dir = ''
                    break

        if not root_dir:
            raise HTTPException(status_code=400, detail="ZIP 文件中未找到 SKILL.md 或 skill.md 文件")

        # 目标目录
        debug_skills_dir = Path(__file__).parent.parent / ".claude" / "debug_skills"
        debug_skills_dir.mkdir(parents=True, exist_ok=True)

        skill_target_dir = debug_skills_dir / skill_name
        if skill_target_dir.exists():
            shutil.rmtree(skill_target_dir)
        skill_target_dir.mkdir()

        # 解压文件
        for file_info in zip_file.filelist:
            # 跳过隐藏文件和 __MACOSX
            if file_info.filename.startswith('__MACOSX/') or file_info.filename.startswith('.'):
                continue

            # 计算相对路径
            if root_dir:
                if not file_info.filename.startswith(root_dir):
                    continue
                relative_path = file_info.filename[len(root_dir):].lstrip('/')
            else:
                relative_path = file_info.filename

            if not relative_path:
                continue

            # 目标文件路径
            target_path = skill_target_dir / relative_path

            # 创建目录
            if file_info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                # 写入文件
                with zip_file.open(file_info) as source:
                    target_path.write_bytes(source.read())

        logger.info(f"Skill uploaded and extracted to: {skill_target_dir}")

        # 解析技能信息
        skill_md = skill_target_dir / "SKILL.md"
        if not skill_md.exists():
            skill_md = skill_target_dir / "skill.md"

        if not skill_md.exists():
            raise HTTPException(status_code=400, detail="解压后未找到 SKILL.md 或 skill.md 文件")

        # 读取技能描述
        import re
        import yaml

        content = skill_md.read_text(encoding="utf-8", errors="ignore")
        description = ""

        # 解析 YAML front matter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter_text = match.group(1)
            try:
                frontmatter = yaml.safe_load(frontmatter_text) or {}
                description = frontmatter.get('description', '')
            except yaml.YAMLError:
                pass

        # 如果没有描述，从内容提取
        if not description:
            lines = content.split('\n')
            for line in lines[:30]:
                line = line.strip()
                if line.startswith('#'):
                    description = line.lstrip('#').strip()
                    break
                if line and not line.startswith('<!--'):
                    description = line[:200]
                    break

        # 检查是否已存在
        existing = await db.execute(
            select(SkillDB).where(SkillDB.name == skill_name)
        )
        existing_skill = existing.scalar_one_or_none()

        if existing_skill:
            # 更新现有记录
            existing_skill.skill_path = str(skill_target_dir)
            existing_skill.status = 'testing'
            existing_skill.description = description
            existing_skill.source = 'upload'
            await db.commit()
            await db.refresh(existing_skill)
            logger.info(f"Updated existing skill: {skill_name}")
        else:
            # 创建新记录
            new_skill = SkillDB(
                name=skill_name,
                description=description,
                skill_path=str(skill_target_dir),
                status='testing',
                author_id=current_user.id,
                usage_count=0,
                source='upload'
            )

            db.add(new_skill)
            await db.commit()
            await db.refresh(new_skill)
            logger.info(f"Created new skill record: {new_skill.id} - {new_skill.name}")

        return {
            "status": "success",
            "skill_id": existing_skill.id if existing_skill else new_skill.id,
            "skill_name": skill_name,
            "message": "技能上传成功",
            "files": [f for f in extracted_files if not f.startswith('__MACOSX/') and not f.startswith('.')]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading skill ZIP: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/create-from-conversation")
async def create_skill_from_conversation(
    skill_name: str = Query(..., description="技能名称"),
    description: str = Query("", description="技能描述"),
    skill_content: str = Query(..., description="SKILL.md 内容"),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    从对话创建技能（需要登录）

    保存通过 AI 对话生成的技能到 debug_skills 目录，状态为 draft
    """
    from pathlib import Path
    from sqlalchemy import select
    import re
    import yaml
    from models.database import SkillDB

    try:
        # 验证技能名称（只允许字母、数字、连字符和下划线）
        if not re.match(r'^[a-zA-Z0-9_-]+$', skill_name):
            raise HTTPException(
                status_code=400,
                detail="技能名称只能包含字母、数字、连字符和下划线"
            )

        # 目标目录
        debug_skills_dir = Path(__file__).parent.parent / ".claude" / "debug_skills"
        debug_skills_dir.mkdir(parents=True, exist_ok=True)

        skill_target_dir = debug_skills_dir / skill_name

        # 如果技能已存在，先删除旧版本
        if skill_target_dir.exists():
            import shutil
            shutil.rmtree(skill_target_dir)

        skill_target_dir.mkdir()

        # 写入 SKILL.md
        skill_file = skill_target_dir / "SKILL.md"
        skill_file.write_text(skill_content, encoding='utf-8')

        logger.info(f"Skill created from conversation: {skill_file}")

        # 如果没有提供描述，尝试从 SKILL.md 中解析
        if not description:
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
            match = re.match(frontmatter_pattern, skill_content, re.DOTALL)

            if match:
                frontmatter_text = match.group(1)
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                    description = frontmatter.get('description', '')
                except yaml.YAMLError:
                    pass

            # 如果仍然没有描述，从内容提取
            if not description:
                lines = skill_content.split('\n')
                for line in lines[:30]:
                    line = line.strip()
                    if line.startswith('#'):
                        description = line.lstrip('#').strip()
                        break
                    if line and not line.startswith('<!--'):
                        description = line[:200]
                        break

        # 检查数据库中是否已存在
        existing = await db.execute(
            select(SkillDB).where(SkillDB.name == skill_name)
        )
        existing_skill = existing.scalar_one_or_none()

        if existing_skill:
            # 更新现有记录
            existing_skill.skill_path = str(skill_target_dir)
            existing_skill.status = 'draft'  # 对话生成的技能，状态为 draft
            existing_skill.description = description
            existing_skill.source = 'conversation'  # 标记为对话生成
            await db.commit()
            await db.refresh(existing_skill)
            logger.info(f"Updated existing skill from conversation: {skill_name}")
            return {
                "status": "success",
                "skill_id": existing_skill.id,
                "skill_name": skill_name,
                "message": "技能已更新",
                "skill_path": str(skill_target_dir)
            }
        else:
            # 创建新记录
            new_skill = SkillDB(
                name=skill_name,
                description=description,
                skill_path=str(skill_target_dir),
                status='draft',  # 对话生成的技能，状态为 draft
                author_id=current_user.id,
                usage_count=0,
                source='conversation'  # 标记为对话生成
            )

            db.add(new_skill)
            await db.commit()
            await db.refresh(new_skill)
            logger.info(f"Created new skill from conversation: {new_skill.id} - {new_skill.name}")

            return {
                "status": "success",
                "skill_id": new_skill.id,
                "skill_name": skill_name,
                "message": "技能已保存到调试目录",
                "skill_path": str(skill_target_dir)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating skill from conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
