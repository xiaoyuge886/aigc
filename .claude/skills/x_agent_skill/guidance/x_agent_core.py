# -*- coding: utf-8 -*-
"""
XAgent核心指导器 - 为Claude模型提供专业分析指导

这是正确的XAgent实现，作为Claude Agent SDK的Skill，
为Claude模型提供SOP规划、数据分析方法论、工具协调等专业指导，
而不是替代Claude执行分析逻辑。

架构：用户查询 → Claude Agent SDK → XAgent Skill → Claude执行 → 返回结果
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

try:
    # 相对导入 (作为包使用时)
    from .sop_planning_guidance import SOPPlanningGuidance
    from .data_analysis_guidance import DataAnalysisGuidance
    from .tool_coordination_guidance import ToolCoordinationGuidance
    from .domain_expertise_guidance import DomainExpertiseGuidance
    from .hierarchical_planning_guidance import HierarchicalPlanningGuidance
    from .intermediate_file_guidance import IntermediateFileGuidance
    from .dynamic_file_loading_guidance import DynamicFileLoadingGuidance
except ImportError:
    # 绝对导入 (独立运行或Jupyter中使用时)
    from sop_planning_guidance import SOPPlanningGuidance
    from data_analysis_guidance import DataAnalysisGuidance
    from tool_coordination_guidance import ToolCoordinationGuidance
    from domain_expertise_guidance import DomainExpertiseGuidance
    from hierarchical_planning_guidance import HierarchicalPlanningGuidance
    from intermediate_file_guidance import IntermediateFileGuidance
    from dynamic_file_loading_guidance import DynamicFileLoadingGuidance

logger = logging.getLogger(__name__)

@dataclass
class XAgentConfig:
    """XAgent配置"""
    enable_sop_guidance: bool = True
    enable_analysis_guidance: bool = True
    enable_tool_coordination: bool = True
    enable_domain_expertise: bool = True
    enable_hierarchical_planning: bool = True
    enable_intermediate_file_management: bool = True  # 中间文件管理
    enable_dynamic_file_loading: bool = True  # 新增：动态文件加载
    prompt_language: str = "zh-CN"  # 支持中文和英文
    detail_level: str = "comprehensive"  # basic, standard, comprehensive

class XAgent:
    """
    XAgent核心 - Claude智能分析指导器

    职责：
    1. 为Claude提供SOP规划框架指导
    2. 提供数据分析方法论建议
    3. 推荐合适的工具和协调策略
    4. 分享领域专业知识和最佳实践
    5. 提供中间文件生成和管理指导
    6. 动态文件系统数据加载指导
    7. 生成结构化的分析指导prompt

    注意：本系统不直接执行分析，而是指导Claude如何执行分析，
    包括如何生成和管理中间文件、动态加载文件数据以支持复杂任务。
    """

    def __init__(self, config: XAgentConfig = None):
        self.config = config or XAgentConfig()
        self.agent_id = f"xagent_{uuid.uuid4().hex[:8]}"

        # 初始化指导模块
        self.sop_guidance = SOPPlanningGuidance() if self.config.enable_sop_guidance else None
        self.analysis_guidance = DataAnalysisGuidance() if self.config.enable_analysis_guidance else None
        self.tool_coordination = ToolCoordinationGuidance() if self.config.enable_tool_coordination else None
        self.domain_expertise = DomainExpertiseGuidance() if self.config.enable_domain_expertise else None
        self.hierarchical_planning = HierarchicalPlanningGuidance() if self.config.enable_hierarchical_planning else None
        self.intermediate_file_guidance = IntermediateFileGuidance() if self.config.enable_intermediate_file_management else None
        self.dynamic_file_loading = DynamicFileLoadingGuidance() if self.config.enable_dynamic_file_loading else None

        # 对话状态管理（简化版）
        self.conversation_states = {}  # user_id -> conversation_state

        logger.info(f"XAgent指导器 {self.agent_id} 初始化完成")

    def process_request(self, user_query: str, user_id: str = "default",
                        session_id: str = "default", context: Dict = None) -> Dict:
        """
        处理用户请求 - 生成给Claude的指导prompt

        这是XAgent的核心功能：基于用户查询，生成专业的分析指导prompt，
        供Claude Agent SDK中的Claude模型使用。
        """
        try:
            logger.info(f"生成Claude指导prompt: {user_query[:50]}...")

            # 1. 分析用户需求和问题类型
            intent_analysis = self._analyze_user_intent(user_query, context)

            # 2. 获取用户对话状态
            conversation_state = self._get_conversation_state(user_id, session_id, user_query)

            # 3. 检查是否需要多层次规划
            hierarchical_plan = None
            planning_guidance = ""

            if self.hierarchical_planning and self._needs_hierarchical_planning(user_query, intent_analysis):
                # 生成多层次规划
                hierarchical_plan = self.hierarchical_planning.create_hierarchical_plan(user_query, intent_analysis['primary_task'])
                planning_guidance = self.hierarchical_planning.get_planning_guidance_prompt(hierarchical_plan)

            # 4. 生成综合指导prompt
            guidance_prompt = self._generate_guidance_prompt(
                user_query, intent_analysis, conversation_state, planning_guidance
            )

            # 5. 推荐工具和方法
            recommendations = self._generate_recommendations(
                user_query, intent_analysis
            )

            # 6. 更新对话状态
            self._update_conversation_state(user_id, session_id, user_query, intent_analysis)

            return {
                'guidance_prompt': guidance_prompt,  # 给Claude的主要指导prompt
                'intent_analysis': intent_analysis,  # 意图分析结果
                'recommended_tools': recommendations['tools'],  # 推荐工具
                'analysis_framework': recommendations['framework'],  # 分析框架建议
                'conversation_state': conversation_state,  # 当前对话状态
                'domain_context': recommendations['domain'],  # 领域上下文
                'hierarchical_plan': hierarchical_plan,  # 多层次规划（如果有）
                'metadata': {
                    'agent_id': self.agent_id,
                    'guidance_version': '2.0.0',
                    'language': self.config.prompt_language,
                    'detail_level': self.config.detail_level,
                    'has_hierarchical_planning': hierarchical_plan is not None
                }
            }

        except Exception as e:
            logger.error(f"生成指导prompt失败: {str(e)}")
            return {
                'guidance_prompt': f"# 错误处理\n\n生成指导prompt时出现错误：{str(e)}\n\n请直接根据用户查询进行处理：{user_query}",
                'error': str(e),
                'agent_id': self.agent_id
            }

    def _analyze_user_intent(self, query: str, context: Dict = None) -> Dict:
        """
        分析用户意图和问题类型
        为后续生成针对性指导提供基础
        """
        intent = {
            'primary_task': 'general_analysis',
            'problem_domain': 'business',
            'complexity_level': 'medium',
            'data_requirements': [],
            'analysis_type': [],
            'output_format': 'report',
            'urgency': 'normal',
            'conversation_stage': 'new_topic'
        }

        query_lower = query.lower()

        # 主要任务识别
        if any(word in query_lower for word in ['分析', '统计', '计算', 'evaluate', 'analyze']):
            intent['primary_task'] = 'data_analysis'
        elif any(word in query_lower for word in ['规划', '计划', 'strategy', 'plan']):
            intent['primary_task'] = 'strategic_planning'
        elif any(word in query_lower for word in ['预测', 'forecast', 'predict']):
            intent['primary_task'] = 'forecasting'
        elif any(word in query_lower for word in ['报告', '总结', 'report', 'summary']):
            intent['primary_task'] = 'reporting'
        elif any(word in query_lower for word in ['问题', '故障', 'troubleshoot', 'problem']):
            intent['primary_task'] = 'problem_solving'

        # 问题领域识别
        if any(word in query_lower for word in ['销售', '营收', 'revenue', 'sales']):
            intent['problem_domain'] = 'sales'
        elif any(word in query_lower for word in ['用户', '客户', 'customer', 'user']):
            intent['problem_domain'] = 'customer'
        elif any(word in query_lower for word in ['市场', '营销', 'marketing', 'market']):
            intent['problem_domain'] = 'marketing'
        elif any(word in query_lower for word in ['财务', '成本', 'finance', 'cost']):
            intent['problem_domain'] = 'finance'
        elif any(word in query_lower for word in ['人力', '员工', 'hr', 'employee']):
            intent['problem_domain'] = 'hr'
        elif any(word in query_lower for word in ['产品', '开发', 'product', 'development']):
            intent['problem_domain'] = 'product'

        # 复杂度评估
        if any(word in query_lower for word in ['详细', '深入', '全面', 'comprehensive', 'detailed']):
            intent['complexity_level'] = 'high'
        elif any(word in query_lower for word in ['简单', '快速', '概览', 'quick', 'simple']):
            intent['complexity_level'] = 'low'

        # 分析类型识别
        if any(word in query_lower for word in ['趋势', 'trend', '变化']):
            intent['analysis_type'].append('trend_analysis')
        if any(word in query_lower for word in ['对比', '比较', 'comparison', 'compare']):
            intent['analysis_type'].append('comparative_analysis')
        if any(word in query_lower for word in ['原因', 'why', '因素', 'factor']):
            intent['analysis_type'].append('causal_analysis')
        if any(word in query_lower for word in ['预测', 'forecast', '未来']):
            intent['analysis_type'].append('predictive_analysis')

        # 数据需求识别
        if any(word in query_lower for word in ['数据', '数据库', 'data', 'database']):
            intent['data_requirements'].append('structured_data')
        if any(word in query_lower for word in ['文件', '文档', 'file', 'document']):
            intent['data_requirements'].append('file_processing')
        if any(word in query_lower for word in ['实时', '当前', 'real-time', 'current']):
            intent['data_requirements'].append('real_time_data')

        # 对话阶段判断
        if context and context.get('history'):
            intent['conversation_stage'] = 'follow_up'

        return intent

    def _needs_hierarchical_planning(self, query: str, intent: Dict) -> bool:
        """判断是否需要多层次规划"""
        # 复杂任务需要多层次规划
        if intent['complexity_level'] == 'high':
            return True

        # 报告写作需要多层次规划
        query_lower = query.lower()
        report_keywords = ['报告', '写作', '撰写', '分析报告', '研究', '规划', '策略']
        if any(keyword in query_lower for keyword in report_keywords):
            return True

        # 多步骤任务
        multi_step_keywords = ['制定', '设计', '实施', '优化', '改进', '全面', '系统']
        if any(keyword in query_lower for keyword in multi_step_keywords):
            return True

        return False

    def _generate_guidance_prompt(self, query: str, intent: Dict, conversation_state: Dict, planning_guidance: str = "") -> str:
        """
        生成给Claude的核心指导prompt

        这是JoyAgent的核心价值：基于专业的分析框架和方法论，
        为Claude提供结构化的分析指导，确保Claude能够：
        1. 遵循标准分析流程
        2. 使用合适的分析方法
        3. 选择最佳的工具组合
        4. 生成专业的分析结果
        """
        prompt_sections = []

        # 1. 角色定义和任务说明
        role_prompt = self._generate_role_guidance(intent)
        prompt_sections.append(role_prompt)

        # 2. 多层次规划指导（如果有）
        if planning_guidance:
            prompt_sections.append(planning_guidance)

        # 3. SOP规划框架指导
        if self.sop_guidance:
            sop_prompt = self.sop_guidance.get_planning_framework(query, intent['primary_task'])
            prompt_sections.append(sop_prompt)

        # 4. 分析方法论指导
        if self.analysis_guidance:
            analysis_prompt = self.analysis_guidance.get_analysis_guidance(
                intent['primary_task'], intent['analysis_type']
            )
            prompt_sections.append(analysis_prompt)

        # 5. 工具协调指导
        if self.tool_coordination:
            tool_prompt = self.tool_coordination.get_tool_coordination_guidance(
                intent['primary_task'], intent['data_requirements']
            )
            prompt_sections.append(tool_prompt)

        # 6. 领域专业知识
        if self.domain_expertise:
            domain_prompt = self.domain_expertise.get_domain_guidance(intent['problem_domain'])
            prompt_sections.append(domain_prompt)

        # 7. 中间文件管理指导（新增）
        if self.intermediate_file_guidance:
            file_prompt = self.intermediate_file_guidance.generate_file_management_prompt(query, intent)
            prompt_sections.append(file_prompt)

        # 8. 动态文件加载指导（新增）
        if self.dynamic_file_loading:
            loading_prompt = self.dynamic_file_loading.generate_file_loading_guidance(query, intent)
            prompt_sections.append(loading_prompt)

        # 9. 对话上下文指导
        context_prompt = self._generate_context_guidance(conversation_state, intent)
        prompt_sections.append(context_prompt)

        # 10. 输出格式指导
        output_prompt = self._generate_output_guidance(intent)
        prompt_sections.append(output_prompt)

        # 组合成完整的指导prompt
        complete_prompt = "\n\n---\n\n".join(prompt_sections)

        # 添加用户原始查询
        complete_prompt += f"\n\n## 用户查询\n\n{query}\n\n请基于以上指导，为用户提供专业的分析和解答。"

        return complete_prompt

    def _generate_role_guidance(self, intent: Dict) -> str:
        """生成角色定义指导"""
        role_mappings = {
            'data_analysis': "数据分析师",
            'strategic_planning': "战略规划师",
            'forecasting': "预测分析师",
            'reporting': "商业报告专家",
            'problem_solving': "问题解决专家"
        }

        role = role_mappings.get(intent['primary_task'], "专业分析师")

        return f"""## 角色定义

