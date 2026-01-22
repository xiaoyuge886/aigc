"""
Prompt进化器

核心职责：
1. 将用户偏好融入prompt（只包含关键信息，简洁高效）
2. 将Session偏好融入prompt（只包含关键信息）
3. 组合进化prompt（确保简洁、不冗长）
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PromptEvolver:
    """Prompt进化器 - 将用户偏好融入prompt"""
    
    def __init__(self):
        """初始化Prompt进化器"""
        pass
    
    def evolve_prompt(
        self,
        base_prompt: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        session_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        进化prompt（将偏好融入基础prompt）
        
        核心原则：
        - 简洁高效：只包含关键偏好信息，不冗长
        - 优先级：会话偏好 > 用户偏好
        - 自然融入：偏好信息自然融入prompt，不突兀
        
        Args:
            base_prompt: 基础prompt（系统默认 + 场景层 + 用户层 + 会话层）
            user_preferences: 用户偏好（可选）
            session_preferences: 会话偏好（可选）
            
        Returns:
            str: 进化后的prompt
        """
        evolved_prompt = base_prompt
        
        # 1. 融入用户偏好（如果存在且有意义）
        if user_preferences and self._has_meaningful_preferences(user_preferences):
            user_pref_section = self._format_user_preferences(user_preferences)
            if user_pref_section:
                evolved_prompt = f"{evolved_prompt}\n\n## 用户偏好（长期）\n\n{user_pref_section}"
        
        # 2. 融入会话偏好（如果存在且有意义，优先级高于用户偏好）
        if session_preferences and self._has_meaningful_preferences(session_preferences):
            session_pref_section = self._format_session_preferences(session_preferences)
            if session_pref_section:
                evolved_prompt = f"{evolved_prompt}\n\n## 会话偏好（临时）\n\n{session_pref_section}"
        
        logger.debug(
            f"[PromptEvolver] Prompt进化完成: "
            f"base_length={len(base_prompt)}, "
            f"evolved_length={len(evolved_prompt)}, "
            f"has_user_pref={user_preferences is not None}, "
            f"has_session_pref={session_preferences is not None}"
        )
        
        return evolved_prompt
    
    def _has_meaningful_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        检查偏好是否有意义（不为空）
        
        Args:
            preferences: 偏好字典
            
        Returns:
            bool: 是否有意义
        """
        if not preferences:
            return False
        
        # 检查是否有非空的关键字段
        meaningful_fields = [
            "preferred_scenarios",
            "preferred_style",
            "learned_rules",
            "work_pattern",
            "feedback_stats"
        ]
        
        for field in meaningful_fields:
            value = preferences.get(field)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    return True
                elif isinstance(value, dict) and len(value) > 0:
                    return True
                elif isinstance(value, str) and value.strip():
                    return True
        
        return False
    
    def _format_user_preferences(self, preferences: Dict[str, Any]) -> str:
        """
        格式化用户偏好（只包含关键信息，简洁）
        
        Args:
            preferences: 用户偏好
            
        Returns:
            str: 格式化后的偏好文本
        """
        lines = []
        
        # 1. 常用场景偏好
        preferred_scenarios = preferences.get("preferred_scenarios", [])
        if preferred_scenarios:
            scenarios_str = "、".join(preferred_scenarios[:3])  # 只显示前3个
            lines.append(f"- **常用场景**：{scenarios_str}")
        
        # 2. 回答风格偏好
        preferred_style = preferences.get("preferred_style", "")
        if preferred_style:
            style_map = {
                "detailed": "详细回答",
                "concise": "简洁回答",
                "professional": "专业风格",
                "casual": "轻松风格"
            }
            style_text = style_map.get(preferred_style, preferred_style)
            lines.append(f"- **回答风格**：偏好{style_text}")
        
        # 3. 从反馈中学习的规则（只显示最重要的3条）
        learned_rules = preferences.get("learned_rules", [])
        if learned_rules:
            rules_str = "；".join(learned_rules[:3])  # 只显示前3条
            lines.append(f"- **用户规则**：{rules_str}")
        
        # 4. 工作模式（如果有）
        work_pattern = preferences.get("work_pattern", "")
        if work_pattern and len(work_pattern) < 100:  # 只显示简短的工作模式
            lines.append(f"- **工作模式**：{work_pattern}")
        
        return "\n".join(lines) if lines else ""
    
    def _format_session_preferences(self, preferences: Dict[str, Any]) -> str:
        """
        格式化会话偏好（只包含关键信息，简洁）
        
        Args:
            preferences: 会话偏好
            
        Returns:
            str: 格式化后的偏好文本
        """
        lines = []
        
        # 1. 反馈统计（如果有）
        feedback_stats = preferences.get("feedback_stats", {})
        if feedback_stats:
            like_count = feedback_stats.get("like", 0)
            dislike_count = feedback_stats.get("dislike", 0)
            if like_count > 0 or dislike_count > 0:
                lines.append(f"- **反馈统计**：👍 {like_count}次，👎 {dislike_count}次")
        
        # 2. 最近反馈（如果有）
        recent_feedback = preferences.get("recent_feedback", [])
        if recent_feedback:
            # 只显示最近3条反馈的关键信息
            feedback_summary = []
            for fb in recent_feedback[-3:]:
                fb_type = fb.get("type", "unknown")
                if fb_type == "dislike":
                    feedback_summary.append("用户对回答不满意")
                elif fb_type == "correct":
                    feedback_summary.append("用户纠正了回答")
            
            if feedback_summary:
                lines.append(f"- **最近反馈**：{'; '.join(feedback_summary)}")
        
        return "\n".join(lines) if lines else ""
