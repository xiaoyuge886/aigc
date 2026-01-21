"""
测试 Claude SDK 文件附件功能

验证：
1. 图像文件上传（base64 格式）
2. 消息格式支持（字符串 vs 数组格式）
3. 不同文件类型的支持情况
4. 文件大小限制
"""

import asyncio
import base64
import os
from pathlib import Path
from typing import List, Optional

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    UserMessage as SDKUserMessage,
    AssistantMessage as SDKAssistantMessage,
    ResultMessage as SDKResultMessage,
)
from loguru import logger

# 配置日志
logger.add("test_file_upload.log", rotation="10 MB", level="DEBUG")


class FileUploadTester:
    """文件上传功能测试类"""
    
    def __init__(self):
        self.test_results = []
        self.options = ClaudeAgentOptions(
            permission_mode="acceptEdits",
            max_turns=3,
        )
    
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[dict] = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")
        if details:
            logger.debug(f"  详情: {details}")
    
    def create_test_image(self, size: int = 100) -> tuple[str, bytes]:
        """
        创建一个简单的测试图像（PNG格式）
        
        Args:
            size: 图像尺寸（像素）
        
        Returns:
            (base64_string, raw_bytes) 元组
        """
        try:
            from PIL import Image
            import io
            
            # 创建一个简单的测试图像
            img = Image.new('RGB', (size, size), color='red')
            
            # 保存到字节流
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            raw_bytes = img_bytes.read()
            
            # 转换为 base64
            base64_str = base64.b64encode(raw_bytes).decode('utf-8')
            
            return base64_str, raw_bytes
        except ImportError:
            # 如果没有 PIL，创建一个最小的 PNG 文件（1x1 红色像素）
            # 这是一个最小的有效 PNG 文件
            minimal_png = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
            )
            base64_str = base64.b64encode(minimal_png).decode('utf-8')
            return base64_str, minimal_png
    
    async def test_1_string_prompt(self):
        """测试1: 字符串格式的 prompt（基础测试）"""
        test_name = "测试1: 字符串格式的 prompt"
        try:
            async with ClaudeSDKClient(self.options) as client:
                await client.query("你好，请回复'收到'")
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if "收到" in text_content or len(text_content) > 0:
                            self.log_result(
                                test_name,
                                True,
                                f"成功收到响应: {text_content[:50]}...",
                                {"response_length": len(text_content)}
                            )
                            return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(test_name, False, f"测试失败: {str(e)}", {"error_type": type(e).__name__})
    
    async def test_2_async_iterator_prompt(self):
        """测试2: 异步迭代器格式的 prompt（流式输入）"""
        test_name = "测试2: 异步迭代器格式的 prompt"
        try:
            async def generate_messages():
                yield {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": "你好，请回复'收到'"
                    }
                }
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(generate_messages())
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if len(text_content) > 0:
                            self.log_result(
                                test_name,
                                True,
                                f"成功收到响应: {text_content[:50]}...",
                                {"response_length": len(text_content)}
                            )
                            return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(test_name, False, f"测试失败: {str(e)}", {"error_type": type(e).__name__})
    
    async def test_3_image_with_async_iterator(self):
        """测试3: 使用异步迭代器发送图像附件"""
        test_name = "测试3: 异步迭代器 + 图像附件"
        try:
            # 创建测试图像
            base64_image, _ = self.create_test_image()
            
            async def generate_messages():
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
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(generate_messages())
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if len(text_content) > 0:
                            self.log_result(
                                test_name,
                                True,
                                f"成功收到响应: {text_content[:100]}...",
                                {
                                    "response_length": len(text_content),
                                    "image_size": len(base64_image)
                                }
                            )
                            return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"测试失败: {str(e)}",
                {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
    
    async def test_4_image_with_string_prompt(self):
        """测试4: 尝试使用字符串 prompt + 图像（可能不支持）"""
        test_name = "测试4: 字符串 prompt + 图像（预期可能失败）"
        try:
            # 创建测试图像
            base64_image, _ = self.create_test_image()
            
            # 尝试将图像数据包含在字符串中（这应该不会工作）
            prompt_with_image = f"请描述这张图片: {base64_image[:100]}..."
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(prompt_with_image)
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        # 这个测试主要是验证字符串格式不支持图像
                        self.log_result(
                            test_name,
                            True,  # 即使收到响应也标记为成功，因为这是验证行为
                            f"收到响应（字符串格式不支持图像）: {text_content[:50]}...",
                            {"response_length": len(text_content)}
                        )
                        return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"测试失败: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    async def test_5_multiple_images(self):
        """测试5: 发送多个图像"""
        test_name = "测试5: 多个图像附件"
        try:
            # 创建多个测试图像
            base64_image1, _ = self.create_test_image(50)
            base64_image2, _ = self.create_test_image(100)
            
            async def generate_messages():
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
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(generate_messages())
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if len(text_content) > 0:
                            self.log_result(
                                test_name,
                                True,
                                f"成功收到响应: {text_content[:100]}...",
                                {
                                    "response_length": len(text_content),
                                    "image_count": 2
                                }
                            )
                            return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"测试失败: {str(e)}",
                {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
    
    async def test_6_large_image(self):
        """测试6: 大图像文件（测试文件大小限制）"""
        test_name = "测试6: 大图像文件（500x500）"
        try:
            # 创建较大的测试图像
            base64_image, raw_bytes = self.create_test_image(500)
            file_size_kb = len(raw_bytes) / 1024
            
            async def generate_messages():
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
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(generate_messages())
                
                response_received = False
                async for message in client.receive_response():
                    if isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if len(text_content) > 0:
                            self.log_result(
                                test_name,
                                True,
                                f"成功收到响应: {text_content[:100]}...",
                                {
                                    "response_length": len(text_content),
                                    "file_size_kb": round(file_size_kb, 2),
                                    "base64_length": len(base64_image)
                                }
                            )
                            return
                
                if not response_received:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"测试失败: {str(e)}",
                {
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                    "file_size_kb": round(file_size_kb, 2) if 'file_size_kb' in locals() else None
                }
            )
    
    async def test_7_pdf_file(self):
        """测试7: PDF 文件（可能不支持）"""
        test_name = "测试7: PDF 文件（预期可能不支持）"
        try:
            # 创建一个最小的 PDF 文件（base64）
            # 这是一个最小的有效 PDF 文件
            minimal_pdf_base64 = base64.b64encode(
                b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n179\n%%EOF"
            ).decode('utf-8')
            
            async def generate_messages():
                yield {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这个PDF文件"
                            },
                            {
                                "type": "image",  # 尝试使用 image 类型
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": minimal_pdf_base64
                                }
                            }
                        ]
                    }
                }
            
            async with ClaudeSDKClient(self.options) as client:
                await client.query(generate_messages())
                
                response_received = False
                error_occurred = False
                async for message in client.receive_response():
                    if isinstance(message, SDKResultMessage) and message.is_error:
                        error_occurred = True
                        self.log_result(
                            test_name,
                            False,  # PDF 不支持，这是预期的
                            f"收到错误响应（预期）: {message.result or '未知错误'}",
                            {"is_error": True}
                        )
                        return
                    elif isinstance(message, SDKAssistantMessage):
                        response_received = True
                        text_content = ""
                        for block in message.content:
                            if hasattr(block, 'text'):
                                text_content += block.text
                        
                        if len(text_content) > 0:
                            # 如果收到响应，说明可能支持（但可能无法解析PDF内容）
                            self.log_result(
                                test_name,
                                True,  # 收到响应就算成功（即使无法解析PDF）
                                f"收到响应（可能无法解析PDF）: {text_content[:100]}...",
                                {
                                    "response_length": len(text_content),
                                    "note": "PDF 文件可能不被支持或无法解析"
                                }
                            )
                            return
                
                if not response_received and not error_occurred:
                    self.log_result(test_name, False, "未收到响应")
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"测试失败: {str(e)}",
                {
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                    "note": "PDF 文件可能不被支持"
                }
            )
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 80)
        logger.info("开始测试 Claude SDK 文件附件功能")
        logger.info("=" * 80)
        
        tests = [
            self.test_1_string_prompt,
            self.test_2_async_iterator_prompt,
            self.test_3_image_with_async_iterator,
            self.test_4_image_with_string_prompt,
            self.test_5_multiple_images,
            self.test_6_large_image,
            self.test_7_pdf_file,
        ]
        
        for i, test in enumerate(tests, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"运行测试 {i}/{len(tests)}: {test.__name__}")
            logger.info(f"{'=' * 80}")
            try:
                await test()
                # 在测试之间添加短暂延迟
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"测试执行异常: {e}", exc_info=True)
        
        # 打印测试总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        logger.info("\n" + "=" * 80)
        logger.info("测试总结")
        logger.info("=" * 80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        logger.info(f"总测试数: {total}")
        logger.info(f"通过: {passed} ✅")
        logger.info(f"失败: {failed} ❌")
        
        logger.info("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test_name']}: {result['message']}")
        
        # 关键发现
        logger.info("\n" + "=" * 80)
        logger.info("关键发现:")
        logger.info("=" * 80)
        
        # 检查图像支持
        image_tests = [r for r in self.test_results if "图像" in r["test_name"] or "image" in r["test_name"].lower()]
        if image_tests:
            image_success = any(r["success"] for r in image_tests)
            logger.info(f"图像附件支持: {'✅ 支持' if image_success else '❌ 不支持'}")
        
        # 检查异步迭代器支持
        async_tests = [r for r in self.test_results if "异步迭代器" in r["test_name"] or "async" in r["test_name"].lower()]
        if async_tests:
            async_success = any(r["success"] for r in async_tests)
            logger.info(f"异步迭代器格式支持: {'✅ 支持' if async_success else '❌ 不支持'}")
        
        # 检查PDF支持
        pdf_tests = [r for r in self.test_results if "PDF" in r["test_name"]]
        if pdf_tests:
            pdf_success = any(r["success"] for r in pdf_tests)
            logger.info(f"PDF 文件支持: {'✅ 支持' if pdf_success else '❌ 不支持（预期）'}")


async def main():
    """主函数"""
    tester = FileUploadTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
