#!/usr/bin/env python3
"""
Skills表管理脚本

用于管理skills表中的skill记录：
- 添加新skill
- 更新现有skill
- 列出所有skills
- 删除skill
- 查看skill详情
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加backend到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import get_database_service
from models.database import SkillDB
from sqlalchemy import select, update
import json


class SkillManager:
    """Skill管理器"""

    def __init__(self):
        self.db = get_database_service()

    async def initialize(self):
        """初始化数据库连接"""
        await self.db.initialize()

    async def close(self):
        """关闭数据库连接"""
        await self.db.close()

    async def add_skill(
        self,
        name: str,
        description: str,
        category: str,
        skill_file: str,
        skill_config: dict = None,
        is_default: bool = False,
        is_public: bool = True
    ):
        """添加新skill"""
        async with self.db.async_session() as session:
            # 检查是否已存在
            stmt = select(SkillDB).where(SkillDB.name == name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"❌ Skill已存在: {name} (id={existing.id})")
                print("💡 如需更新，请使用 update 命令")
                return False

            # 读取skill内容
            skill_path = Path(skill_file)
            if not skill_path.exists():
                print(f"❌ Skill文件不存在: {skill_file}")
                return False

            skill_content = skill_path.read_text(encoding='utf-8')

            # 创建skill记录
            skill = SkillDB(
                name=name,
                description=description,
                category=category,
                skill_content=skill_content,
                skill_config=skill_config or {},
                usage_count=0,
                is_default=is_default,
                is_public=is_public,
                created_by=None
            )

            session.add(skill)
            await session.commit()
            await session.refresh(skill)

            print(f"✅ Skill添加成功: {skill.name} (id={skill.id})")
            return True

    async def update_skill(
        self,
        name: str,
        description: str = None,
        category: str = None,
        skill_file: str = None,
        skill_config: dict = None,
        is_default: bool = None,
        is_public: bool = None
    ):
        """更新现有skill"""
        async with self.db.async_session() as session:
            # 查找skill
            stmt = select(SkillDB).where(SkillDB.name == name)
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()

            if not skill:
                print(f"❌ Skill不存在: {name}")
                return False

            # 更新字段
            if description:
                skill.description = description
            if category:
                skill.category = category
            if skill_file:
                skill_path = Path(skill_file)
                if not skill_path.exists():
                    print(f"❌ Skill文件不存在: {skill_file}")
                    return False
                skill.skill_content = skill_path.read_text(encoding='utf-8')
            if skill_config is not None:
                skill.skill_config = skill_config
            if is_default is not None:
                skill.is_default = is_default
            if is_public is not None:
                skill.is_public = is_public

            skill.updated_at = datetime.utcnow()

            await session.commit()

            print(f"✅ Skill更新成功: {skill.name} (id={skill.id})")
            return True

    async def list_skills(self, category: str = None):
        """列出所有skills"""
        async with self.db.async_session() as session:
            stmt = select(SkillDB)
            if category:
                stmt = stmt.where(SkillDB.category == category)

            stmt = stmt.order_by(SkillDB.id)

            result = await session.execute(stmt)
            skills = result.scalars().all()

            if not skills:
                print("❌ 没有找到任何skills")
                return

            print(f"\n📋 共有 {len(skills)} 个skills:\n")
            print(f"{'ID':<5} {'名称':<30} {'分类':<15} {'使用次数':<10} {'默认':<8} {'公开':<8}")
            print("-" * 90)

            for skill in skills:
                print(f"{skill.id:<5} {skill.name:<30} {skill.category:<15} "
                      f"{skill.usage_count:<10} {'是' if skill.is_default else '否':<8} "
                      f"{'是' if skill.is_public else '否':<8}")

            print()

    async def show_skill(self, name: str):
        """显示skill详情"""
        async with self.db.async_session() as session:
            stmt = select(SkillDB).where(SkillDB.name == name)
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()

            if not skill:
                print(f"❌ Skill不存在: {name}")
                return

            print(f"\n📊 Skill详细信息:\n")
            print(f"ID: {skill.id}")
            print(f"名称: {skill.name}")
            print(f"描述: {skill.description}")
            print(f"分类: {skill.category}")
            print(f"使用次数: {skill.usage_count}")
            print(f"是否默认: {'是' if skill.is_default else '否'}")
            print(f"是否公开: {'是' if skill.is_public else '否'}")
            print(f"创建时间: {skill.created_at}")
            print(f"更新时间: {skill.updated_at}")
            print(f"Skill内容长度: {len(skill.skill_content)} 字符")

            if skill.skill_config:
                print(f"\n📝 Skill Config:")
                print(json.dumps(skill.skill_config, indent=2, ensure_ascii=False))

            print()

    async def delete_skill(self, name: str):
        """删除skill"""
        async with self.db.async_session() as session:
            stmt = select(SkillDB).where(SkillDB.name == name)
            result = await session.execute(stmt)
            skill = result.scalar_one_or_none()

            if not skill:
                print(f"❌ Skill不存在: {name}")
                return False

            skill_id = skill.id
            await session.delete(skill)
            await session.commit()

            print(f"✅ Skill删除成功: {name} (id={skill_id})")
            return True

    async def load_skill_from_directory(self, skill_dir: str):
        """从目录加载skill"""
        skill_path = Path(skill_dir)
        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            print(f"❌ SKILL.md不存在: {skill_md}")
            return False

        # 读取SKILL.md的front matter
        content = skill_md.read_text(encoding='utf-8')
        lines = content.split('\n')

        name = None
        description = None
        category = "general"

        # 解析front matter (---之间的内容)
        in_front_matter = False
        for line in lines:
            if line.strip() == '---':
                in_front_matter = not in_front_matter
                continue

            if in_front_matter:
                if line.startswith('name:'):
                    name = line.split(':', 1)[1].strip()
                elif line.startswith('description:'):
                    description = line.split(':', 1)[1].strip()
                elif line.startswith('category:'):
                    category = line.split(':', 1)[1].strip()

        if not name:
            # 从目录名推断
            name = skill_path.name

        if not description:
            description = f"{name} skill"

        return await self.add_skill(
            name=name,
            description=description,
            category=category,
            skill_file=str(skill_md),
            is_default=True,
            is_public=True
        )


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Skills表管理脚本')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # add命令
    add_parser = subparsers.add_parser('add', help='添加新skill')
    add_parser.add_argument('--name', required=True, help='skill名称')
    add_parser.add_argument('--description', required=True, help='skill描述')
    add_parser.add_argument('--category', default='general', help='skill分类')
    add_parser.add_argument('--file', required=True, help='SKILL.md文件路径')
    add_parser.add_argument('--default', action='store_true', help='设为默认skill')

    # update命令
    update_parser = subparsers.add_parser('update', help='更新skill')
    update_parser.add_argument('--name', required=True, help='skill名称')
    update_parser.add_argument('--description', help='skill描述')
    update_parser.add_argument('--category', help='skill分类')
    update_parser.add_argument('--file', help='SKILL.md文件路径')

    # list命令
    list_parser = subparsers.add_parser('list', help='列出所有skills')
    list_parser.add_argument('--category', help='按分类筛选')

    # show命令
    show_parser = subparsers.add_parser('show', help='显示skill详情')
    show_parser.add_argument('--name', required=True, help='skill名称')

    # delete命令
    delete_parser = subparsers.add_parser('delete', help='删除skill')
    delete_parser.add_argument('--name', required=True, help='skill名称')

    # load命令
    load_parser = subparsers.add_parser('load', help='从目录加载skill')
    load_parser.add_argument('--dir', required=True, help='skill目录路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = SkillManager()
    await manager.initialize()

    try:
        if args.command == 'add':
            await manager.add_skill(
                name=args.name,
                description=args.description,
                category=args.category,
                skill_file=args.file,
                is_default=args.default
            )
        elif args.command == 'update':
            await manager.update_skill(
                name=args.name,
                description=args.description,
                category=args.category,
                skill_file=args.file
            )
        elif args.command == 'list':
            await manager.list_skills(category=args.category)
        elif args.command == 'show':
            await manager.show_skill(name=args.name)
        elif args.command == 'delete':
            await manager.delete_skill(name=args.name)
        elif args.command == 'load':
            await manager.load_skill_from_directory(skill_dir=args.dir)
    finally:
        await manager.close()


if __name__ == '__main__':
    asyncio.run(main())
