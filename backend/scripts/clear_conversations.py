"""
清空对话记录 - SQLite 数据库清理脚本

清理选项：
1. 清空所有会话和消息
2. 只清空消息，保留会话
3. 清空特定时间之前的记录
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, select, func
from loguru import logger
from services.database import get_database_service


async def check_conversations():
    """检查对话记录数量"""
    db_service = get_database_service()
    await db_service.initialize()

    async with db_service.async_session() as db:
        # 检查会话数量
        sessions_result = await db.execute(
            select(func.count()).select_from(text("sessions"))
        )
        sessions_count = sessions_result.scalar() or 0

        # 检查消息数量
        messages_result = await db.execute(
            select(func.count()).select_from(text("messages"))
        )
        messages_count = messages_result.scalar() or 0

        # 检查活跃会话数
        active_result = await db.execute(
            select(func.count()).select_from(text("sessions")).where(text("is_connected = 1"))
        )
        active_count = active_result.scalar() or 0

        print(f"📊 当前数据库状态：")
        print(f"  - 会话总数：{sessions_count}")
        print(f"  - 消息总数：{messages_count}")
        print(f"  - 活跃会话：{active_count}")

        # 显示最近的会话
        recent_sessions = await db.execute(
            text("""
                SELECT session_id, model, created_at, last_activity, is_connected
                FROM sessions
                ORDER BY created_at DESC
                LIMIT 5
            """)
        )
        print(f"\n最近的 5 个会话：")
        for row in recent_sessions.fetchall():
            print(f"  - {row[0]} | {row[1]} | {row[2]} | 活跃：{row[4]}")


async def clear_all_conversations():
    """清空所有会话和消息"""
    logger.info("开始清空所有对话记录...")

    db_service = get_database_service()
    await db_service.initialize()

    async with db_service.async_session() as db:
        try:
            # 删除所有消息（由于有外键级联，会自动删除）
            await db.execute(text("DELETE FROM messages"))

            # 删除所有会话
            await db.execute(text("DELETE FROM sessions"))

            await db.commit()

            logger.success("✅ 已清空所有对话记录")

        except Exception as e:
            logger.error(f"❌ 清空失败: {e}")
            await db.rollback()
            raise


async def clear_all_messages_only():
    """只清空消息，保留会话"""
    logger.info("开始清空所有消息...")

    db_service = get_database_service()
    await db_service.initialize()

    async with db_service.async_session() as db:
        try:
            # 删除所有消息
            result = await db.execute(text("DELETE FROM messages"))
            await db.commit()

            logger.success(f"✅ 已清空 {result.rowcount} 条消息")

        except Exception as e:
            logger.error(f"❌ 清空消息失败: {e}")
            await db.rollback()
            raise


async def clear_old_messages(days=30):
    """清空指定天数之前的记录"""
    logger.info(f"开始清空 {days} 天之前的记录...")

    db_service = get_database_service()
    await db_service.initialize()

    async with db_service.async_session() as db:
        try:
            # 删除旧消息
            delete_date = datetime.utcnow() - timedelta(days=days)
            result_msg = await db.execute(
                text("DELETE FROM messages WHERE created_at < :date"),
                {"date": delete_date}
            )

            # 删除旧会话（没有消息的会话）
            result_sess = await db.execute(
                text("""
                    DELETE FROM sessions
                    WHERE id NOT IN (SELECT DISTINCT session_id FROM messages)
                """)
            )

            await db.commit()

            logger.success(f"✅ 已清空 {result_msg.rowcount} 条旧消息和 {result_sess.rowcount} 个空会话")

        except Exception as e:
            logger.error(f"❌ 清空旧记录失败: {e}")
            await db.rollback()
            raise


async def clear_inactive_sessions():
    """清空所有非活跃会话"""
    logger.info("开始清空非活跃会话...")

    db_service = get_database_service()
    await db_service.initialize()

    async with db_service.async_session() as db:
        try:
            # 删除非活跃会话
            result = await db.execute(
                text("DELETE FROM sessions WHERE is_connected = 0")
            )
            await db.commit()

            logger.success(f"✅ 已清空 {result.rowcount} 个非活跃会话")

        except Exception as e:
            logger.error(f"❌ 清空非活跃会话失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse
    from datetime import timedelta

    parser = argparse.ArgumentParser(description="清空对话记录")
    parser.add_argument(
        "--check",
        action="store_true",
        help="只检查，不清空"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="清空所有会话和消息"
    )
    parser.add_argument(
        "--messages-only",
        action="store_true",
        help="只清空消息，保留会话"
    )
    parser.add_argument(
        "--old",
        type=int,
        metavar="DAYS",
        help="清空指定天数之前的记录"
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="清空所有非活跃会话"
    )

    args = parser.parse_args()

    # 默认先检查
    if not any([args.all, args.messages_only, args.old, args.inactive]):
        asyncio.run(check_conversations())
    else:
        if args.all:
            asyncio.run(clear_all_conversations())
        elif args.messages_only:
            asyncio.run(clear_all_messages_only())
        elif args.old:
            asyncio.run(clear_old_messages(args.old))
        elif args.inactive:
            asyncio.run(clear_inactive_sessions())
