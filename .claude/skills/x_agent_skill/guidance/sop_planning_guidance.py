# -*- coding: utf-8 -*-
"""
SOP规划指导模块

为Claude提供标准作业程序(SOP)框架，确保分析的系统性、完整性和专业性。
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SOPPlanningGuidance:
    """
    SOP规划指导器

    为Claude提供结构化的问题解决框架，确保：
    1. 分析步骤的系统性和完整性
    2. 不同类型问题的标准化处理流程
    3. 专业分析的深度和广度
    """

    def __init__(self):
        """初始化SOP指导器"""
        self.sop_templates = self._initialize_sop_templates()

    def _initialize_sop_templates(self) -> Dict[str, Dict]:
        """初始化SOP模板库"""
        return {
            'sales_analysis': {
                'name': '销售业绩分析SOP',
                'description': '系统化分析销售数据和业绩表现',
                'keywords': ['销售', '业绩', '收入', '营业额', 'revenue', 'sales'],
                'steps': [
                    {
                        'step': 1,
                        'title': '数据准备与验证',
                        'description': '检查数据完整性、准确性和时效性',
                        'key_questions': [
                            '数据来源是否可靠？',
                            '时间范围是否完整？',
                            '关键字段是否无缺失？'
                        ],
                        'expected_outputs': ['数据质量报告', '缺失值分析', '异常值记录']
                    },
                    {
                        'step': 2,
                        'title': '描述性统计分析',
                        'description': '计算关键指标，了解数据基本特征',
                        'key_questions': [
                            '总体销售规模如何？',
                            '时间趋势是怎样的？',
                            '地区/产品分布如何？'
                        ],
                        'expected_outputs': [
                            '销售总额、平均值统计',
                            '时间序列图表',
                            '维度分布分析'
                        ]
                    },
                    {
                        'step': 3,
                        'title': '趋势与模式分析',
                        'description': '识别增长趋势、季节性模式和异常变化',
                        'key_questions': [
                            '销售增长或下降的趋势？',
                            '是否存在季节性波动？',
                            '哪些时期表现异常？'
                        ],
                        'expected_outputs': [
                            '趋势分析报告',
                            '季节性分解',
                            '异常事件识别'
                        ]
                    },
                    {
                        'step': 4,
                        'title': '对比分析',
                        'description': '不同维度的横向和纵向对比',
                        'key_questions': [
                            '各地区/产品表现如何对比？',
                            '同比、环比变化怎样？',
                            '与目标/预算的差距？'
                        ],
                        'expected_outputs': [
                            '对比分析表格',
                            '排名和份额分析',
                            '目标完成情况'
                        ]
                    },
                    {
                        'step': 5,
                        'title': '因素分析',
                        'description': '识别影响销售表现的关键因素',
                        'key_questions': [
                            '哪些因素驱动销售增长？',
                            '内部和外部因素影响如何？',
                            '相关性最强的因素是什么？'
                        ],
                        'expected_outputs': [
                            '因素相关性分析',
                            '驱动因素排序',
                            '影响程度量化'
                        ]
                    },
                    {
                        'step': 6,
                        'title': '预测与建议',
                        'description': '基于分析结果进行预测和提出建议',
                        'key_questions': [
                            '未来趋势预测如何？',
                            '应该采取什么措施？',
                            '风险和机会是什么？'
                        ],
                        'expected_outputs': [
                            '销售预测报告',
                            '具体行动建议',
                            '风险评估报告'
                        ]
                    }
                ]
            },

            'customer_analysis': {
                'name': '客户分析SOP',
                'description': '全面分析客户行为、价值和满意度',
                'keywords': ['客户', '用户', 'customer', '用户行为', '用户价值'],
                'steps': [
                    {
                        'step': 1,
                        'title': '客户画像构建',
                        'description': '分析客户基本特征和分布',
                        'key_questions': [
                            '客户的基本特征分布？',
                            '客户分层情况如何？',
                            '不同客户群体的特点？'
                        ],
                        'expected_outputs': ['客户人口统计报告', '客户分群分析', '用户画像']
                    },
                    {
                        'step': 2,
                        'title': '行为分析',
                        'description': '分析客户购买行为和使用模式',
                        'key_questions': [
                            '购买频率和金额分布？',
                            '偏好产品和渠道？',
                            '使用时间和路径？'
                        ],
                        'expected_outputs': ['行为模式分析', '偏好统计', '路径分析']
                    },
                    {
                        'step': 3,
                        'title': '价值分析',
                        'description': '评估客户终身价值和贡献度',
                        'key_questions': [
                            '客户价值分布如何？',
                            '高价值客户特征？',
                            '价值变化趋势？'
                        ],
                        'expected_outputs': ['客户价值报告', '价值分层', '价值趋势']
                    },
                    {
                        'step': 4,
                        'title': '满意度分析',
                        'description': '分析客户满意度和反馈',
                        'key_questions': [
                            '整体满意度水平？',
                            '影响满意度的关键因素？',
                            '不满意的主要原因？'
                        ],
                        'expected_outputs': ['满意度报告', '影响因素分析', '改进建议']
                    },
                    {
                        'step': 5,
                        'title': '流失分析',
                        'description': '识别流失风险和原因',
                        'key_questions': [
                            '客户流失率如何？',
                            '流失的预警信号？',
                            '流失的主要原因？'
                        ],
                        'expected_outputs': ['流失率分析', '风险预警', '原因分析']
                    }
                ]
            },

            'data_analysis': {
                'name': '通用数据分析SOP',
                'description': '标准的数据分析流程',
                'keywords': ['数据', '分析', '统计', '报告'],
                'steps': [
                    {
                        'step': 1,
                        'title': '数据理解',
                        'description': '理解数据背景和分析目标',
                        'key_questions': [
                            '数据的业务含义？',
                            '分析目标是什么？',
                            '数据的局限性？'
                        ],
                        'expected_outputs': ['数据说明文档', '分析目标明确', '局限性识别']
                    },
                    {
                        'step': 2,
                        'title': '数据质量评估',
                        'description': '检查数据质量和完整性',
                        'key_questions': [
                            '数据是否完整？',
                            '是否存在异常值？',
                            '数据是否准确？'
                        ],
                        'expected_outputs': ['质量评估报告', '问题清单', '清洗建议']
                    },
                    {
                        'step': 3,
                        'title': '探索性分析',
                        'description': '初步探索数据特征和关系',
                        'key_questions': [
                            '数据的基本统计特征？',
                            '变量间的关系？',
                            '是否有明显模式？'
                        ],
                        'expected_outputs': ['统计摘要', '关系分析', '模式发现']
                    },
                    {
                        'step': 4,
                        'title': '深度分析',
                        'description': '根据目标进行深入分析',
                        'key_questions': [
                            '关键发现是什么？',
                            '假设是否成立？',
                            '深层含义如何？'
                        ],
                        'expected_outputs': ['深度分析报告', '关键发现', '洞察总结']
                    },
                    {
                        'step': 5,
                        'title': '结果验证',
                        'description': '验证分析结果的可靠性',
                        'key_questions': [
                            '结果是否可靠？',
                            '方法是否恰当？',
                            '结论是否有支撑？'
                        ],
                        'expected_outputs': ['验证报告', '可靠性评估', '结论确认']
                    }
                ]
            }
        }

    def get_planning_framework(self, user_query: str, problem_type: str) -> str:
        """
        获取规划框架指导

        Args:
            user_query: 用户查询
            problem_type: 问题类型

        Returns:
            str: 规划框架指导
        """
        # 选择最匹配的SOP模板
        sop_template = self._select_sop_template(problem_type)

        if not sop_template:
            return self._get_generic_framework()

        # 生成框架指导
        framework_parts = []

        # 1. SOP介绍
        framework_parts.append(f"### {sop_template['name']}")
        framework_parts.append(f"{sop_template['description']}")
        framework_parts.append(f"")

        # 2. 分析步骤
        framework_parts.append(f"#### 分析步骤：")
        framework_parts.append(f"")

        for step in sop_template['steps']:
            framework_parts.append(f"**步骤{step['step']}: {step['title']}**")
            framework_parts.append(f"- **目标**: {step['description']}")

            if step['key_questions']:
                framework_parts.append(f"- **关键问题**:")
                for question in step['key_questions']:
                    framework_parts.append(f"  - {question}")

            if step['expected_outputs']:
                framework_parts.append(f"- **预期输出**:")
                for output in step['expected_outputs']:
                    framework_parts.append(f"  - {output}")

            framework_parts.append(f"")

        # 3. 执行原则
        framework_parts.append(f"#### 执行原则：")
        framework_parts.append(f"- 按步骤顺序执行，确保完整性")
        framework_parts.append(f"- 每个步骤都要有明确的分析结果")
        framework_parts.append(f"- 注意步骤间的逻辑关系和数据衔接")
        framework_parts.append(f"- 根据实际需要可以适当调整和扩展")
        framework_parts.append(f"")

        # 4. 灵活性提示
        framework_parts.append(f"#### 灵活性提示：")
        framework_parts.append(f"- 根据数据情况和分析深度，可以合并或拆分步骤")
        framework_parts.append(f"- 重点回答每个步骤的关键问题")
        framework_parts.append(f"- 确保最终输出包含所有预期结果")

        return "\n".join(framework_parts)

    def _select_sop_template(self, problem_type: str) -> Dict:
        """选择最匹配的SOP模板"""
        # 直接匹配
        if problem_type in self.sop_templates:
            return self.sop_templates[problem_type]

        # 模糊匹配
        mapping = {
            'sales_analysis': 'sales_analysis',
            'customer_analysis': 'customer_analysis',
            'market_analysis': 'sales_analysis',  # 可以复用销售分析框架
            'financial_analysis': 'data_analysis',  # 可以复用数据分析框架
            'trend_analysis': 'data_analysis',
            'report_generation': 'data_analysis'
        }

        return self.sop_templates.get(mapping.get(problem_type, 'data_analysis'))

    def _get_generic_framework(self) -> str:
        """获取通用分析框架"""
        return """
