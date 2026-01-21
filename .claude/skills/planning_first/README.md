# Planning First Skill

强制先规划后执行的Claude思考指导框架。

## 📋 概述

Planning First是一个Claude Agent SDK skill，它确保Claude在执行任何任务前都会先制定执行计划。通过提供完整的思考框架，包括：

- ✅ **强制规划优先**：永远不要直接开始行动
- ✅ **ReAct执行范式**：思考-行动-观察循环
- ✅ **5阶段协调框架**：处理复杂问题
- ✅ **3种思维模式**：编程/分析/创作

## 🚀 使用方法

### 基础使用

```python
from planning_first import PlanningFirst

# 创建skill实例
agent = PlanningFirst()

# 处理用户请求
result = agent.process_request(
    user_query="修复登录功能的bug",
    user_id="user_001"
)

# 获取指导prompt
guidance_prompt = result['guidance_prompt']

# 将guidance_prompt作为system_prompt传递给Claude
# 这样Claude就会先制定计划，再执行任务
```

### 与Session API集成

```python
import requests

# 1. 使用Planning First skill
from planning_first import PlanningFirst
agent = PlanningFirst()
result = agent.process_request("修复登录bug", "user_001")
system_prompt = result['guidance_prompt']

# 2. 创建session时传入system_prompt
response = requests.post(
    "http://localhost:8000/api/v1/session",
    json={
        "system_prompt": system_prompt,  # ← 使用skill生成的prompt
        "allowed_tools": ["Read", "Write", "Grep", "Bash"],
        "model": "claude-sonnet-4-5-20250929",
        "incremental_stream": True
    }
)
session_info = response.json()
session_id = session_info['session_id']

# 3. 在session中查询
response = requests.post(
    f"http://localhost:8000/api/v1/session/{session_id}/query/stream",
    json={"prompt": "修复登录功能的bug"},
    stream=True
)

# 4. Claude现在会先制定计划，再执行
for line in response.iter_lines():
    print(line.decode('utf-8'))
```

## 📁 目录结构

```
planning_first/
├── SKILL.md                 # Skill元数据
├── skill.json              # Skill配置
├── setup.py                # 安装配置
├── README.md               # 本文件
├── planning_first.py       # 主入口
├── guidance/               # 指导模块
│   ├── __init__.py
│   └── planning_first_core.py
└── prompts/                # Prompt模板
    └── planning_first.md   # 主要prompt (14,023字符)
```

## 🎯 核心特性

### 1. 强制规划优先

Claude在执行任何任务前必须先列出执行计划：

```
用户：修复登录bug
Claude：
📋 执行计划：
步骤1：定位问题
   目的：找到bug的根本原因
   方法：使用Grep搜索登录相关代码

步骤2：分析问题
   目的：理解问题所在

步骤3：修复代码
   目的：解决问题

步骤4：验证修复
   目的：确认bug已修复

🤔 这个计划可以吗？
```

### 2. ReAct执行范式

思考-行动-观察的精细化执行：

```
🤔 Thought 1: 我需要先了解登录功能的代码结构
🔧 Action 1: 使用Glob查找登录相关文件
👁️ Observation 1: 找到了3个文件

🤔 Thought 2: 现在我需要查看登录的具体实现
🔧 Action 2: 使用Read读取登录代码
👁️ Observation 2: 看到了login()函数...
```

### 3. 5阶段协调框架

对于复杂任务，提供完整的协调框架：

- 阶段1：问题理解与目标设定
- 阶段2：任务分解与规划
- 阶段3：执行协调与进度跟踪
- 阶段4：动态调整与风险管理
- 阶段5：结果整合与质量保证

### 4. 3种思维模式

- **编程思维**：理解需求 → 设计方案 → 实现策略 → 验证标准
- **分析思维**：收集信息 → 分析方法 → 洞察提取 → 建议方案
- **创作思维**：构思框架 → 内容创作 → 质量检查

## 📊 返回结果

`process_request()` 返回一个包含以下字段的字典：

```python
{
    'guidance_prompt': str,      # 给Claude的主要指导prompt
    'user_query': str,           # 原始用户查询
    'query_analysis': {          # 查询分析结果
        'complexity': 'simple|medium|complex',
        'task_type': 'programming|analysis|writing|general',
        'query_length': int,
        'estimated_steps': int
    },
    'metadata': {                # 元数据
        'agent_id': str,
        'skill_name': 'planning_first',
        'skill_version': '3.0.0',
        ...
    },
    'planning_emphasis': True,   # 强调规划优先
    'requires_plan': True,        # 要求必须先规划
    'supports_coordination': True,
    'supports_react': True
}
```

## 🔧 配置选项

```python
from planning_first import PlanningFirst, PlanningFirstConfig

config = PlanningFirstConfig(
    enable_planning_emphasis=True,      # 启用规划强调
    enable_react_paradigm=True,         # 启用ReAct范式
    enable_coordination_framework=True, # 启用协调框架
    enable_thinking_modes=True,         # 启用思维模式
    prompt_language="zh-CN"             # 提示语言
)

agent = PlanningFirst(config)
```

## 📝 适用场景

- ✅ 需要严格规划的任务（编程、分析、创作）
- ✅ 复杂的多阶段任务（需要3+个阶段）
- ✅ 需要可追溯执行过程的任务
- ✅ 涉及多个思维模式的综合性任务

## ⚠️ 注意事项

1. **Prompt规模**：14,023字符，建议增加请求超时时间（timeout=120s）
2. **适用性**：更适合复杂任务，简单任务可能有点"杀鸡用牛刀"
3. **灵活性**：计划不是僵化的，可以根据情况动态调整

## 🎉 版本信息

- **版本**: 3.0.0
- **发布日期**: 2024-12-28
- **Prompt规模**: 14,023 字符
- **核心理念**: 先规划，后执行 + ReAct范式 + 宏观协调 + 思维模式

## 📚 相关文档

- [SKILL.md](SKILL.md) - Skill元数据和特性说明
- [prompts/planning_first.md](prompts/planning_first.md) - 完整的prompt内容

## 🤖 贡献者

Generated with [Claude Code](https://claude.com/claude-code)
