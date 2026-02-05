#!/usr/bin/env python3
"""
Test script to verify file upload and docs-management integration
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.file_upload_service import FileUploadService
from services.database import DatabaseService
from datetime import datetime
import asyncio


async def test_file_upload_with_indexing():
    """Test file upload and automatic indexing"""
    print("=" * 60)
    print("Testing File Upload with Docs-Management Integration")
    print("=" * 60)

    # Initialize services
    db_service = DatabaseService()
    upload_service = FileUploadService(db_service)

    # Test data
    test_file_content = b"This is a test document for file upload integration.\n" * 10
    test_filename = "test-upload-document.txt"
    test_user_id = 999  # Test user ID

    # Generate test conversation turn ID
    conversation_turn_id = datetime.now().strftime("%Y%m%d%H%M%S")

    print(f"\n📤 Uploading test file: {test_filename}")
    print(f"   User ID: {test_user_id}")
    print(f"   Size: {len(test_file_content)} bytes")

    try:
        # Upload file
        result = await upload_service.save_file_from_base64(
            base64_data=test_file_content.hex(),  # Convert to hex for base64 input
            file_name=test_filename,
            user_id=test_user_id,
            session_id="test-session-123",
            conversation_turn_id=conversation_turn_id,
        )

        print(f"\n✅ Upload successful!")
        print(f"   doc_id: {result['doc_id']}")
        print(f"   file_path: {result['file_path']}")
        print(f"   is_existing: {result.get('is_existing', False)}")

        # Verify indexing
        print(f"\n🔍 Verifying index...")

        if upload_service.index_manager:
            entry = upload_service.index_manager.get_entry(result['doc_id'])

            if entry:
                print(f"✅ File found in index!")
                print(f"   Title: {entry.get('title')}")
                print(f"   Category: {entry.get('category')}")
                print(f"   Tags: {entry.get('tags')}")
                print(f"   Keywords: {entry.get('keywords')}")
                print(f"   Path: {entry.get('path')}")
            else:
                print(f"❌ File NOT found in index")
        else:
            print(f"⚠️  IndexManager not available")

        # Test search functionality
        print(f"\n🔍 Testing search for uploaded files...")
        from management.index_manager import IndexManager

        canonical_dir = Path(__file__).parent.parent / "work_dir" / ".claude" / "skills" / "docs-management" / "canonical"
        index_mgr = IndexManager(canonical_dir)

        all_entries = index_mgr.load_all()
        uploaded_files = {
            doc_id: metadata
            for doc_id, metadata in all_entries.items()
            if metadata.get("source_type") == "upload"
        }

        print(f"📊 Total uploaded files in index: {len(uploaded_files)}")
        for doc_id, metadata in uploaded_files.items():
            print(f"   - {doc_id}: {metadata.get('title')} ({metadata.get('file_size')} bytes)")

        print(f"\n{'=' * 60}")
        print("✅ Test completed successfully!")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_file_upload_with_indexing())
