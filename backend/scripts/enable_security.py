#!/usr/bin/env python3
"""
快速启用安全保护

运行此脚本以快速启用系统安全保护功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from loguru import logger


async def enable_security():
    """启用安全保护"""
    print("=" * 60)
    print("🔒 启用系统安全保护")
    print("=" * 60)

    # 1. 检查配置文件
    config_file = project_root / "backend" / "core" / "config.py"
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        return False

    print(f"\n✓ 找到配置文件: {config_file}")

    # 2. 读取当前配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config_content = f.read()

    # 3. 检查是否已经启用
    if "enable_security_control" in config_content and "True" in config_content:
        print("\n✓ 安全控制已启用")
        return True

    # 4. 修改配置
    print("\n正在修改配置...")

    # 修改 permission_mode
    if 'permission_mode = Field(default="acceptEdits"' in config_content:
        config_content = config_content.replace(
            'permission_mode = Field(default="acceptEdits"',
            'permission_mode = Field(default="default"'
        )
        print("  ✓ 修改 permission_mode: acceptEdits → default")

    # 添加安全开关
    if "enable_security_control" not in config_content:
        # 在 permission_mode 后添加
        insert_pos = config_content.find("permission_mode")
        if insert_pos > 0:
            # 找到这一行的结尾
            line_end = config_content.find("\n", insert_pos)
            new_field = '\n    enable_security_control: bool = Field(\n        default=True,\n        description="Enable runtime security control"\n    )'

            # 在下一个字段定义前插入
            next_field = config_content.find("\n    ", line_end + 1)
            if next_field > 0:
                config_content = config_content[:next_field] + new_field + config_content[next_field:]
                print("  ✓ 添加 enable_security_control = True")

    # 5. 备份原文件
    backup_file = config_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"\n✓ 备份原文件: {backup_file}")

    # 6. 写入新配置
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"✓ 更新配置文件: {config_file}")

    # 7. 检查 security_controller
    security_controller_file = project_root / "backend" / "services" / "security_controller.py"
    if not security_controller_file.exists():
        print(f"\n✗ 安全控制器不存在: {security_controller_file}")
        print("  请确保已创建 security_controller.py")
        return False

    print(f"\n✓ 安全控制器存在: {security_controller_file}")

    # 8. 检查 agent_service.py 集成
    agent_service_file = project_root / "backend" / "services" / "agent_service.py"
    with open(agent_service_file, 'r', encoding='utf-8') as f:
        agent_service_content = f.read()

    if "security_controller" in agent_service_content:
        print(f"✓ agent_service.py 已集成安全控制器")
    else:
        print(f"\n⚠ agent_service.py 尚未集成安全控制器")
        print("  请手动集成，参考 devolop_doc/系统安全保护方案.md")

    print("\n" + "=" * 60)
    print("✓ 安全保护启用完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 重启后端服务: pnpm run dev:backend")
    print("2. 测试安全保护:")
    print("   - 询问 AI: '读取 .env 文件'")
    print("   - 应该被阻止")
    print("3. 查看完整文档: devolop_doc/系统安全保护方案.md")
    print()

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(enable_security())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"启用失败: {e}")
        sys.exit(1)
