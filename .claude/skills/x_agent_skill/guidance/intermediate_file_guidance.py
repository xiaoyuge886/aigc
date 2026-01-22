# -*- coding: utf-8 -*-
"""
中间文件管理指导模块

为Claude提供中间文件生成和管理的专业指导，确保复杂分析任务的
中间结果能够被有效保存、组织和利用。
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class IntermediateFileGuidance:
    """
    中间文件管理指导器

    为Claude提供：
    1. 中间文件生成策略
    2. 文件命名和组织规范
    3. 任务历史记录管理
    4. 基于中间结果的最终整合方法
    """

    def __init__(self):
        """初始化中间文件管理指导器"""
        self.file_strategies = self._initialize_file_strategies()

    def _initialize_file_strategies(self) -> Dict[str, Dict]:
        """初始化文件管理策略"""
        return {
            'data_analysis': {
                'description': '数据分析任务的中间文件管理',
                'intermediate_files': [
                    {
                        'file_type': 'data_cleaning_log',
                        'filename_template': 'step1_data_cleaning_{timestamp}.md',
                        'description': '数据清洗过程记录',
                        'content_structure': [
                            '原始数据概况',
                            '数据质量问题识别',
                            '清洗步骤和方法',
                            '清洗后数据统计'
                        ]
                    },
                    {
                        'file_type': 'descriptive_analysis',
                        'filename_template': 'step2_descriptive_analysis_{timestamp}.csv',
                        'description': '描述性统计分析结果',
                        'content_structure': [
                            '基础统计指标',
                            '数据分布情况',
                            '趋势分析结果',
                            '异常值识别'
                        ]
                    },
                    {
                        'file_type': 'correlation_analysis',
                        'filename_template': 'step3_correlation_analysis_{timestamp}.csv',
                        'description': '相关性分析结果',
                        'content_structure': [
                            '相关性矩阵',
                            '显著相关性',
                            '关键发现',
                            '可视化建议'
                        ]
                    },
                    {
                        'file_type': 'predictive_models',
                        'filename_template': 'step4_predictive_models_{timestamp}.json',
                        'description': '预测模型结果',
                        'content_structure': [
                            '模型参数',
                            '预测结果',
                            '模型评估指标',
                            '置信区间'
                        ]
                    }
                ],
                'final_integration': {
                    'method': 'synthesize_from_intermediate',
                    'description': '基于所有中间文件生成最终报告',
                    'integration_steps': [
                        '读取所有中间文件',
                        '提取关键发现和洞察',
                        '整合分析结论',
                        '生成结构化报告'
                    ]
                }
            },
            'report_generation': {
                'description': '报告写作任务的中间文件管理',
                'intermediate_files': [
                    {
                        'file_type': 'research_notes',
                        'filename_template': 'research_notes_{topic}_{timestamp}.md',
                        'description': '研究笔记和数据收集记录',
                        'content_structure': [
                            '数据源清单',
                            '关键信息摘录',
                            '初步发现',
                            '需要进一步验证的问题'
                        ]
                    },
                    {
                        'file_type': 'outline_draft',
                        'filename_template': 'outline_{report_type}_{timestamp}.md',
                        'description': '报告大纲草稿',
                        'content_structure': [
                            '执行摘要要点',
                            '主要章节结构',
                            '关键论点和论据',
                            '图表需求规划'
                        ]
                    },
                    {
                        'file_type': 'section_drafts',
                        'filename_template': 'section_{section_name}_{timestamp}.md',
                        'description': '各章节草稿',
                        'content_structure': [
                            '章节标题',
                            '核心内容',
                            '支撑数据',
                            '图表引用'
                        ]
                    },
                    {
                        'file_type': 'chart_data',
                        'filename_template': 'chart_data_{chart_id}_{timestamp}.csv',
                        'description': '图表数据文件',
                        'content_structure': [
                            '图表标题',
                            '数据系列',
                            '坐标轴标签',
                            '数据表格'
                        ]
                    }
                ]
            }
        }

    def generate_file_management_guidance(self, task_type: str, complexity_level: str) -> Dict[str, Any]:
        """
        生成中间文件管理指导

        Args:
            task_type: 任务类型 (data_analysis, report_generation, etc.)
            complexity_level: 复杂度级别 (simple, medium, complex)

        Returns:
            中间文件管理指导
        """
        strategy = self.file_strategies.get(task_type, self.file_strategies['data_analysis'])

        guidance = {
            'file_management_principle': self._get_file_management_principle(),
            'naming_conventions': self._get_naming_conventions(),
            'intermediate_files_strategy': self._adapt_strategy_for_complexity(
                strategy['intermediate_files'],
                complexity_level
            ),
            'task_history_tracking': self._get_task_history_guidance(),
            'final_integration_method': strategy.get('final_integration', {}),
            'best_practices': self._get_best_practices()
        }

        return guidance

    def _get_file_management_principle(self) -> str:
        """获取文件管理基本原则"""
        return """
