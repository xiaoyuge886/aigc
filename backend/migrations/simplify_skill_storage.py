"""
技能存储简化迁移脚本

简化 SkillDB 表结构，删除 UserSkillRelationDB 表

迁移内容：
1. 备份现有 skills 表数据
2. 简化 skills 表结构（移除 category, source, is_official 等字段）
3. 删除 user_skill_relations 表
4. 恢复数据到新表

使用方法：
    python backend/migrations/simplify_skill_storage.py
    python backend/migrations/simplify_skill_storage.py --rollback  # 回滚
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

    logger.info("开始技能存储简化迁移...")

    db_service = get_database_service()
    await db_service.initialize()
    async with db_service.async_session() as db:
        try:
            # ==================== 1. 备份现有数据 ====================
            logger.info("步骤 1/6: 备份现有 skills 表数据...")

            # 检查 skills 表是否存在
            check_table_sql = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='skills'
            """
            result = await db.execute(text(check_table_sql))
            skills_table_exists = result.fetchone() is not None

            if skills_table_exists:
                # 创建备份表
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS skills_backup AS
                    SELECT * FROM skills
                """))
                await db.commit()
                logger.info("✅ skills 表数据已备份到 skills_backup")
            else:
                logger.info("ℹ️  skills 表不存在，跳过备份")

            # ==================== 2. 删除旧表 ====================
            logger.info("步骤 2/6: 删除旧表...")

            # 删除 user_skill_relations 表
            await db.execute(text("DROP TABLE IF EXISTS user_skill_relations"))
            logger.info("✅ user_skill_relations 表已删除")

            # 删除 skills 表
            await db.execute(text("DROP TABLE IF EXISTS skills"))
            logger.info("✅ skills 表已删除")

            # ==================== 3. 创建新的 skills 表 ====================
            logger.info("步骤 3/6: 创建新的 skills 表（极简结构）...")

            create_skills_sql = """
                CREATE TABLE skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    skill_path VARCHAR(500) UNIQUE NOT NULL,
                    status VARCHAR(20) DEFAULT 'draft',
                    author_id INTEGER NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """
            await db.execute(text(create_skills_sql))

            # 创建索引
            await db.execute(text("CREATE INDEX idx_skills_status ON skills(status)"))
            await db.execute(text("CREATE INDEX idx_skills_author ON skills(author_id)"))
            await db.execute(text("CREATE INDEX idx_skills_usage ON skills(usage_count)"))

            await db.commit()
            logger.info("✅ skills 表创建成功（极简结构）")

            # ==================== 4. 恢复数据 ====================
            logger.info("步骤 4/6: 从备份恢复数据...")

            # 检查备份表是否有数据
            check_backup_sql = "SELECT COUNT(*) as count FROM skills_backup"
            result = await db.execute(text(check_backup_sql))
            backup_count = result.fetchone()[0]

            if backup_count > 0:
                # 从备份恢复数据（映射旧字段到新字段）
                restore_sql = """
                    INSERT INTO skills (
                        name, description, skill_path, status,
                        author_id, usage_count, created_at, updated_at
                    )
                    SELECT
                        name,
                        description,
                        COALESCE(filesystem_path, '.claude/skills/' || name || '/'),
                        CASE
                            WHEN is_default = 1 THEN 'official'
                            ELSE 'published'
                        END as status,
                        created_by as author_id,
                        COALESCE(usage_count, 0) as usage_count,
                        created_at,
                        updated_at
                    FROM skills_backup
                """
                await db.execute(text(restore_sql))
                await db.commit()
                logger.info(f"✅ 已恢复 {backup_count} 条技能数据")
            else:
                logger.info("ℹ️  备份表无数据，跳过恢复")

            # ==================== 5. 验证数据 ====================
            logger.info("步骤 5/6: 验证迁移结果...")

            # 检查 skills 表数据
            check_skills_sql = "SELECT COUNT(*) as count FROM skills"
            result = await db.execute(text(check_skills_sql))
            skills_count = result.fetchone()[0]

            logger.info(f"✅ skills 表现有 {skills_count} 条记录")

            # 显示前几条记录
            sample_sql = "SELECT id, name, status, author_id FROM skills LIMIT 5"
            result = await db.execute(text(sample_sql))
            samples = result.fetchall()

            if samples:
                logger.info("示例记录：")
                for row in samples:
                    logger.info(f"  - ID: {row[0]}, Name: {row[1]}, Status: {row[2]}, Author: {row[3]}")

            # ==================== 6. 清理备份表（可选）====================
            logger.info("步骤 6/6: 迁移完成！")
            logger.info("ℹ️  备份表 skills_backup 已保留，如需删除请手动执行：")
            logger.info("   DROP TABLE skills_backup;")

            logger.success("✨ 技能存储简化迁移完成！")

        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            await db.rollback()
            raise


async def rollback():
    """回滚迁移（从备份恢复）"""

    logger.warning("开始回滚迁移...")

    db_service = get_database_service()
    await db_service.initialize()
    async with db_service.async_session() as db:
        try:
            # 检查备份表是否存在
            check_backup_sql = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='skills_backup'
            """
            result = await db.execute(text(check_backup_sql))
            backup_exists = result.fetchone() is not None

            if not backup_exists:
                logger.error("❌ 备份表不存在，无法回滚")
                return

            # 删除新表
            await db.execute(text("DROP TABLE IF EXISTS skills"))
            logger.info("✅ 新的 skills 表已删除")

            # 从备份恢复旧表结构（完整版本）
            restore_old_sql = """
                CREATE TABLE skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    skill_path VARCHAR(500) UNIQUE NOT NULL,
                    category VARCHAR(50),
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'draft',
                    source VARCHAR(20) DEFAULT 'user',
                    author_id INTEGER NULL,
                    is_official BOOLEAN DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """
            await db.execute(text(restore_old_sql))

            # 恢复索引
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_skills_path ON skills(skill_path)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_skills_author ON skills(author_id)"))

            # 恢复数据
            restore_data_sql = """
                INSERT INTO skills SELECT * FROM skills_backup
            """
            await db.execute(text(restore_data_sql))

            await db.commit()
            logger.success("✅ 回滚完成，已恢复到迁移前状态")

        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="技能存储简化迁移脚本")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移（从备份恢复）"
    )

    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
