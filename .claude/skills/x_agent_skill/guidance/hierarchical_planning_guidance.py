# -*- coding: utf-8 -*-
"""
多层次规划指导模块

实现大计划分解小计划、问题拆解和泛化查询功能，
特别适用于报告写作等复杂任务的规划管理。
"""

from typing import Dict, List, Any, Tuple
import logging
import json
import re

logger = logging.getLogger(__name__)

class HierarchicalPlanningGuidance:
    """
    多层次规划指导器

    核心功能：
    1. 大计划分解小计划（分层规划）
    2. 问题拆解和泛化查询
    3. 任务依赖关系分析
    4. 动态规划调整
    5. 报告写作专门优化
    """

    def __init__(self):
        """初始化多层次规划指导器"""
        self.report_writing_templates = self._initialize_report_templates()
        self.task_decomposition_patterns = self._initialize_decomposition_patterns()
        self.query_generalization_rules = self._initialize_generalization_rules()

    def _initialize_report_templates(self) -> Dict:
        """初始化报告写作模板"""
        return {
            'business_report': {
                'name': '商业分析报告',
                'phases': [
                    {
                        'phase': 'preparation',
                        'title': '准备阶段',
                        'description': '明确报告目标、受众和框架',
                        'subtasks': [
                            {'task': '需求分析', 'estimate': '30分钟'},
                            {'task': '资料收集', 'estimate': '60分钟'},
                            {'task': '框架设计', 'estimate': '30分钟'}
                        ]
                    },
                    {
                        'phase': 'analysis',
                        'title': '分析阶段',
                        'description': '数据分析和洞察发现',
                        'subtasks': [
                            {'task': '数据处理', 'estimate': '90分钟'},
                            {'task': '趋势分析', 'estimate': '60分钟'},
                            {'task': '问题诊断', 'estimate': '60分钟'},
                            {'task': '机会识别', 'estimate': '30分钟'}
                        ]
                    },
                    {
                        'phase': 'writing',
                        'title': '写作阶段',
                        'description': '报告撰写和图表制作',
                        'subtasks': [
                            {'task': '大纲细化', 'estimate': '30分钟'},
                            {'task': '初稿撰写', 'estimate': '120分钟'},
                            {'task': '图表制作', 'estimate': '60分钟'},
                            {'task': '结论建议', 'estimate': '30分钟'}
                        ]
                    },
                    {
                        'phase': 'refinement',
                        'title': '完善阶段',
                        'description': '审核、修改和定稿',
                        'subtasks': [
                            {'task': '内容审核', 'estimate': '45分钟'},
                            {'task': '语言润色', 'estimate': '30分钟'},
                            {'task': '格式调整', 'estimate': '15分钟'},
                            {'task': '最终确认', 'estimate': '15分钟'}
                        ]
                    }
                ]
            },
            'market_research': {
                'name': '市场研究报告',
                'phases': [
                    {
                        'phase': 'market_overview',
                        'title': '市场概览',
                        'description': '市场整体分析',
                        'subtasks': [
                            {'task': '市场规模评估', 'estimate': '60分钟'},
                            {'task': '增长趋势分析', 'estimate': '45分钟'},
                            {'task': '竞争格局分析', 'estimate': '90分钟'}
                        ]
                    },
                    {
                        'phase': 'customer_analysis',
                        'title': '客户分析',
                        'description': '目标客户群体分析',
                        'subtasks': [
                            {'task': '客户画像', 'estimate': '60分钟'},
                            {'task': '需求分析', 'estimate': '45分钟'},
                            {'task': '行为分析', 'estimate': '60分钟'}
                        ]
                    }
                ]
            }
        }

    def _initialize_decomposition_patterns(self) -> Dict:
        """初始化任务分解模式"""
        return {
            'analysis_task': {
                'pattern': r'分析(.+)',
                'subtasks': [
                    '数据收集与验证',
                    '描述性统计分析',
                    '趋势与模式识别',
                    '异常与问题诊断',
                    '因果关系分析',
                    '结论与建议'
                ]
            },
            'report_task': {
                'pattern': r'(.+)报告',
                'subtasks': [
                    '需求调研与目标确认',
                    '资料收集与数据准备',
                    '分析框架设计',
                    '数据分析与洞察',
                    '报告结构设计',
                    '内容撰写',
                    '图表制作',
                    '审核修改'
                ]
            },
            'strategy_task': {
                'pattern': r'制定(.+策略)|(.+规划)',
                'subtasks': [
                    '现状分析',
                    '目标设定',
                    '战略选择',
                    '行动计划',
                    '资源配置',
                    '风险识别',
                    '实施计划'
                ]
            }
        }

    def _initialize_generalization_rules(self) -> List[Dict]:
        """初始化查询泛化规则"""
        return [
            {
                'type': 'domain_expansion',
                'rule': '将具体领域扩展到相关领域',
                'examples': [
                    {'specific': '销售数据分析', 'general': ['市场数据分析', '业绩数据分析', '客户数据分析']},
                    {'specific': '产品优化建议', 'general': ['服务优化建议', '流程优化建议', '体验优化建议']}
                ]
            },
            {
                'type': 'temporal_expansion',
                'rule': '扩展时间维度',
                'examples': [
                    {'specific': '本月销售分析', 'general': ['季度销售分析', '年度销售分析', '同比分析']},
                    {'specific': '当前问题诊断', 'general': ['历史问题回顾', '趋势预测', '周期性分析']}
                ]
            },
            {
                'type': 'perspective_expansion',
                'rule': '多角度思考',
                'examples': [
                    {'specific': '内部效率分析', 'general': ['外部竞争分析', '客户视角分析', '行业标杆分析']},
                    {'specific': '技术实现方案', 'general': ['商业可行性分析', '成本效益分析', '风险评估']}
                ]
            }
        ]

    def create_hierarchical_plan(self, user_query: str, query_type: str = "general") -> Dict:
        """
        创建多层次规划

        Args:
            user_query: 用户查询
            query_type: 查询类型

        Returns:
            Dict: 多层次规划结果
        """
        logger.info(f"创建多层次规划: {user_query}")

        # 1. 识别任务类型和复杂度
        task_info = self._analyze_task_complexity(user_query)

        # 2. 选择合适的规划模板
        planning_template = self._select_planning_template(task_info, query_type)

        # 3. 生成高层次计划（大计划）
        high_level_plan = self._create_high_level_plan(user_query, task_info, planning_template)

        # 4. 分解为子计划（小计划）
        sub_plans = self._decompose_to_sub_plans(high_level_plan, task_info)

        # 5. 生成问题拆解和泛化查询
        query_analysis = self._analyze_and_generalize_query(user_query, task_info)

        # 6. 分析任务依赖关系
        dependencies = self._analyze_task_dependencies(sub_plans)

        return {
            'original_query': user_query,
            'task_complexity': task_info,
            'high_level_plan': high_level_plan,
            'sub_plans': sub_plans,
            'query_analysis': query_analysis,
            'dependencies': dependencies,
            'estimated_timeline': self._estimate_timeline(sub_plans),
            'planning_metadata': {
                'template_used': planning_template.get('name') if planning_template else 'custom',
                'total_subtasks': len(sub_plans),
                'estimated_hours': sum(plan.get('estimated_hours', 0) for plan in sub_plans)
            }
        }

    def _analyze_task_complexity(self, user_query: str) -> Dict:
        """分析任务复杂度"""
        complexity_indicators = {
            'keywords': {
                'high': ['深入', '全面', '详细', '综合', '系统', '多维度', '整体', '完整'],
                'medium': ['分析', '评估', '研究', '调查', '对比'],
                'low': ['简单', '快速', '概览', '摘要', '简要']
            },
            'scope_indicators': {
                'large': ['全公司', '整个市场', '所有部门', '全面覆盖'],
                'medium': ['某个部门', '特定区域', '部分产品'],
                'small': ['单个指标', '具体问题', '特定案例']
            }
        }

        query_lower = user_query.lower()
        complexity_score = 0
        scope_level = 'medium'

        # 分析复杂度关键词
        for level, keywords in complexity_indicators['keywords'].items():
            if any(keyword in query_lower for keyword in keywords):
                if level == 'high':
                    complexity_score += 3
                elif level == 'medium':
                    complexity_score += 2
                else:
                    complexity_score += 1

        # 分析范围关键词
        for level, keywords in complexity_indicators['scope_indicators'].items():
            if any(keyword in query_lower for keyword in keywords):
                scope_level = level
                break

        # 判断复杂度等级
        if complexity_score >= 3 or scope_level == 'large':
            complexity_level = 'high'
        elif complexity_score >= 2 or scope_level == 'medium':
            complexity_level = 'medium'
        else:
            complexity_level = 'low'

        return {
            'complexity_level': complexity_level,
            'complexity_score': complexity_score,
            'scope_level': scope_level,
            'estimated_phases': 3 if complexity_level == 'high' else (2 if complexity_level == 'medium' else 1)
        }

    def _select_planning_template(self, task_info: Dict, query_type: str) -> Dict:
        """选择合适的规划模板"""
        query_lower = query_type.lower()

        # 报告写作类型
        if any(keyword in query_lower for keyword in ['报告', '写作', '报告撰写']):
            return self.report_writing_templates.get('business_report')

        # 市场研究类型
        if any(keyword in query_lower for keyword in ['市场', '调研', '研究']):
            return self.report_writing_templates.get('market_research')

        # 通用分析任务
        if task_info['complexity_level'] == 'high':
            return {
                'name': '复杂项目规划',
                'phases': [
                    {'phase': 'planning', 'title': '规划阶段', 'description': '项目规划和准备'},
                    {'phase': 'execution', 'title': '执行阶段', 'description': '核心任务执行'},
                    {'phase': 'review', 'title': '审查阶段', 'description': '结果审查和优化'}
                ]
            }

        return None

    def _create_high_level_plan(self, user_query: str, task_info: Dict, template: Dict) -> Dict:
        """创建高层次计划（大计划）"""
        if template:
            return {
                'plan_type': 'template_based',
                'plan_title': f"{template['name']} - {user_query}",
                'phases': template['phases'],
                'overall_goal': user_query,
                'success_criteria': self._generate_success_criteria(user_query)
            }
        else:
            # 自定义规划
            phases = []

            if task_info['complexity_level'] == 'high':
                phases = [
                    {'phase': 'preparation', 'title': '准备阶段', 'description': '项目准备和规划'},
                    {'phase': 'analysis', 'title': '分析阶段', 'description': '核心分析工作'},
                    {'phase': 'synthesis', 'title': '整合阶段', 'description': '结果整合和总结'},
                    {'phase': 'presentation', 'title': '呈现阶段', 'description': '结果呈现和建议'}
                ]
            elif task_info['complexity_level'] == 'medium':
                phases = [
                    {'phase': 'analysis', 'title': '分析阶段', 'description': '分析和研究'},
                    {'phase': 'conclusion', 'title': '结论阶段', 'description': '结论和建议'}
                ]
            else:
                phases = [
                    {'phase': 'quick_analysis', 'title': '快速分析', 'description': '快速分析和回答'}
                ]

            return {
                'plan_type': 'custom',
                'plan_title': f"项目规划 - {user_query}",
                'phases': phases,
                'overall_goal': user_query,
                'success_criteria': self._generate_success_criteria(user_query)
            }

    def _decompose_to_sub_plans(self, high_level_plan: Dict, task_info: Dict) -> List[Dict]:
        """分解为子计划（小计划）"""
        sub_plans = []

        for phase in high_level_plan['phases']:
            phase_plan = {
                'phase_id': phase['phase'],
                'phase_title': phase['title'],
                'phase_description': phase['description'],
                'subtasks': [],
                'estimated_hours': 0,
                'deliverables': []
            }

            # 根据阶段类型生成具体子任务
            if phase['phase'] in ['preparation', 'planning']:
                subtasks = [
                    {'task': '明确目标和范围', 'estimated_hours': 1, 'priority': 'high'},
                    {'task': '收集必要资料', 'estimated_hours': 2, 'priority': 'high'},
                    {'task': '制定详细计划', 'estimated_hours': 1, 'priority': 'medium'}
                ]
                deliverables = ['项目章程', '详细计划文档']

            elif phase['phase'] in ['analysis', 'execution', 'quick_analysis']:
                subtasks = [
                    {'task': '数据收集和验证', 'estimated_hours': 2, 'priority': 'high'},
                    {'task': '深入分析研究', 'estimated_hours': 3, 'priority': 'high'},
                    {'task': '问题识别和诊断', 'estimated_hours': 2, 'priority': 'medium'}
                ]
                deliverables = ['分析报告', '问题诊断', '初步发现']

            elif phase['phase'] in ['synthesis', 'conclusion']:
                subtasks = [
                    {'task': '结果整合分析', 'estimated_hours': 2, 'priority': 'high'},
                    {'task': '结论和建议', 'estimated_hours': 1, 'priority': 'high'},
                    {'task': '方案制定', 'estimated_hours': 1, 'priority': 'medium'}
                ]
                deliverables = ['综合报告', '建议方案']

            elif phase['phase'] in ['presentation', 'refinement', 'review']:
                subtasks = [
                    {'task': '报告撰写', 'estimated_hours': 2, 'priority': 'high'},
                    {'task': '图表制作', 'estimated_hours': 1, 'priority': 'medium'},
                    {'task': '审核修改', 'estimated_hours': 1, 'priority': 'medium'}
                ]
                deliverables = ['最终报告', '演示材料']

            else:
                # 通用任务
                subtasks = [
                    {'task': '执行阶段任务', 'estimated_hours': 2, 'priority': 'high'},
                    {'task': '质量检查', 'estimated_hours': 1, 'priority': 'medium'}
                ]
                deliverables = ['阶段成果']

            phase_plan['subtasks'] = subtasks
            phase_plan['estimated_hours'] = sum(task['estimated_hours'] for task in subtasks)
            phase_plan['deliverables'] = deliverables

            sub_plans.append(phase_plan)

        return sub_plans

    def _analyze_and_generalize_query(self, user_query: str, task_info: Dict) -> Dict:
        """分析和泛化查询"""
        # 1. 问题拆解
        problem_breakdown = self._break_down_problem(user_query)

        # 2. 泛化查询
        generalized_queries = self._generalize_query(user_query)

        # 3. 相关问题建议
        related_questions = self._generate_related_questions(user_query, task_info)

        return {
            'original_query': user_query,
            'problem_breakdown': problem_breakdown,
            'generalized_queries': generalized_queries,
            'related_questions': related_questions,
            'query_expansion_suggestions': self._generate_expansion_suggestions(user_query)
        }

    def _break_down_problem(self, user_query: str) -> List[str]:
        """拆解问题"""
        # 基于查询类型进行问题拆解
        breakdown_patterns = {
            'analysis': [
                'What are the key components to analyze?',
                'What data sources are needed?',
                'What analysis methods should be used?',
                'What are the success criteria?'
            ],
            'report': [
                'Who is the target audience?',
                'What is the main message?',
                'What supporting data is needed?',
                'What is the desired outcome?'
            ],
            'strategy': [
                'What is the current situation?',
                'What are the objectives?',
                'What are the constraints?',
                'What are the available resources?'
            ]
        }

        # 判断查询类型
        query_lower = user_query.lower()
        if '分析' in query_lower or 'analysis' in query_lower:
            pattern = breakdown_patterns['analysis']
        elif '报告' in query_lower or 'report' in query_lower:
            pattern = breakdown_patterns['report']
        elif '策略' in query_lower or 'strategy' in query_lower:
            pattern = breakdown_patterns['strategy']
        else:
            pattern = breakdown_patterns['analysis']  # 默认

        return pattern

    def _generalize_query(self, user_query: str) -> List[str]:
        """泛化查询"""
        generalized = []

        # 应用泛化规则
        for rule in self.query_generalization_rules:
            if rule['type'] == 'domain_expansion':
                # 领域扩展
                for example in rule['examples']:
                    if example['specific'] in user_query:
                        generalized.extend(example['general'])
                        break

            elif rule['type'] == 'temporal_expansion':
                # 时间扩展
                time_keywords = ['本月', '本季度', '今年', '当前']
                for keyword in time_keywords:
                    if keyword in user_query:
                        generalized.append(user_query.replace(keyword, '历史同期'))
                        generalized.append(user_query.replace(keyword, '未来趋势'))
                        break

            elif rule['type'] == 'perspective_expansion':
                # 视角扩展
                perspective_keywords = ['内部', '技术', '操作']
                for keyword in perspective_keywords:
                    if keyword in user_query:
                        generalized.append(user_query.replace(keyword, '外部'))
                        generalized.append(user_query.replace(keyword, '客户'))
                        generalized.append(user_query.replace(keyword, '竞争对手'))
                        break

        # 如果没有找到具体的泛化模式，使用通用扩展
        if not generalized:
            generic_expansions = [
                f"{user_query} - 深入分析",
                f"{user_query} - 最佳实践",
                f"{user_query} - 风险评估",
                f"{user_query} - 改进建议"
            ]
            generalized.extend(generic_expansions[:3])

        return list(set(generalized))  # 去重

    def _generate_related_questions(self, user_query: str, task_info: Dict) -> List[str]:
        """生成相关问题"""
        related_questions = []

        # 基于复杂度生成相关问题
        if task_info['complexity_level'] == 'high':
            related_questions.extend([
                f"如何确保{user_query}的质量和准确性？",
                f"{user_query}可能面临哪些风险和挑战？",
                f"有哪些最佳实践可以参考？"
            ])

        # 通用相关问题
        related_questions.extend([
            f"执行{user_query}需要哪些资源？",
            f"如何衡量{user_query}的成功？",
            f"{user_query}的关键影响因素有哪些？"
        ])

        return related_questions[:5]  # 返回最多5个相关问题

    def _generate_expansion_suggestions(self, user_query: str) -> List[str]:
        """生成扩展建议"""
        suggestions = []

        # 分析扩展建议
        if '分析' in user_query:
            suggestions.extend([
                "可以考虑增加对比分析维度",
                "建议加入时间序列分析",
                "可以尝试相关性分析"
            ])

        # 报告扩展建议
        if '报告' in user_query:
            suggestions.extend([
                "建议增加可视化图表",
                "可以考虑加入案例研究",
                "建议提供具体的实施建议"
            ])

        return suggestions

    def _generate_success_criteria(self, user_query: str) -> List[str]:
        """生成成功标准"""
        return [
            "问题得到清晰解答",
            "分析结论有数据支撑",
            "建议具有可操作性",
            "结果满足用户需求"
        ]

    def _analyze_task_dependencies(self, sub_plans: List[Dict]) -> Dict:
        """分析任务依赖关系"""
        dependencies = {
            'sequential': [],
            'parallel': [],
            'critical_path': []
        }

        # 简化的依赖关系分析
        for i, plan in enumerate(sub_plans):
            # 顺序依赖：前一个阶段完成后一个阶段
            if i > 0:
                dependencies['sequential'].append({
                    'from': sub_plans[i-1]['phase_id'],
                    'to': plan['phase_id'],
                    'type': 'finish_to_start'
                })

            # 关键路径：高优先级任务
            high_priority_tasks = [
                task for task in plan['subtasks']
                if task['priority'] == 'high'
            ]

            if high_priority_tasks:
                dependencies['critical_path'].append({
                    'phase': plan['phase_id'],
                    'critical_tasks': [task['task'] for task in high_priority_tasks]
                })

        # 并行任务：同一阶段的某些任务可以并行
        for plan in sub_plans:
            parallel_tasks = [
                task for task in plan['subtasks']
                if task['priority'] == 'medium'
            ]

            if len(parallel_tasks) > 1:
                dependencies['parallel'].append({
                    'phase': plan['phase_id'],
                    'parallel_tasks': [task['task'] for task in parallel_tasks]
                })

        return dependencies

    def _estimate_timeline(self, sub_plans: List[Dict]) -> Dict:
        """估算时间线"""
        total_hours = sum(plan['estimated_hours'] for plan in sub_plans)

        # 考虑并行任务的优化
        parallel_optimization = 0
        for plan in sub_plans:
            medium_priority_tasks = len([task for task in plan['subtasks'] if task['priority'] == 'medium'])
            if medium_priority_tasks > 1:
                # 假设中等优先级任务可以并行，节省20%时间
                parallel_optimization += plan['estimated_hours'] * 0.2

        optimized_hours = total_hours - parallel_optimization

        return {
            'total_estimated_hours': total_hours,
            'optimized_hours': max(optimized_hours, total_hours * 0.7),  # 最少保留70%时间
            'parallel_optimization': parallel_optimization,
            'recommended_working_days': max(1, int(optimized_hours / 8)),  # 假设每天8小时
            'timeline_suggestions': self._generate_timeline_suggestions(total_hours)
        }

    def _generate_timeline_suggestions(self, total_hours: float) -> List[str]:
        """生成时间线建议"""
        if total_hours <= 8:
            return ["可以在1个工作日内完成", "建议安排上午开始，下午完成"]
        elif total_hours <= 24:
            return ["建议在2-3个工作日内完成", "可以分阶段进行，每天安排6-8小时"]
        elif total_hours <= 48:
            return ["建议在一周内完成", "需要合理分配任务，避免后期赶工"]
        else:
            return ["大型项目，建议分阶段交付", "需要制定详细的项目进度计划"]

    def get_planning_guidance_prompt(self, hierarchical_plan: Dict) -> str:
        """生成规划指导prompt"""
        prompt_parts = []

        # 1. 整体规划概览
        prompt_parts.append(f"""## 多层次规划指导

### 整体项目概览
**项目目标**: {hierarchical_plan['original_query']}
**复杂度等级**: {hierarchical_plan['task_complexity']['complexity_level']}
**预计总工时**: {hierarchical_plan['estimated_timeline']['total_estimated_hours']}小时
**建议工作周期**: {hierarchical_plan['estimated_timeline']['recommended_working_days']}天

### 高层次计划（大计划）""")

        # 2. 高层次计划详情
        high_level_plan = hierarchical_plan['high_level_plan']
        for phase in high_level_plan['phases']:
            prompt_parts.append(f"""
**{phase['title']} ({phase['phase']})**
- 目标: {phase['description']}
- 成功标准: {', '.join(high_level_plan.get('success_criteria', []))}
""")

        # 3. 详细子计划（小计划）
        prompt_parts.append("""### 详细子计划（小计划）""")

        for sub_plan in hierarchical_plan['sub_plans']:
            prompt_parts.append(f"""
#### {sub_plan['phase_title']} (预计{sub_plan['estimated_hours']}小时)

**核心任务**:""")

            for task in sub_plan['subtasks']:
                priority_emoji = "🔴" if task['priority'] == 'high' else "🟡" if task['priority'] == 'medium' else "🟢"
                prompt_parts.append(f"- {priority_emoji} {task['task']} (预计{task['estimated_hours']}小时)")

            prompt_parts.append(f"""
**阶段交付物**: {', '.join(sub_plan['deliverables'])}
""")

        # 4. 任务依赖关系
        dependencies = hierarchical_plan['dependencies']
        if dependencies['sequential']:
            prompt_parts.append("""### 任务执行顺序

**必须按顺序执行的任务**:""")
            for dep in dependencies['sequential']:
                prompt_parts.append(f"- {dep['from']} → {dep['to']}")

        if dependencies['critical_path']:
            prompt_parts.append("""### 关键路径

**关键路径上的重要任务**:""")
            for critical in dependencies['critical_path']:
                prompt_parts.append(f"- **{critical['phase']}**: {', '.join(critical['critical_tasks'])}")

        # 5. 问题拆解和扩展分析
        query_analysis = hierarchical_plan['query_analysis']
        prompt_parts.append(f"""### 问题拆解和扩展分析

**需要深入思考的问题**:""")
        for i, question in enumerate(query_analysis['problem_breakdown'], 1):
            prompt_parts.append(f"{i}. {question}")

        if query_analysis['generalized_queries']:
            prompt_parts.append(f"""
**建议考虑的相关分析维度**:""")
            for query in query_analysis['generalized_queries'][:3]:
                prompt_parts.append(f"- {query}")

        # 6. 执行建议
        timeline = hierarchical_plan['estimated_timeline']
        prompt_parts.append(f"""### 执行建议

**时间安排建议**:""")
        for suggestion in timeline['timeline_suggestions']:
            prompt_parts.append(f"- {suggestion}")

        prompt_parts.append(f"""
**执行策略**:
1. 优先完成关键路径上的任务
2. 合理利用并行任务提高效率
3. 定期检查进度，及时调整计划
4. 确保每个阶段的交付物质量
5. 保持与相关方的沟通和反馈

**质量控制要点**:
- 每个阶段完成后进行质量检查
- 确保分析结论有数据支撑
- 保持分析过程的可追溯性
- 及时记录和解决问题
""")

        return "\n".join(prompt_parts)