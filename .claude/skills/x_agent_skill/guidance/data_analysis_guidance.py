# -*- coding: utf-8 -*-
"""
数据分析指导模块

为Claude提供专业的数据分析方法指导，确保分析的科学性和准确性。
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DataAnalysisGuidance:
    """
    数据分析指导器

    为Claude提供：
    1. 不同类型问题的分析方法
    2. 统计技术的正确应用
    3. 数据解读的专业角度
    4. 分析深度的把控建议
    """

    def __init__(self):
        """初始化分析指导器"""
        self.analysis_methods = self._initialize_analysis_methods()

    def _initialize_analysis_methods(self) -> Dict[str, Dict]:
        """初始化分析方法库"""
        return {
            'sales_analysis': {
                'name': '销售业绩分析方法',
                'description': '专业的销售数据分析技术和指标',
                'key_metrics': [
                    '销售额 (Sales Revenue)',
                    '销售量 (Sales Volume)',
                    '平均客单价 (Average Transaction Value)',
                    '销售增长率 (Sales Growth Rate)',
                    '毛利率 (Gross Margin)',
                    '转化率 (Conversion Rate)'
                ],
                'analysis_techniques': [
                    {
                        'technique': '时间序列分析',
                        'description': '分析销售数据的时间趋势',
                        'when_to_use': '当有按时间记录的销售数据时',
                        'key_steps': [
                            '绘制时间序列图识别趋势',
                            '计算移动平均平滑波动',
                            '识别季节性模式',
                            '检测异常值和突变点',
                            '进行趋势分解'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '同比环比分析',
                        'description': '比较不同时间段的销售表现',
                        'when_to_use': '评估业绩增长和周期性变化',
                        'key_steps': [
                            '计算同比增长率 (YoY)',
                            '计算环比增长率 (MoM)',
                            '分析增长驱动因素',
                            '识别周期性模式',
                            '对比预期和实际表现'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '维度分析',
                        'description': '按不同维度分析销售表现',
                        'when_to_use': '了解结构性差异和机会',
                        'key_steps': [
                            '按地区分析销售分布',
                            '按产品分析销售贡献',
                            '按渠道分析销售效率',
                            '按客户群体分析购买行为',
                            '识别高价值维度'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': 'ABC分析',
                        'description': '识别重要产品/客户',
                        'when_to_use': '资源优化和重点管理',
                        'key_steps': [
                            '按销售额排序产品/客户',
                            '计算累计贡献率',
                            '划分ABC三类 (80/20原则)',
                            '分析A类产品/客户特征',
                            '制定差异化策略'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    }
                ],
                'quality_checks': [
                    '数据时间连续性检查',
                    '异常值合理性验证',
                    '统计方法适用性确认',
                    '业务逻辑一致性检查'
                ]
            },

            'customer_analysis': {
                'name': '客户分析方法',
                'description': '客户行为和价值分析技术',
                'key_metrics': [
                    '客户终身价值 (CLV)',
                    '客户获取成本 (CAC)',
                    '客户流失率 (Churn Rate)',
                    '客户满意度 (CSAT)',
                    '净推荐值 (NPS)',
                    '活跃度指标 (DAU/MAU)'
                ],
                'analysis_techniques': [
                    {
                        'technique': 'RFM分析',
                        'description': '基于最近购买、频率、金额的客户分群',
                        'when_to_use': '客户价值分群和精准营销',
                        'key_steps': [
                            '计算Recency (最近购买时间)',
                            '计算Frequency (购买频率)',
                            '计算Monetary (购买金额)',
                            '进行RFM评分和分群',
                            '分析各群体特征和行为'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '客户生命周期分析',
                        'description': '分析客户从获取到流失的全程',
                        'when_to_use': '理解客户旅程和优化体验',
                        'key_steps': [
                            '定义客户生命周期阶段',
                            '计算各阶段转化率',
                            '分析阶段停留时间',
                            '识别流失关键节点',
                            '优化客户旅程'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '留存分析',
                        'description': '分析客户留存和流失模式',
                        'when_to_use': '提升客户保留和满意度',
                        'key_steps': [
                            '计算留存率曲线',
                            '进行同期群分析',
                            '识别流失风险因素',
                            '分析留存驱动因素',
                            '制定保留策略'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    }
                ],
                'quality_checks': [
                    '客户ID唯一性验证',
                    '时间计算准确性检查',
                    '分群逻辑合理性确认',
                    '业务含义一致性验证'
                ]
            },

            'trend_analysis': {
                'name': '趋势分析方法',
                'description': '时间序列趋势识别和预测技术',
                'key_metrics': [
                    '趋势方向',
                    '趋势强度',
                    '季节性幅度',
                    '周期长度',
                    '预测准确度',
                    '置信区间'
                ],
                'analysis_techniques': [
                    {
                        'technique': '移动平均分析',
                        'description': '平滑数据识别长期趋势',
                        'when_to_use': '消除短期波动，看长期趋势',
                        'key_steps': [
                            '选择合适的移动平均窗口',
                            '计算简单或加权移动平均',
                            '比较不同周期的移动平均',
                            '识别趋势转折点',
                            '评估趋势强度'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '季节性分解',
                        'description': '分离趋势、季节性和随机成分',
                        'when_to_use': '理解数据的周期性模式',
                        'key_steps': [
                            '识别季节性周期长度',
                            '进行季节性分解',
                            '分析季节性模式',
                            '评估季节性影响',
                            '调整季节性因素'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    },
                    {
                        'technique': '相关分析',
                        'description': '分析变量间的关系',
                        'when_to_use': '理解影响因素和驱动关系',
                        'key_steps': [
                            '计算相关系数',
                            '绘制散点图',
                            '进行回归分析',
                            '识别强相关变量',
                            '验证因果关系'
                        ],
                        'tools': ['data_analysis', 'visualization']
                    }
                ],
                'quality_checks': [
                    '时间序列平稳性检查',
                    '季节性模式稳定性验证',
                    '预测模型拟合度评估',
                    '外推有效性确认'
                ]
            }
        }

    def get_analysis_methodology(self, problem_type: str, context: Dict = None) -> str:
        """
        获取分析方法指导

        Args:
            problem_type: 问题类型
            context: 上下文信息

        Returns:
            str: 分析方法指导
        """
        method = self.analysis_methods.get(problem_type, self._get_generic_methodology())

        guidance_parts = []

        # 1. 方法介绍
        guidance_parts.append(f"### {method['name']}")
        guidance_parts.append(f"{method['description']}")
        guidance_parts.append(f"")

        # 2. 关键指标
        if 'key_metrics' in method:
            guidance_parts.append(f"#### 关键分析指标:")
            for i, metric in enumerate(method['key_metrics'], 1):
                guidance_parts.append(f"{i}. **{metric}**")
            guidance_parts.append(f"")

        # 3. 分析技术
        if 'analysis_techniques' in method:
            guidance_parts.append(f"#### 推荐分析技术:")

            for technique in method['analysis_techniques']:
                guidance_parts.append(f"")
                guidance_parts.append(f"**{technique['technique']}**")
                guidance_parts.append(f"- **用途**: {technique['description']}")
                guidance_parts.append(f"- **适用场景**: {technique['when_to_use']}")
                guidance_parts.append(f"- **关键步骤**:")
                for step in technique['key_steps']:
                    guidance_parts.append(f"  - {step}")
                guidance_parts.append(f"- **建议工具**: {', '.join(technique['tools'])}")

            guidance_parts.append(f"")

        # 4. 质量检查
        if 'quality_checks' in method:
            guidance_parts.append(f"#### 质量检查要点:")
            for check in method['quality_checks']:
                guidance_parts.append(f"- {check}")
            guidance_parts.append(f"")

        # 5. 上下文相关建议
        if context:
            contextual_guidance = self._get_contextual_guidance(problem_type, context)
            if contextual_guidance:
                guidance_parts.append(f"#### 基于上下文的建议:")
                guidance_parts.append(contextual_guidance)

        return "\n".join(guidance_parts)

    def _get_generic_methodology(self) -> Dict:
        """获取通用分析方法"""
        return {
            'name': '通用数据分析方法',
            'description': '适用于大多数数据分析场景的通用技术',
            'key_metrics': [
                '中心趋势指标 (均值、中位数、众数)',
                '离散程度指标 (标准差、四分位距)',
                '分布形态指标 (偏度、峰度)',
                '相关性指标 (相关系数)',
                '显著性指标 (p值、置信区间)'
            ],
            'analysis_techniques': [
                {
                    'technique': '描述性统计分析',
                    'description': '了解数据的基本特征',
                    'when_to_use': '任何数据分析的起始步骤',
                    'key_steps': [
                        '计算基本统计量 (均值、中位数、标准差)',
                        '分析数据分布形态',
                        '识别异常值',
                        '检查数据质量'
                    ],
                    'tools': ['data_analysis']
                },
                {
                    'technique': '可视化分析',
                    'description': '通过图表直观理解数据',
                    'when_to_use': '探索数据模式和关系',
                    'key_steps': [
                        '选择合适的图表类型',
                        '创建分布图和趋势图',
                        '绘制关系图和对比图',
                        '解读图表含义'
                    ],
                    'tools': ['visualization', 'data_analysis']
                }
            ],
            'quality_checks': [
                '数据代表性检查',
                '统计方法适用性验证',
                '结果合理性确认',
                '结论可靠性评估'
            ]
        }

    def _get_contextual_guidance(self, problem_type: str, context: Dict) -> str:
        """获取基于上下文的指导建议"""
        suggestions = []

        # 数据规模相关建议
        if 'data_size' in context:
            data_size = context['data_size']
            if data_size < 100:
                suggestions.append("- **小数据集提示**: 数据量较少，建议关注数据质量，避免过度解读随机变化")
            elif data_size > 10000:
                suggestions.append("- **大数据集提示**: 数据量充足，可以进行更复杂的统计分析和机器学习建模")

        # 时间范围相关建议
        if 'time_range' in context:
            time_range = context['time_range']
            if time_range > 365:  # 超过一年
                suggestions.append("- **长时间序列**: 可以进行年度对比和季节性分析")
            elif time_range < 30:  # 少于一个月
                suggestions.append("- **短时间序列**: 重点分析近期趋势和波动")

        # 数据类型相关建议
        if 'data_types' in context:
            data_types = context['data_types']
            if 'numerical' in data_types:
                suggestions.append("- **数值数据**: 可以进行各种统计计算和数学建模")
            if 'categorical' in data_types:
                suggestions.append("- **分类数据**: 适合进行分组分析和频率统计")
            if 'temporal' in data_types:
                suggestions.append("- **时间数据**: 可以进行时间序列分析和趋势预测")

        # 业务领域相关建议
        if 'business_domain' in context:
            domain = context['business_domain']
            if domain == 'retail':
                suggestions.append("- **零售业**: 建议重点关注库存周转率、坪效、客流量等指标")
            elif domain == 'technology':
                suggestions.append("- **科技业**: 建议关注用户增长、留存率、产品使用深度等指标")
            elif domain == 'finance':
                suggestions.append("- **金融业**: 建议关注风险控制、合规性、资产质量等指标")

        return "\n".join(suggestions) if suggestions else ""

    def get_technique_details(self, technique_name: str, problem_type: str) -> str:
        """
        获取特定分析技术的详细指导

        Args:
            technique_name: 技术名称
            problem_type: 问题类型

        Returns:
            str: 技术详细指导
        """
        method = self.analysis_methods.get(problem_type, self._get_generic_methodology())

        if 'analysis_techniques' not in method:
            return "分析方法不存在"

        # 查找指定技术
        for technique in method['analysis_techniques']:
            if technique['technique'] == technique_name:
                details_parts = [
                    f"## {technique['technique']} 详细指导",
                    f"",
                    f"**描述**: {technique['description']}",
                    f"",
                    f"**适用场景**: {technique['when_to_use']}",
                    f"",
                    f"### 详细步骤:"
                ]

                for i, step in enumerate(technique['key_steps'], 1):
                    details_parts.append(f"{i}. {step}")

                details_parts.extend([
                    f"",
                    f"### 工具建议:",
                    f"- 推荐使用: {', '.join(technique['tools'])}",
                    f"",
                    f"### 注意事项:",
                    f"- 确保数据满足方法的前提条件",
                    f"- 正确解释分析结果",
                    f"- 结合业务背景进行解读",
                    f"- 验证结果的可靠性"
                ])

                return "\n".join(details_parts)

        return f"技术 '{technique_name}' 在当前分析方法中不存在"

    def suggest_analysis_plan(self, problem_type: str, data_info: Dict) -> str:
        """
        基于数据信息建议分析计划

        Args:
            problem_type: 问题类型
            data_info: 数据信息

        Returns:
            str: 分析计划建议
        """
        plan_parts = [
            "### 个性化分析计划",
            f"基于您的数据特点和问题类型，建议以下分析计划：",
            f""
        ]

        # 根据数据特点推荐技术
        recommended_techniques = self._recommend_techniques(problem_type, data_info)

        plan_parts.append("#### 推荐的分析技术:")
        for i, technique in enumerate(recommended_techniques, 1):
            plan_parts.append(f"{i}. **{technique['name']}** - {technique['reason']}")

        plan_parts.append("")
        plan_parts.append("#### 分析顺序建议:")
        plan_parts.extend([
            "1. **数据准备和验证** - 确保数据质量",
            "2. **基础统计分析** - 了解数据特征",
            "3. **深度分析** - 应用推荐技术",
            "4. **结果验证** - 确保分析可靠性",
            "5. **结论总结** - 形成专业见解"
        ])

        return "\n".join(plan_parts)

    def _recommend_techniques(self, problem_type: str, data_info: Dict) -> List[Dict]:
        """根据数据信息推荐分析技术"""
        recommendations = []

        method = self.analysis_methods.get(problem_type, self._get_generic_methodology())

        for technique in method.get('analysis_techniques', []):
            # 简单的推荐逻辑 (可以根据需要扩展)
            if 'temporal' in data_info.get('features', []):
                if '时间' in technique['description'] or '趋势' in technique['description']:
                    recommendations.append({
                        'name': technique['technique'],
                        'reason': '适合时间序列数据分析'
                    })

            if 'categorical' in data_info.get('features', []):
                if '维度' in technique['description'] or '分组' in technique['description']:
                    recommendations.append({
                        'name': technique['technique'],
                        'reason': '适合分类数据分析'
                    })

        # 如果没有特定推荐，返回前3个技术
        if not recommendations and 'analysis_techniques' in method:
            for technique in method['analysis_techniques'][:3]:
                recommendations.append({
                    'name': technique['technique'],
                    'reason': '通用分析技术，适用于多数场景'
                })

        return recommendations