你现在是一名{role}，具备以下专业能力：

- **专业知识**：在{intent['problem_domain']}领域拥有深厚的理论知识和实践经验
- **分析能力**：能够运用多种分析方法解决复杂问题
- **工具技能**：熟练掌握数据分析、可视化、报告生成等工具
- **沟通能力**：能够清晰地表达分析过程和结论，并提供可操作的建议

## 分析原则

1. **结构化思维**：采用标准分析框架，确保分析过程逻辑清晰
2. **数据驱动**：基于数据和事实进行分析，避免主观臆测
3. **问题导向**：紧密围绕用户的核心问题展开分析
4. **实用性强**：提供具体、可操作的分析结论和建议"""

    def _generate_context_guidance(self, conversation_state: Dict, intent: Dict) -> str:
        """生成对话上下文指导"""
        context_guidance = "## 对话上下文指导\n\n"

        if intent['conversation_stage'] == 'follow_up':
            context_guidance += """- 这是后续对话，请参考之前的分析内容
- 保持分析的连贯性和一致性
- 可以基于之前的分析结果进行深化
- 避免重复已经分析过的内容\n\n"""
        else:
            context_guidance += """- 这是新的对话主题，请从基础分析开始
- 建立完整的分析框架
- 考虑用户可能的后续问题
- 提供全面而深入的分析\n\n"""

        if conversation_state.get('previous_topics'):
            context_guidance += f"**相关话题**：{', '.join(conversation_state['previous_topics'])}\n\n"

        return context_guidance

    def _generate_output_guidance(self, intent: Dict) -> str:
        """生成输出格式指导"""
        output_guidance = """## 输出格式指导

