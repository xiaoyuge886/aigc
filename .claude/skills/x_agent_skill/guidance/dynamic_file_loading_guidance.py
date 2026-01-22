# -*- coding: utf-8 -*-
"""
动态文件加载指导模块

为Claude提供动态文件系统数据加载的专业指导，
充分利用Claude Skill的核心特性：按需加载文件数据
"""

from typing import Dict, List, Any, Optional
import logging

try:
    from ..core.file_system_loader import get_file_loader
except ImportError:
    from core.file_system_loader import get_file_loader

logger = logging.getLogger(__name__)

class DynamicFileLoadingGuidance:
    """
    动态文件加载指导器

    为Claude提供：
    1. 何时以及如何动态加载文件数据
    2. 文件系统资源的智能利用策略
    3. 数据缓存和更新机制指导
    4. 基于动态数据的分析优化方法
    """

    def __init__(self):
        """初始化动态文件加载指导器"""
        self.file_loader = get_file_loader()
        self.loading_strategies = self._initialize_loading_strategies()

    def _initialize_loading_strategies(self) -> Dict[str, Dict]:
        """初始化文件加载策略"""
        return {
            'sop_templates': {
                'description': '动态SOP模板加载',
                'when_to_load': [
                    '用户查询涉及特定业务领域时',
                    '检测到复杂分析任务时',
                    '需要标准作业程序指导时'
                ],
                'loading_pattern': '按需加载 + 缓存',
                'fallback': '使用通用SOP模板'
            },
            'domain_knowledge': {
                'description': '领域专业知识动态加载',
                'when_to_load': [
                    '识别到特定专业领域时',
                    '需要行业基准数据时',
                    '要求专业分析视角时'
                ],
                'loading_pattern': '预加载 + 按需补充',
                'fallback': '使用通用分析框架'
            },
            'reference_data': {
                'description': '参考数据动态加载',
                'when_to_load': [
                    '需要进行对比分析时',
                    '要求基准数据时',
                    '识别数据验证需求时'
                ],
                'loading_pattern': '按需加载',
                'fallback': '基于用户提供数据进行分析'
            },
            'user_data': {
                'description': '用户历史数据动态加载',
                'when_to_load': [
                    '多轮对话需要上下文时',
                    '需要历史分析结果时',
                    '识别用户特定需求时'
                ],
                'loading_pattern': '会话级缓存',
                'fallback': '基于当前查询进行分析'
            },
            'config_files': {
                'description': '配置文件动态加载',
                'when_to_load': [
                    '系统初始化时',
                    '检测到配置更新时',
                    '需要自定义参数时'
                ],
                'loading_pattern': '启动加载 + 变更检测',
                'fallback': '使用默认配置'
            }
        }

    def generate_file_loading_guidance(self, user_query: str, intent_analysis: Dict) -> str:
        """
        生成动态文件加载指导

        Args:
            user_query: 用户查询
            intent_analysis: 意图分析结果

        Returns:
            动态文件加载指导prompt
        """
        # 识别需要加载的文件类型
        required_files = self._identify_required_files(user_query, intent_analysis)

        # 生成加载策略
        loading_strategies = self._generate_loading_strategies(required_files)

        # 构建完整的指导prompt
        prompt = f"""
## 动态文件系统数据加载指导

### 分析背景
用户查询: {user_query}
识别领域: {intent_analysis.get('problem_domain', 'general')}
任务复杂度: {intent_analysis.get('complexity_level', 'medium')}

### 需要动态加载的文件资源

根据查询分析，建议加载以下文件资源：

{self._format_file_requirements(required_files)}

### 文件加载策略和时机

{loading_strategies}

### 具体加载操作指导

#### 1. SOP模板动态加载
```python
# 示例：根据任务类型加载对应SOP模板
domain = intent_analysis.get('problem_domain')
if domain == 'finance':
    sop_template = file_loader.load_sop_template('financial_analysis')
elif domain == 'marketing':
    sop_template = file_loader.load_sop_template('marketing_campaign')
else:
    sop_template = file_loader.load_sop_template('general_analysis')
```

#### 2. 领域专业知识加载
```python
# 示例：加载领域知识
domain = intent_analysis.get('problem_domain')
topic = intent_analysis.get('analysis_type', ['general'])[0]

try:
    domain_knowledge = file_loader.load_domain_knowledge(domain, topic)
    # 将专业知识融入分析过程
except FileNotFoundError:
    # 使用通用知识库
    domain_knowledge = file_loader.load_domain_knowledge('general')
```

#### 3. 参考数据动态加载
```python
# 示例：加载行业基准数据
if intent_analysis.get('complexity_level') == 'high':
    try:
        benchmark_data = file_loader.load_reference_data('industry_benchmarks')
        # 使用基准数据进行对比分析
    except FileNotFoundError:
        # 基于用户提供数据生成内部基准
        benchmark_data = generate_internal_benchmarks(user_data)
```

#### 4. 用户历史数据加载
```python
# 示例：加载用户历史分析结果
user_id = context.get('user_id', 'default')
if context.get('conversation_stage') == 'follow_up':
    try:
        history_data = file_loader.load_user_data(user_id, 'analysis_history')
        # 基于历史数据提供连贯的分析
    except FileNotFoundError:
        # 作为新对话处理
        pass
```

### 数据缓存和更新机制

#### 缓存策略
- **SOP模板**: 长期缓存，版本更新时刷新
- **领域知识**: 中期缓存，定期更新
- **参考数据**: 短期缓存，按需验证最新性
- **用户数据**: 会话级缓存，隐私保护

#### 更新时机
- 检测到文件修改时间变化
- 用户明确要求更新数据
- 分析结果明显异常时
- 定期自动更新（每日/每周）

### 文件加载最佳实践

#### 1. 智能加载决策
```python
# 决策是否需要加载外部数据
def should_load_external_data(query, intent):
    # 复杂任务需要更多外部数据
    if intent.get('complexity_level') == 'high':
        return True

    # 专业领域需要领域知识
    if intent.get('problem_domain') != 'general':
        return True

    # 简单查询可以基于用户提供数据
    return False
```

#### 2. 错误处理和降级策略
```python
# 优雅降级处理
def load_with_fallback(loader_func, fallback_func, *args, **kwargs):
    try:
        return loader_func(*args, **kwargs)
    except (FileNotFoundError, Exception) as e:
        logger.warning(f"文件加载失败，使用降级策略: {e}")
        return fallback_func(*args, **kwargs)
```

#### 3. 性能优化
```python
# 批量预加载策略
def preload_common_data(domains):
    # 预加载常用数据
    common_templates = ['financial_analysis', 'marketing_analysis', 'general_analysis']
    for template in common_templates:
        file_loader.load_sop_template(template)
```

### 分析优化建议

#### 基于动态数据的分析增强
1. **实时基准对比**: 使用最新的行业基准数据
2. **专业方法论**: 应用特定领域的分析框架
3. **历史趋势分析**: 结合用户历史数据进行趋势分析
4. **个性化建议**: 基于用户偏好和过往反馈调整建议

#### 数据质量保证
1. **来源验证**: 确保数据来源的可靠性
2. **时效性检查**: 验证数据的时效性
3. **一致性验证**: 检查数据的一致性
4. **异常值处理**: 识别和处理异常数据

### 执行指令

1. **根据查询类型确定需要加载的文件**
2. **使用相应的加载方法获取数据**
3. **验证数据质量和时效性**
4. **将动态数据融入分析过程**
5. **在结果中引用数据来源**
6. **管理好数据缓存，避免重复加载**

### 注意事项

- 确保文件加载失败时有合理的降级策略
- 注意保护用户隐私数据
- 定期更新和验证外部数据的准确性
- 监控文件加载性能，避免影响用户体验
- 记录数据来源，便于审计和验证
        """

        return prompt

    def _identify_required_files(self, user_query: str, intent_analysis: Dict) -> Dict[str, List[str]]:
        """识别需要加载的文件类型"""
        required_files = {
            'sop_templates': [],
            'domain_knowledge': [],
            'reference_data': [],
            'user_data': [],
            'config_files': []
        }

        # 基于意图分析确定需要的文件
        domain = intent_analysis.get('problem_domain', 'general')
        complexity = intent_analysis.get('complexity_level', 'medium')
        analysis_types = intent_analysis.get('analysis_type', [])

        # SOP模板需求
        if domain != 'general':
            required_files['sop_templates'].append(f'{domain}_analysis')

        if complexity == 'high':
            required_files['sop_templates'].append('comprehensive_analysis')

        # 领域知识需求
        if domain != 'general':
            required_files['domain_knowledge'].append(domain)
            for analysis_type in analysis_types:
                if analysis_type in ['trend_analysis', 'comparative_analysis', 'risk_assessment']:
                    required_files['domain_knowledge'].append(f'{domain}_{analysis_type}')

        # 参考数据需求
        if 'comparative_analysis' in analysis_types or complexity == 'high':
            required_files['reference_data'].append('industry_benchmarks')
            required_files['reference_data'].append('historical_data')

        # 用户数据需求（多轮对话）
        if intent_analysis.get('conversation_stage') == 'follow_up':
            required_files['user_data'].append('analysis_history')
            required_files['user_data'].append('user_preferences')

        return required_files

    def _generate_loading_strategies(self, required_files: Dict[str, List[str]]) -> str:
        """生成文件加载策略指导"""
        strategies = []

        for file_type, files in required_files.items():
            if files:
                strategy_info = self.loading_strategies.get(file_type, {})
                strategies.append(f"""
**{strategy_info.get('description', file_type)}**

需要加载: {', '.join(files)}

加载时机:
{chr(10).join(f'• {condition}' for condition in strategy_info.get('when_to_load', []))}

加载模式: {strategy_info.get('loading_pattern', '按需加载')}

降级策略: {strategy_info.get('fallback', '跳过该数据源')}
""")

        return '\n'.join(strategies)

    def _format_file_requirements(self, required_files: Dict[str, List[str]]) -> str:
        """格式化文件需求"""
        requirements = []

        for file_type, files in required_files.items():
            if files:
                type_descriptions = {
                    'sop_templates': '📋 SOP模板',
                    'domain_knowledge': '🎯 领域知识',
                    'reference_data': '📊 参考数据',
                    'user_data': '👤 用户数据',
                    'config_files': '⚙️ 配置文件'
                }

                requirements.append(f"""
**{type_descriptions.get(file_type, file_type)}**
- 文件列表: {', '.join(files)}
- 重要性: {'高' if file_type in ['sop_templates', 'domain_knowledge'] else '中'}
""")

        return '\n'.join(requirements) if requirements else "无需加载外部文件，基于用户提供数据进行分析"

    def get_available_resources(self) -> Dict[str, List[str]]:
        """获取当前可用的文件资源"""
        available_resources = {}

        for data_type in self.file_loader.data_dirs.keys():
            try:
                files = self.file_loader.list_available_files(data_type)
                if files:
                    available_resources[data_type] = files[:10]  # 显示前10个文件
            except Exception as e:
                logger.warning(f"获取文件列表失败 {data_type}: {e}")

        return available_resources

    def refresh_cache(self, data_types: List[str] = None):
        """刷新文件缓存"""
        if data_types:
            for data_type in data_types:
                self.file_loader.clear_cache(data_type)
                logger.info(f"刷新缓存: {data_type}")
        else:
            self.file_loader.clear_cache()
            logger.info("刷新所有缓存")