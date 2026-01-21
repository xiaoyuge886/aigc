"""
数据库迁移脚本：为 business_scenarios 表添加 category 和 meta 字段

运行方式：
python -m backend.migrations.add_scenario_meta_fields
"""
import asyncio
import sqlite3
from pathlib import Path
from loguru import logger

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


async def migrate():
    """添加 category 和 meta 字段到 business_scenarios 表"""
    if not DB_PATH.exists():
        logger.warning(f"数据库文件不存在: {DB_PATH}")
        return

    logger.info(f"开始迁移数据库: {DB_PATH}")

    # 使用同步 SQLite 连接（因为 sqlite3 不支持异步）
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='business_scenarios'")
        if not cursor.fetchone():
            logger.warning("表 business_scenarios 不存在，跳过迁移")
            return

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(business_scenarios)")
        columns = [row[1] for row in cursor.fetchall()]

        # 添加 category 字段
        if "category" not in columns:
            logger.info("添加 category 字段...")
            cursor.execute(
                "ALTER TABLE business_scenarios ADD COLUMN category VARCHAR(50)"
            )
            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS ix_business_scenarios_category ON business_scenarios(category)"
            )
            logger.info("✅ 已添加 category 字段和索引")
        else:
            logger.info("字段 category 已存在，跳过")

        # 添加 meta 字段
        if "meta" not in columns:
            logger.info("添加 meta 字段...")
            cursor.execute(
                "ALTER TABLE business_scenarios ADD COLUMN meta TEXT"
            )
            logger.info("✅ 已添加 meta 字段")
        else:
            logger.info("字段 meta 已存在，跳过")

        conn.commit()
        logger.info("✅ 迁移成功：已添加 category 和 meta 字段到 business_scenarios 表")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
