"""
Migration: 添加系统默认配置表
创建时间: 2026-01-04
描述: 添加 system_default_config 表，用于存储系统级别的默认配置
"""
import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from services.database import DatabaseService


async def upgrade():
    """执行迁移"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            # 创建 system_default_config 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS system_default_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_default_config_key 
                ON system_default_config(config_key)
            """))
            
            await session.commit()
            print("✅ 成功创建 system_default_config 表")
            
            # 插入默认配置
            await session.execute(text("""
                INSERT OR IGNORE INTO system_default_config (config_key, config_value, description)
                VALUES 
                ('default_scenario_id', 'default', '默认场景ID'),
                ('default_system_prompt_placeholder', '你是一个强大的AI助手，具备自主规划和执行任务的能力。\\n\\n## 核心能力\\n- 任务理解：仔细理解用户需求\\n- 自主规划：根据任务复杂度决定是否需要分解步骤\\n- 工具使用：根据需要选择合适的工具\\n- 自我检查：持续验证结果，发现错误及时调整\\n\\n## 可用场景能力\\n你可以根据用户需求自主选择和组合使用以下场景能力，或直接使用通用能力：\\n\\n{available_scenarios_list}\\n\\n## 使用原则\\n- 根据用户需求自主判断需要哪些场景能力\\n- 可以组合多个场景能力\\n- 如果用户需求不匹配任何场景，使用通用能力即可\\n- 灵活应对，不限制自己的能力边界\\n\\n使用ReAct范式（推理-行动-观察-反思）循环执行任务，确保准确完成用户目标。', '默认系统提示模板（包含场景列表占位符）')
            """))
            
            await session.commit()
            print("✅ 成功插入默认配置")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 迁移失败: {e}")
            raise
    await db_service.close()


async def downgrade():
    """回滚迁移"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            await session.execute(text("DROP TABLE IF EXISTS system_default_config"))
            await session.commit()
            print("✅ 成功删除 system_default_config 表")
        except Exception as e:
            await session.rollback()
            print(f"❌ 回滚失败: {e}")
            raise
    await db_service.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
