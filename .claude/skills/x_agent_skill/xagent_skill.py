# -*- coding: utf-8 -*-
"""
XAgent - Claude智能分析指导Skill

作为Claude Agent SDK的Skill，为Claude模型提供专业的问题解决框架、
分析方法和工具使用指导，而不是直接执行分析逻辑。

架构：
用户查询 → Claude Agent SDK → 加载XAgent Skill → 提供prompt指导 → Claude执行 → 返回结果

核心组件：
- XAgent：主要prompt指导协调器
- SOPPlanningGuidance：SOP规划框架指导
- DataAnalysisGuidance：数据分析方法指导
- ToolCoordinationGuidance：工具协调建议
- DomainExpertiseGuidance：领域专业知识指导

使用：
    from xagent_skill import XAgent

    agent = XAgent()
    result = agent.process_request("分析销售数据趋势", user_id="user_001")
    # result['guidance_prompt'] 包含给Claude的指导prompt
"""

__version__ = "2.0.0"
__author__ = "XAgent Team"
__license__ = "MIT"

# 核心prompt指导协调器
from .guidance.x_agent_core import XAgent, XAgentConfig

# 导入指导模块（用于直接使用）
from .guidance.sop_planning_guidance import SOPPlanningGuidance
from .guidance.data_analysis_guidance import DataAnalysisGuidance
from .guidance.tool_coordination_guidance import ToolCoordinationGuidance
from .guidance.domain_expertise_guidance import DomainExpertiseGuidance
from .guidance.intermediate_file_guidance import IntermediateFileGuidance
from .guidance.dynamic_file_loading_guidance import DynamicFileLoadingGuidance

# 导出主要接口
__all__ = [
    'XAgent',
    'XAgentConfig',
    'SOPPlanningGuidance',
    'DataAnalysisGuidance',
    'ToolCoordinationGuidance',
    'DomainExpertiseGuidance',
    'IntermediateFileGuidance',
    'DynamicFileLoadingGuidance'
]

# 版本信息
def get_version():
    """获取版本信息"""
    return {
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'description': 'Claude智能分析指导Skill - XAgent版本',
        'architecture': 'Prompt-based guidance for Claude Agent SDK',
        'upgrade_note': '从JoyAgent升级到XAgent，提供更强的跨域能力'
    }