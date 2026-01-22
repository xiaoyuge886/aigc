"""
数据库迁移脚本：初始化默认场景到 business_scenarios 表

运行方式：
python -m backend.migrations.init_default_scenario
"""
import asyncio
import sqlite3
import json
from pathlib import Path
from loguru import logger

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


async def migrate():
    """初始化默认场景到数据库"""
    if not DB_PATH.exists():
        logger.warning(f"数据库文件不存在: {DB_PATH}")
        return

    logger.info(f"开始初始化默认场景: {DB_PATH}")

    # 使用同步 SQLite 连接（因为 sqlite3 不支持异步）
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='business_scenarios'")
        if not cursor.fetchone():
            logger.warning("表 business_scenarios 不存在，跳过初始化")
            return

        # 检查默认场景是否已存在
        cursor.execute("SELECT id FROM business_scenarios WHERE scenario_id = 'default'")
        existing = cursor.fetchone()
        
        if existing:
            logger.info("默认场景已存在，跳过初始化")
            return

        # 默认场景配置
        default_scenario = {
            "scenario_id": "default",
            "name": "通用场景",
            "description": "不限制能力的通用场景，让模型自主规划",
            "category": None,
            "meta": None,
            "system_prompt": "",  # 空，主要依赖系统默认prompt
            "allowed_tools": None,  # None表示不限制
            "recommended_model": None,
            "custom_tools": None,
            "skills": None,
            "workflow": None,
            "permission_mode": None,
            "max_turns": None,
            "work_dir": None,
            "is_public": True,  # 默认场景应该是公开的，所有用户可用
            "is_default": True,  # 标识为系统默认场景
            "created_by": None,  # 系统创建
        }

        # 插入默认场景
        logger.info("插入默认场景到数据库...")
        cursor.execute("""
            INSERT INTO business_scenarios (
                scenario_id, name, description, category, meta,
                system_prompt, allowed_tools, recommended_model,
                custom_tools, skills, workflow,
                permission_mode, max_turns, work_dir,
                is_public, is_default, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            default_scenario["scenario_id"],
            default_scenario["name"],
            default_scenario["description"],
            default_scenario["category"],
            json.dumps(default_scenario["meta"]) if default_scenario["meta"] else None,
            default_scenario["system_prompt"],
            json.dumps(default_scenario["allowed_tools"]) if default_scenario["allowed_tools"] else None,
            default_scenario["recommended_model"],
            json.dumps(default_scenario["custom_tools"]) if default_scenario["custom_tools"] else None,
            json.dumps(default_scenario["skills"]) if default_scenario["skills"] else None,
            json.dumps(default_scenario["workflow"]) if default_scenario["workflow"] else None,
            default_scenario["permission_mode"],
            default_scenario["max_turns"],
            default_scenario["work_dir"],
            default_scenario["is_public"],
            default_scenario["is_default"],
            default_scenario["created_by"],
        ))

        conn.commit()
        logger.info("✅ 默认场景初始化成功")

    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
