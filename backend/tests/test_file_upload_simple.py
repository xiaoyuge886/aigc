"""
简化版文件上传测试 - 验证消息格式

这个测试主要验证：
1. Claude SDK 的 query() 方法接受的消息格式
2. 异步迭代器格式是否支持图像附件
3. 消息格式的正确构造方式
"""

import asyncio
import base64
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from loguru import logger

# 配置日志
logger.remove()  # 移除默认处理器
logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")


def create_minimal_png() -> str:
    """创建一个最小的有效 PNG 图像（1x1 红色像素）"""
    # 这是一个最小的有效 PNG 文件（base64）
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


async def test_message_formats():
    """测试不同的消息格式"""
    
    options = ClaudeAgentOptions(
        permission_mode="acceptEdits",
        max_turns=1,
    )
    
    print("\n" + "=" * 80)
    print("测试 Claude SDK 消息格式")
    print("=" * 80)
    
    # 测试1: 字符串格式
    print("\n[测试1] 字符串格式的 prompt")
    try:
        async with ClaudeSDKClient(options) as client:
            # 直接传递字符串
            await client.query("你好")
            print("✅ 字符串格式被接受")
    except Exception as e:
        print(f"❌ 字符串格式失败: {type(e).__name__}: {e}")
    
    await asyncio.sleep(1)
    
    # 测试2: 异步迭代器 - 简单文本
    print("\n[测试2] 异步迭代器格式 - 简单文本")
    try:
        async def simple_text_generator():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "你好"
                }
            }
        
        async with ClaudeSDKClient(options) as client:
            await client.query(simple_text_generator())
            print("✅ 异步迭代器格式（文本）被接受")
    except Exception as e:
        print(f"❌ 异步迭代器格式（文本）失败: {type(e).__name__}: {e}")
    
    await asyncio.sleep(1)
    
    # 测试3: 异步迭代器 - 图像附件
    print("\n[测试3] 异步迭代器格式 - 图像附件")
    try:
        base64_image = create_minimal_png()
        
        async def image_generator():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请描述这张图片"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }
            }
        
        async with ClaudeSDKClient(options) as client:
            await client.query(image_generator())
            print("✅ 异步迭代器格式（图像附件）被接受")
            print(f"   图像大小: {len(base64_image)} 字符 (base64)")
    except Exception as e:
        print(f"❌ 异步迭代器格式（图像附件）失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    await asyncio.sleep(1)
    
    # 测试4: 验证消息格式结构
    print("\n[测试4] 验证消息格式结构")
    print("根据 Claude SDK 文档，消息格式应该是：")
    print("""
    {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "文本内容"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "base64编码的数据"
                    }
                }
            ]
        }
    }
    """)
    
    # 测试5: 多个图像
    print("\n[测试5] 多个图像附件")
    try:
        base64_image1 = create_minimal_png()
        base64_image2 = create_minimal_png()
        
        async def multiple_images_generator():
            yield {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请比较这两张图片"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image1
                            }
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image2
                            }
                        }
                    ]
                }
            }
        
        async with ClaudeSDKClient(options) as client:
            await client.query(multiple_images_generator())
            print("✅ 多个图像附件格式被接受")
            print(f"   图像1大小: {len(base64_image1)} 字符")
            print(f"   图像2大小: {len(base64_image2)} 字符")
    except Exception as e:
        print(f"❌ 多个图像附件失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print("\n关键发现：")
    print("1. 如果所有测试都显示 '被接受'，说明格式正确")
    print("2. 如果出现错误，请检查错误信息以了解问题")
    print("3. 注意：即使格式被接受，Claude Code CLI 必须运行才能实际处理请求")


if __name__ == "__main__":
    asyncio.run(test_message_formats())
