#!/usr/bin/env python3
"""
Script to index existing uploaded files into docs-management index
Simplified version without complex dependencies
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add docs-management scripts to path
project_root = Path(__file__).parent.parent.parent
docs_scripts = project_root / ".claude" / "skills" / "docs-management" / "scripts"
sys.path.insert(0, str(docs_scripts))

from management.index_manager import IndexManager


def index_existing_uploads():
    """Index all existing uploaded files"""
    # Initialize index manager
    canonical_dir = project_root / "work_dir" / ".claude" / "skills" / "docs-management" / "canonical"
    index_manager = IndexManager(canonical_dir)

    # Find all uploaded files
    upload_dir = canonical_dir / "user-uploads"

    if not upload_dir.exists():
        print(f"❌ Upload directory not found: {upload_dir}")
        return

    print(f"📂 Scanning: {upload_dir}")

    success_count = 0
    failed_count = 0

    # Iterate through user directories
    for user_dir in upload_dir.iterdir():
        if not user_dir.is_dir():
            continue

        user_id = user_dir.name
        print(f"\n👤 User {user_id}:")

        # Iterate through files
        for file_path in user_dir.iterdir():
            if not file_path.is_file():
                continue

            try:
                # Extract doc_id from filename (remove extension)
                doc_id = file_path.stem
                file_name = file_path.name
                file_size = file_path.stat().st_size

                # Determine file type
                file_ext = file_path.suffix.lower()
                file_type = {
                    '.pdf': 'application/pdf',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.txt': 'text/plain',
                    '.md': 'text/markdown',
                }.get(file_ext, 'application/octet-stream')

                # Generate relative path
                relative_path = file_path.relative_to(canonical_dir)

                # Extract keywords from filename
                keywords = extract_keywords_from_filename(file_name)

                # Build metadata
                metadata = {
                    "doc_id": doc_id,
                    "path": str(relative_path),
                    "title": file_name,
                    "description": f"User uploaded file ({file_type})",
                    "category": "user-upload",
                    "source_type": "upload",
                    "file_type": file_type,
                    "file_size": file_size,
                    "user_id": int(user_id),
                    "keywords": keywords,
                    "tags": generate_tags(file_type),
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "hash": f"sha256:{doc_id.split('-')[-1]}",
                }

                # Add to index
                success = index_manager.update_entry(doc_id, metadata)

                if success:
                    print(f"  ✅ {file_name} ({file_size} bytes)")
                    success_count += 1
                else:
                    print(f"  ❌ {file_name} - Failed to add to index")
                    failed_count += 1

            except Exception as e:
                print(f"  ❌ {file_path.name} - Error: {e}")
                failed_count += 1

    print(f"\n{'='*50}")
    print(f"Indexing complete:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"{'='*50}")

    # Verify by searching for uploaded files
    print("\n🔍 Verifying indexed files:")
    all_entries = index_manager.load_all()
    uploaded_count = sum(1 for m in all_entries.values() if m.get("source_type") == "upload")
    print(f"  📊 Total uploaded files in index: {uploaded_count}")


def extract_keywords_from_filename(filename: str) -> list:
    """Extract keywords from filename"""
    import re
    name_without_ext = Path(filename).stem
    parts = re.split(r'[-_\s]+', name_without_ext)

    stop_words = {'user', 'upload', 'file', 'document', 'the', 'a', 'an'}
    keywords = [p.lower() for p in parts if len(p) > 2 and p.lower() not in stop_words]

    return keywords[:10]


def generate_tags(file_type: str) -> list:
    """Generate tags based on file type"""
    tags = ["user-upload"]

    if "pdf" in file_type:
        tags.append("pdf")
    elif "image" in file_type or file_type.startswith("image/"):
        tags.append("image")
        if "png" in file_type:
            tags.append("png")
        elif "jpeg" in file_type or "jpg" in file_type:
            tags.append("jpg")
    elif "text" in file_type:
        tags.append("text")
    elif "markdown" in file_type:
        tags.append("markdown")

    return tags


if __name__ == "__main__":
    index_existing_uploads()