#### 通用分析框架

**步骤1: 问题理解**
- 明确分析目标和业务背景
- 识别关键成功指标
- 确定分析范围和约束

**步骤2: 数据评估**
- 检查数据质量和完整性
- 识别数据局限性和风险
- 准备数据清洗计划

**步骤3: 探索分析**
- 计算基本统计指标
- 识别数据模式和关系
- 发现初步洞察

**步骤4: 深度分析**
- 根据具体问题进行深入分析
- 运用适当的分析方法
- 验证假设和发现

**步骤5: 结果总结**
- 整合分析发现
- 提供专业见解
- 给出可操作建议

**执行原则：**
- 确保分析的逻辑性和系统性
- 注重数据的准确性和分析的可靠性
- 提供清晰、可操作的结论和建议
"""

    def get_step_guidance(self, step_number: int, problem_type: str) -> str:
        """
        获取特定步骤的详细指导

        Args:
            step_number: 步骤编号
            problem_type: 问题类型

        Returns:
            str: 步骤指导
        """
        sop_template = self._select_sop_template(problem_type)
        if not sop_template:
            return "请参考通用分析框架"

        # 查找指定步骤
        for step in sop_template['steps']:
            if step['step'] == step_number:
                guidance_parts = [
                    f"### 步骤{step['step']}: {step['title']}",
                    f"",
                    f"**目标**: {step['description']}",
                    f""
                ]

                if step['key_questions']:
                    guidance_parts.append("**需要回答的关键问题**:")
                    for i, question in enumerate(step['key_questions'], 1):
                        guidance_parts.append(f"{i}. {question}")
                    guidance_parts.append("")

                if step['expected_outputs']:
                    guidance_parts.append("**预期产出**:")
                    for output in step['expected_outputs']:
                        guidance_parts.append(f"- {output}")
                    guidance_parts.append("")

                guidance_parts.append("**注意事项**:")
                guidance_parts.append("- 确保分析的深度和专业性")
                guidance_parts.append("- 使用适当的工具和方法")
                guidance_parts.append("- 为下一步分析提供基础")

                return "\n".join(guidance_parts)

        return f"步骤{step_number}不存在，请检查步骤编号"

    def customize_sop(self, problem_type: str, custom_steps: List[Dict]) -> str:
        """
        自定义SOP步骤

        Args:
            problem_type: 问题类型
            custom_steps: 自定义步骤

        Returns:
            str: 自定义SOP指导
        """
        framework_parts = [
            f"### 自定义{problem_type}分析框架",
            f""
        ]

        for i, step in enumerate(custom_steps, 1):
            framework_parts.append(f"**步骤{i}: {step.get('title', f'分析步骤{i}')}**")
            framework_parts.append(f"- **目标**: {step.get('description', '执行分析任务')}")

            if 'key_questions' in step:
                framework_parts.append(f"- **关键问题**: {', '.join(step['key_questions'])}")

            if 'expected_outputs' in step:
                framework_parts.append(f"- **预期输出**: {', '.join(step['expected_outputs'])}")

            framework_parts.append("")

        return "\n".join(framework_parts)