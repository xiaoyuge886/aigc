"""
数据库迁移脚本：为 messages 表添加 result_info 字段

运行方式：
python -m backend.migrations.add_result_info_column
"""
import asyncio
import sqlite3
from pathlib import Path
from loguru import logger

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


async def migrate():
    """添加 result_info 字段到 messages 表"""
    if not DB_PATH.exists():
        logger.warning(f"数据库文件不存在: {DB_PATH}")
        return

    logger.info(f"开始迁移数据库: {DB_PATH}")

    # 使用同步 SQLite 连接（因为 sqlite3 不支持异步）
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]

        if "result_info" in columns:
            logger.info("字段 result_info 已存在，跳过迁移")
            return

        # 添加 result_info 字段
        logger.info("添加 result_info 字段...")
        cursor.execute(
            "ALTER TABLE messages ADD COLUMN result_info TEXT"
        )
        conn.commit()
        logger.info("✅ 迁移成功：已添加 result_info 字段")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
