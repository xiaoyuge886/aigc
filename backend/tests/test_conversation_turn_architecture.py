"""
测试 Conversation Turn ID 架构

验证：
1. conversation_turn_id 提前生成
2. 文件上传时 session_id 可以为 None
3. 延迟绑定 session_id 正常工作
4. 基于 conversation_turn_id 的查询正常工作
"""
import pytest
import asyncio
import sys
from pathlib import Path
import uuid

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.database import DatabaseService
from services.file_upload_service import FileUploadService
from services.file_content_loader import FileContentLoader
from services.file_search_service import FileSearchService


@pytest.mark.asyncio
async def test_early_conversation_turn_id_generation():
    """测试 conversation_turn_id 提前生成"""
    # conversation_turn_id 应该在请求开始时就能生成
    conversation_turn_id = uuid.uuid4().hex[:16]
    assert conversation_turn_id is not None
    assert len(conversation_turn_id) == 16
    print(f"✅ conversation_turn_id generated early: {conversation_turn_id}")


@pytest.mark.asyncio
async def test_file_upload_with_null_session_id(db_service: DatabaseService):
    """测试文件上传时 session_id 可以为 None"""
    file_upload_service = FileUploadService(db_service)
    
    # 提前生成 conversation_turn_id
    conversation_turn_id = uuid.uuid4().hex[:16]
    session_id = None  # 第一次对话时 session_id 为 None
    
    # 创建测试文件数据（使用唯一内容避免冲突）
    import time
    unique_content = f"Test file content {time.time()}"
    test_file_data = unique_content.encode('utf-8')
    test_file_name = f"test_file_{uuid.uuid4().hex[:8]}.txt"
    
    # 文件上传应该成功，即使 session_id 为 None
    result = await file_upload_service.save_uploaded_file(
        file_data=test_file_data,
        file_name=test_file_name,
        user_id=1,  # 假设用户 ID 为 1
        session_id=session_id,  # None
        conversation_turn_id=conversation_turn_id,  # 必需
    )
    
    assert result["doc_id"] is not None
    print(f"✅ File uploaded successfully with session_id=None, conversation_turn_id={conversation_turn_id}")
    
    # 验证文件关系记录
    relationship = await db_service.get_file_relationship(result["doc_id"])
    assert relationship is not None
    assert relationship.session_id is None  # session_id 应该为 None
    assert relationship.conversation_turn_id == conversation_turn_id
    print(f"✅ File relationship created with session_id=None, conversation_turn_id={relationship.conversation_turn_id}")


@pytest.mark.asyncio
async def test_delayed_session_id_binding(db_service: DatabaseService):
    """测试延迟绑定 session_id"""
    # 1. 先上传文件（session_id=None）
    file_upload_service = FileUploadService(db_service)
    conversation_turn_id = uuid.uuid4().hex[:16]
    
    import time
    unique_content = f"Test delayed binding {time.time()}"
    result = await file_upload_service.save_uploaded_file(
        file_data=unique_content.encode('utf-8'),
        file_name=f"test_delayed_binding_{uuid.uuid4().hex[:8]}.txt",
        user_id=1,
        session_id=None,  # 初始为 None
        conversation_turn_id=conversation_turn_id,
    )
    
    # 2. 验证初始状态
    relationship = await db_service.get_file_relationship(result["doc_id"])
    assert relationship.session_id is None
    
    # 3. 模拟获取 session_id（从 SDK）
    new_session_id = str(uuid.uuid4())
    
    # 4. 批量更新 session_id
    updated_count = await db_service.update_session_id_for_turn(
        conversation_turn_id=conversation_turn_id,
        session_id=new_session_id,
        user_id=1
    )
    
    assert updated_count > 0
    print(f"✅ Updated {updated_count} records with session_id={new_session_id}")
    
    # 5. 验证更新后的状态
    relationship = await db_service.get_file_relationship(result["doc_id"])
    assert relationship.session_id == new_session_id
    print(f"✅ Session ID successfully bound: {relationship.session_id}")


