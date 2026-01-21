"""
删除 skills 表的 skill_id 列

SQLite 不支持直接 DROP COLUMN，需要重建表
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"


def drop_skill_id_column():
    """删除 skills 表的 skill_id 列"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(skills)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "skill_id" not in columns:
            print("✅ skills 表中不存在 skill_id 列，无需删除")
            return
        
        print("开始删除 skills 表的 skill_id 列...")
        
        # 1. 创建新表（不包含 skill_id）
        cursor.execute("""
            CREATE TABLE skills_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                skill_content TEXT NOT NULL,
                skill_config JSON,
                usage_count INTEGER NOT NULL DEFAULT 0,
                is_default BOOLEAN NOT NULL DEFAULT 0,
                created_by INTEGER,
                is_public BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # 2. 复制数据（排除 skill_id 列）
        cursor.execute("""
            INSERT INTO skills_new (
                id, name, description, category, skill_content, skill_config,
                usage_count, is_default, created_by, is_public, created_at, updated_at
            )
            SELECT 
                id, name, description, category, skill_content, skill_config,
                usage_count, is_default, created_by, is_public, created_at, updated_at
            FROM skills
        """)
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE skills")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE skills_new RENAME TO skills")
        
        # 5. 重建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_skills_name ON skills(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_skills_category ON skills(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_skills_is_default ON skills(is_default)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_skills_created_by ON skills(created_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_skills_is_public ON skills(is_public)")
        
        conn.commit()
        print("✅ 成功删除 skills 表的 skill_id 列")
        
    except Exception as e:
        print(f"❌ 删除 skill_id 列失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    drop_skill_id_column()
