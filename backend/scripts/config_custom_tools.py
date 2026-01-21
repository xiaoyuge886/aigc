#!/usr/bin/env python3
"""
配置 custom_tools (MCP服务器) 到场景或用户配置

用法:
1. 为特定场景配置 custom_tools:
   python scripts/config_custom_tools.py --scenario-id 1 --enable

2. 为特定用户配置 custom_tools:
   python scripts/config_custom_tools.py --user-id 1 --enable

3. 查看当前配置:
   python scripts/config_custom_tools.py --scenario-id 1 --view
"""
import sys
import asyncio
from pathlib import Path

# 添加backend到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import get_database_service
from models.database import BusinessScenarioDB, UserConfigDB
from sqlalchemy import select, update
from tools.custom_tools import get_custom_tools_server


async def view_scenario_config(scenario_id: int):
    """查看场景配置"""
    db = get_database_service()
    await db.initialize()

    try:
        async with db.async_session() as session:
            stmt = select(BusinessScenarioDB).where(BusinessScenarioDB.id == scenario_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 场景配置不存在: scenario_id={scenario_id}")
                return

            print(f"\n📋 场景配置 (ID={scenario_id}):")
            print(f"  场景名称: {config.name}")
            print(f"  custom_tools: {config.custom_tools}")
            print(f"  skills: {config.skills}")
    finally:
        await db.close()


async def view_user_config(user_id: int):
    """查看用户配置"""
    db = get_database_service()
    await db.initialize()

    try:
        async with db.async_session() as session:
            stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 用户配置不存在: user_id={user_id}")
                return

            print(f"\n📋 用户配置 (user_id={user_id}):")
            print(f"  custom_tools: {config.custom_tools}")
            print(f"  custom_skills: {config.custom_skills}")
    finally:
        await db.close()


async def enable_custom_tools_for_scenario(scenario_id: int):
    """为场景启用 custom_tools"""
    db = get_database_service()
    await db.initialize()

    try:
        # 获取 MCP 服务器配置
        custom_tools_server = get_custom_tools_server()

        async with db.async_session() as session:
            # 检查场景配置是否存在
            stmt = select(BusinessScenarioDB).where(BusinessScenarioDB.id == scenario_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 场景配置不存在: scenario_id={scenario_id}")
                return

            # 更新 custom_tools
            config.custom_tools = {
                "custom_tools": custom_tools_server
            }

            await session.commit()

            print(f"✅ 已为场景 '{config.name}' (ID={scenario_id}) 启用 custom_tools")
            print(f"   MCP 服务器: custom_tools")
            print(f"   可用工具: sqlite_query, sqlite_get_tables, sqlite_get_schema, sqlite_test_connection")
    finally:
        await db.close()


async def enable_custom_tools_for_user(user_id: int):
    """为用户启用 custom_tools"""
    db = get_database_service()
    await db.initialize()

    try:
        # 获取 MCP 服务器配置
        custom_tools_server = get_custom_tools_server()

        async with db.async_session() as session:
            # 检查用户配置是否存在
            stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 用户配置不存在: user_id={user_id}")
                return

            # 更新 custom_tools
            config.custom_tools = {
                "custom_tools": custom_tools_server
            }

            await session.commit()

            print(f"✅ 已为用户 (user_id={user_id}) 启用 custom_tools")
            print(f"   MCP 服务器: custom_tools")
            print(f"   可用工具: sqlite_query, sqlite_get_tables, sqlite_get_schema, sqlite_test_connection")
    finally:
        await db.close()


async def disable_custom_tools_for_scenario(scenario_id: int):
    """禁用场景的 custom_tools"""
    db = get_database_service()
    await db.initialize()

    try:
        async with db.async_session() as session:
            stmt = select(BusinessScenarioDB).where(BusinessScenarioDB.id == scenario_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 场景配置不存在: scenario_id={scenario_id}")
                return

            config.custom_tools = None
            await session.commit()

            print(f"✅ 已禁用场景 '{config.name}' (ID={scenario_id}) 的 custom_tools")
    finally:
        await db.close()


async def disable_custom_tools_for_user(user_id: int):
    """禁用用户的 custom_tools"""
    db = get_database_service()
    await db.initialize()

    try:
        async with db.async_session() as session:
            stmt = select(UserConfigDB).where(UserConfigDB.user_id == user_id)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                print(f"❌ 用户配置不存在: user_id={user_id}")
                return

            config.custom_tools = None
            await session.commit()

            print(f"✅ 已禁用用户 (user_id={user_id}) 的 custom_tools")
    finally:
        await db.close()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='配置 custom_tools (MCP服务器)')
    group = parser.add_mutually_exclusive_group(required=True)

    # 场景配置
    group.add_argument('--scenario-id', type=int, help='场景ID')
    # 用户配置
    group.add_argument('--user-id', type=int, help='用户ID')

    # 操作
    parser.add_argument('--enable', action='store_true', help='启用 custom_tools')
    parser.add_argument('--disable', action='store_true', help='禁用 custom_tools')
    parser.add_argument('--view', action='store_true', help='查看当前配置')

    args = parser.parse_args()

    # 默认操作是查看
    if not any([args.enable, args.disable, args.view]):
        args.view = True

    if args.scenario_id:
        if args.enable:
            await enable_custom_tools_for_scenario(args.scenario_id)
        elif args.disable:
            await disable_custom_tools_for_scenario(args.scenario_id)
        else:
            await view_scenario_config(args.scenario_id)
    elif args.user_id:
        if args.enable:
            await enable_custom_tools_for_user(args.user_id)
        elif args.disable:
            await disable_custom_tools_for_user(args.user_id)
        else:
            await view_user_config(args.user_id)


if __name__ == '__main__':
    asyncio.run(main())