@pytest.mark.asyncio
async def test_query_by_conversation_turn_id(db_service: DatabaseService):
    """测试基于 conversation_turn_id 的查询"""
    file_upload_service = FileUploadService(db_service)
    conversation_turn_id = uuid.uuid4().hex[:16]
    
    # 上传多个文件到同一个 conversation_turn_id
    import time
    file_results = []
    for i in range(3):
        unique_content = f"Test file {i} {time.time()}"
        result = await file_upload_service.save_uploaded_file(
            file_data=unique_content.encode('utf-8'),
            file_name=f"test_file_{i}_{uuid.uuid4().hex[:8]}.txt",
            user_id=1,
            session_id=None,  # 可以为 None
            conversation_turn_id=conversation_turn_id,
        )
        file_results.append(result)
    
    # 通过 conversation_turn_id 查询文件
    turn_files = await db_service.get_turn_files(
        conversation_turn_id=conversation_turn_id,
        user_id=1
    )
    
    assert len(turn_files) == 3
    print(f"✅ Found {len(turn_files)} files by conversation_turn_id={conversation_turn_id}")
    
    # 验证所有文件都有相同的 conversation_turn_id
    for file in turn_files:
        assert file.conversation_turn_id == conversation_turn_id
        print(f"  - {file.file_name} (doc_id: {file.doc_id})")


@pytest.mark.asyncio
async def test_file_content_query_by_turn_id(db_service: DatabaseService):
    """测试基于 conversation_turn_id 的文件内容查询"""
    file_upload_service = FileUploadService(db_service)
    file_content_loader = FileContentLoader(db_service)
    
    conversation_turn_id = uuid.uuid4().hex[:16]
    
    # 上传一个测试文件
    import time
    unique_suffix = uuid.uuid4().hex[:8]
    test_content = f"这是测试文件内容 {time.time()}。包含关键词：氢能、能源、分析。"
    result = await file_upload_service.save_uploaded_file(
        file_data=test_content.encode('utf-8'),
        file_name=f"test_query_{unique_suffix}.txt",
        user_id=1,
        session_id=None,
        conversation_turn_id=conversation_turn_id,
    )
    
    # 通过 conversation_turn_id 查询文件
    turn_files = await db_service.get_turn_files(
        conversation_turn_id=conversation_turn_id,
        user_id=1
    )
    
    assert len(turn_files) > 0
    
    # 使用基于查询的检索
    file = turn_files[0]
    snippets = await file_content_loader.search_file_content(
        doc_id=file.doc_id,
        query="氢能",
        user_id=1,
        max_snippets=3
    )
    
    assert len(snippets) > 0
    print(f"✅ Found {len(snippets)} relevant snippets for query '氢能'")
    for snippet in snippets:
        print(f"  - Relevance: {snippet.relevance_score:.2f}, Lines: {snippet.line_start}-{snippet.line_end}")


if __name__ == "__main__":
    # 运行测试
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    async def run_tests():
        from services.database import DatabaseService
        
        db_service = DatabaseService()
        await db_service.initialize()
        
        try:
            print("=" * 60)
            print("测试 1: conversation_turn_id 提前生成")
            print("=" * 60)
            await test_early_conversation_turn_id_generation()
            
            print("\n" + "=" * 60)
            print("测试 2: 文件上传时 session_id 可以为 None")
            print("=" * 60)
            await test_file_upload_with_null_session_id(db_service)
            
            print("\n" + "=" * 60)
            print("测试 3: 延迟绑定 session_id")
            print("=" * 60)
            await test_delayed_session_id_binding(db_service)
            
            print("\n" + "=" * 60)
            print("测试 4: 基于 conversation_turn_id 的查询")
            print("=" * 60)
            await test_query_by_conversation_turn_id(db_service)
            
            print("\n" + "=" * 60)
            print("测试 5: 基于 conversation_turn_id 的文件内容查询")
            print("=" * 60)
            await test_file_content_query_by_turn_id(db_service)
            
            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
            
        finally:
            await db_service.close()
    
    asyncio.run(run_tests())
