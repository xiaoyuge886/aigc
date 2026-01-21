# -*- coding: utf-8 -*-
"""
XAgent指导模块

包含所有为Claude提供prompt指导的核心模块。
"""

from .x_agent_core import XAgent, XAgentConfig
from .sop_planning_guidance import SOPPlanningGuidance
from .data_analysis_guidance import DataAnalysisGuidance
from .tool_coordination_guidance import ToolCoordinationGuidance
from .domain_expertise_guidance import DomainExpertiseGuidance
from .intermediate_file_guidance import IntermediateFileGuidance
from .dynamic_file_loading_guidance import DynamicFileLoadingGuidance

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