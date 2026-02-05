#!/usr/bin/env python3
"""
Add missing versions to existing skill packages
为现有技能包添加缺失的版本信息
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text
from services.database import DatabaseService


async def add_skill_package_versions():
    """为所有现有技能包添加版本信息"""
    logger.info("Adding versions to skill packages...")

    # 获取数据库服务
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        async with db_service.async_session() as session:
            # 查询所有没有版本的技能包
            result = await session.execute(text("""
                SELECT sp.id, sp.name, sp.current_version, sp.identifier
                FROM skill_packages sp
                LEFT JOIN skill_package_versions spv ON sp.id = spv.package_id
                WHERE spv.id IS NULL
                AND sp.is_active = 1
            """))

            packages_without_versions = result.fetchall()

            if not packages_without_versions:
                logger.info("✓ All packages already have versions!")
                return

            logger.info(f"Found {len(packages_without_versions)} packages without versions")

            # 为每个包添加版本
            for pkg_id, pkg_name, current_version, identifier in packages_without_versions:
                version = current_version or "1.0.0"

                # 插入版本记录
                await session.execute(text("""
                    INSERT INTO skill_package_versions (
                        package_id, version, changelog,
                        created_at
                    ) VALUES (
                        :package_id, :version, :changelog,
                        datetime('now')
                    )
                """), {
                    "package_id": pkg_id,
                    "version": version,
                    "changelog": f"Initial release of {pkg_name}"
                })

                logger.info(f"✓ Added version {version} to package: {pkg_name} (ID: {pkg_id})")

            await session.commit()
            logger.info("✓ Successfully added versions to all packages!")

            # 显示统计信息
            count_result = await session.execute(text("""
                SELECT
                    COUNT(DISTINCT sp.id) as total_packages,
                    COUNT(DISTINCT spv.package_id) as packages_with_versions
                FROM skill_packages sp
                LEFT JOIN skill_package_versions spv ON sp.id = spv.package_id
                WHERE sp.is_active = 1
            """))
            stats = count_result.fetchone()

            logger.info(f"📊 Statistics: {stats[1]}/{stats[0]} packages now have versions")

    except Exception as e:
        logger.error(f"Error adding skill package versions: {e}")
        raise
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(add_skill_package_versions())