## 中间文件管理原则

### 1. 渐进式记录原则
- 每个重要步骤都应生成对应的中间文件
- 记录分析过程、关键发现和决策理由
- 确保分析过程的可追溯性和可重现性

### 2. 结构化存储原则
- 使用标准化的文件命名格式
- 按步骤顺序组织文件（step1, step2, step3...）
- 采用适当的文件格式（.csv数据, .md文本, .json结构化数据）

### 3. 内容完整性原则
- 每个中间文件都应包含完整的上下文信息
- 记录生成时间、方法参数、关键假设
- 提供足够的元数据支持后续整合

### 4. 结果导向原则
- 中间文件应服务于最终分析目标
- 包含有助于最终决策的关键信息
- 便于后续步骤的引用和整合
        """

    def _get_naming_conventions(self) -> Dict[str, str]:
        """获取文件命名规范"""
        return {
            'timestamp_format': '%Y%m%d_%H%M%S',
            'step_prefix': 'step{order}_',
            'file_type_mapping': {
                'data': '.csv',
                'text': '.md',
                'structured': '.json',
                'visualization': '.png',
                'log': '.log'
            },
            'naming_template': '{step_prefix}{content}_{timestamp}.{extension}'
        }

    def _adapt_strategy_for_complexity(self, base_files: List[Dict], complexity: str) -> List[Dict]:
        """根据复杂度调整文件策略"""
        if complexity == 'simple':
            # 简单任务：只保留关键步骤的文件
            return [f for f in base_files if f['file_type'] in ['descriptive_analysis', 'section_drafts']]
        elif complexity == 'medium':
            # 中等复杂度：保留大部分中间文件
            return [f for f in base_files if f['file_type'] not in ['data_cleaning_log']]
        else:
            # 复杂任务：保留所有中间文件
            return base_files

    def _get_task_history_guidance(self) -> str:
        """获取任务历史记录指导"""
        return """
## 任务历史记录管理

### 1. 任务结构记录
```
{
  "task_id": "唯一任务标识",
  "task_name": "任务名称",
  "step_order": 1,
  "step_description": "步骤描述",
  "input_files": ["输入文件列表"],
  "output_files": ["输出文件列表"],
  "key_findings": ["关键发现"],
  "execution_time": "执行时间戳",
  "status": "completed/pending/failed"
}
```

### 2. 任务依赖关系
- 明确记录任务间的依赖关系
- 标识并行任务和串行任务
- 记录任务优先级

### 3. 结果追踪机制
- 每个步骤完成后记录生成文件
- 跟踪文件间的引用关系
- 维护任务执行的完整链路
        """

    def _get_best_practices(self) -> List[str]:
        """获取最佳实践建议"""
        return [
            "始终为每个分析步骤生成中间文件",
            "使用描述性的文件名，便于理解和检索",
            "在文件中记录分析方法和参数设置",
            "定期检查中间文件的完整性和一致性",
            "建立文件版本管理，避免覆盖重要结果",
            "确保最终报告能够引用具体的中间文件",
            "为复杂任务创建执行摘要文件",
            "保持文件格式的标准化和兼容性"
        ]

    def generate_file_management_prompt(self, user_query: str, task_analysis: Dict) -> str:
        """
        生成完整的中间文件管理prompt

        Args:
            user_query: 用户查询
            task_analysis: 任务分析结果

        Returns:
            中间文件管理指导prompt
        """
        task_type = task_analysis.get('primary_task', 'data_analysis')
        complexity = task_analysis.get('complexity_level', 'medium')

        guidance = self.generate_file_management_guidance(task_type, complexity)

        prompt = f"""
## 中间文件管理指导

### 任务背景
用户查询: {user_query}
任务类型: {task_type}
复杂度级别: {complexity}

### 文件管理策略
{guidance['file_management_principle']}

### 推荐的中间文件
根据任务类型和复杂度，建议生成以下中间文件：

"""

        for i, file_info in enumerate(guidance['intermediate_files_strategy'], 1):
            prompt += f"""
**步骤{i}: {file_info['description']}**
- 文件名格式: {file_info['filename_template']}
- 内容结构: {', '.join(file_info['content_structure'])}
- 文件类型: {file_info['file_type']}

"""

        prompt += f"""
### 任务历史追踪
{guidance['task_history_tracking']}

### 最终整合方法
使用以下方法基于中间文件生成最终结果：
{guidance['final_integration_method'].get('description', '逐步整合所有中间文件')}

### 最佳实践提醒
{chr(10).join(f"• {practice}" for practice in guidance['best_practices'])}

### 执行指令
1. 为每个主要步骤生成对应的中间文件
2. 确保文件名清晰且包含时间戳
3. 在最终报告中引用具体的中间文件
4. 维护完整的任务执行历史
        """

        return prompt