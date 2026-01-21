#!/usr/bin/env python3
"""验证用户配置是否生效

验证 guoyu2 用户调用 /api/v1/session/query/stream 时，配置的场景是否生效
"""
import asyncio
import sys
import os
import httpx
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import DatabaseService
from services.configuration_manager import ConfigurationManager
from services.auth import AuthService
from models.database import UserDB
from sqlalchemy import select


async def check_user_config():
    """检查用户配置"""
    db_service = DatabaseService()
    await db_service.initialize()  # 初始化数据库连接
    config_manager = ConfigurationManager(db_service)
    auth_service = AuthService(db_service)
    
    try:
        # 查找 guoyu2 用户
        async with db_service.async_session() as session:
            result = await session.execute(select(UserDB).where(UserDB.username == 'guoyu2'))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ 用户 guoyu2 不存在")
                return None
            
            print(f"✅ 找到用户: {user.username} (id={user.id})")
            
            # 获取用户配置
            user_config = await config_manager.get_user_config(user.id)
            if user_config:
                print(f"\n📋 用户配置:")
                print(f"  - default_system_prompt: {user_config.default_system_prompt[:100] if user_config.default_system_prompt else None}...")
                print(f"  - associated_scenario_id: {user_config.associated_scenario_id}")
                
                # 如果有关联场景，加载场景配置
                scenario_config = None
                if user_config.associated_scenario_id:
                    scenario_config = await config_manager.get_business_scenario(user_config.associated_scenario_id)
                    if scenario_config:
                        print(f"\n🎯 关联的场景配置:")
                        print(f"  - scenario_id: {scenario_config.scenario_id}")
                        print(f"  - name: {scenario_config.name}")
                        print(f"  - allowed_tools: {scenario_config.allowed_tools}")
                        print(f"  - custom_tools: {scenario_config.custom_tools}")
                        print(f"  - skills: {scenario_config.skills}")
                        
                        # 合并配置查看最终结果
                        merged_config, _ = config_manager.merge_agent_config(
                            request_config={},
                            session_config={},
                            user_config=user_config,
                            scenario_config=scenario_config,
                        )
                        print(f"\n🔧 合并后的配置:")
                        print(f"  - system_prompt: {merged_config.system_prompt[:100] if merged_config.system_prompt else None}...")
                        print(f"  - allowed_tools: {merged_config.allowed_tools}")
                        print(f"  - model: {merged_config.model}")
                        print(f"  - custom_tools: {merged_config.custom_tools}")
                        print(f"  - setting_sources: {merged_config.setting_sources}")
                        print(f"  - enabled_skill_ids: {merged_config.enabled_skill_ids}")
                    else:
                        print(f"\n⚠️ 场景配置不存在: {user_config.associated_scenario_id}")
                else:
                    print(f"\n⚠️ 用户未关联场景")
                
                return {
                    'user': user,
                    'user_config': user_config,
                    'scenario_config': scenario_config,
                }
            else:
                print("\n⚠️ 用户没有配置")
                return {'user': user, 'user_config': None, 'scenario_config': None}
    finally:
        await db_service.close()


async def test_api_call(user_info):
    """测试 API 调用"""
    if not user_info or not user_info.get('user'):
        print("\n❌ 无法测试：用户信息不完整")
        return
    
    user = user_info['user']
    db_service = DatabaseService()
    await db_service.initialize()  # 初始化数据库连接
    auth_service = AuthService(db_service)
    
    # 生成 token（sub 字段必须是用户 ID 的字符串形式）
    token = auth_service.create_access_token(data={"sub": str(user.id)})
    
    print(f"\n🧪 测试 API 调用:")
    print(f"  - 用户: {user.username}")
    print(f"  - Token: {token[:50]}...")
    
    # 调用接口
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "http://localhost:8000/api/v1/session/query/stream"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = {
            "prompt": "你好，请告诉我你的配置信息",
            "incremental_stream": True,
        }
        
        print(f"\n📤 发送请求:")
        print(f"  - URL: {url}")
        print(f"  - Headers: Authorization: Bearer {token[:20]}...")
        print(f"  - Body: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            async with client.stream("POST", url, headers=headers, json=data) as response:
                print(f"\n📥 响应状态: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"❌ 错误响应: {error_text.decode()}")
                    return
                
                print(f"\n✅ 流式响应开始，检查日志以确认配置是否生效...")
                print(f"   查看 backend.log 中的 [session_query_stream] 日志")
                
                # 读取前几个数据块
                chunk_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_count += 1
                        try:
                            chunk_data = json.loads(line[6:])
                            if chunk_count <= 3:
                                print(f"\n  数据块 {chunk_count}: {json.dumps(chunk_data, ensure_ascii=False)[:200]}...")
                        except:
                            pass
                        if chunk_count >= 3:
                            break
                
                print(f"\n✅ 已收到 {chunk_count} 个数据块")
                print(f"\n💡 提示: 查看 backend.log 确认以下日志:")
                print(f"   - [session_query_stream] Loading config for user_id={user.id}")
                print(f"   - [session_query_stream] Found associated_scenario_id")
                print(f"   - [session_query_stream] ✅ Loaded scenario config")
                print(f"   - [session_query_stream] ✅ Applied platform configuration")
                
        except Exception as e:
            print(f"\n❌ API 调用失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    print("=" * 70)
    print("验证用户配置是否生效")
    print("=" * 70)
    
    # 检查配置
    user_info = await check_user_config()
    
    # 测试 API 调用
    if user_info:
        await test_api_call(user_info)
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
