#!/usr/bin/env python3
"""
脚本用于查看用户上传的文件状态
对比数据库记录和实际文件，找出缺失或未索引的文件
"""
import sys
from pathlib import Path

# 添加 docs-management 脚本到路径
project_root = Path(__file__).parent.parent.parent
docs_scripts = project_root / ".claude" / "skills" / "docs-management" / "scripts"
sys.path.insert(0, str(docs_scripts))

from management.index_manager import IndexManager

import sqlite3


def check_uploads():
    """检查上传文件状态"""
    print("=" * 80)
    print("📊 用户上传文件状态检查")
    print("=" * 80)

    # 1. 数据库记录
    db_path = project_root / "data" / "sessions.db"
    if not db_path.exists():
        print(f"❌ 数据库不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT doc_id, file_name, file_type, file_size, user_id, session_id, datetime(created_at, 'localtime') as created
        FROM user_file_relationships
        ORDER BY created_at DESC
    """)
    db_records = cursor.fetchall()
    conn.close()

    print(f"\n📋 数据库记录: {len(db_records)} 个文件")
    print("-" * 80)

    # 2. 实际文件
    upload_dir = project_root / "work_dir" / ".claude" / "skills" / "docs-management" / "canonical" / "user-uploads"
    print(f"\n📁 上传目录: {upload_dir}")

    if not upload_dir.exists():
        print(f"❌ 上传目录不存在")
        return

    # 收集所有实际文件
    actual_files = {}
    for user_dir in upload_dir.iterdir():
        if user_dir.is_dir():
            user_id = user_dir.name
            for file_path in user_dir.iterdir():
                if file_path.is_file():
                    doc_id = file_path.stem
                    actual_files[doc_id] = {
                        "path": file_path,
                        "size": file_path.stat().st_size,
                        "user_id": int(user_id)
                    }

    print(f"📄 实际文件: {len(actual_files)} 个")

    # 3. 索引记录
    canonical_dir = upload_dir.parent
    index_manager = IndexManager(canonical_dir)
    all_entries = index_manager.load_all()

    indexed_uploads = {
        doc_id: metadata
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload"
    }

    print(f"🔍 索引中的上传文件: {len(indexed_uploads)} 个")
    print("-" * 80)

    # 4. 对比分析
    print(f"\n📊 详细状态:")
    print("-" * 80)

    # 统计
    missing_files = []  # 数据库有但文件没有
    unindexed_files = []  # 文件有但索引没有
    all_ok = []  # 三者都有

    for doc_id, file_name, file_type, file_size, user_id, session_id, created in db_records:
        has_file = doc_id in actual_files
        has_index = doc_id in indexed_uploads

        status = "✅" if has_file and has_index else "⚠️"

        print(f"\n{status} {doc_id}")
        print(f"   文件名: {file_name}")
        print(f"   用户: {user_id}")
        print(f"   大小: {file_size} bytes" if file_size else "   大小: 未知")
        print(f"   上传时间: {created}")
        print(f"   会话: {session_id or 'None'}")
        print(f"   文件存在: {'✅' if has_file else '❌'}")
        print(f"   已索引: {'✅' if has_index else '❌'}")

        if not has_file:
            missing_files.append(doc_id)
        elif not has_index:
            unindexed_files.append((doc_id, actual_files[doc_id]))
        else:
            all_ok.append(doc_id)

    # 5. 总结
    print(f"\n{'=' * 80}")
    print("📈 统计总结:")
    print("-" * 80)
    print(f"  ✅ 完整（数据库+文件+索引）: {len(all_ok)} 个")
    print(f"  ⚠️  缺失文件（仅数据库）: {len(missing_files)} 个")
    print(f"  ⚠️  未索引（仅文件）: {len(unindexed_files)} 个")
    print(f"{'=' * 80}")

    # 6. 处理未索引的文件
    if unindexed_files:
        print(f"\n🔧 发现 {len(unindexed_files)} 个未索引的文件，是否需要添加到索引？")
        print("运行以下命令:")
        print("  python backend/scripts/index_existing_uploads_simple.py")

    return {
        "total_db": len(db_records),
        "total_files": len(actual_files),
        "total_indexed": len(indexed_uploads),
        "missing": len(missing_files),
        "unindexed": len(unindexed_files),
        "ok": len(all_ok)
    }


if __name__ == "__main__":
    check_uploads()
