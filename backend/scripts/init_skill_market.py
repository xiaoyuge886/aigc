#!/usr/bin/env python3
"""
Initialize Skill Market Database Tables
初始化技能市场数据库表
"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from loguru import logger
from sqlalchemy import text
from services.database import DatabaseService


async def init_skill_market_tables():
    """初始化技能市场数据库表"""
    logger.info("Initializing Skill Market database tables...")

    # 获取数据库服务
    db_service = DatabaseService()
    await db_service.initialize()

    try:
        # 获取数据库连接
        async with db_service.async_session() as session:
            # 创建表的 SQL 语句
            create_statements = [
                # 1. 技能包表
                """
                CREATE TABLE IF NOT EXISTS skill_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    identifier VARCHAR(200) UNIQUE NOT NULL,
                    display_name VARCHAR(200),
                    description TEXT,
                    long_description TEXT,
                    author_id INTEGER,
                    author_name VARCHAR(100),
                    author_email VARCHAR(255),
                    category VARCHAR(50),
                    tags JSON,
                    current_version VARCHAR(20),
                    repository_url VARCHAR(500),
                    homepage_url VARCHAR(500),
                    documentation_url VARCHAR(500),
                    download_count INTEGER DEFAULT 0,
                    install_count INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    rating_average REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    is_featured BOOLEAN DEFAULT 0,
                    is_official BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    visibility VARCHAR(20) DEFAULT 'public',
                    source_type VARCHAR(50) DEFAULT 'upload',
                    source_location VARCHAR(500),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    published_at DATETIME,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
                );
                """,

                # 2. 技能包版本表
                """
                CREATE TABLE IF NOT EXISTS skill_package_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    changelog TEXT,
                    download_url VARCHAR(500),
                    file_size INTEGER,
                    checksum VARCHAR(64),
                    min_agent_version VARCHAR(20),
                    max_agent_version VARCHAR(20),
                    dependencies JSON,
                    install_command TEXT,
                    uninstall_command TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
                    UNIQUE(package_id, version)
                );
                """,

                # 3. 技能项表
                """
                CREATE TABLE IF NOT EXISTS skill_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER,
                    package_version_id INTEGER,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200),
                    description TEXT,
                    category VARCHAR(50),
                    skill_content TEXT NOT NULL,
                    skill_type VARCHAR(20) DEFAULT 'markdown',
                    trigger_keywords JSON,
                    use_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    is_builtin BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
                    FOREIGN KEY (package_version_id) REFERENCES skill_package_versions(id) ON DELETE SET NULL
                );
                """,

                # 4. 用户已安装技能表
                """
                CREATE TABLE IF NOT EXISTS user_installed_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    package_id INTEGER NOT NULL,
                    version_id INTEGER NOT NULL,
                    installed_version VARCHAR(20) NOT NULL,
                    install_path VARCHAR(500),
                    is_enabled BOOLEAN DEFAULT 1,
                    custom_config JSON,
                    has_update BOOLEAN DEFAULT 0,
                    last_check_at DATETIME,
                    installed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
                    FOREIGN KEY (version_id) REFERENCES skill_package_versions(id) ON DELETE CASCADE,
                    UNIQUE(user_id, package_id)
                );
                """,

                # 5. 技能评价表
                """
                CREATE TABLE IF NOT EXISTS skill_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    title VARCHAR(200),
                    content TEXT,
                    helpful_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package_id) REFERENCES skill_packages(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(package_id, user_id)
                );
                """,

                # 6. 技能使用日志表
                """
                CREATE TABLE IF NOT EXISTS skill_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id VARCHAR(36),
                    skill_name VARCHAR(100) NOT NULL,
                    skill_id INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    user_query TEXT,
                    agent_response TEXT,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (skill_id) REFERENCES skill_items(id) ON DELETE SET NULL
                );
                """,
            ]

            # 创建索引
            index_statements = [
                "CREATE INDEX IF NOT EXISTS idx_skill_packages_name ON skill_packages(name);",
                "CREATE INDEX IF NOT EXISTS idx_skill_packages_category ON skill_packages(category);",
                "CREATE INDEX IF NOT EXISTS idx_skill_packages_author ON skill_packages(author_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_packages_active_featured ON skill_packages(is_active, is_featured);",
                "CREATE INDEX IF NOT EXISTS idx_skill_versions_package ON skill_package_versions(package_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_items_name ON skill_items(name);",
                "CREATE INDEX IF NOT EXISTS idx_skill_items_package ON skill_items(package_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_installed_skills_user ON user_installed_skills(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_installed_skills_package ON user_installed_skills(package_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_reviews_package ON skill_reviews(package_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_reviews_user ON skill_reviews(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_usage_logs_user ON skill_usage_logs(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_skill_usage_logs_skill ON skill_usage_logs(skill_name);",
                "CREATE INDEX IF NOT EXISTS idx_skill_usage_logs_time ON skill_usage_logs(used_at);",
            ]

            # 执行创建表语句
            for stmt in create_statements:
                try:
                    await session.execute(text(stmt))
                    logger.info(f"✓ Created table: {stmt.split()[5] if 'skill_packages' in stmt else stmt.split()[5] if 'skill_package_versions' in stmt else stmt.split()[5] if 'skill_items' in stmt else stmt.split()[5] if 'user_installed_skills' in stmt else stmt.split()[5] if 'skill_reviews' in stmt else stmt.split()[5]}")
                except Exception as e:
                    logger.warning(f"Table might already exist: {e}")

            # 执行创建索引语句
            for stmt in index_statements:
                try:
                    await session.execute(text(stmt))
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

            await session.commit()

            logger.info("✓ Skill Market database tables initialized successfully!")

            # 插入示例数据
            await insert_sample_data(session)

    except Exception as e:
        logger.error(f"Error initializing Skill Market tables: {e}")
        raise
    finally:
        await db_service.close()


async def insert_sample_data(session):
    """插入示例数据"""
    logger.info("Inserting sample Skill Market data...")

    sample_data = [
        # 示例技能包
        {
            'name': 'marketing-skills',
            'identifier': 'examples/marketing-skills',
            'display_name': 'Marketing Skills',
            'description': 'Marketing skills for AI agents - CRO, copywriting, SEO, and analytics',
            'long_description': 'A comprehensive collection of marketing-focused skills for AI agents. Includes skills for conversion rate optimization, copywriting, SEO auditing, analytics tracking, and more.',
            'author_name': 'Corey Haines',
            'category': 'marketing',
            'tags': ['marketing', 'seo', 'cro', 'analytics', 'copywriting'],
            'current_version': '1.2.0',
            'repository_url': 'https://github.com/coreyhaines31/marketingskills',
            'is_featured': True,
            'visibility': 'public',
            'download_count': 1250,
            'install_count': 850,
            'rating_average': 4.8,
            'rating_count': 42,
        },
        {
            'name': 'data-analysis-skills',
            'identifier': 'examples/data-analysis-skills',
            'display_name': 'Data Analysis Skills',
            'description': 'Advanced data analysis and visualization skills',
            'long_description': 'Professional data analysis skills including statistical analysis, data visualization, ETL operations, and business intelligence reporting.',
            'author_name': 'Data Team',
            'category': 'data-analysis',
            'tags': ['data', 'analysis', 'visualization', 'statistics', 'python'],
            'current_version': '2.1.0',
            'is_featured': True,
            'visibility': 'public',
            'download_count': 2100,
            'install_count': 1500,
            'rating_average': 4.9,
            'rating_count': 128,
        },
        {
            'name': 'productivity-boost',
            'identifier': 'examples/productivity-boost',
            'display_name': 'Productivity Booster',
            'description': 'Boost your productivity with automation and optimization skills',
            'long_description': 'Automation and productivity enhancement skills for workflow optimization, task automation, and time management.',
            'author_name': 'Productivity Guru',
            'category': 'productivity',
            'tags': ['productivity', 'automation', 'workflow', 'optimization'],
            'current_version': '1.0.0',
            'is_featured': False,
            'visibility': 'public',
            'download_count': 580,
            'install_count': 320,
            'rating_average': 4.5,
            'rating_count': 25,
        }
    ]

    for pkg_data in sample_data:
        try:
            # 检查是否已存在
            result = await session.execute(
                text("SELECT id FROM skill_packages WHERE identifier = :identifier"),
                {"identifier": pkg_data['identifier']}
            )
            if result.scalar_one_or_none():
                logger.info(f"Sample package {pkg_data['name']} already exists, skipping...")
                continue

            # 插入技能包
            await session.execute(
                text("""
                    INSERT INTO skill_packages (
                        name, identifier, display_name, description, long_description,
                        author_name, category, tags, current_version, repository_url,
                        is_featured, visibility, download_count, install_count,
                        rating_average, rating_count
                    ) VALUES (
                        :name, :identifier, :display_name, :description, :long_description,
                        :author_name, :category, :tags, :current_version, :repository_url,
                        :is_featured, :visibility, :download_count, :install_count,
                        :rating_average, :rating_count
                    )
                """),
                {
                    **pkg_data,
                    'tags': json.dumps(pkg_data['tags']) if isinstance(pkg_data.get('tags'), list) else pkg_data.get('tags'),
                    'repository_url': pkg_data.get('repository_url')  # 可以为 None
                }
            )

            logger.info(f"✓ Inserted sample package: {pkg_data['name']}")

        except Exception as e:
            logger.warning(f"Error inserting sample package {pkg_data.get('name')}: {e}")

    await session.commit()
    logger.info("✓ Sample data inserted successfully!")


if __name__ == "__main__":
    asyncio.run(init_skill_market_tables())
