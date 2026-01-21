"""
调试流式输出 - 查看 SDK 实际返回什么
"""
import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from claude_agent_sdk import query, ClaudeAgentOptions

async def test_streaming():
    """测试 SDK 的流式输出"""
    print("=" * 60)
    print("测试 SDK 流式输出")
    print("=" * 60)

    options = ClaudeAgentOptions(
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=1,
        model="sonnet"
    )

    message_count = 0
    start_time = asyncio.get_event_loop().time()

    async for message in query(
        prompt="写一个简单的Python函数",
        options=options
    ):
        message_count += 1
        elapsed = asyncio.get_event_loop().time() - start_time

        print(f"\n[消息 #{message_count}] 时间: {elapsed*1000:.0f}ms")
        print(f"  类型: {type(message).__name__}")

        # 检查消息内容
        if hasattr(message, 'content'):
            print(f"  内容块数: {len(message.content)}")
            for i, block in enumerate(message.content):
                block_type = getattr(block, 'type', 'unknown')
                print(f"    块 #{i}: type={block_type}")

                # 处理 TextBlock
                if hasattr(block, 'text') and block.text:
                    text_len = len(block.text)
                    print(f"      文本长度: {text_len}")
                    print(f"      完整文本:")
                    print(f"      >>>{block.text}<<<")
                    print(f"      --- 文本结束 ---")

                # 处理 ThinkingBlock
                elif hasattr(block, 'thinking') and block.thinking:
                    print(f"      Thinking: {block.thinking[:100]}...")

                # 处理 ToolUseBlock
                elif hasattr(block, 'name'):
                    print(f"      工具调用: {block.name}")
                    print(f"      参数: {getattr(block, 'input', {})}")

                # 处理 ToolResultBlock
                elif hasattr(block, 'tool_use_id'):
                    print(f"      工具结果 ID: {block.tool_use_id}")
                    print(f"      结果: {str(getattr(block, 'content', None))[:100]}...")

    print(f"\n总消息数: {message_count}")

if __name__ == "__main__":
    asyncio.run(test_streaming())
