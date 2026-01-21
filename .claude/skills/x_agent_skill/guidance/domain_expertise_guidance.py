# -*- coding: utf-8 -*-
"""
领域专业知识指导模块

为Claude提供特定领域的专业知识和行业洞察，确保分析的专业性和深度。
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DomainExpertiseGuidance:
    """
    领域专业知识指导器

    为Claude提供：
    1. 行业专业知识
    2. 业务分析框架
    3. 专业术语解释
    4. 行业基准和标准
    5. 专业洞察和建议
    """

    def __init__(self):
        """初始化领域专业知识指导器"""
        self.domain_knowledge = self._initialize_domain_knowledge()
        self.business_frameworks = self._initialize_business_frameworks()
        self.industry_benchmarks = self._initialize_industry_benchmarks()

    def _initialize_domain_knowledge(self) -> Dict[str, Dict]:
        """初始化领域知识库"""
        return {
            'retail': {
                'name': '零售行业',
                'description': '包含传统零售、电商、新零售等',
                'key_metrics': [
                    '销售额 (Sales Revenue)',
                    '同店销售增长 (Same Store Sales Growth)',
                    '坪效 (Sales per Square Foot)',
                    '客流量 (Foot Traffic)',
                    '转化率 (Conversion Rate)',
                    '客单价 (Average Transaction Value)',
                    '库存周转率 (Inventory Turnover)',
                    '毛利率 (Gross Margin)'
                ],
                'analysis_focus': [
                    '销售效率分析',
                    '客户行为分析',
                    '库存管理分析',
                    '渠道效果分析',
                    '促销活动分析'
                ],
                'professional_insights': [
                    '零售业绩受季节性影响显著，需进行同期对比',
                    '线上线下融合是趋势，需要全渠道视角',
                    '客户体验和满意度是关键差异化因素',
                    '供应链效率直接影响盈利能力'
                ],
                'common_pitfalls': [
                    '忽视季节性因素导致误判业绩',
                    '过度关注短期销售而忽视长期客户价值',
                    '库存管理不善导致资金占用',
                    '缺乏全渠道数据整合'
                ]
            },

            'technology': {
                'name': '科技行业',
                'description': '包含软件、硬件、互联网、AI等',
                'key_metrics': [
                    '月活跃用户 (MAU)',
                    '日活跃用户 (DAU)',
                    '用户留存率 (User Retention Rate)',
                    '客户获取成本 (CAC)',
                    '客户终身价值 (LTV)',
                    '付费转化率 (Conversion Rate)',
                    '服务器正常运行时间 (Uptime)',
                    '用户满意度 (CSAT/NPS)'
                ],
                'analysis_focus': [
                    '用户增长和活跃度分析',
                    '产品使用行为分析',
                    '技术性能分析',
                    '商业化分析',
                    '竞争格局分析'
                ],
                'professional_insights': [
                    '用户增长模式通常遵循S曲线，需要识别不同阶段',
                    '技术产品的网络效应很重要，用户规模影响价值',
                    '数据驱动决策是核心竞争力',
                    '技术迭代速度快，需要持续创新投入'
                ],
                'common_pitfalls': [
                    '过度关注用户数量而忽视用户质量',
                    '忽视技术债务和系统稳定性',
                    '商业化过早影响用户体验',
                    '缺乏长期技术路线规划'
                ]
            },

            'finance': {
                'name': '金融行业',
                'description': '包含银行、保险、投资、FinTech等',
                'key_metrics': [
                    '资产回报率 (ROA)',
                    '股东权益回报率 (ROE)',
                    '净息差 (Net Interest Margin)',
                    '不良贷款率 (NPL Ratio)',
                    '成本收入比 (Cost to Income Ratio)',
                    '资本充足率 (Capital Adequacy Ratio)',
                    '流动性覆盖率 (LCR)',
                    '客户满意度指数'
                ],
                'analysis_focus': [
                    '风险管理分析',
                    '盈利能力分析',
                    '资本效率分析',
                    '客户结构分析',
                    '合规性分析'
                ],
                'professional_insights': [
                    '风险管理是金融业的核心，需要全面的风险评估',
                    '监管环境变化对业务影响巨大',
                    '数字化转型是必然趋势',
                    '客户信任和关系维护至关重要'
                ],
                'common_pitfalls': [
                    '忽视系统性风险',
                    '过度追求收益而忽视风险',
                    '合规成本控制不当',
                    '客户数据保护不足'
                ]
            },

            'manufacturing': {
                'name': '制造业',
                'description': '包含传统制造、智能制造、工业4.0等',
                'key_metrics': [
                    '产能利用率 (Capacity Utilization Rate)',
                    '设备综合效率 (OEE)',
                    '库存周转天数 (Days Inventory Outstanding)',
                    '准时交货率 (On-Time Delivery Rate)',
                    '产品质量合格率 (Quality Pass Rate)',
                    '生产效率 (Production Efficiency)',
                    '单位制造成本 (Unit Manufacturing Cost)',
                    '设备故障率 (Equipment Failure Rate)'
                ],
                'analysis_focus': [
                    '生产效率分析',
                    '质量控制分析',
                    '供应链分析',
                    '成本分析',
                    '设备维护分析'
                ],
                'professional_insights': [
                    '精益生产是提升效率的重要方法',
                    '供应链韧性越来越重要',
                    '智能化和自动化是发展趋势',
                    '质量是制造业的生命线'
                ],
                'common_pitfalls': [
                    '忽视预防性维护',
                    '库存管理不当导致资金占用',
                    '质量成本控制不力',
                    '供应链风险意识不足'
                ]
            },

            'healthcare': {
                'name': '医疗健康',
                'description': '包含医院、制药、医疗器械、数字健康等',
                'key_metrics': [
                    '患者满意度 (Patient Satisfaction)',
                    '平均住院日 (Average Length of Stay)',
                    '床位使用率 (Bed Occupancy Rate)',
                    '药品不良反应率 (Adverse Drug Reaction Rate)',
                    '手术成功率 (Surgical Success Rate)',
                    '医疗成本控制 (Medical Cost Control)',
                    '患者再入院率 (Readmission Rate)',
                    '医护人员满意度 (Staff Satisfaction)'
                ],
                'analysis_focus': [
                    '医疗质量分析',
                    '运营效率分析',
                    '成本效益分析',
                    '患者体验分析',
                    '资源配置分析'
                ],
                'professional_insights': [
                    '医疗质量和安全是首要考虑',
                    '数据隐私保护要求极高',
                    '成本控制需要平衡医疗质量',
                    '预防医学和健康管理越来越重要'
                ],
                'common_pitfalls': [
                    '过度医疗导致成本上升',
                    '数据隐私保护不足',
                    '忽视预防和健康管理',
                    '资源分配不合理'
                ]
            }
        }

    def _initialize_business_frameworks(self) -> Dict[str, Dict]:
        """初始化商业分析框架"""
        return {
            'swot_analysis': {
                'name': 'SWOT分析',
                'description': '优势(Strengths)、劣势(Weaknesses)、机会(Opportunities)、威胁(Threats)分析',
                'application': '战略规划和竞争分析',
                'structure': [
                    '内部因素分析 (优势+劣势)',
                    '外部环境分析 (机会+威胁)',
                    'SWOT矩阵构建',
                    '战略建议制定'
                ]
            },

            'porter_five_forces': {
                'name': '波特五力模型',
                'description': '行业竞争结构分析',
                'application': '行业分析和战略定位',
                'structure': [
                    '供应商议价能力分析',
                    '买方议价能力分析',
                    '新进入者威胁分析',
                    '替代品威胁分析',
                    '现有竞争者分析'
                ]
            },

            'value_chain_analysis': {
                'name': '价值链分析',
                'description': '企业价值创造过程分析',
                'application': '运营优化和成本控制',
                'structure': [
                    '主要活动分析 (生产、销售、服务等)',
                    '支持活动分析 (采购、技术、人力资源等)',
                    '价值链优化识别',
                    '竞争优势定位'
                ]
            },

            'bcg_matrix': {
                'name': 'BCG矩阵',
                'description': '产品组合分析',
                'application': '产品战略和资源配置',
                'structure': [
                    '市场份额评估',
                    '市场增长率分析',
                    'BCG矩阵定位',
                    '战略建议制定 (明星、现金牛、问题、瘦狗)'
                ]
            }
        }

    def _initialize_industry_benchmarks(self) -> Dict[str, Dict]:
        """初始化行业基准数据"""
        return {
            'retail': {
                'sales_growth_rate': {'average': 0.08, 'good': 0.15, 'excellent': 0.25},
                'gross_margin': {'average': 0.25, 'good': 0.35, 'excellent': 0.45},
                'inventory_turnover': {'average': 6, 'good': 8, 'excellent': 12},
                'conversion_rate': {'average': 0.03, 'good': 0.05, 'excellent': 0.08}
            },
            'technology': {
                'mau_growth_rate': {'average': 0.10, 'good': 0.20, 'excellent': 0.30},
                'user_retention_rate': {'average': 0.70, 'good': 0.80, 'excellent': 0.90},
                'ltv_cac_ratio': {'average': 2, 'good': 3, 'excellent': 5},
                'churn_rate': {'average': 0.05, 'good': 0.03, 'excellent': 0.01}
            },
            'finance': {
                'roe': {'average': 0.10, 'good': 0.15, 'excellent': 0.20},
                'net_interest_margin': {'average': 0.025, 'good': 0.035, 'excellent': 0.045},
                'cost_income_ratio': {'average': 0.60, 'good': 0.50, 'excellent': 0.40},
                'npl_ratio': {'average': 0.02, 'good': 0.015, 'excellent': 0.01}
            }
        }

    def get_domain_knowledge(self, problem_type: str, context: Dict = None) -> str:
        """
        获取领域专业知识指导

        Args:
            problem_type: 问题类型
            context: 上下文信息

        Returns:
            str: 领域专业知识指导
        """
        # 从上下文或问题类型推断行业领域
        domain = self._infer_domain(context, problem_type)

        if not domain or domain not in self.domain_knowledge:
            return self._get_generic_domain_guidance()

        domain_info = self.domain_knowledge[domain]
        guidance_parts = []

        # 1. 行业介绍
        guidance_parts.append(f"### {domain_info['name']}专业知识")
        guidance_parts.append(f"{domain_info['description']}")
        guidance_parts.append(f"")

        # 2. 关键指标
        if domain_info['key_metrics']:
            guidance_parts.append(f"#### 核心指标:")
            for metric in domain_info['key_metrics']:
                guidance_parts.append(f"- **{metric}**")
            guidance_parts.append(f"")

        # 3. 分析重点
        if domain_info['analysis_focus']:
            guidance_parts.append(f"#### 分析重点:")
            for focus in domain_info['analysis_focus']:
                guidance_parts.append(f"- {focus}")
            guidance_parts.append(f"")

        # 4. 专业洞察
        if domain_info['professional_insights']:
            guidance_parts.append(f"#### 专业洞察:")
            for insight in domain_info['professional_insights']:
                guidance_parts.append(f"- {insight}")
            guidance_parts.append(f"")

        # 5. 常见陷阱
        if domain_info['common_pitfalls']:
            guidance_parts.append(f"#### 注意事项:")
            for pitfall in domain_info['common_pitfalls']:
                guidance_parts.append(f"- 避免{pitfall}")
            guidance_parts.append(f"")

        # 6. 行业基准
        if domain in self.industry_benchmarks:
            guidance_parts.append(self._get_benchmark_guidance(domain))

        return "\n".join(guidance_parts)

    def _infer_domain(self, context: Dict, problem_type: str) -> str:
        """推断行业领域"""
        # 从上下文推断
        if context:
            if 'industry' in context:
                return context['industry'].lower()
            if 'business_domain' in context:
                return context['business_domain'].lower()
            if 'sector' in context:
                return context['sector'].lower()

        # 从问题类型推断
        domain_mapping = {
            'sales_analysis': 'retail',  # 默认零售
            'customer_analysis': 'retail',
            'market_analysis': 'retail',
            'financial_analysis': 'finance',
            'trend_analysis': 'technology',  # 默认科技
            'general_analysis': 'retail'
        }

        return domain_mapping.get(problem_type, 'retail')

    def _get_generic_domain_guidance(self) -> str:
        """获取通用领域指导"""
        return """
