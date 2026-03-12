"""
数据库迁移脚本：添加能力包系统

运行方式：
    cd backend
    python migrations/add_capability_packages.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from loguru import logger
from services.database import DatabaseService
from core.config import settings


async def migrate():
    """执行数据库迁移"""
    db_path = str(settings.work_dir.parent / "data" / "sessions.db")
    db_service = DatabaseService(db_path)

    # 初始化数据库连接
    await db_service.initialize()

    async with db_service.async_session() as session:
        # 检查表是否已存在
        check_sql = text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='capability_packages'
        """)
        result = await session.execute(check_sql)
        row = result.fetchone()
        if row:
            logger.warning("[Migration] capability_packages 表已存在，跳过创建")
            return

        logger.info("[Migration] 开始创建 capability_packages 表...")

        # 创建 capability_packages 表
        create_packages_sql = text("""
            CREATE TABLE capability_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                version VARCHAR(20) DEFAULT '1.0.0',
                author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                is_public BOOLEAN DEFAULT 0,
                is_official BOOLEAN DEFAULT 1,
                category VARCHAR(50),
                skills JSON,
                allowed_tools JSON,
                mcp_servers JSON,
                custom_prompt_extension TEXT,
                plugin_path VARCHAR(500),
                icon_url VARCHAR(500),
                tags JSON,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await session.execute(create_packages_sql)
        logger.info("[Migration] ✅ capability_packages 表创建成功")

        # 创建索引
        index_sql = text("""
            CREATE INDEX IF NOT EXISTS ix_capability_packages_name ON capability_packages(name);
            CREATE INDEX IF NOT EXISTS ix_capability_packages_author ON capability_packages(author_id);
            CREATE INDEX IF NOT EXISTS ix_capability_packages_is_public ON capability_packages(is_public);
            CREATE INDEX IF NOT EXISTS ix_capability_packages_category ON capability_packages(category);
        """)
        await session.execute(index_sql)
        logger.info("[Migration] ✅ 索引创建成功")

        # 创建 user_capability_bindings 表
        logger.info("[Migration] 开始创建 user_capability_bindings 表...")

        create_bindings_sql = text("""
            CREATE TABLE user_capability_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                package_id INTEGER NOT NULL REFERENCES capability_packages(id) ON DELETE CASCADE,
                is_enabled BOOLEAN DEFAULT 1,
                granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                granted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                usage_count INTEGER DEFAULT 1,
                last_used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, package_id)
            )
        """)
        await session.execute(create_bindings_sql)
        logger.info("[Migration] ✅ user_capability_bindings 表创建成功")

        # 创建索引
        binding_index_sql = text("""
            CREATE INDEX IF NOT EXISTS ix_user_capability_bindings_user ON user_capability_bindings(user_id);
            CREATE INDEX IF NOT EXISTS ix_user_capability_bindings_package ON user_capability_bindings(package_id);
        """)
        await session.execute(binding_index_sql)
        logger.info("[Migration] ✅ 绑定表索引创建成功")

        # 给 business_scenarios 添加 package_ids 列（向后兼容）
        try:
            alter_sql = text("""
                ALTER TABLE business_scenarios ADD COLUMN package_ids JSON DEFAULT '[]'
            """)
            await session.execute(alter_sql)
            logger.info("[Migration] ✅ business_scenarios.package_ids 列添加成功")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.warning("[Migration] business_scenarios.package_ids 列已存在，跳过")
            else:
                raise

        await session.commit()
        logger.info("[Migration] 🎉 迁移完成！")

    # 关闭数据库连接
    await db_service.close()


async def create_default_packages():
    """创建默认能力包"""
    db_path = str(settings.work_dir.parent / "data" / "sessions.db")
    db_service = DatabaseService(db_path)
    await db_service.initialize()

    async with db_service.async_session() as session:
        from sqlalchemy import select
        from models.database import CapabilityPackageDB

        # 检查是否已有能力包
        stmt = select(CapabilityPackageDB).limit(1)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            logger.info("[Migration] 已有能力包，跳过默认创建")
            return

        logger.info("[Migration] 创建默认能力包...")

        # 创建数据分析能力包
        data_analysis_pkg = CapabilityPackageDB(
            name="data-analysis-pack",
            display_name="数据分析工具包",
            description="包含数据分析、图表生成等能力",
            version="1.0.0",
            is_public=True,
            is_official=True,
            category="analysis",
            skills={"skills": ["data-analysis", "echarts_chart"]},
            allowed_tools=["Read", "Write", "Bash"],
            tags={"tags": ["data", "chart", "report"]},
        )
        session.add(data_analysis_pkg)

        # 创建开发工具能力包
        dev_pkg = CapabilityPackageDB(
            name="development-pack",
            display_name="开发工具包",
            description="包含代码开发、调试等能力",
            version="1.0.0",
            is_public=True,
            is_official=True,
            category="development",
            skills={"skills": ["code-generation", "debugging"]},
            allowed_tools=["Read", "Write", "Bash", "Edit"],
            tags={"tags": ["code", "dev", "programming"]},
        )
        session.add(dev_pkg)

        # 创建文档处理能力包
        doc_pkg = CapabilityPackageDB(
            name="document-pack",
            display_name="文档处理工具包",
            description="包含文档创建、编辑、PDF处理等能力",
            version="1.0.0",
            is_public=True,
            is_official=True,
            category="document",
            skills={"skills": ["docx", "pdf", "pptx"]},
            allowed_tools=["Read", "Write", "Bash"],
            tags={"tags": ["document", "pdf", "word", "ppt"]},
        )
        session.add(doc_pkg)

        await session.commit()
        logger.info("[Migration] ✅ 默认能力包创建成功")

    await db_service.close()


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("[Migration] 能力包系统迁移脚本")
    logger.info("=" * 60)

    try:
        await migrate()
        await create_default_packages()
        logger.info("[Migration] 🎉 全部完成！")
    except Exception as e:
        logger.error(f"[Migration] 迁移失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
