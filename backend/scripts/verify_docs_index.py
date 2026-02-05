#!/usr/bin/env python3
"""
Simple verification script for docs-management index integration
"""
import sys
from pathlib import Path

# Add docs-management scripts to path
project_root = Path(__file__).parent.parent.parent
docs_scripts = project_root / ".claude" / "skills" / "docs-management" / "scripts"
sys.path.insert(0, str(docs_scripts))

from management.index_manager import IndexManager


def verify_index():
    """Verify the docs-management index"""
    print("=" * 60)
    print("Verifying Docs-Management Index Integration")
    print("=" * 60)

    # Path to index
    canonical_dir = project_root / "work_dir" / ".claude" / "skills" / "docs-management" / "canonical"
    print(f"\n📂 Index location: {canonical_dir}")

    if not canonical_dir.exists():
        print(f"❌ Canonical directory not found!")
        return

    # Initialize index manager
    index_manager = IndexManager(canonical_dir)

    # Load all entries
    print(f"\n📊 Loading index...")
    all_entries = index_manager.load_all()
    print(f"   Total entries: {len(all_entries)}")

    # Filter uploaded files
    uploaded_files = {
        doc_id: metadata
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload"
    }

    print(f"\n📤 Uploaded files: {len(uploaded_files)}")

    if uploaded_files:
        for doc_id, metadata in uploaded_files.items():
            print(f"\n  📄 {doc_id}:")
            print(f"     Title: {metadata.get('title')}")
            print(f"     Type: {metadata.get('file_type')}")
            print(f"     Size: {metadata.get('file_size')} bytes")
            print(f"     User: {metadata.get('user_id')}")
            print(f"     Tags: {metadata.get('tags')}")
            print(f"     Path: {metadata.get('path')}")

            # Verify file exists
            file_path = canonical_dir / metadata.get('path')
            if file_path.exists():
                print(f"     ✅ File exists on disk")
            else:
                print(f"     ❌ File NOT found on disk!")
    else:
        print("   ⚠️  No uploaded files found in index")

    print(f"\n{'=' * 60}")
    print("✅ Verification complete!")
    print(f"{'=' * 60}")

    # Test search functionality
    print(f"\n🔍 Testing search by user_id=2...")
    user_2_files = [
        (doc_id, metadata)
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload" and metadata.get("user_id") == 2
    ]
    print(f"   Found {len(user_2_files)} files for user 2")

    # Test search by tag
    print(f"\n🏷️  Testing search by tag='pdf'...")
    pdf_files = [
        (doc_id, metadata)
        for doc_id, metadata in all_entries.items()
        if metadata.get("source_type") == "upload" and "pdf" in metadata.get("tags", [])
    ]
    print(f"   Found {len(pdf_files)} PDF files")

    return len(uploaded_files) > 0


if __name__ == "__main__":
    has_uploaded_files = verify_index()
    sys.exit(0 if has_uploaded_files else 1)
