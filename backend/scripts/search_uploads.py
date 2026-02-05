#!/usr/bin/env python3
"""
搜索用户上传的文件
支持按用户ID、文件名、标签等条件搜索
"""
import sys
from pathlib import Path

# 添加 docs-management 脚本到路径
project_root = Path(__file__).parent.parent.parent
docs_scripts = project_root / ".claude" / "skills" / "docs-management" / "scripts"
sys.path.insert(0, str(docs_scripts))

from management.index_manager import IndexManager


def search_uploads(user_id=None, keyword=None, file_type=None):
    """
    搜索上传的文件

    Args:
        user_id: 用户ID过滤
        keyword: 关键词搜索（文件名或关键词）
        file_type: 文件类型过滤（pdf, image, text等）
    """
    print("=" * 80)
    print("🔍 搜索上传文件")
    print("=" * 80)

    # 初始化索引管理器
    canonical_dir = project_root / "work_dir" / ".claude" / "skills" / "docs-management" / "canonical"
    index_manager = IndexManager(canonical_dir)

    # 加载所有条目
    all_entries = index_manager.load_all()

    # 过滤上传的文件
    uploaded_files = [
        (doc_id, metadata)
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload"
    ]

    print(f"\n📊 总共 {len(uploaded_files)} 个已索引的上传文件")

    # 应用过滤条件
    if user_id:
        uploaded_files = [
            (doc_id, meta)
            for doc_id, meta in uploaded_files
            if meta.get("user_id") == user_id
        ]
        print(f"   用户 ID: {user_id}")

    if keyword:
        uploaded_files = [
            (doc_id, meta)
            for doc_id, meta in uploaded_files
            if keyword.lower() in meta.get("title", "").lower() or
               any(keyword.lower() in k.lower() for k in meta.get("keywords", []))
        ]
        print(f"   关键词: {keyword}")

    if file_type:
        uploaded_files = [
            (doc_id, meta)
            for doc_id, meta in uploaded_files
            if file_type.lower() in meta.get("file_type", "").lower() or
               file_type.lower() in str(meta.get("tags", []))
        ]
        print(f"   文件类型: {file_type}")

    print(f"\n📋 找到 {len(uploaded_files)} 个文件:")
    print("-" * 80)

    if not uploaded_files:
        print("   没有找到匹配的文件")
        return

    for i, (doc_id, metadata) in enumerate(uploaded_files, 1):
        print(f"\n{i}. 📄 {metadata.get('title')}")
        print(f"   🆔 ID: {doc_id}")
        print(f"   👤 用户: {metadata.get('user_id')}")
        print(f"   📦 类型: {metadata.get('file_type')}")
        print(f"   📏 大小: {metadata.get('file_size')} bytes")
        print(f"   🏷️  标签: {', '.join(metadata.get('tags', []))}")
        print(f"   🔑 关键词: {', '.join(metadata.get('keywords', []))}")
        print(f"   📅 上传时间: {metadata.get('uploaded_at')}")
        print(f"   📁 路径: {metadata.get('path')}")

        # 检查文件是否存在
        file_path = canonical_dir / metadata.get('path')
        if file_path.exists():
            print(f"   ✅ 文件存在")
        else:
            print(f"   ❌ 文件不存在")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="搜索用户上传的文件")
    parser.add_argument("--user-id", type=int, help="按用户ID过滤")
    parser.add_argument("--keyword", type=str, help="按关键词搜索")
    parser.add_argument("--type", type=str, help="按文件类型过滤（pdf, image, text等）")

    args = parser.parse_args()

    search_uploads(
        user_id=args.user_id,
        keyword=args.keyword,
        file_type=args.type
    )
