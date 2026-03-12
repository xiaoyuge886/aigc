"""
插件导入迁移脚本

从 /plugins/claude-plugins-official-main/.claude-plugin/marketplace.json 导入插件到数据库

使用方法：
    cd backend
    python -m migrations.import_plugins
    python -m migrations.import_plugins --list  # 列出已导入的插件
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from loguru import logger

from models.database import CapabilityPackageDB
from services.database import DatabaseService
from core.config import settings


# 插件目录路径
PLUGINS_BASE_DIR = Path(__file__).parent.parent.parent / "plugins" / "claude-plugins-official-main"
MARKETPLACE_FILE = PLUGINS_BASE_DIR / ".claude-plugin" / "marketplace.json"


async def import_plugins():
    """导入插件到数据库"""
    # 读取 marketplace.json
    if not MARKETPLACE_FILE.exists():
        logger.error(f"Marketplace file not found: {MARKETPLACE_FILE}")
        return (0, 0, 0)

    with open(MARKETPLACE_FILE, 'r', encoding='utf-8') as f:
        marketplace = json.load(f)

    plugins = marketplace.get('plugins', [])
    logger.info(f"Found {len(plugins)} plugins in marketplace.json")

    # 初始化数据库
    db_path = str(settings.work_dir.parent / "data" / "sessions.db")
    db_service = DatabaseService(db_path)
    await db_service.initialize()

    imported_count = 0
    updated_count = 0
    skipped_count = 0

    async with db_service.async_session() as session:
        for plugin_data in plugins:
            plugin_name = plugin_data.get('name')
            if not plugin_name:
                logger.warning(f"Plugin missing name, skipping")
                skipped_count += 1
                continue

            # 检查是否已存在
            stmt = select(CapabilityPackageDB).where(CapabilityPackageDB.name == plugin_name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            # 构建插件路径
            source = plugin_data.get('source', f"./plugins/{plugin_name}")
            if isinstance(source, dict):
                plugin_path = source.get('url', '')
            else:
                plugin_path = str(PLUGINS_BASE_DIR / source.lstrip('./'))

            category = plugin_data.get('category', 'general')

            mcp_servers = None
            if 'lspServers' in plugin_data:
                mcp_servers = {"lspServers": plugin_data['lspServers']}

            tags = plugin_data.get('tags', [])
            homepage = plugin_data.get('homepage', '')

            if existing:
                existing.display_name = plugin_name.replace('-', ' ').replace('_', ' ').title()
                existing.description = plugin_data.get('description', existing.description)
                existing.version = plugin_data.get('version', '1.0.0')
                existing.category = category
                existing.plugin_path = plugin_path
                existing.is_public = True
                existing.is_official = True
                if mcp_servers:
                    existing.mcp_servers = mcp_servers
                if tags:
                    existing.tags = {"tags": tags}
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated plugin: {plugin_name}")
                updated_count += 1
            else:
                new_plugin = CapabilityPackageDB(
                    name=plugin_name,
                    display_name=plugin_name.replace('-', ' ').replace('_', ' ').title(),
                    description=plugin_data.get('description', ''),
                    version=plugin_data.get('version', '1.0.0'),
                    category=category,
                    is_public=True,
                    is_official=True,
                    author_id=None,
                    plugin_path=plugin_path,
                    mcp_servers=mcp_servers,
                    tags={"tags": tags} if tags else None,
                    icon_url=homepage,
                )
                session.add(new_plugin)
                logger.info(f"Created plugin: {plugin_name}")
                imported_count += 1

        await session.commit()

    await db_service.close()

    logger.info(f"Plugin Import Summary: Total={len(plugins)}, Imported={imported_count}, Updated={updated_count}, Skipped={skipped_count}")
    return imported_count, updated_count, skipped_count


async def list_imported_plugins():
    """列出已导入的插件"""
    db_path = str(settings.work_dir.parent / "data" / "sessions.db")
    db_service = DatabaseService(db_path)
    await db_service.initialize()

    async with db_service.async_session() as session:
        stmt = select(CapabilityPackageDB).order_by(CapabilityPackageDB.category, CapabilityPackageDB.name)
        result = await session.execute(stmt)
        plugins = list(result.scalars().all())

        print(f"\nImported plugins ({len(plugins)}):")
        print(f"{'Name':<30} {'Category':<15} {'Version':<10} {'Official':<8}")
        print("-" * 70)

        for plugin in plugins:
            official = "Y" if plugin.is_official else "N"
            print(f"{plugin.name:<30} {plugin.category or 'N/A':<15} {plugin.version or 'N/A':<10} {official:<8}")

        return plugins

    await db_service.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plugin import tool")
    parser.add_argument('--list', action='store_true', help='List imported plugins')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import plugins')
    args = parser.parse_args()

    if args.list:
        asyncio.run(list_imported_plugins())
    elif args.do_import:
        asyncio.run(import_plugins())
    else:
        asyncio.run(import_plugins())
