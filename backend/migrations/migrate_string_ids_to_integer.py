"""
数据库迁移脚本：将字符串业务ID统一改为整数ID

迁移内容：
1. business_scenarios: 移除 scenario_id 字段，使用 id 作为业务标识
2. system_prompts: 移除 prompt_id 字段，使用 id 作为业务标识
3. skills: 移除 skill_id 字段，使用 id 作为业务标识
4. 更新所有外键关联：从字符串ID改为整数ID

运行方式：
python -m backend.migrations.migrate_string_ids_to_integer
"""
import sqlite3
import json
from pathlib import Path
from loguru import logger
from typing import Dict, Optional

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


def create_id_mapping(cursor, table_name: str, string_id_column: str) -> Dict[str, int]:
    """
    创建字符串ID到整数ID的映射
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        string_id_column: 字符串ID列名
        
    Returns:
        Dict[str, int]: 字符串ID -> 整数ID 的映射
    """
    mapping = {}
    cursor.execute(f"SELECT id, {string_id_column} FROM {table_name}")
    rows = cursor.fetchall()
    for row in rows:
        int_id, str_id = row
        if str_id:
            mapping[str_id] = int_id
    logger.info(f"创建 {table_name} 的ID映射: {len(mapping)} 条记录")
    return mapping


def update_foreign_keys(
    cursor,
    table_name: str,
    column_name: str,
    id_mapping: Dict[str, int],
    allow_null: bool = True
):
    """
    更新外键字段，将字符串ID替换为整数ID
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        column_name: 外键列名
        id_mapping: 字符串ID到整数ID的映射
        allow_null: 是否允许NULL值
    """
    # 检查列是否存在
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    if column_name not in columns:
        logger.warning(f"表 {table_name} 中不存在列 {column_name}，跳过")
        return
    
    # 获取当前数据
    cursor.execute(f"SELECT id, {column_name} FROM {table_name}")
    rows = cursor.fetchall()
    
    updated_count = 0
    null_count = 0
    
    for row_id, str_id in rows:
        if str_id is None:
            if not allow_null:
                logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name} 为 NULL，但不允许NULL")
            null_count += 1
            continue
            
        # 查找对应的整数ID
        if str_id in id_mapping:
            int_id = id_mapping[str_id]
            # 更新为整数ID
            cursor.execute(
                f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?",
                (int_id, row_id)
            )
            updated_count += 1
        else:
            logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name}='{str_id}' 在映射中不存在，设置为 NULL")
            if allow_null:
                cursor.execute(
                    f"UPDATE {table_name} SET {column_name} = NULL WHERE id = ?",
                    (row_id,)
                )
                null_count += 1
    
    logger.info(f"更新表 {table_name}.{column_name}: {updated_count} 条记录更新，{null_count} 条设置为NULL")


def update_json_array_field(
    cursor,
    table_name: str,
    column_name: str,
    id_mapping: Dict[str, int]
):
    """
    更新JSON数组字段中的字符串ID为整数ID
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        column_name: JSON列名
        id_mapping: 字符串ID到整数ID的映射
    """
    # 检查列是否存在
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    if column_name not in columns:
        logger.warning(f"表 {table_name} 中不存在列 {column_name}，跳过")
        return
    
    # 获取当前数据
    cursor.execute(f"SELECT id, {column_name} FROM {table_name}")
    rows = cursor.fetchall()
    
    updated_count = 0
    
    for row_id, json_str in rows:
        if json_str is None:
            continue
        
        try:
            # 解析JSON数组
            str_ids = json.loads(json_str)
            if not isinstance(str_ids, list):
                logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name} 不是数组格式，跳过")
                continue
            
            # 转换字符串ID为整数ID
            int_ids = []
            for str_id in str_ids:
                if isinstance(str_id, str):
                    if str_id in id_mapping:
                        int_ids.append(id_mapping[str_id])
                    else:
                        logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name} 中包含未知ID: {str_id}")
                        # 如果找不到映射，保留原值（可能是其他类型的ID）
                        int_ids.append(str_id)
                elif isinstance(str_id, int):
                    # 已经是整数，直接保留
                    int_ids.append(str_id)
                else:
                    logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name} 中包含非字符串/整数ID: {type(str_id)}")
                    int_ids.append(str_id)
            
            # 更新JSON字段
            new_json_str = json.dumps(int_ids)
            cursor.execute(
                f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?",
                (new_json_str, row_id)
            )
            updated_count += 1
            
        except json.JSONDecodeError as e:
            logger.warning(f"表 {table_name} 记录 {row_id} 的 {column_name} JSON解析失败: {e}")
    
    logger.info(f"更新表 {table_name}.{column_name}: {updated_count} 条记录更新")


