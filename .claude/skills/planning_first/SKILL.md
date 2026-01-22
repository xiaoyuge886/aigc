---
name: planning_first
description: Planning First - 强制先规划后执行的思考指导框架，确保Claude在执行任何任务前先列出执行计划
---

# Planning First - 思考指导框架

一个强大的 Claude Agent SDK skill，为任务提供完整的"先规划、后执行"思考指导框架。

## 核心特性

### 🎯 强制规划优先
- **最重要原则**：永远不要直接开始行动
- 在执行任何任务前，必须先列出执行计划（Plan）
- 向用户展示计划并获得确认

### 🔄 ReAct 执行范式
- **ReAct** = **Rea**soning（推理）+ **Act**ing（行动）
- Thought（思考）→ Action（行动）→ Observation（观察）→ 循环
- 提供完整的思考模板和质量检查清单

### 🎯 复杂问题协调框架
- 阶段1：问题理解与目标设定
- 阶段2：任务分解与规划
- 阶段3：执行协调与进度跟踪
- 阶段4：动态调整与风险管理
- 阶段5：结果整合与质量保证

### 🧠 三种思维模式
- **编程思维**：理解需求 → 设计方案 → 实现策略 → 验证标准
- **分析思维**：收集信息 → 分析方法 → 洞察提取 → 建议方案
- **创作思维**：构思框架 → 内容创作 → 质量检查

## 使用方法

```python
from planning_first import PlanningFirst

agent = PlanningFirst()

# 处理用户请求，生成指导 prompt
result = agent.process_request(
    user_query="用户的任务或问题",
    user_id="user_001"
)

# result['guidance_prompt'] 包含完整的思考框架
# 将此作为 system_prompt 传递给 Claude
```

## 适用场景

- ✅ 需要严格规划的任务（编程、分析、创作）
- ✅ 复杂的多阶段任务（需要3+个阶段）
- ✅ 需要可追溯执行过程的任务
- ✅ 涉及多个思维模式的综合性任务

## 核心理念

**你是指挥官，不是士兵** - 提供框架，不直接执行

## 版本信息

- **版本**: 3.0.0
- **Prompt 规模**: 14,023 字符
- **核心理念**: 先规划，后执行 + ReAct范式 + 宏观协调 + 思维模式
