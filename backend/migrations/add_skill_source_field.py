"""
技能来源字段迁移脚本

为 skills 表添加 source 字段，用于标识技能来源（GitHub、对话生成、手动上传、官方预设）

迁移内容：
1. 添加 source 字段到 skills 表
2. 为现有记录设置默认值
3. 创建索引

使用方法：
    python backend/migrations/add_skill_source_field.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from loguru import logger
from sqlalchemy import text
from services.database import get_database_service


async def migrate():
    """执行数据库迁移"""

    logger.info("开始添加技能来源字段...")

    db_service = get_database_service()
    await db_service.initialize()
    async with db_service.async_session() as db:
        try:
            # ==================== 1. 检查字段是否存在 ====================
            logger.info("步骤 1/4: 检查 source 字段是否存在...")

            check_column_sql = """
                PRAGMA table_info(skills)
            """
            result = await db.execute(text(check_column_sql))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            if 'source' in column_names:
                logger.info("ℹ️  source 字段已存在，跳过迁移")
                return

            logger.info("✅ source 字段不存在，开始添加...")

            # ==================== 2. 添加 source 字段 ====================
            logger.info("步骤 2/4: 添加 source 字段...")

            add_column_sql = """
                ALTER TABLE skills
                ADD COLUMN source VARCHAR(50) DEFAULT 'conversation'
            """
            await db.execute(text(add_column_sql))
            await db.commit()
            logger.info("✅ source 字段已添加")

            # ==================== 3. 为现有记录设置合理的来源值 ====================
            logger.info("步骤 3/4: 为现有记录设置来源值...")

            # 将官方技能（author_id IS NULL 或 status = 'official'）设置为 'official'
            update_official_sql = """
                UPDATE skills
                SET source = 'official'
                WHERE author_id IS NULL OR status = 'official'
            """
            result = await db.execute(text(update_official_sql))
            official_count = result.rowcount
            logger.info(f"✅ 已将 {official_count} 个官方技能标记为 'official'")

            # 其余技能默认为 'conversation'
            update_others_sql = """
                UPDATE skills
                SET source = 'conversation'
                WHERE source IS NULL OR source = ''
            """
            result = await db.execute(text(update_others_sql))
            others_count = result.rowcount
            logger.info(f"✅ 已将 {others_count} 个技能标记为 'conversation'")

            await db.commit()

            # ==================== 4. 创建索引 ====================
            logger.info("步骤 4/4: 创建索引...")

            create_index_sql = """
                CREATE INDEX IF NOT EXISTS idx_skills_source ON skills(source)
            """
            await db.execute(text(create_index_sql))
            await db.commit()
            logger.info("✅ source 字段索引已创建")

            # ==================== 验证结果 ====================
            logger.info("验证迁移结果...")

            verify_sql = """
                SELECT source, COUNT(*) as count
                FROM skills
                GROUP BY source
            """
            result = await db.execute(text(verify_sql))
            stats = result.fetchall()

            logger.info("技能来源统计：")
            for row in stats:
                logger.info(f"  - {row[0]}: {row[1]} 个")

            logger.success("✨ 技能来源字段迁移完成！")

        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            await db.rollback()
            raise


async def rollback():
    """回滚迁移（删除 source 字段）"""

    logger.warning("开始回滚迁移...")

    db_service = get_database_service()
    await db_service.initialize()
    async with db_service.async_session() as db:
        try:
            # SQLite 不支持 DROP COLUMN，需要重建表
            logger.info("ℹ️  SQLite 不支持 DROP COLUMN，需要手动重建表")
            logger.info("如需回滚，请手动执行以下步骤：")
            logger.info("1. 创建新表（不包含 source 字段）")
            logger.info("2. 复制数据")
            logger.info("3. 删除旧表")
            logger.info("4. 重命名新表")

            # 删除索引
            drop_index_sql = "DROP INDEX IF EXISTS idx_skills_source"
            await db.execute(text(drop_index_sql))
            await db.commit()
            logger.info("✅ source 字段索引已删除")

            logger.warning("⚠️  索引已删除，但字段仍存在（SQLite 限制）")

        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="技能来源字段迁移脚本")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移"
    )

    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