def migrate():
    """执行迁移"""
    if not DB_PATH.exists():
        logger.warning(f"数据库文件不存在: {DB_PATH}")
        return
    
    logger.info(f"开始迁移: {DB_PATH}")
    
    # 使用同步 SQLite 连接
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 1. 创建ID映射
        logger.info("=" * 80)
        logger.info("步骤1: 创建ID映射")
        logger.info("=" * 80)
        
        scenario_mapping = {}
        prompt_mapping = {}
        skill_mapping = {}
        
        # 检查表是否存在并创建映射
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if "business_scenarios" in tables:
            scenario_mapping = create_id_mapping(cursor, "business_scenarios", "scenario_id")
        else:
            logger.warning("表 business_scenarios 不存在，跳过")
        
        if "system_prompts" in tables:
            prompt_mapping = create_id_mapping(cursor, "system_prompts", "prompt_id")
        else:
            logger.warning("表 system_prompts 不存在，跳过")
        
        if "skills" in tables:
            skill_mapping = create_id_mapping(cursor, "skills", "skill_id")
        else:
            logger.warning("表 skills 不存在，跳过")
        
        # 2. 更新外键关联
        logger.info("=" * 80)
        logger.info("步骤2: 更新外键关联")
        logger.info("=" * 80)
        
        # 更新 user_configs.associated_scenario_id
        if "user_configs" in tables:
            update_foreign_keys(cursor, "user_configs", "associated_scenario_id", scenario_mapping, allow_null=True)
        
        # 更新 conversation_turn_configs.scenario_id
        if "conversation_turn_configs" in tables:
            update_foreign_keys(cursor, "conversation_turn_configs", "scenario_id", scenario_mapping, allow_null=True)
        
        # 3. 更新JSON数组字段
        logger.info("=" * 80)
        logger.info("步骤3: 更新JSON数组字段")
        logger.info("=" * 80)
        
        # 更新 user_scenario_configs.scenario_ids
        if "user_scenario_configs" in tables:
            update_json_array_field(cursor, "user_scenario_configs", "scenario_ids", scenario_mapping)
        
        # 更新 session_scenario_configs.scenario_ids
        if "session_scenario_configs" in tables:
            update_json_array_field(cursor, "session_scenario_configs", "scenario_ids", scenario_mapping)
        
        # 4. 删除字符串ID列（可选，建议先备份）
        logger.info("=" * 80)
        logger.info("步骤4: 删除字符串ID列")
        logger.info("=" * 80)
        logger.warning("⚠️  注意：删除列操作在SQLite中比较复杂，建议手动执行或使用备份恢复")
        logger.info("建议的SQL命令（需要手动执行或使用备份恢复策略）：")
        logger.info("  ALTER TABLE business_scenarios DROP COLUMN scenario_id;")
        logger.info("  ALTER TABLE system_prompts DROP COLUMN prompt_id;")
        logger.info("  ALTER TABLE skills DROP COLUMN skill_id;")
        
        # 注意：SQLite不支持直接DROP COLUMN，需要重建表
        # 这里我们只更新数据，不删除列（列会在下次表重建时自动移除）
        
        conn.commit()
        logger.info("=" * 80)
        logger.info("✅ 迁移完成")
        logger.info("=" * 80)
        logger.info(f"场景ID映射: {len(scenario_mapping)} 条")
        logger.info(f"提示词ID映射: {len(prompt_mapping)} 条")
        logger.info(f"技能ID映射: {len(skill_mapping)} 条")
        logger.info("")
        logger.info("⚠️  重要提示：")
        logger.info("1. 请备份数据库后再执行此迁移")
        logger.info("2. 删除字符串ID列需要重建表，建议在维护窗口期执行")
        logger.info("3. 迁移后请测试所有功能，确保数据一致性")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()  # migrate 函数是同步的，不需要 asyncio.run
