# -*- coding: utf-8 -*-
"""
Planning First核心指导器 - 为Claude模型提供"先规划、后执行"的思考指导

这是Planning First的核心实现，作为Claude Agent SDK的Skill，
为Claude模型提供完整的思考框架指导，而不是替代Claude执行任务。

架构：用户查询 → Claude Agent SDK → PlanningFirst Skill → Claude执行 → 返回结果
"""

import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PlanningFirstConfig:
    """Planning First配置"""
    enable_planning_emphasis: bool = True
    enable_react_paradigm: bool = True
    enable_coordination_framework: bool = True
    enable_thinking_modes: bool = True
    prompt_language: str = "zh-CN"

class PlanningFirst:
    """
    Planning First核心 - Claude思考指导器

    职责：
    1. 为Claude提供"先规划、后执行"的思考框架
    2. 提供ReAct执行范式指导（思考-行动-观察循环）
    3. 提供5阶段复杂问题协调框架
    4. 提供3种思维模式指导（编程/分析/创作）
    5. 生成结构化的思考指导prompt

    注意：本系统不直接执行任务，而是指导Claude如何思考和执行任务
    """

    def __init__(self, config: PlanningFirstConfig = None):
        self.config = config or PlanningFirstConfig()
        self.agent_id = f"planning_first_{uuid.uuid4().hex[:8]}"

        # Prompt文件路径
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt_file = self.prompts_dir / "planning_first.md"

        # 验证prompt文件存在
        if not self.prompt_file.exists():
            logger.warning(f"Prompt file not found: {self.prompt_file}, using fallback")

        logger.info(f"Planning First指导器 {self.agent_id} 初始化完成")

    def process_request(
        self,
        user_query: str,
        user_id: str = "default",
        session_id: str = "default",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理用户请求 - 生成给Claude的指导prompt

        这是Planning First的核心功能：基于用户查询，生成完整的思考框架指导prompt，
        供Claude Agent SDK中的Claude模型使用。

        Args:
            user_query: 用户的查询或任务
            user_id: 用户标识
            session_id: 会话标识
            context: 额外的上下文信息

        Returns:
            Dict 包含：
                - guidance_prompt: 给Claude的主要指导prompt（完整内容）
                - user_query: 原始用户查询
                - metadata: 元数据（包含时间戳、用户信息等）
                - planning_emphasis: 规划强调标识
        """
        try:
            logger.info(f"生成Claude思考指导prompt: {user_query[:50]}...")

            # 读取完整的planning_first.md prompt
            if self.prompt_file.exists():
                guidance_prompt = self.prompt_file.read_text(encoding="utf-8")
            else:
                # 使用降级版本
                guidance_prompt = self._get_fallback_prompt()

            # 分析用户查询（简单分析）
            query_analysis = self._analyze_query(user_query)

            # 生成元数据
            metadata = {
                'agent_id': self.agent_id,
                'skill_name': 'planning_first',
                'skill_version': '3.0.0',
                'language': self.config.prompt_language,
                'query_analysis': query_analysis,
                'has_planning_emphasis': self.config.enable_planning_emphasis,
                'has_react_framework': self.config.enable_react_paradigm,
                'has_coordination_framework': self.config.enable_coordination_framework,
                'has_thinking_modes': self.config.enable_thinking_modes,
            }

            return {
                # 核心：完整的指导prompt
                'guidance_prompt': guidance_prompt,

                # 用户查询
                'user_query': user_query,

                # 查询分析
                'query_analysis': query_analysis,

                # 元数据
                'metadata': metadata,

                # 标识
                'planning_emphasis': True,  # 强调规划优先
                'requires_plan': True,       # 要求必须先规划
                'supports_coordination': True,  # 支持协调框架
                'supports_react': True,      # 支持ReAct范式
            }

        except Exception as e:
            logger.error(f"生成指导prompt失败: {str(e)}")
            return {
                'guidance_prompt': self._get_fallback_prompt(),
                'error': str(e),
                'agent_id': self.agent_id
            }

    def _analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        分析用户查询的类型和复杂度

        Args:
            user_query: 用户查询

        Returns:
            查询分析结果
        """
        query_lower = user_query.lower()

        # 简单的关键词检测
        complexity_indicators = {
            "simple": ["解释", "是什么", "如何", "什么是", "说明", "告诉我"],
            "medium": ["修复", "优化", "实现", "添加", "创建", "编写", "分析"],
            "complex": ["设计", "重构", "诊断", "并", "然后", "最后", "完整", "系统"]
        }

        # 检测复杂度
        complexity = "medium"  # 默认中等
        for level, indicators in complexity_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                if level == "simple":
                    complexity = "simple"
                elif level == "complex":
                    complexity = "complex"
                    break  # 复杂度最高，不再检查

        # 检测任务类型
        task_types = {
            "programming": ["代码", "函数", "类", "api", "bug", "测试", "数据库"],
            "analysis": ["分析", "数据", "性能", "日志", "统计", "报告"],
            "writing": ["文档", "报告", "说明", "手册", "readme", "注释"],
            "general": []  # 通用
        }

        task_type = "general"
        for type_name, indicators in task_types.items():
            if any(indicator in query_lower for indicator in indicators):
                task_type = type_name
                break

        return {
            "complexity": complexity,
            "task_type": task_type,
            "query_length": len(user_query),
            "estimated_steps": self._estimate_steps(complexity)
        }

    def _estimate_steps(self, complexity: str) -> int:
        """估算需要的步骤数"""
        steps_map = {
            "simple": 3,
            "medium": 6,
            "complex": 10
        }
        return steps_map.get(complexity, 6)

    def _get_fallback_prompt(self) -> str:
        """降级处理：当读取prompt文件失败时返回简化版本"""
        return """# 任务领导者 - 思考模式指导者

## ⚠️ 最重要的原则

**永远不要直接开始行动！在执行任何任务之前，必须先列出执行计划（Plan）。**

## 📋 执行流程

1️⃣ 理解任务
   - 用户想要什么？
   - 成功的标准是什么？
   - 有什么约束条件？

2️⃣ 列出计划
   📋 执行计划：
   步骤1：[做什么] - [为什么]
   步骤2：[做什么] - [为什么]
   步骤3：[做什么] - [为什么]
   ...

3️⃣ 向用户展示
   📋 我准备这样完成任务：
   [上述计划]
   🤔 这个计划可以吗？

4️⃣ 执行任务
   ✅ 严格按照计划执行
   ✅ 每完成一步，标记进度
   ⚠️ 如果需要调整，说明原因

## 🎯 任务类型

- 编程任务 → 理解需求 → 设计方案 → 实现策略 → 验证标准
- 分析任务 → 收集信息 → 分析方法 → 洞察提取 → 建议方案
- 创作任务 → 构思框架 → 内容创作 → 质量检查

## 💪 开始行动

记住：
1. **先规划，后执行**
2. **向用户展示计划**
3. **严格按照计划执行**

现在，完成用户的任务！
"""

    def get_health_status(self) -> Dict:
        """获取健康状态"""
        return {
            'agent_id': self.agent_id,
            'status': 'healthy',
            'type': 'guidance_provider',
            'config': {
                'language': self.config.prompt_language,
                'enable_planning_emphasis': self.config.enable_planning_emphasis,
                'enable_react_paradigm': self.config.enable_react_paradigm,
                'enable_coordination_framework': self.config.enable_coordination_framework,
                'enable_thinking_modes': self.config.enable_thinking_modes,
            }
        }
