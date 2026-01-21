"""
安全控制器 - 保护源代码和敏感信息

提供运行时权限控制、敏感信息保护和危险命令拦截
"""
import re
import os
from typing import Dict, Any, List, Optional
from loguru import logger
from pathlib import Path

# Import PermissionResult types from SDK
try:
    from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny
except ImportError:
    # Fallback for older SDK versions
    PermissionResultAllow = None
    PermissionResultDeny = None


class SecurityController:
    """
    安全控制器 - 保护系统安全和敏感信息
    """

    # 敏感文件列表（不可读取、修改或删除）
    SENSITIVE_FILES = [
        '.env',
        '.env.*',
        '*.key',
        '*.pem',
        'config.py',
        'secrets.yaml',
        'credentials.json',
        'settings.py',
        '*_secrets.*',
    ]

    # 敏感目录（不可访问）
    SENSITIVE_DIRS = [
        '.git',
        '.svn',
        '__pycache__',
        'node_modules/.cache',
        '.claude',
        '.config',
    ]

    # 危险命令模式
    DANGEROUS_COMMANDS = [
        r'rm\s+-rf\s+/',
        r'rmdir\s+/',
        r':\(\s*\)',
        r'dd\s+if=.*of=/',
        r'mkfs\.',
        r'fdisk',
        r'format',
        r'chmod\s+000',
        r'chown\s+.*root',
        r'shutdown',
        r'reboot',
        r'init\s+0',
        r'curl.*\|.*sh',  # 下载并执行脚本
        r'wget.*\|.*sh',
    ]

    # 敏感信息关键词
    SENSITIVE_KEYWORDS = [
        'api_key',
        'apikey',
        'secret',
        'password',
        'token',
        'credential',
        'private_key',
        'access_token',
        'auth_token',
        'database_url',
        'connection_string',
    ]

    def __init__(self):
        """初始化安全控制器"""
        self.compile_patterns()

    def compile_patterns(self):
        """编译正则表达式模式"""
        self.dangerous_command_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DANGEROUS_COMMANDS
        ]
        self.sensitive_file_patterns = [
            re.compile(pattern.replace('*', '.*'))
            for pattern in self.SENSITIVE_FILES
        ]

    async def can_use_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        运行时权限控制 - 决定是否允许工具使用

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            context: 上下文信息（用户ID、会话ID等）

        Returns:
            PermissionResultAllow 或 PermissionResultDeny 对象
        """
        try:
            # 1. 检查敏感文件访问
            if tool_name in ['Read', 'Write', 'Edit']:
                file_path = tool_input.get('file_path', '')
                if self._is_sensitive_file(file_path):
                    logger.warning(f"[Security] Blocked access to sensitive file: {file_path}")
                    if PermissionResultDeny:
                        return PermissionResultDeny(
                            message=f"安全保护：无法访问敏感文件 '{Path(file_path).name}'"
                        )
                    else:
                        # Fallback for older SDK
                        return {"behavior": "deny", "message": f"安全保护：无法访问敏感文件 '{Path(file_path).name}'"}

            # 2. 检查危险命令
            if tool_name == 'Bash':
                command = tool_input.get('command', '')
                if self._is_dangerous_command(command):
                    logger.warning(f"[Security] Blocked dangerous command: {command[:100]}")
                    if PermissionResultDeny:
                        return PermissionResultDeny(
                            message="安全保护：此命令具有潜在危险性，已被阻止"
                        )
                    else:
                        return {"behavior": "deny", "message": "安全保护：此命令具有潜在危险性，已被阻止"}

            # 3. 检查敏感信息泄露
            if tool_name in ['Read', 'Grep', 'Glob']:
                for key, value in tool_input.items():
                    if isinstance(value, str) and self._contains_sensitive_keyword(value):
                        logger.warning(f"[Security] Blocked potential sensitive info access: {tool_name}")
                        # 对于敏感信息，我们返回 deny（而不是 ask）
                        if PermissionResultDeny:
                            return PermissionResultDeny(
                                message="安全警告：此操作可能访问敏感信息"
                            )
                        else:
                            return {"behavior": "deny", "message": "安全警告：此操作可能访问敏感信息"}

            # 4. 允许操作
            if PermissionResultAllow:
                return PermissionResultAllow()
            else:
                return {"behavior": "allow"}

        except Exception as e:
            logger.error(f"[Security] Error in can_use_tool: {e}", exc_info=True)
            # 出错时默认拒绝，确保安全
            if PermissionResultDeny:
                return PermissionResultDeny(
                    message=f"安全检查失败：{str(e)}"
                )
            else:
                return {"behavior": "deny", "message": f"安全检查失败：{str(e)}"}

    def _is_sensitive_file(self, file_path: str) -> bool:
        """检查是否为敏感文件"""
        if not file_path:
            return False

        path = Path(file_path)
        file_name = path.name

        # 检查文件名模式
        for pattern in self.sensitive_file_patterns:
            if pattern.match(file_name):
                return True

        # 检查敏感目录
        for part in path.parts:
            if part in self.SENSITIVE_DIRS:
                return True

        # 检查配置文件
        if file_name.endswith('.py') and any(keyword in file_name for keyword in ['config', 'setting', 'secret', 'credential']):
            return True

        return False

    def _is_dangerous_command(self, command: str) -> bool:
        """检查是否为危险命令"""
        if not command:
            return False

        for pattern in self.dangerous_command_patterns:
            if pattern.search(command):
                return True

        return False

    def _contains_sensitive_keyword(self, text: str) -> bool:
        """检查是否包含敏感关键词"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.SENSITIVE_KEYWORDS)

    def sanitize_file_content(self, content: str, file_path: str) -> str:
        """
        清理文件内容中的敏感信息

        Args:
            content: 文件内容
            file_path: 文件路径

        Returns:
            清理后的内容
        """
        if not content:
            return content

        lines = content.split('\n')
        sanitized_lines = []

        for line in lines:
            # 检查是否包含敏感信息
            if self._contains_sensitive_keyword(line):
                # 隐藏敏感值
                sanitized_line = re.sub(
                    r'=["\'](.*?)["\']',
                    r'="***HIDDEN***"',
                    line
                )
                sanitized_lines.append(sanitized_line)
            else:
                sanitized_lines.append(line)

        return '\n'.join(sanitized_lines)


# 全局单例
security_controller = SecurityController()
