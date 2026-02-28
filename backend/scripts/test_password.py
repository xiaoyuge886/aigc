#!/usr/bin/env python3
"""
测试密码哈希和验证逻辑
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


async def test_password(username: str, password: str):
    """测试密码验证"""
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        async with db_service.async_session() as session:
            from sqlalchemy import select
            stmt = select(UserDB).where(UserDB.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"用户 '{username}' 不存在")
                return False

            logger.info(f"用户 ID: {user.id}")
            logger.info(f"用户名: {user.username}")
            logger.info(f"邮箱: {user.email}")
            logger.info(f"是否活跃: {user.is_active}")
            logger.info(f"哈希后的密码: {user.hashed_password[:50]}...")
            logger.info("")

            # 测试密码验证
            logger.info("测试密码验证...")
            is_valid = user.verify_password(password)
            logger.info(f"密码验证结果: {'✅ 成功' if is_valid else '❌ 失败'}")

            # 测试重新哈希并比较
            logger.info("")
            logger.info("测试重新哈希...")
            new_hash = UserDB.hash_password(password)
            logger.info(f"新哈希: {new_hash[:50]}...")
            logger.info(f"哈希相同: {user.hashed_password == new_hash}")

            # 测试新哈希的验证
            logger.info("")
            logger.info("验证新哈希...")
            # 创建临时用户对象来测试新哈希
            temp_user = UserDB(username="test", email="test@test.com", hashed_password=new_hash)
            is_valid_new = temp_user.verify_password(password)
            logger.info(f"新哈希验证结果: {'✅ 成功' if is_valid_new else '❌ 失败'}")

            return is_valid

    except Exception as e:
        logger.error(f"测试时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
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

    if len(sys.argv) < 3:
        logger.info("用法: python test_password.py <username> <password>")
        logger.info("示例: python test_password.py admin 123456")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    logger.info(f"正在测试用户 '{username}' 的密码 '{password}'")
    logger.info("=" * 60)

    success = await test_password(username, password)

    logger.info("=" * 60)
    if success:
        logger.success("密码验证成功！")
    else:
        logger.error("密码验证失败！")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())