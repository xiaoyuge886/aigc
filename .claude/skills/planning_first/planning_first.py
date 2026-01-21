# -*- coding: utf-8 -*-
"""
Planning First - Claude思考指导Skill

作为Claude Agent SDK的Skill，为Claude模型提供"先规划、后执行"的
完整思考框架指导，而不是直接执行任务逻辑。

架构：
用户查询 → Claude Agent SDK → PlanningFirst Skill → 提供prompt指导 → Claude执行 → 返回结果

核心特性：
- 强制规划优先：永远不要直接开始行动
- ReAct执行范式：思考-行动-观察循环
- 5阶段协调框架：处理复杂问题
- 3种思维模式：编程/分析/创作

使用：
    from planning_first import PlanningFirst

    agent = PlanningFirst()
    result = agent.process_request("修复登录bug", user_id="user_001")
    # result['guidance_prompt'] 包含给Claude的指导prompt
"""

__version__ = "3.0.0"
__author__ = "AIGC Team"
__license__ = "MIT"

# 核心prompt指导器
try:
    # 相对导入 (作为包使用时)
    from .guidance.planning_first_core import PlanningFirst, PlanningFirstConfig
except ImportError:
    # 绝对导入 (独立运行或测试时)
    from guidance.planning_first_core import PlanningFirst, PlanningFirstConfig

# 导出主要接口
__all__ = [
    'PlanningFirst',
    'PlanningFirstConfig'
]

# 版本信息
def get_version():
    """获取版本信息"""
    return {
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'description': 'Claude思考指导Skill - Planning First版本',
        'architecture': 'Prompt-based guidance for Claude Agent SDK',
        'core_features': [
            '强制规划优先',
            'ReAct执行范式',
            '5阶段协调框架',
            '3种思维模式'
        ]
    }