请按照以下结构组织你的回答：

### 1. 分析概述
简要说明你的分析思路和采用的方法

### 2. 核心分析
- 展示详细的分析过程
- 提供数据支持和分析依据
- 使用清晰的结构和逻辑

### 3. 关键发现
总结分析中的重要发现和洞察

### 4. 结论建议
基于分析结果提供具体的结论和可操作的建议

### 5. 后续方向
如果需要进一步分析，建议可能的方向"""

        if intent['complexity_level'] == 'high':
            output_guidance += "\n\n**高级分析要求**：请确保分析深度足够，包含多个维度的分析和交叉验证。"

        return output_guidance

    def _generate_recommendations(self, query: str, intent: Dict) -> Dict:
        """生成工具和方法推荐"""
        recommendations = {
            'tools': [],
            'framework': '',
            'domain': ''
        }

        # 工具推荐
        if self.tool_coordination:
            recommendations['tools'] = self.tool_coordination.recommend_tools(
                intent['primary_task'], intent['data_requirements']
            )

        # 分析框架推荐
        if self.analysis_guidance:
            recommendations['framework'] = self.analysis_guidance.recommend_framework(
                intent['primary_task'], intent['complexity_level']
            )

        # 领域知识推荐
        if self.domain_expertise:
            recommendations['domain'] = self.domain_expertise.get_domain_context(
                intent['problem_domain']
            )

        return recommendations

    def _get_conversation_state(self, user_id: str, session_id: str, query: str) -> Dict:
        """获取对话状态"""
        key = f"{user_id}:{session_id}"
        return self.conversation_states.get(key, {
            'stage': 'new',
            'previous_topics': [],
            'last_intent': None,
            'message_count': 0
        })

    def _update_conversation_state(self, user_id: str, session_id: str, query: str, intent: Dict):
        """更新对话状态"""
        key = f"{user_id}:{session_id}"

        if key not in self.conversation_states:
            self.conversation_states[key] = {
                'stage': 'ongoing',
                'previous_topics': [],
                'last_intent': None,
                'message_count': 0
            }

        state = self.conversation_states[key]
        state['message_count'] += 1
        state['last_intent'] = intent

        # 提取关键词作为话题
        topic_keywords = self._extract_topic_keywords(query)
        state['previous_topics'].extend(topic_keywords)
        state['previous_topics'] = list(set(state['previous_topics']))[-10:]  # 保留最近10个话题

    def _extract_topic_keywords(self, query: str) -> List[str]:
        """从查询中提取话题关键词"""
        # 简单的关键词提取逻辑
        keywords = []
        business_terms = ['销售', '用户', '市场', '财务', '产品', '运营', '人力资源']

        for term in business_terms:
            if term in query:
                keywords.append(term)

        return keywords[:3]  # 最多返回3个关键词

    def get_health_status(self) -> Dict:
        """获取健康状态"""
        return {
            'agent_id': self.agent_id,
            'status': 'healthy',
            'type': 'guidance_provider',
            'components': {
                'sop_guidance': 'enabled' if self.sop_guidance else 'disabled',
                'analysis_guidance': 'enabled' if self.analysis_guidance else 'disabled',
                'tool_coordination': 'enabled' if self.tool_coordination else 'disabled',
                'domain_expertise': 'enabled' if self.domain_expertise else 'disabled',
                'hierarchical_planning': 'enabled' if self.hierarchical_planning else 'disabled'
            },
            'active_conversations': len(self.conversation_states),
            'config': {
                'language': self.config.prompt_language,
                'detail_level': self.config.detail_level
            }
        }