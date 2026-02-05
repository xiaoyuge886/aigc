"""
GitHub Skills API
从 GitHub 拉取技能的 API 端点
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.database import SkillDB, UserDB
from services.github_skill_service import GitHubSkillService
from services.database import get_db
from services.auth import get_current_user
from api.v1.auth import is_admin_user


# 创建路由
router = APIRouter(prefix="/github-skills", tags=["github-skills"])


# ========================================================================
# Request/Response Models
# ========================================================================

class GitHubRepoResponse(BaseModel):
    """GitHub 仓库响应"""
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    stars: int
    language: Optional[str] = None
    updated_at: Optional[str] = None


class SkillListItem(BaseModel):
    """技能列表项"""
    name: str
    description: str
    relative_path: str
    has_config: bool


class InstallSkillRequest(BaseModel):
    """安装技能请求"""
    repo_url: str = Field(..., description="GitHub 仓库 URL")
    skill_name: str = Field(..., description="技能名称")
    subpath: Optional[str] = Field(None, description="技能子路径（如果仓库包含多个技能）")
    branch: Optional[str] = Field(None, description="分支名")


class InstallSkillResponse(BaseModel):
    """安装技能响应"""
    id: int
    name: str
    description: Optional[str] = None
    skill_path: str
    status: str
    author_id: Optional[int] = None
    usage_count: int
    created_at: str
    updated_at: str


# ========================================================================
# Dependencies
# ========================================================================

async def get_github_service(db: AsyncSession = Depends(get_db)) -> GitHubSkillService:
    """获取 GitHub 技能服务"""
    return GitHubSkillService(db)


# ========================================================================
# API Endpoints
# ========================================================================

@router.get("/search", response_model=List[GitHubRepoResponse])
async def search_github_repos(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: UserDB = Depends(get_current_user),
    service: GitHubSkillService = Depends(get_github_service)
):
    """
    搜索 GitHub 仓库

    搜索包含技能的 GitHub 仓库
    """
    try:
        repos = await service.search_github_repos(query, limit)
        return [GitHubRepoResponse(**repo) for repo in repos]

    except Exception as e:
        logger.error(f"Error searching GitHub repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{repo_url:path}/skills", response_model=List[SkillListItem])
async def list_repo_skills(
    repo_url: str,
    current_user: UserDB = Depends(get_current_user),
    service: GitHubSkillService = Depends(get_github_service)
):
    """
    列出仓库中的所有技能

    扫描 GitHub 仓库，返回其中包含的所有技能
    """
    try:
        # URL 解码
        from urllib.parse import unquote
        repo_url = unquote(repo_url)

        skills = await service.list_repo_skills(repo_url)
        return [SkillListItem(**skill) for skill in skills]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error listing repo skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/install", response_model=InstallSkillResponse)
async def install_skill_from_github(
    request: InstallSkillRequest,
    current_user: UserDB = Depends(get_current_user),
    service: GitHubSkillService = Depends(get_github_service)
):
    """
    从 GitHub 安装技能

    将 GitHub 仓库中的技能安装到调试目录
    """
    try:
        skill = await service.install_skill_from_github(
            repo_url=request.repo_url,
            skill_name=request.skill_name,
            subpath=request.subpath,
            branch=request.branch,
            author_id=current_user.id
        )

        return InstallSkillResponse(
            id=skill.id,
            name=skill.name,
            description=skill.description,
            skill_path=skill.skill_path,
            status=skill.status,
            author_id=skill.author_id,
            usage_count=skill.usage_count,
            created_at=skill.created_at.isoformat() + "Z",
            updated_at=skill.updated_at.isoformat() + "Z"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error installing skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish/{skill_id}", response_model=InstallSkillResponse)
async def publish_skill(
    skill_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发布技能到生产环境

    将技能从调试目录 (backend/.claude/debug_skills/)
    发布到生产目录 (.claude/skills/)

    同时更新状态为 published
    """
    try:
        from sqlalchemy import select
        from pathlib import Path
        import shutil

        # 获取技能记录
        result = await db.execute(select(SkillDB).where(SkillDB.id == skill_id))
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        # 检查权限
        is_admin = is_admin_user(current_user)
        is_creator = skill.author_id == current_user.id

        if not (is_admin or is_creator):
            raise HTTPException(status_code=403, detail="Not authorized")

        # 源目录和目标目录
        debug_dir = Path(__file__).parent.parent.parent / ".claude" / "debug_skills" / skill.name
        prod_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "skills" / skill.name

        if not debug_dir.exists():
            raise HTTPException(status_code=400, detail="Debug skill directory not found")

        # 复制到生产目录
        if prod_dir.exists():
            shutil.rmtree(prod_dir)

        shutil.copytree(debug_dir, prod_dir)

        # 更新状态
        skill.status = 'published'
        skill.skill_path = str(prod_dir)

        await db.commit()
        await db.refresh(skill)

        logger.info(f"Published skill: {skill.name} to {prod_dir}")

        return InstallSkillResponse(
            id=skill.id,
            name=skill.name,
            description=skill.description,
            skill_path=skill.skill_path,
            status=skill.status,
            author_id=skill.author_id,
            usage_count=skill.usage_count,
            created_at=skill.created_at.isoformat() + "Z",
            updated_at=skill.updated_at.isoformat() + "Z"
        )

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Error publishing skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-skills", response_model=List[InstallSkillResponse])
async def list_debug_skills(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    列出调试中的技能

    返回所有 status='testing' 的技能
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(SkillDB)
            .where(SkillDB.status == 'testing')
            .order_by(SkillDB.updated_at.desc())
        )
        skills = result.scalars().all()

        return [
            InstallSkillResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                skill_path=s.skill_path,
                status=s.status,
                author_id=s.author_id,
                usage_count=s.usage_count,
                created_at=s.created_at.isoformat() + "Z",
                updated_at=s.updated_at.isoformat() + "Z"
            )
            for s in skills
        ]

    except Exception as e:
        logger.error(f"Error listing debug skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/debug-skills/{skill_id}")
async def delete_debug_skill(
    skill_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除调试中的技能

    删除 testing 状态的技能及其文件
    """
    try:
        from sqlalchemy import select
        from pathlib import Path

        # 获取技能记录
        result = await db.execute(select(SkillDB).where(SkillDB.id == skill_id))
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")

        # 检查权限
        is_admin = is_admin_user(current_user)
        is_creator = skill.author_id == current_user.id

        if not (is_admin or is_creator):
            raise HTTPException(status_code=403, detail="Not authorized")

        # 只允许删除 testing 状态的技能
        if skill.status != 'testing':
            raise HTTPException(
                status_code=400,
                detail="Can only delete skills in testing status"
            )

        # 删除文件
        skill_dir = Path(skill.skill_path)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            logger.info(f"Deleted skill directory: {skill_dir}")

        # 删除数据库记录
        await db.delete(skill)
        await db.commit()

        return {"status": "deleted", "skill_id": skill_id}

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting debug skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))
