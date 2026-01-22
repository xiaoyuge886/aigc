# -*- coding: utf-8 -*-
"""
工具协调指导模块

为Claude提供工具选择和使用指导，确保工具的高效、合理使用。
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ToolCoordinationGuidance:
    """
    工具协调指导器

    为Claude提供：
    1. 工具选择建议
    2. 工具使用顺序指导
    3. 工具组合优化
    4. 参数设置建议
    """

    def __init__(self):
        """初始化工具协调指导器"""
        self.tool_registry = self._initialize_tool_registry()
        self.tool_combinations = self._initialize_tool_combinations()

    def _initialize_tool_registry(self) -> Dict[str, Dict]:
        """初始化工具注册表"""
        return {
            'data_analysis': {
                'name': '数据分析工具',
                'description': '用于数据清洗、统计计算、数据处理',
                'capabilities': [
                    '数据清洗和预处理',
                    '描述性统计计算',
                    '相关性分析',
                    '分组聚合分析',
                    '数据格式转换'
                ],
                'best_for': [
                    '数据质量问题处理',
                    '统计指标计算',
                    '数据特征分析',
                    '数据预处理'
                ],
                'parameters': [
                    {'name': 'operation', 'type': 'string', 'description': '操作类型 (clean, stats, aggregate, correlate)'},
                    {'name': 'columns', 'type': 'list', 'description': '指定分析的列名'},
                    {'name': 'group_by', 'type': 'string', 'description': '分组字段'},
                    {'name': 'filters', 'type': 'dict', 'description': '数据过滤条件'}
                ],
                'output_format': '结构化数据或统计结果',
                'limitations': '不适用于大规模复杂计算和机器学习建模'
            },

            'visualization': {
                'name': '可视化工具',
                'description': '用于创建各种图表和可视化展示',
                'capabilities': [
                    '创建折线图、柱状图、散点图',
                    '生成统计图表',
                    '热力图和相关性图',
                    '时间序列图',
                    '分布图和箱线图'
                ],
                'best_for': [
                    '数据趋势展示',
                    '分布模式可视化',
                    '对比分析展示',
                    '关系探索',
                    '异常值识别'
                ],
                'parameters': [
                    {'name': 'chart_type', 'type': 'string', 'description': '图表类型 (line, bar, scatter, heatmap, histogram)'},
                    {'name': 'x_column', 'type': 'string', 'description': 'X轴数据列'},
                    {'name': 'y_column', 'type': 'string', 'description': 'Y轴数据列'},
                    {'name': 'title', 'type': 'string', 'description': '图表标题'},
                    {'name': 'group_by', 'type': 'string', 'description': '分组字段'}
                ],
                'output_format': '图表文件或可视化对象',
                'limitations': '不适合展示过于复杂的多维关系'
            },

            'search': {
                'name': '搜索工具',
                'description': '用于搜索外部信息和数据',
                'capabilities': [
                    '网络搜索',
                    '数据库查询',
                    '信息检索',
                    '事实核查'
                ],
                'best_for': [
                    '获取最新信息',
                    '补充背景资料',
                    '验证数据准确性',
                    '寻找参考资料'
                ],
                'parameters': [
                    {'name': 'query', 'type': 'string', 'description': '搜索查询关键词'},
                    {'name': 'source', 'type': 'string', 'description': '信息来源限制'},
                    {'name': 'time_range', 'type': 'string', 'description': '时间范围限制'},
                    {'name': 'max_results', 'type': 'integer', 'description': '最大结果数量'}
                ],
                'output_format': '搜索结果列表或摘要信息',
                'limitations': '搜索结果的准确性和时效性依赖外部源'
            },

            'report': {
                'name': '报告生成工具',
                'description': '用于生成结构化分析报告',
                'capabilities': [
                    '生成HTML报告',
                    '创建PDF文档',
                    '格式化文本报告',
                    '图表嵌入',
                    '报告模板应用'
                ],
                'best_for': [
                    '最终结果展示',
                    '正式报告生成',
                    '分析结果汇总',
                    '管理层报告',
                    '自动化报告'
                ],
                'parameters': [
                    {'name': 'format', 'type': 'string', 'description': '报告格式 (html, pdf, markdown)'},
                    {'name': 'template', 'type': 'string', 'description': '报告模板'},
                    {'name': 'sections', 'type': 'list', 'description': '报告章节结构'},
                    {'name': 'include_charts', 'type': 'boolean', 'description': '是否包含图表'}
                ],
                'output_format': '格式化报告文件',
                'limitations': '报告格式和样式受模板限制'
            },

            'file_tool': {
                'name': '文件工具',
                'description': '用于文件读写和数据交换',
                'capabilities': [
                    '读取CSV/Excel文件',
                    '写入数据文件',
                    '文件格式转换',
                    '数据导入导出'
                ],
                'best_for': [
                    '数据文件处理',
                    '结果保存',
                    '格式转换',
                    '批量数据处理'
                ],
                'parameters': [
                    {'name': 'operation', 'type': 'string', 'description': '操作类型 (read, write, convert)'},
                    {'name': 'file_path', 'type': 'string', 'description': '文件路径'},
                    {'name': 'format', 'type': 'string', 'description': '文件格式'},
                    {'name': 'data', 'type': 'object', 'description': '要写入的数据'}
                ],
                'output_format': '文件内容或操作结果',
                'limitations': '受文件大小和格式限制'
            },

            'code_interpreter': {
                'name': '代码解释器',
                'description': '用于执行自定义代码和复杂计算',
                'capabilities': [
                    'Python代码执行',
                    '复杂数学计算',
                    '自定义算法实现',
                    '数据处理脚本',
                    '统计分析'
                ],
                'best_for': [
                    '复杂统计计算',
                    '自定义分析逻辑',
                    '数据处理脚本',
                    '算法实现',
                    '高级建模'
                ],
                'parameters': [
                    {'name': 'code', 'type': 'string', 'description': '要执行的Python代码'},
                    {'name': 'libraries', 'type': 'list', 'description': '需要的Python库'},
                    {'name': 'input_data', 'type': 'object', 'description': '输入数据'},
                    {'name': 'output_format', 'type': 'string', 'description': '输出格式'}
                ],
                'output_format': '代码执行结果或计算结果',
                'limitations': '执行时间和资源限制，无法访问外部服务'
            }
        }

    def _initialize_tool_combinations(self) -> Dict[str, List[Dict]]:
        """初始化工具组合模式"""
        return {
            'sales_analysis': [
                {
                    'phase': '数据准备',
                    'tools': ['file_tool', 'data_analysis'],
                    'description': '读取数据并进行清洗和预处理',
                    'sequence': [
                        {'tool': 'file_tool', 'params': {'operation': 'read', 'format': 'csv'}},
                        {'tool': 'data_analysis', 'params': {'operation': 'clean'}}
                    ]
                },
                {
                    'phase': '基础分析',
                    'tools': ['data_analysis', 'visualization'],
                    'description': '计算基础指标并创建初步图表',
                    'sequence': [
                        {'tool': 'data_analysis', 'params': {'operation': 'stats'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'line', 'x_column': 'date', 'y_column': 'sales'}}
                    ]
                },
                {
                    'phase': '深度分析',
                    'tools': ['data_analysis', 'visualization'],
                    'description': '进行趋势分析和对比分析',
                    'sequence': [
                        {'tool': 'data_analysis', 'params': {'operation': 'correlate'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'bar', 'group_by': 'region'}}
                    ]
                },
                {
                    'phase': '结果输出',
                    'tools': ['report', 'file_tool'],
                    'description': '生成分析报告并保存结果',
                    'sequence': [
                        {'tool': 'report', 'params': {'format': 'html', 'include_charts': True}},
                        {'tool': 'file_tool', 'params': {'operation': 'write', 'format': 'csv'}}
                    ]
                }
            ],

            'customer_analysis': [
                {
                    'phase': '数据整合',
                    'tools': ['file_tool', 'data_analysis'],
                    'description': '整合客户数据并进行质量检查',
                    'sequence': [
                        {'tool': 'file_tool', 'params': {'operation': 'read', 'format': 'csv'}},
                        {'tool': 'data_analysis', 'params': {'operation': 'clean', 'filters': {'customer_id': 'not_null'}}}
                    ]
                },
                {
                    'phase': '行为分析',
                    'tools': ['data_analysis', 'visualization'],
                    'description': '分析客户行为模式和价值分布',
                    'sequence': [
                        {'tool': 'data_analysis', 'params': {'operation': 'aggregate', 'group_by': 'customer_id'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'histogram', 'x_column': 'total_value'}}
                    ]
                },
                {
                    'phase': '分群分析',
                    'tools': ['code_interpreter', 'visualization'],
                    'description': '进行RFM分析和客户分群',
                    'sequence': [
                        {'tool': 'code_interpreter', 'params': {'operation': 'rfm_analysis'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'scatter', 'group_by': 'segment'}}
                    ]
                }
            ],

            'trend_analysis': [
                {
                    'phase': '数据预处理',
                    'tools': ['file_tool', 'data_analysis'],
                    'description': '准备时间序列数据并处理缺失值',
                    'sequence': [
                        {'tool': 'file_tool', 'params': {'operation': 'read'}},
                        {'tool': 'data_analysis', 'params': {'operation': 'clean', 'filters': {'date': 'not_null'}}}
                    ]
                },
                {
                    'phase': '趋势识别',
                    'tools': ['data_analysis', 'visualization'],
                    'description': '识别趋势模式和季节性',
                    'sequence': [
                        {'tool': 'data_analysis', 'params': {'operation': 'trend_analysis'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'line', 'x_column': 'date'}}
                    ]
                },
                {
                    'phase': '预测建模',
                    'tools': ['code_interpreter', 'visualization'],
                    'description': '进行趋势预测和模型评估',
                    'sequence': [
                        {'tool': 'code_interpreter', 'params': {'operation': 'forecasting'}},
                        {'tool': 'visualization', 'params': {'chart_type': 'line', 'include_forecast': True}}
                    ]
                }
            ]
        }

    def get_tool_recommendations(self, problem_type: str, context: Dict = None) -> str:
        """
        获取工具使用建议

        Args:
            problem_type: 问题类型
            context: 上下文信息

        Returns:
            str: 工具使用建议
        """
        recommendations_parts = []

        # 1. 核心工具推荐
        core_tools = self._get_core_tools(problem_type)
        recommendations_parts.append(f"#### 推荐核心工具:")
        for tool in core_tools:
            tool_info = self.tool_registry.get(tool, {})
            recommendations_parts.append(f"- **{tool_info.get('name', tool)}**: {tool_info.get('description', '专业工具')}")

        recommendations_parts.append(f"")

        # 2. 工具使用流程
        workflow = self.tool_combinations.get(problem_type, [])
        if workflow:
            recommendations_parts.append(f"#### 工具使用流程:")
            for phase in workflow:
                recommendations_parts.append(f"")
                recommendations_parts.append(f"**{phase['phase']}**:")
                recommendations_parts.append(f"- **目标**: {phase['description']}")
                recommendations_parts.append(f"- **工具组合**: {', '.join(phase['tools'])}")
                recommendations_parts.append(f"- **关键步骤**:")

                for step in phase['sequence']:
                    tool_name = step['tool']
                    tool_info = self.tool_registry.get(tool_name, {})
                    recommendations_parts.append(f"  1. 使用{tool_info.get('name', tool_name)}: {self._get_step_description(step)}")

        # 3. 工具选择原则
        recommendations_parts.append(f"")
        recommendations_parts.append(f"#### 工具选择原则:")
        recommendations_parts.extend([
            "- **效率优先**: 选择最适合当前任务的工具，避免过度复杂化",
            "- **结果导向**: 专注于获得有价值的分析结果，而不是工具使用本身",
            "- **渐进深入**: 从简单工具开始，根据需要逐步使用更复杂的工具",
            "- **质量控制**: 每个工具的输出都要进行质量检查",
            "- **资源考虑**: 注意执行时间和资源消耗"
        ])

        # 4. 上下文相关建议
        if context:
            contextual_advice = self._get_contextual_tool_advice(problem_type, context)
            if contextual_advice:
                recommendations_parts.append(f"")
                recommendations_parts.append(f"#### 基于上下文的建议:")
                recommendations_parts.append(contextual_advice)

        return "\n".join(recommendations_parts)

    def _get_core_tools(self, problem_type: str) -> List[str]:
        """获取核心工具推荐"""
        core_tools_mapping = {
            'sales_analysis': ['data_analysis', 'visualization', 'report'],
            'customer_analysis': ['data_analysis', 'visualization', 'code_interpreter'],
            'trend_analysis': ['data_analysis', 'visualization', 'code_interpreter'],
            'market_analysis': ['search', 'data_analysis', 'visualization'],
            'financial_analysis': ['data_analysis', 'visualization', 'report'],
            'report_generation': ['report', 'visualization', 'data_analysis'],
            'data_analysis': ['data_analysis', 'visualization'],
            'general_analysis': ['data_analysis', 'visualization', 'search']
        }

        return core_tools_mapping.get(problem_type, ['data_analysis', 'visualization'])

    def _get_step_description(self, step: Dict) -> str:
        """获取步骤描述"""
        params = step['params']
        if params.get('operation'):
            return f"执行{params['operation']}操作"
        elif params.get('chart_type'):
            return f"创建{params['chart_type']}图表"
        else:
            return f"使用工具处理数据"

    def _get_contextual_tool_advice(self, problem_type: str, context: Dict) -> str:
        """获取基于上下文的工具建议"""
        advice = []

        # 数据规模相关建议
        if 'data_size' in context:
            data_size = context['data_size']
            if data_size > 100000:
                advice.append("- **大数据集**: 建议优先使用data_analysis工具进行聚合，避免直接可视化全量数据")
            elif data_size < 1000:
                advice.append("- **小数据集**: 可以直接使用visualization工具进行详细探索")

        # 数据类型相关建议
        if 'data_types' in context:
            data_types = context['data_types']
            if 'text' in data_types:
                advice.append("- **文本数据**: 可能需要使用search工具进行信息补充")
            if 'image' in data_types:
                advice.append("- **图像数据**: 当前工具集对图像数据处理有限，建议转换格式后分析")

        # 复杂度相关建议
        if 'complexity' in context:
            complexity = context['complexity']
            if complexity == 'high':
                advice.append("- **高复杂度任务**: 建议使用code_interpreter实现自定义分析逻辑")
            elif complexity == 'low':
                advice.append("- **低复杂度任务**: 优先使用data_analysis和visualization工具，避免过度工程化")

        # 时间敏感度相关建议
        if 'time_sensitive' in context and context['time_sensitive']:
            advice.append("- **时间敏感任务**: 优先使用执行速度快的工具，如data_analysis，避免复杂的code_interpreter")

        # 外部信息需求
        if 'external_info_needed' in context and context['external_info_needed']:
            advice.append("- **外部信息需求**: 建议早期使用search工具获取背景信息")

        return "\n".join(advice) if advice else ""

    def get_tool_details(self, tool_name: str) -> str:
        """
        获取工具详细说明

        Args:
            tool_name: 工具名称

        Returns:
            str: 工具详细说明
        """
        tool_info = self.tool_registry.get(tool_name)

        if not tool_info:
            return f"工具 '{tool_name}' 不在当前工具库中"

        details_parts = [
            f"### {tool_info['name']}",
            f"",
            f"**描述**: {tool_info['description']}",
            f"",
            f"**主要能力**:"
        ]

        for capability in tool_info['capabilities']:
            details_parts.append(f"- {capability}")

        details_parts.extend([
            f"",
            f"**适用场景**:"
        ])

        for scenario in tool_info['best_for']:
            details_parts.append(f"- {scenario}")

        details_parts.extend([
            f"",
            f"**参数配置**:"
        ])

        for param in tool_info['parameters']:
            details_parts.append(f"- **{param['name']}** ({param['type']}): {param['description']}")

        details_parts.extend([
            f"",
            f"**输出格式**: {tool_info['output_format']}",
            f"",
            f"**限制说明**: {tool_info['limitations']}",
            f"",
            f"**使用建议**:"
        ])

        usage_tips = self._get_tool_usage_tips(tool_name)
        details_parts.extend(usage_tips)

        return "\n".join(details_parts)

    def _get_tool_usage_tips(self, tool_name: str) -> List[str]:
        """获取工具使用技巧"""
        tips_mapping = {
            'data_analysis': [
                "- 先进行数据质量检查，再进行统计计算",
                "- 注意处理缺失值和异常值",
                "- 根据数据类型选择合适的分析方法"
            ],
            'visualization': [
                "- 根据数据特点选择合适的图表类型",
                "- 注意图表的可读性和美观性",
                "- 添加必要的标题和标签"
            ],
            'search': [
                "- 使用具体和准确的搜索关键词",
                "- 限制搜索时间范围获得最新信息",
                "- 验证搜索结果的准确性"
            ],
            'report': [
                "- 选择合适的报告模板和格式",
                "- 确保报告结构的逻辑性",
                "- 包含关键图表和数据支撑"
            ],
            'file_tool': [
                "- 检查文件格式和路径的正确性",
                "- 注意文件大小和读取性能",
                "- 及时关闭文件句柄"
            ],
            'code_interpreter': [
                "- 编写简洁高效的代码",
                "- 添加必要的注释和说明",
                "- 测试关键逻辑和边界条件"
            ]
        }

        return tips_mapping.get(tool_name, ["- 仔细阅读工具说明", "- 根据任务需要配置参数", "- 验证输出结果的正确性"])

    def suggest_optimal_sequence(self, problem_type: str, specific_goals: List[str]) -> str:
        """
        基于特定目标建议最优工具使用序列

        Args:
            problem_type: 问题类型
            specific_goals: 具体目标列表

        Returns:
            str: 优化的工具序列建议
        """
        sequence_parts = [
            "### 针对性工具序列建议",
            f"基于您的具体目标，建议以下优化的工具使用序列：",
            f""
        ]

        # 基于目标调整标准流程
        workflow = self.tool_combinations.get(problem_type, [])

        # 根据具体目标调整
        adjusted_workflow = self._adjust_workflow_for_goals(workflow, specific_goals)

        if adjusted_workflow:
            for i, phase in enumerate(adjusted_workflow, 1):
                sequence_parts.append(f"**步骤{i}: {phase['phase']}**")
                sequence_parts.append(f"- 使用工具: {', '.join(phase['tools'])}")
                sequence_parts.append(f"- 重点: {phase['description']}")

                # 显示关键操作
                if phase['sequence']:
                    sequence_parts.append("- 关键操作:")
                    for step in phase['sequence'][:2]:  # 只显示前2个操作
                        sequence_parts.append(f"  • {self._get_step_description(step)}")
                sequence_parts.append("")

        else:
            # 通用序列
            sequence_parts.extend([
                "1. **数据准备**: file_tool → data_analysis",
                "2. **基础分析**: data_analysis → visualization",
                "3. **深度分析**: 根据需要选择工具",
                "4. **结果输出**: report → file_tool"
            ])

        sequence_parts.extend([
            "#### 优化建议:",
            "- 根据实际执行结果调整工具选择",
            "- 遇到困难时简化工具使用",
            "- 确保每个步骤都有明确的目标输出",
            "- 保持工具使用的逻辑连贯性"
        ])

        return "\n".join(sequence_parts)

    def _adjust_workflow_for_goals(self, workflow: List[Dict], goals: List[str]) -> List[Dict]:
        """根据目标调整工作流程"""
        adjusted = []

        for phase in workflow:
            # 检查这个阶段是否与目标相关
            phase_relevant = False
            for goal in goals:
                if any(keyword in phase['description'].lower() for keyword in goal.lower().split()):
                    phase_relevant = True
                    break

            if phase_relevant or not goals:  # 如果没有特定目标，保持原流程
                adjusted.append(phase)

        return adjusted if adjusted else workflow