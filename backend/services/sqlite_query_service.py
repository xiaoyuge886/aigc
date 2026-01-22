"""
SQLite数据库查询服务 - 用于智能问数skill
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import sqlite3
from contextlib import contextmanager


class SQLiteQueryService:
    """SQLite数据库查询服务 - 用于业务数据查询"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化SQLite查询服务

        Args:
            db_path: 数据库文件路径（默认使用backend/data/sessions.db）
        """
        if db_path is None:
            # 默认使用backend/data/sessions.db
            current_dir = Path(__file__).parent.parent.parent
            db_path = str(current_dir / "data" / "sessions.db")

        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询并返回结果

        Args:
            query: SQL查询语句
            params: 查询参数（可选，用于防止SQL注入）

        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                rows = cursor.fetchall()

                # 转换为字典列表
                result = [dict(row) for row in rows]
                logger.info(f"查询执行成功，返回 {len(result)} 行数据")
                return result

        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            logger.error(f"失败的SQL: {query}")
            raise

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息

        Args:
            table_name: 表名

        Returns:
            List[Dict]: 字段信息列表
        """
        query = f"""
        SELECT
            name as column_name,
            type as data_type,
            'notnull' as is_nullable
        FROM pragma_table_info(?)
        ORDER BY cid
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (table_name,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            raise

    def get_tables(self) -> List[str]:
        """
        获取数据库所有表名

        Returns:
            List[str]: 表名列表
        """
        query = """
        SELECT name as table_name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return [row["table_name"] for row in rows]
        except Exception as e:
            logger.error(f"获取表列表失败: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """
        测试数据库连接

        Returns:
            Dict: 测试结果
        """
        try:
            tables = self.get_tables()

            # 获取每个表的记录数
            table_stats = []
            for table in tables[:10]:  # 只取前10个表
                try:
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    count = self.execute_query(count_query)[0]["count"]
                    table_stats.append({
                        "table_name": table,
                        "row_count": count
                    })
                except:
                    table_stats.append({
                        "table_name": table,
                        "row_count": "N/A"
                    })

            return {
                "status": "success",
                "db_path": self.db_path,
                "tables_count": len(tables),
                "tables": tables,
                "table_stats": table_stats
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "db_path": self.db_path
            }

    def analyze_business_data(self, table_name: str) -> Dict[str, Any]:
        """
        分析业务数据

        Args:
            table_name: 表名

        Returns:
            Dict: 分析结果
        """
        try:
            # 获取表结构
            schema = self.get_table_schema(table_name)

            # 获取总记录数
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            total = self.execute_query(count_query)[0]["total"]

            # 获取前5条样本数据
            sample_query = f"SELECT * FROM {table_name} LIMIT 5"
            sample_data = self.execute_query(sample_query)

            return {
                "table_name": table_name,
                "total_rows": total,
                "columns": schema,
                "sample_data": sample_data
            }
        except Exception as e:
            logger.error(f"分析业务数据失败: {e}")
            raise


# 全局SQLite查询服务实例
_sqlite_query_service: Optional[SQLiteQueryService] = None


def get_sqlite_query_service() -> SQLiteQueryService:
    """获取SQLite查询服务单例"""
    global _sqlite_query_service
    if _sqlite_query_service is None:
        _sqlite_query_service = SQLiteQueryService()
    return _sqlite_query_service
