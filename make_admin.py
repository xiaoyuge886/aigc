#!/usr/bin/env python3
"""
将指定用户改为管理员的脚本
用法: python make_admin.py <username>
"""

import sys
import sqlite3
from pathlib import Path


def make_user_admin(username: str, db_path: str = "/root/aigc/data/sessions.db"):
    """将指定用户改为管理员"""

    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询管理员角色ID
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()

        if not admin_role:
            print(f"❌ 未找到管理员角色")
            return False

        admin_role_id = admin_role[0]

        # 查询用户是否存在
        cursor.execute("SELECT id, username, email, role_id, is_active FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ 用户 '{username}' 不存在")
            return False

        user_id, username, email, role_id, is_active = user

        print(f"找到用户:")
        print(f"  ID: {user_id}")
        print(f"  用户名: {username}")
        print(f"  邮箱: {email}")
        print(f"  当前角色ID: {role_id if role_id else 'None'} ({'管理员' if role_id == admin_role_id else '普通用户'})")
        print(f"  激活状态: {'是' if is_active else '否'}")

        if role_id == admin_role_id:
            print(f"\n✅ 用户 '{username}' 已经是管理员，无需修改")
            return True

        # 更新为管理员
        print(f"\n正在将用户 '{username}' 改为管理员（role_id={admin_role_id}）...")
        cursor.execute(
            "UPDATE users SET role_id = ?, is_active = 1, is_verified = 1, updated_at = datetime('now') WHERE id = ?",
            (admin_role_id, user_id)
        )
        conn.commit()

        print(f"✅ 成功！用户 '{username}' 已被设为管理员")
        return True

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        if conn:
            conn.close()


def list_all_users(db_path: str = "/root/aigc/data/sessions.db"):
    """列出所有用户"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取管理员角色ID
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()
        admin_role_id = admin_role[0] if admin_role else None

        cursor.execute("""
            SELECT id, username, email, role_id, is_active, is_verified
            FROM users
            ORDER BY id
        """)

        users = cursor.fetchall()

        print("\n所有用户列表:")
        print("-" * 100)
        print(f"{'ID':<5} {'用户名':<15} {'邮箱':<30} {'角色':<10} {'激活':<6} {'验证':<6}")
        print("-" * 100)

        for user in users:
            user_id, username, email, role_id, is_active, is_verified = user
            role = "管理员" if role_id == admin_role_id else "普通用户"
            print(f"{user_id:<5} {username:<15} {email:<30} {role:<10} {'是' if is_active else '否':<6} {'是' if is_verified else '否':<6}")

        print("-" * 100)

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 支持两种路径：本地和服务器
    possible_paths = [
        "/Users/hehe/pycharm_projects/aigc/data/sessions.db",
        "/root/aigc/data/sessions.db",
        "./data/sessions.db"
    ]

    db_path = None
    for path in possible_paths:
        if Path(path).exists():
            db_path = path
            break

    if not db_path:
        print(f"❌ 找不到数据库文件，请检查路径")
        print(f"尝试过的路径: {possible_paths}")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("用法: python make_admin.py <username>")
        print("      python make_admin.py --list    # 列出所有用户")
        list_all_users(db_path)
        sys.exit(1)

    username = sys.argv[1]

    if username == "--list":
        list_all_users(db_path)
    else:
        make_user_admin(username, db_path)
