#!/usr/bin/env python3
"""
修改用户登录密码脚本

用法:
    python change_password.py <username> <new_password>

示例:
    python change_password.py admin NewPassword123
"""
import asyncio
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from models.database import UserDB
from services.database import DatabaseService
from loguru import logger


async def change_password(username: str, new_password: str) -> bool:
    """
    修改用户密码

    Args:
        username: 用户名
        new_password: 新密码

    Returns:
        bool: 是否修改成功
    """
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        async with db_service.async_session() as session:
            # 查找用户
            from sqlalchemy import select
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"用户 '{username}' 不存在")
                return False

            # 检查密码长度
            if len(new_password) < 6:
                logger.error("密码长度不能少于6位")
                return False

            # 更新密码
            user.hashed_password = UserDB.hash_password(new_password)
            user.updated_at = user.updated_at  # 触发 onupdate
            await session.commit()

            logger.success(f"✅ 用户 '{username}' 的密码已成功修改")
            return True

    except Exception as e:
        logger.error(f"修改密码时发生错误: {e}")
        return False
    finally:
        await db_service.close()


async def list_users():
    """列出所有用户"""
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        async with db_service.async_session() as session:
            from sqlalchemy import select
            stmt = select(UserDB)
            result = await session.execute(stmt)
            users = result.scalars().all()

            if not users:
                logger.info("数据库中没有用户")
                return

            logger.info("=" * 60)
            logger.info("系统用户列表:")
            logger.info("=" * 60)
            for user in users:
                status = "活跃" if user.is_active else "禁用"
                logger.info(f"  - 用户名: {user.username:20s} | 邮箱: {user.email:30s} | 状态: {status}")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"列出用户时发生错误: {e}")
    finally:
        await db_service.close()


async def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # 解析命令行参数
    if len(sys.argv) < 2:
        logger.info("用法: python change_password.py <username> [new_password]")
        logger.info("       python change_password.py --list")
        logger.info("")
        logger.info("示例:")
        logger.info("  - 修改密码: python change_password.py admin NewPassword123")
        logger.info("  - 查看用户: python change_password.py --list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--list":
        # 列出所有用户
        await list_users()
    elif len(sys.argv) < 3:
        logger.error("请提供新密码")
        logger.info("用法: python change_password.py <username> <new_password>")
        sys.exit(1)
    else:
        username = sys.argv[1]
        new_password = sys.argv[2]

        # 修改密码
        logger.info(f"正在为用户 '{username}' 修改密码...")
        success = await change_password(username, new_password)

        if success:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())