"""
SQLite查询工具 - 提供给skill使用
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from services.sqlite_query_service import get_sqlite_query_service


def sqlite_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    执行SQLite查询

    这是一个BMC工具函数，可以被skill直接调用。

    Args:
        query: SQL查询语句
        params: 查询参数（可选）

    Returns:
        List[Dict]: 查询结果列表

    Example:
        >>> result = sqlite_query("SELECT * FROM users LIMIT 10")
        >>> result = sqlite_query("SELECT * FROM users WHERE id = ?", (1,))
    """
    try:
        service = get_sqlite_query_service()
        result = service.execute_query(query, params)
        logger.info(f"sqlite_query执行成功，返回 {len(result)} 行")
        return result
    except Exception as e:
        logger.error(f"sqlite_query执行失败: {e}")
        raise


def sqlite_get_tables() -> List[str]:
    """
    获取所有表名

    Returns:
        List[str]: 表名列表

    Example:
        >>> tables = sqlite_get_tables()
        >>> print(tables)
    """
    try:
        service = get_sqlite_query_service()
        tables = service.get_tables()
        logger.info(f"获取到 {len(tables)} 个表")
        return tables
    except Exception as e:
        logger.error(f"获取表名失败: {e}")
        raise


def sqlite_get_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    获取表结构

    Args:
        table_name: 表名

    Returns:
        List[Dict]: 字段信息列表

    Example:
        >>> schema = sqlite_get_schema("users")
        >>> for col in schema:
        >>>     print(f"{col['column_name']}: {col['data_type']}")
    """
    try:
        service = get_sqlite_query_service()
        schema = service.get_table_schema(table_name)
        logger.info(f"获取表 {table_name} 的结构，共 {len(schema)} 个字段")
        return schema
    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
        raise


def sqlite_analyze(table_name: str) -> Dict[str, Any]:
    """
    分析表数据

    Args:
        table_name: 表名

    Returns:
        Dict: 分析结果（包括总行数、字段信息、样本数据）

    Example:
        >>> analysis = sqlite_analyze("users")
        >>> print(f"总行数: {analysis['total_rows']}")
        >>> print(f"字段: {analysis['columns']}")
    """
    try:
        service = get_sqlite_query_service()
        analysis = service.analyze_business_data(table_name)
        logger.info(f"分析表 {table_name} 完成")
        return analysis
    except Exception as e:
        logger.error(f"分析表数据失败: {e}")
        raise
