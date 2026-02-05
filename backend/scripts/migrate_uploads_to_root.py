#!/usr/bin/env python3
"""
将用户上传的文件从 work_dir 迁移到项目根目录的 docs-management
"""
import sys
import shutil
from pathlib import Path

# 添加 docs-management 脚本到路径
project_root = Path(__file__).parent.parent.parent
docs_scripts = project_root / ".claude" / "skills" / "docs-management" / "scripts"
sys.path.insert(0, str(docs_scripts))

from management.index_manager import IndexManager


def migrate_uploads():
    """迁移上传文件和索引"""
    print("=" * 80)
    print("🔄 迁移用户上传文件到项目根目录")
    print("=" * 80)

    # 源目录（work_dir）
    work_dir = project_root / "work_dir"
    old_canonical_dir = work_dir / ".claude" / "skills" / "docs-management" / "canonical"
    old_upload_dir = old_canonical_dir / "user-uploads"
    old_index_json = old_canonical_dir / "index.json"
    old_index_yaml = old_canonical_dir / "index.yaml"

    # 目标目录（项目根目录）
    new_canonical_dir = project_root / ".claude" / "skills" / "docs-management" / "canonical"
    new_upload_dir = new_canonical_dir / "user-uploads"
    new_index_json = new_canonical_dir / "index.json"
    new_index_yaml = new_canonical_dir / "index.yaml"

    print(f"\n📍 源目录: {old_upload_dir}")
    print(f"📍 目标目录: {new_upload_dir}")

    # 1. 检查源目录
    if not old_upload_dir.exists():
        print(f"\n✅ 源目录不存在，无需迁移")
        return

    # 2. 迁移文件
    print(f"\n📦 开始迁移文件...")

    # 创建目标目录
    new_upload_dir.mkdir(parents=True, exist_ok=True)

    migrated_files = []

    for user_dir in old_upload_dir.iterdir():
        if not user_dir.is_dir():
            continue

        user_id = user_dir.name
        new_user_dir = new_upload_dir / user_id
        new_user_dir.mkdir(exist_ok=True)

        for file_path in user_dir.iterdir():
            if not file_path.is_file():
                continue

            # 目标文件路径
            dest_path = new_user_dir / file_path.name

            # 移动文件
            shutil.move(str(file_path), str(dest_path))
            migrated_files.append((file_path.name, dest_path))
            print(f"  ✅ {file_path.name} -> {dest_path}")

    print(f"\n📊 迁移了 {len(migrated_files)} 个文件")

    # 3. 合并索引
    print(f"\n📝 合并索引...")

    # 加载旧索引
    if old_index_json.exists():
        import json
        with open(old_index_json, 'r', encoding='utf-8') as f:
            old_index = json.load(f)

        print(f"  旧索引: {len(old_index)} 个条目")

        # 初始化新索引管理器
        index_manager = IndexManager(new_canonical_dir)
        new_index = index_manager.load_all()

        print(f"  新索引: {len(new_index)} 个条目")

        # 合并上传文件的条目
        added_count = 0
        for doc_id, metadata in old_index.items():
            if metadata.get("source_type") == "upload":
                # 更新路径（移除 user-uploads 前缀）
                old_path = metadata.get("path", "")
                if old_path.startswith("user-uploads/"):
                    metadata["path"] = old_path  # 路径已经是相对路径，保持不变

                # 添加到新索引
                new_index[doc_id] = metadata
                added_count += 1
                print(f"  ✅ 添加到索引: {doc_id}")

        # 保存合并后的索引
        if added_count > 0:
            index_manager.update_entry("__bulk__", new_index)
            print(f"\n📊 索引合并完成，添加了 {added_count} 个上传文件")

            # 保存完整的索引
            with open(new_index_json, 'w', encoding='utf-8') as f:
                json.dump(new_index, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 保存到: {new_index_json}")

    # 4. 验证
    print(f"\n🔍 验证迁移结果...")

    index_manager = IndexManager(new_canonical_dir)
    all_entries = index_manager.load_all()
    uploaded_files = {
        doc_id: metadata
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload"
    }

    print(f"  ✅ 新索引中的上传文件: {len(uploaded_files)} 个")

    for doc_id, metadata in uploaded_files.items():
        file_path = new_canonical_dir / metadata.get("path")
        if file_path.exists():
            print(f"    ✅ {doc_id}: {metadata.get('title')} ({metadata.get('file_size')} bytes)")
        else:
            print(f"    ❌ {doc_id}: 文件不存在")

    # 5. 清理旧目录
    print(f"\n🧹 清理旧目录...")

    try:
        # 删除旧的 user-uploads 目录
        if old_upload_dir.exists():
            shutil.rmtree(old_upload_dir)
            print(f"  ✅ 删除: {old_upload_dir}")

        # 删除旧的索引文件
        if old_index_json.exists():
            old_index_json.unlink()
            print(f"  ✅ 删除: {old_index_json}")

        if old_index_yaml.exists():
            old_index_yaml.unlink()
            print(f"  ✅ 删除: {old_index_yaml}")

        # 如果 canonical 目录为空，也删除
        if old_canonical_dir.exists() and not list(old_canonical_dir.iterdir()):
            shutil.rmtree(old_canonical_dir)
            print(f"  ✅ 删除空目录: {old_canonical_dir}")

    except Exception as e:
        print(f"  ⚠️  清理时出错: {e}")

    print(f"\n{'=' * 80}")
    print("✅ 迁移完成！")
    print(f"{'=' * 80}")
    print(f"\n📁 新的文件位置: {new_upload_dir}")
    print(f"📝 新的索引位置: {new_index_json}")
    print(f"\n现在用户上传的文件会被 docs-management skill 检索到！")


if __name__ == "__main__":
    migrate_uploads()