### 通用商业分析指导

在缺乏特定行业信息时，建议采用以下通用方法：

#### 分析维度:
- **财务维度**: 盈利能力、效率、成长性
- **客户维度**: 满意度、忠诚度、价值
- **运营维度**: 效率、质量、成本
- **战略维度**: 市场地位、竞争优势、发展潜力

#### 专业原则:
- **数据驱动**: 基于客观数据进行分析
- **业务导向**: 紧密结合业务目标和背景
- **系统性**: 考虑各方面的相互影响
- **可操作性**: 提供具体可行的建议

#### 分析要点:
- 区分相关性和因果关系
- 注意数据的时效性和代表性
- 考虑外部环境的影响
- 识别关键驱动因素
"""

    def _get_benchmark_guidance(self, domain: str) -> str:
        """获取基准指导"""
        benchmarks = self.industry_benchmarks.get(domain, {})
        if not benchmarks:
            return ""

        guidance_parts = ["#### 行业基准对比:"]
        for metric, levels in benchmarks.items():
            guidance_parts.append(f"- **{metric}**:")
            guidance_parts.append(f"  - 行业平均: {self._format_benchmark_value(metric, levels['average'])}")
            guidance_parts.append(f"  - 优秀水平: {self._format_benchmark_value(metric, levels['good'])}")
            guidance_parts.append(f"  - 卓越水平: {self._format_benchmark_value(metric, levels['excellent'])}")

        guidance_parts.append("")
        guidance_parts.append("**基准使用建议**:")
        guidance_parts.append("- 将分析结果与行业基准对比")
        guidance_parts.append("- 识别优势和改进空间")
        guidance_parts.append("- 考虑企业特定情况调整基准")

        return "\n".join(guidance_parts)

    def _format_benchmark_value(self, metric: str, value: float) -> str:
        """格式化基准值"""
        if 'rate' in metric.lower() or 'ratio' in metric.lower():
            return f"{value:.1%}"
        elif 'margin' in metric.lower():
            return f"{value:.1%}"
        elif 'turnover' in metric.lower():
            return f"{value:.1f}次"
        else:
            return f"{value:.2f}"

    def apply_business_framework(self, framework_name: str, analysis_context: Dict) -> str:
        """
        应用商业分析框架

        Args:
            framework_name: 框架名称
            analysis_context: 分析上下文

        Returns:
            str: 框架应用指导
        """
        framework = self.business_frameworks.get(framework_name.lower())

        if not framework:
            return f"框架 '{framework_name}' 不存在。可用框架: {list(self.business_frameworks.keys())}"

        guidance_parts = [
            f"### {framework['name']}应用指导",
            f"",
            f"**用途**: {framework['description']}",
            f"**适用场景**: {framework['application']}",
            f""
        ]

        guidance_parts.append("**分析结构**:")
        for i, step in enumerate(framework['structure'], 1):
            guidance_parts.append(f"{i}. {step}")

        guidance_parts.extend([
            "",
            "**应用建议**:",
            "- 根据具体情况调整框架细节",
            "- 结合数据可用性选择分析重点",
            "- 确保分析结果的逻辑性",
            "- 提供可操作的战略建议"
        ])

        return "\n".join(guidance_parts)

    def get_professional_terms_glossary(self, domain: str = None) -> str:
        """
        获取专业术语解释

        Args:
            domain: 行业领域 (可选)

        Returns:
            str: 专业术语解释
        """
        common_terms = {
            'YOY (Year-over-Year)': '同比，与去年同期比较',
            'MoM (Month-over-Month)': '环比，与上个月比较',
            'MAU (Monthly Active Users)': '月活跃用户数',
            'DAU (Daily Active Users)': '日活跃用户数',
            'CAC (Customer Acquisition Cost)': '客户获取成本',
            'LTV (Lifetime Value)': '客户终身价值',
            'ROI (Return on Investment)': '投资回报率',
            'ROE (Return on Equity)': '股东权益回报率',
            'EBITDA': '息税折旧摊销前利润',
            'KPI (Key Performance Indicator)': '关键绩效指标'
        }

        guidance_parts = ["### 专业术语解释", ""]

        if domain and domain in self.domain_knowledge:
            domain_info = self.domain_knowledge[domain]
            if domain == 'retail':
                domain_specific_terms = {
                    '坪效': '每平方米销售额',
                    'SKU (Stock Keeping Unit)': '库存量单位',
                    'OOS (Out of Stock)': '缺货率',
                    'ATV (Average Transaction Value)': '平均交易额'
                }
            elif domain == 'technology':
                domain_specific_terms = {
                    'Churn Rate': '客户流失率',
                    'Burn Rate': '现金消耗率',
                    'Run Rate': '运行率',
                    'ARR (Annual Recurring Revenue)': '年度经常性收入'
                }
            elif domain == 'finance':
                domain_specific_terms = {
                    'NPL (Non-Performing Loan)': '不良贷款',
                    'LCR (Liquidity Coverage Ratio)': '流动性覆盖率',
                    'Tier 1 Capital': '一级资本',
                    'Net Interest Margin': '净息差'
                }
            else:
                domain_specific_terms = {}

            # 合并通用术语和领域特定术语
            all_terms = {**common_terms, **domain_specific_terms}
        else:
            all_terms = common_terms

        for term, explanation in all_terms.items():
            guidance_parts.append(f"**{term}**: {explanation}")

        return "\n".join(guidance_parts)

    def get_strategic_insights(self, problem_type: str, analysis_results: Dict) -> str:
        """
        基于分析结果提供战略洞察

        Args:
            problem_type: 问题类型
            analysis_results: 分析结果

        Returns:
            str: 战略洞察建议
        """
        domain = self._infer_domain({}, problem_type)
        domain_info = self.domain_knowledge.get(domain, {})

        insights_parts = ["### 战略洞察和建议", ""]

        # 基于问题类型的通用洞察
        problem_insights = self._get_problem_type_insights(problem_type)
        insights_parts.extend(problem_insights)

        # 领域特定洞察
        if domain_info and 'professional_insights' in domain_info:
            insights_parts.extend([
                "",
                "#### 行业专业洞察:",
            ])
            for insight in domain_info['professional_insights']:
                insights_parts.append(f"- {insight}")

        # 行动建议
        insights_parts.extend([
            "",
            "#### 战略建议:",
            "- 制定具体、可衡量的行动计划",
            "- 建立关键指标监控体系",
            - "定期评估和调整策略",
            "- 考虑长期和短期平衡",
            "- 重视风险管理"
        ])

        return "\n".join(insights_parts)

    def _get_problem_type_insights(self, problem_type: str) -> List[str]:
        """获取问题类型相关的洞察"""
        insights_mapping = {
            'sales_analysis': [
                "- 销售分析应关注趋势、结构和效率三个维度",
                "- 考虑季节性因素和外部环境影响",
                "- 结合市场对比分析评价业绩表现"
            ],
            'customer_analysis': [
                "- 客户分析应注重价值和行为两个层面",
                "- 客户满意度和忠诚度是长期成功的关键",
                "- 客户获取成本和终身价值的平衡很重要"
            ],
            'trend_analysis': [
                "- 趋势分析要区分短期波动和长期趋势",
                "- 考虑多个时间维度的对比分析",
                "- 结合外部因素解释趋势变化"
            ],
            'financial_analysis': [
                "- 财务分析要关注盈利能力、效率和风险",
                "- 现金流分析比利润分析更重要",
                "- 行业对比和趋势分析同样重要"
            ]
        }

        return insights_mapping.get(problem_type, ["- 综合考虑定量和定性分析", "- 注重分析结果的可操作性", "- 保持客观和批判性思维"])