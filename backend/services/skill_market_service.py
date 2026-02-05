"""
Skill Market Service - 极简版本
技能市场服务 - 基于 SkillDB 表的极简设计

设计理念：
1. 技能存储在文件系统（.claude/skills/）
2. 数据库只存：名称、路径、状态、描述、作者、使用次数
3. 通过 status 区分：draft（草稿）| testing（调试中）| published（已发布）| official（官方）| archived（归档）
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models.database import SkillDB, UserDB


class SkillMarketService:
    """技能市场服务类 - 极简版本"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Skill CRUD - 技能 CRUD
    # =========================================================================

    async def create_skill(
        self,
        name: str,
        skill_path: str,
        description: Optional[str] = None,
        status: str = 'draft',
        author_id: Optional[int] = None
    ) -> SkillDB:
        """创建技能"""
        try:
            # 检查名称是否已存在
            existing = await self.db.execute(
                select(SkillDB).where(SkillDB.name == name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Skill with name '{name}' already exists")

            # 创建技能
            db_skill = SkillDB(
                name=name,
                skill_path=skill_path,
                description=description,
                status=status,
                author_id=author_id
            )

            self.db.add(db_skill)
            await self.db.commit()
            await self.db.refresh(db_skill)

            logger.info(f"Created skill: {db_skill.name}")
            return db_skill

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating skill: {e}")
            raise

    async def get_skill(self, skill_id: int) -> Optional[SkillDB]:
        """获取技能"""
        result = await self.db.execute(
            select(SkillDB).where(SkillDB.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def get_skill_by_name(self, name: str) -> Optional[SkillDB]:
        """通过名称获取技能"""
        result = await self.db.execute(
            select(SkillDB).where(SkillDB.name == name)
        )
        return result.scalar_one_or_none()

    async def update_skill(
        self,
        skill_id: int,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[SkillDB]:
        """更新技能"""
        try:
            db_skill = await self.get_skill(skill_id)
            if not db_skill:
                return None

            # 更新字段
            if description is not None:
                db_skill.description = description
            if status is not None:
                db_skill.status = status

            await self.db.commit()
            await self.db.refresh(db_skill)

            logger.info(f"Updated skill: {db_skill.name}")
            return db_skill

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating skill: {e}")
            raise

    async def delete_skill(self, skill_id: int) -> bool:
        """删除技能（软删除 - 标记为 archived）"""
        try:
            db_skill = await self.get_skill(skill_id)
            if not db_skill:
                return False

            db_skill.status = 'archived'
            await self.db.commit()

            logger.info(f"Deleted skill: {db_skill.name}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting skill: {e}")
            raise

    # =========================================================================
    # Market Query - 技能市场查询
    # =========================================================================

    async def list_published_skills(
        self,
        search: Optional[str] = None,
        author_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SkillDB]:
        """列出已发布的技能（市场展示）"""
        try:
            # 构建查询：只显示已发布和官方技能
            stmt = select(SkillDB).where(
                SkillDB.status.in_(['published', 'official'])
            )

            # 应用筛选条件
            if search:
                search_term = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        SkillDB.name.ilike(search_term),
                        SkillDB.description.ilike(search_term)
                    )
                )

            if author_id is not None:
                stmt = stmt.where(SkillDB.author_id == author_id)

            # 排序：按使用次数降序
            stmt = stmt.order_by(desc(SkillDB.usage_count))

            # 分页
            stmt = stmt.limit(limit).offset(offset)

            # 执行查询
            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error listing published skills: {e}")
            raise

    async def list_user_skills(
        self,
        user_id: int,
        status_filter: Optional[List[str]] = None
    ) -> List[SkillDB]:
        """列出用户的技能（草稿、调试中）"""
        try:
            stmt = select(SkillDB).where(SkillDB.author_id == user_id)

            # 默认显示草稿和调试中的技能
            if status_filter:
                stmt = stmt.where(SkillDB.status.in_(status_filter))
            else:
                stmt = stmt.where(SkillDB.status.in_(['draft', 'testing']))

            # 排序：按更新时间降序
            stmt = stmt.order_by(desc(SkillDB.updated_at))

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error listing user skills: {e}")
            raise

    async def list_official_skills(self) -> List[SkillDB]:
        """列出官方技能"""
        try:
            result = await self.db.execute(
                select(SkillDB)
                .where(SkillDB.status == 'official')
                .order_by(SkillDB.name)
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error listing official skills: {e}")
            raise

    # =========================================================================
    # Debug & Test - 调试和测试
    # =========================================================================

    async def start_debug_session(self, skill_id: int, user_id: int) -> Optional[SkillDB]:
        """开始调试会话（将技能标记为 testing）"""
        try:
            db_skill = await self.get_skill(skill_id)
            if not db_skill:
                return None

            # 检查权限
            if db_skill.author_id != user_id:
                raise ValueError("You don't have permission to debug this skill")

            # 标记为调试中
            db_skill.status = 'testing'
            await self.db.commit()
            await self.db.refresh(db_skill)

            logger.info(f"Started debug session for skill: {db_skill.name}")
            return db_skill

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting debug session: {e}")
            raise

    async def end_debug_session(self, skill_id: int, user_id: int) -> Optional[SkillDB]:
        """结束调试会话（将技能标记回 draft）"""
        try:
            db_skill = await self.get_skill(skill_id)
            if not db_skill:
                return None

            # 检查权限
            if db_skill.author_id != user_id:
                raise ValueError("You don't have permission to modify this skill")

            # 标记回草稿
            db_skill.status = 'draft'
            await self.db.commit()
            await self.db.refresh(db_skill)

            logger.info(f"Ended debug session for skill: {db_skill.name}")
            return db_skill

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error ending debug session: {e}")
            raise

    # =========================================================================
    # Usage Statistics - 使用统计
    # =========================================================================

    async def increment_usage_count(self, skill_name: str) -> bool:
        """增加技能使用次数"""
        try:
            db_skill = await self.get_skill_by_name(skill_name)
            if not db_skill:
                return False

            db_skill.usage_count += 1
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error incrementing usage count: {e}")
            await self.db.rollback()
            return False

    async def get_skill_statistics(self) -> Dict[str, Any]:
        """获取技能市场统计信息"""
        try:
            # 总技能数（已发布和官方）
            total_result = await self.db.execute(
                select(func.count())
                .select_from(SkillDB)
                .where(SkillDB.status.in_(['published', 'official']))
            )
            total_skills = total_result.scalar() or 0

            # 总使用次数
            usage_result = await self.db.execute(
                select(func.sum(SkillDB.usage_count))
                .where(SkillDB.status.in_(['published', 'official']))
            )
            total_usage = usage_result.scalar() or 0

            # 官方技能数
            official_result = await self.db.execute(
                select(func.count())
                .select_from(SkillDB)
                .where(SkillDB.status == 'official')
            )
            official_count = official_result.scalar() or 0

            # 草稿技能数
            draft_result = await self.db.execute(
                select(func.count())
                .select_from(SkillDB)
                .where(SkillDB.status == 'draft')
            )
            draft_count = draft_result.scalar() or 0

            return {
                "total_skills": total_skills,
                "total_usage": total_usage,
                "official_count": official_count,
                "draft_count": draft_count
            }

        except Exception as e:
            logger.error(f"Error getting skill statistics: {e}")
            raise

    # =========================================================================
    # Helper Methods - 辅助方法
    # =========================================================================

    def skill_to_dict(self, skill: SkillDB) -> Dict[str, Any]:
        """技能转字典"""
        return {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "skill_path": skill.skill_path,
            "status": skill.status,
            "author_id": skill.author_id,
            "is_official": skill.is_official,
            "can_load_in_chat": skill.can_load_in_chat,
            "can_debug_online": skill.can_debug_online,
            "usage_count": skill.usage_count,
            "created_at": skill.created_at,
            "updated_at": skill.updated_at
        }
