"""Skill 管理服务

提供预定义的 agent skill prompts，让 Claude 具备不同能力。
"""
from pathlib import Path
from typing import Optional
from loguru import logger


class SkillManager:
    """Skill 管理器

    职责：
    1. 加载和管理预定义的 skill prompts
    2. 为不同类型的任务提供合适的 system prompt
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """初始化 Skill Manager

        Args:
            prompts_dir: skill prompts 文件目录
        """
        if prompts_dir is None:
            # 默认使用 backend/prompts 目录
            current_dir = Path(__file__).parent.parent.parent
            prompts_dir = current_dir / "prompts"

        self.prompts_dir = Path(prompts_dir)
        logger.info(f"SkillManager initialized with prompts_dir: {self.prompts_dir}")

    def get_skill(self, skill_name: str) -> str:
        """获取 skill prompt

        优先从 .claude/skills/ 目录加载（SDK 标准位置），
        如果找不到，再从 prompts/ 目录加载（向后兼容）。

        Args:
            skill_name: skill 名称（如 "meta_agent", "intelligent_agent", "coder", "analyst"）

        Returns:
            str: skill prompt 内容
        """
        # 优先从 .claude/skills/ 目录加载（SDK 标准位置）
        current_dir = Path(__file__).parent.parent.parent
        claude_skills_dir = current_dir / ".claude" / "skills" / skill_name / "SKILL.md"
        
        if claude_skills_dir.exists():
            try:
                content = claude_skills_dir.read_text(encoding="utf-8")
                logger.info(f"Loaded skill from .claude/skills/: {skill_name} ({len(content)} chars)")
                return content
            except Exception as e:
                logger.warning(f"Failed to load skill from .claude/skills/: {e}")

        # 备用：从 prompts/ 目录加载（向后兼容）
        prompt_file = self.prompts_dir / f"{skill_name}.md"
        if prompt_file.exists():
            try:
                content = prompt_file.read_text(encoding="utf-8")
                logger.info(f"Loaded skill from prompts/: {skill_name} ({len(content)} chars)")
                return content
            except Exception as e:
                logger.warning(f"Failed to load skill from prompts/: {e}")

        # 如果都找不到，使用默认
        logger.warning(f"Skill file not found: {skill_name}, using default")
        return self._get_default_skill()

    def _get_default_skill(self) -> str:
        """获取默认 skill prompt（使用 leader_agent_v3）"""
        # 优先使用 leader_agent_v3（思考指导版本）
        leader_v3_file = self.prompts_dir / "leader_agent_v3.md"
        if leader_v3_file.exists():
            try:
                content = leader_v3_file.read_text(encoding="utf-8")
                logger.info("Using leader_agent_v3 as default skill (thinking guidance mode)")
                return content
            except Exception:
                pass

        # 备用：使用 leader_agent
        leader_file = self.prompts_dir / "leader_agent.md"
        if leader_file.exists():
            try:
                return leader_file.read_text(encoding="utf-8")
            except Exception:
                pass

        # 最后备用：返回内置的简单 prompt
        return """你是一个强大的 AI 助手，具备自主规划和执行任务的能力。

核心能力：
1. 任务理解 - 仔细理解用户需求
2. 自主规划 - 根据任务复杂度决定是否需要分解步骤
3. 工具使用 - 根据需要选择合适的工具（Read、Write、Bash、Grep、Glob）
4. 自我检查 - 持续验证结果，发现错误及时调整

使用 ReAct 范式（推理-行动-观察-反思）循环执行任务，确保准确完成用户目标。"""


# 全局单例
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """获取 SkillManager 单例"""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager
