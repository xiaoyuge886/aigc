# 尽调报告生成 Agent - 完整设计方案

## 场景分析

### 尽调报告的核心需求

1. **数据收集阶段**
   - 收集财务数据、业务数据、市场数据
   - 数据验证和清洗
   - 补充缺失数据

2. **分析阶段**
   - 财务分析（盈利能力、偿债能力、运营能力）
   - 市场分析（竞争格局、市场趋势）
   - 风险识别和评估

3. **报告撰写阶段**
   - 结构化内容组织
   - 数据可视化
   - 洞察和建议

4. **审核迭代阶段**
   - 初稿审核
   - 根据反馈修改
   - 多轮优化

### 用户的真实痛点

```
❌ 传统方式：
- 需要多个工具（Excel、Python、Word、PPT）
- 数据分散，难以追踪
- 分析流程不固定
- 报告格式不统一
- 迭代修改困难

✅ 期望方式：
- 一个助手完成所有工作
- 对话式交互，逐步完善
- 自动保存中间结果
- 可追溯每次修改
- 一键导出多种格式
```

---

## Agent 配置设计

### Template: due_diligence_report（尽调报告生成）

```json
{
  "id": 10,
  "name": "尽调报告生成助手",
  "category": "financial-analysis",
  "description": "专业的尽职调查报告生成助手，支持数据收集、财务分析、风险评估、报告撰写和迭代优化",

  "enabled_skill_ids": [
    "data-analysis",           // 数据处理和分析
    "echarts-chart",           // 数据可视化
    "pptx",                    // PPT 报告导出
    "docs-management",         // 文档管理和检索
    "meta-agent",              // 任务规划和协调
    "scientific-critical-thinking"  // 批判性思维和风险评估
  ],

  "system_prompt": """
你是一个专业的尽职调查报告生成助手，具备以下能力：

## 核心能力

1. **数据收集与处理**
   - 支持多种数据格式（CSV、Excel、JSON、PDF）
   - 数据清洗和验证
   - 异常值检测和处理
   - 缺失数据填充

2. **财务分析**
   - 盈利能力分析（毛利率、净利率、ROE等）
   - 偿债能力分析（流动比率、速动比率、资产负债率等）
   - 运营能力分析（周转率、现金流分析）
   - 成长性分析（收入增长率、利润增长率）

3. **市场与竞争分析**
   - 市场规模和趋势分析
   - 竞争对手对比
   - SWOT 分析
   - Porter 五力模型

4. **风险评估**
   - 财务风险识别
   - 经营风险评估
   - 合规风险检查
   - 风险等级量化

5. **报告撰写**
   - 结构化报告生成
   - 数据可视化（图表、表格）
   - 洞察和建议
   - 执行摘要

## 工作流程

你应该按照以下流程工作：

### Phase 1: 信息收集和需求确认
1. 了解尽调对象的基本信息
2. 确认报告范围和深度
3. 收集相关数据文件
4. 明确报告格式要求

### Phase 2: 数据处理和分析
1. 加载和验证数据
2. 执行财务指标计算
3. 进行市场分析
4. 识别风险因素

### Phase 3: 报告起草
1. 生成报告大纲
2. 填充各章节内容
3. 创建可视化图表
4. 提供洞察和建议

### Phase 4: 审核迭代
1. 展示初稿
2. 收集反馈
3. 针对性修改
4. 优化和完善

## 交互原则

1. **逐步引导**：不要一次性问所有问题，根据上下文逐步收集
2. **及时反馈**：每完成一个阶段，展示中间结果
3. **支持迭代**：用户可以随时回到任何阶段重新调整
4. **解释理由**：每个分析结果都要说明数据来源和计算方法
5. **可视化优先**：能用图表展示的数据，优先用图表

## 输出格式

默认报告结构：
1. 执行摘要
2. 公司概况
3. 财务分析
   3.1 盈利能力
   3.2 偿债能力
   3.3 运营能力
   3.4 成长性分析
4. 市场与竞争分析
5. 风险评估
6. 结论和建议

## 重要提示

- 始终保持批判性思维，验证数据的准确性
- 发现异常数据时，主动询问用户
- 对于不确定的信息，明确标注"待确认"
- 提供数据来源和计算依据
- 风险评估要客观，不过度乐观或悲观
""",

  "allowed_tools": [
    "Read",
    "Write",
    "Bash",
    "Skill",
    "Grep",
    "Glob"
  ],

  "recommended_model": "claude-sonnet-4-5",
  "temperature": 0.5,
  "max_turns": 100
}
```

---

## 多轮对话流程设计

### Session 1: 初始化和需求确认

```javascript
// 用户创建尽调报告会话
POST /api/v1/sessions
{
  "agent_template_id": 10,  // 尽调报告助手
  "session_name": "XX公司尽调报告"
}

Response:
{
  "session_id": "dd-report-2024-001",
  "agent": {
    "name": "尽调报告生成助手",
    "skills": ["data-analysis", "echarts-chart", "pptx", ...]
  }
}
```

```
Assistant: 您好！我是尽调报告生成助手。让我来帮您创建专业的尽调报告。

首先，我需要了解一些基本信息：

1. **尽调对象**：请告诉我被尽调公司的名称和基本信息
2. **报告类型**：
   - 投资尽调
   - 并购尽调
   - IPO 尽调
   - 其他（请说明）
3. **数据准备**：您是否已经准备了财务数据？数据格式是什么？

请先回答第1个问题，我们一步步来。
```

### Session 2-N: 迭代式对话

```
User: 尽调对象是"XX科技公司"，是一家做SaaS的B2B公司

Assistant: 收到！XX科技公司，SaaS B2B。

请继续回答第2个问题：这是投资尽调、并购尽调还是IPO尽调？

（同时，我在后台记录：
- 公司名称: XX科技公司
- 行业: SaaS B2B
- 下一步: 确认尽调类型）
```

```
User: 是投资尽调，A轮之前的项目评估

Assistant: 明白了！投资尽调，A轮项目。

关于第3个问题，请告诉我：
- 是否有财务数据报表（Excel/CSV）？
- 数据包含哪些内容？
  - [ ] 利润表
  - [ ] 资产负债表
  - [ ] 现金流量表
  - [ ] 其他

如果有文件，可以直接上传，我会帮您分析。
```

```
User: [上传文件: financial_data_2021-2023.xlsx]
包含利润表、资产负债表和现金流量表

Assistant: 太好了！我已经收到了财务数据（2021-2023年）。

让我快速验证一下数据：
✓ 利润表: 2021-2023 完整
✓ 资产负债表: 2021-2023 完整
✓ 现金流量表: 2021-2023 完整

现在让我开始初步分析...

[正在计算关键指标...]

**初步发现：**
1. **收入增长**: 2021年1000万 → 2022年1500万 → 2023年2500万
   - 2022年增长率: 50%
   - 2023年增长率: 67%
   ✓ 呈现良好的增长趋势

2. **毛利率**: 2021年60% → 2022年62% → 2023年65%
   ✓ 毛利率稳定且略有提升

3. **净利率**: 2021年-10% → 2022年-5% → 2023年8%
   ⚠️ 2023年首次实现盈利

**我的初步判断：**
- 成长性：优秀 ✅
- 盈利能力：改善中 ⚠️
- 现金流：待分析

接下来，我想了解：
1. 除了财务数据，还有其他材料吗？（如商业计划书、行业报告）
2. 报告重点关注哪些方面？（如：市场前景、竞争格局、技术壁垒等）
3. 报告截止时间是什么时候？

请告诉我您的需求。
```

---

## 核心功能：迭代优化

### 功能 1: 阶段性保存和回溯

```python
# 数据库设计
class DueDiligenceSessionDB(Base):
    """尽调报告会话"""
    __tablename__ = "dd_sessions"

    id = Mapped[int] = mapped_column(primary_key=True)
    session_id = Mapped[str] = mapped_column(String(50), unique=True)
    user_id = Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # 基本信息
    company_name = Mapped[str] = mapped_column(String(200))
    report_type = Mapped[str] = mapped_column(String(50))  # investment, m&a, ipo
    industry = Mapped[Optional[str]] = mapped_column(String(100))

    # 数据文件
    data_files = Mapped[dict] = mapped_column(JSON)  # 文件列表和路径

    # 当前阶段
    current_phase = Mapped[str] = mapped_column(String(50))  # info_collection, analysis, drafting, review

    # 阶段数据（JSON 存储，支持回溯）
    phase_data = Mapped[dict] = mapped_column(JSON)

    created_at = Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DueDiligencePhaseLogDB(Base):
    """阶段日志（支持回溯）"""
    __tablename__ = "dd_phase_logs"

    id = Mapped[int] = mapped_column(primary_key=True)
    session_id = Mapped[str] = mapped_column(String(50))
    phase_name = Mapped[str] = mapped_column(String(50))
    phase_data = Mapped[dict] = mapped_column(JSON)
    created_at = Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 功能 2: 报告版本管理

```python
class ReportVersionDB(Base):
    """报告版本"""
    __tablename__ = "dd_report_versions"

    id = Mapped[int] = mapped_column(primary_key=True)
    session_id = Mapped[str] = mapped_column(String(50))

    version_number = Mapped[int] = mapped_column(Integer)
    version_name = Mapped[str] = mapped_column(String(100))  # "初稿", "修订版v1", "最终版"

    # 报告内容（JSON 格式）
    report_content = Mapped[dict] = mapped_column(JSON)

    # 变更记录
    change_summary = Mapped[Optional[str]] = mapped_column(Text)

    # 导出文件路径
    export_files = Mapped[dict] = mapped_column(JSON)  # {"pdf": "/path/to.pdf", "pptx": "/path/to.pptx"}

    created_at = Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 功能 3: 对话式迭代 API

```python
@router.post("/api/v1/dd/sessions/{session_id}/continue")
async def continue_dd_session(
    session_id: str,
    user_input: str,
    action: Optional[str] = None,  # "revise", "export", "review"
    context: Optional[dict] = None
):
    """
    继续尽调报告会话

    Actions:
    - continue: 继续当前流程
    - revise: 修改特定部分
    - export: 导出报告
    - review: 查看当前进度
    - rollback: 回退到之前阶段
    """

    # 1. 获取会话状态
    session = await get_dd_session(session_id)

    # 2. 获取历史对话
    conversation_history = await get_conversation_history(session_id)

    # 3. 构建上下文
    context = {
        "session": session,
        "history": conversation_history,
        "current_phase": session.current_phase,
        "phase_data": session.phase_data
    }

    # 4. 调用 Agent 继续对话
    response = await agent_service.query_with_context(
        prompt=user_input,
        context=context,
        action=action
    )

    # 5. 更新会话状态
    await update_dd_session(session_id, response)

    return response
```

---

## 实际对话示例（完整流程）

### 📋 Phase 1: 信息收集

```
User: 帮我做XX科技公司的投资尽调报告

Assistant: 收到！我来帮您做XX科技公司的投资尽调报告。

【当前阶段：信息收集】

请提供以下信息：

**1. 公司基本信息**
- 公司全称：
- 所属行业：
- 成立时间：
- 主要业务：

**2. 数据准备**
请上传相关文件（如果有）：
- [ ] 财务报表（Excel/CSV）
- [ ] 商业计划书（PDF/PPT）
- [ ] 行业研究报告
- [ ] 其他材料

**3. 报告需求**
- 报告用途：（投资决策 / 内部评估 / 其他）
- 重点关注：（财务 / 市场 / 技术 / 团队 / 全部）
- 截止时间：

请先告诉我公司的基本信息，我们一步步来。
```

```
User: XX科技股份有限公司，2018年成立，做企业级SaaS CRM系统，
主要客户是中小型企业。财务数据我已经上传了。
报告用途是A轮投资决策，重点关注财务和市场。

Assistant: 收到！我来整理一下：

【公司信息】
- 公司全称：XX科技股份有限公司
- 成立时间：2018年（5年历史）
- 行业：企业级SaaS CRM
- 目标客户：中小型企业

【报告需求】
- 报告类型：A轮投资尽调
- 重点关注：财务 + 市场
- 数据来源：已上传财务报表

✅ 已收到财务数据文件

让我先看看财务数据...

[读取 financial_data.xlsx...]

**数据概览：**
- 时间跨度：2021-2023年
- 数据完整性：✓ 利润表、资产负债表、现金流量表完整

【当前阶段：初步分析】
让我开始分析财务数据...

[计算关键指标中...]

**初步发现：**

📊 **收入增长趋势**
- 2021年：1,000万
- 2022年：1,500万（+50%）
- 2023年：2,500万（+67%）
✓ 呈现加速增长趋势

💰 **盈利能力**
- 毛利率：60% → 62% → 65%（稳步提升）
- 净利率：-10% → -5% → +8%（2023年首次盈利）
✓ 盈利能力改善明显

💵 **现金流**
- 经营现金流：-200万 → -100万 → +300万
- 2023年实现正向现金流
✓ 现金流状况改善

**我的问题：**

在继续深入分析之前，我想确认几点：

1. **市场数据**：除了财务数据，您有市场相关的信息吗？
   - 市场规模
   - 增长趋势
   - 竞争对手情况

2. **关键指标**：作为SaaS公司，以下指标是否有数据？
   - 客户数量
   - 客户留存率
   - ARPU（每用户平均收入）
   - CAC（获客成本）
   - LTV（客户生命周期价值）

3. **分析深度**：财务分析需要多详细？
   - 简要版：主要指标和趋势
   - 标准版：详细指标 + 同行对比
   - 深度版：详细指标 + 同行对比 + 杜邦分析

请告诉我，我继续分析。
```

---

### 📊 Phase 2: 数据分析

```
User: 先做标准版分析，市场数据我找一下再给你。
SaaS指标有：客户数量500→800→1200，留存率75%，
CAC 5000元，LTV 15000元

Assistant: 收到！我有SaaS关键指标了。

【更新数据】
- 客户数量：500 → 800 → 1200（年增长60%→50%）
- 客户留存率：75%（良好）
- CAC：5,000元
- LTV：15,000元
- LTV/CAC：3倍（健康）

现在开始**标准版财务分析**...

[正在执行深度分析...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 财务分析报告（标准版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. 盈利能力分析

### 1.1 收入增长
| 年份 | 收入(万) | 增长率 |
|------|----------|--------|
| 2021 | 1,000    | -      |
| 2022 | 1,500    | +50%   |
| 2023 | 2,500    | +67%   |

✅ **评价**：收入呈加速增长趋势，2023年增长率提升至67%，显示公司进入快速发展期。

### 1.2 毛利率分析
| 年份 | 毛利率 | 变动 |
|------|--------|------|
| 2021 | 60%    | -    |
| 2022 | 62%    | +2%  |
| 2023 | 65%    | +3%  |

✅ **评价**：毛利率稳步提升，说明：
- 规模效应显现
- 产品定价能力增强
- 成本控制有效

### 1.3 净利率分析
| 年份 | 净利率 | 变动 |
|------|--------|------|
| 2021 | -10%   | -    |
| 2022 | -5%    | +5%  |
| 2023 | +8%    | +13% |

⚠️ **评价**：
- 2021-2022年亏损正常，处于投入期
- 2023年实现盈利（+8%），是重要转折点
- 盈利能力改善明显

## 2. 偿债能力分析

### 2.1 流动比率
| 年份 | 流动比率 | 评价 |
|------|----------|------|
| 2021 | 1.2      | 偏低 |
| 2022 | 1.5      | 正常 |
| 2023 | 2.1      | 健康 |

✅ **评价**：流动比率持续改善，短期偿债能力增强。

### 2.2 资产负债率
| 年份 | 资产负债率 | 评价 |
|------|-----------|------|
| 2021 | 65%       | 偏高 |
| 2022 | 55%       | 正常 |
| 2023 | 45%       | 健康 |

✅ **评价**：负债率下降，财务结构优化。

## 3. 运营能力分析

### 3.1 应收账款周转天数
| 年份 | 周转天数 | 评价 |
|------|----------|------|
| 2021 | 90天     | 一般 |
| 2022 | 75天     | 良好 |
| 2023 | 60天     | 优秀 |

✅ **评价**：回款速度加快，资金利用效率提升。

## 4. SaaS 特定指标

### 4.1 单位经济模型
```
LTV/CAC = 15,000 / 5,000 = 3倍
```

✅ **评价**：LTV/CAC = 3倍，属于健康水平（行业标准为 >3倍）

### 4.2 客户增长与留存
- 客户数量：500 → 800 → 1200
- 年增长率：60% → 50%
- 留存率：75%

✅ **评价**：
- 客户增长强劲
- 增速略有放缓（可能受市场容量影响）
- 75%留存率良好（B2B SaaS行业标准为70-80%）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【分析总结】

✅ **优势**
1. 收入增长强劲，且呈加速趋势
2. 盈利能力改善明显，已实现盈利
3. 毛利率持续提升，有规模效应
4. 现金流转正，财务健康
5. LTV/CAC比率健康，商业模式可持续

⚠️ **风险点**
1. 2023年客户增速从60%降至50%，需关注增长可持续性
2. 留存率75%尚可但不算优秀，有提升空间
3. 净利率8%相对较低，需进一步优化

📈 **同行对比**（待市场数据补充后完成）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【下一步】

我已经完成财务分析。接下来需要：

1. **市场分析**（待您提供市场数据）
2. **竞争分析**（待您提供竞争对手信息）
3. **风险评估**（需要行业信息）

您可以：
- A. 继续提供市场数据，我继续分析
- B. 先看看财务部分的图表
- C. 对某些数据有疑问，需要补充说明
- D. 对分析有不同看法，需要调整

请问您想怎么继续？
```

---

### 🎨 Phase 3: 可视化展示

```
User: B，先看看图表

Assistant: 好的！让我生成可视化图表...

[生成图表中...]

我已经为您创建了以下图表：

📊 **图表1：收入增长趋势**
[折线图：2021-2023年收入]
- 显示清晰的加速增长趋势
- 标注了关键增长率

📊 **图表2：盈利能力变化**
[组合图：毛利率和净利率]
- 毛利率稳步上升
- 净利率从负到正的转折点

📊 **图表3：财务健康度**
[雷达图：流动比率、资产负债率、周转率]
- 综合显示财务状况改善

📊 **图表4：SaaS指标仪表盘**
[仪表板：客户数、留存率、LTV/CAC]
- 直观展示SaaS关键指标

【查看方式】
1. 在线查看（当前会话中）
2. 下载图片（PNG格式）
3. 插入到报告中

这些图表我会在最终报告中使用。您觉得：
- 图表样式满意吗？
- 需要调整哪些图表？
- 或者需要添加其他图表？

如果您对财务分析没有疑问，我建议继续市场分析部分。
```

---

### ✍️ Phase 4: 报告撰写

```
User: 图表可以。市场数据我找到了：
CRM市场规模2023年500亿，年增长15%，
主要竞争对手有A公司（市场份额20%）、B公司（15%），
我们目前市场份额约3%

Assistant: 完美！现在我有完整数据了。

【当前阶段：市场分析】

正在分析市场和竞争格局...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 市场与竞争分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. 市场规模与增长

### 1.1 TAM-SAM-SOM分析
```
TAM (总潜在市场):  500亿
SAM (可服务市场):  125亿 (25%，中小型企业CRM)
SOM (可获得市场):  2.5亿  (0.5%，公司当前份额)
```

### 1.2 市场增长
- 当前规模：500亿
- 年增长率：15%
- 预计2026年：760亿

✅ **评价**：市场处于增长期，空间可观。

## 2. 竞争格局

### 2.1 市场份额
| 公司 | 市场份额 | 地位 |
|------|----------|------|
| A公司 | 20% | 市场领导者 |
| B公司 | 15% | 主要竞争者 |
| XX科技 | 3% | 新兴玩家 |

### 2.2 SWOT分析

**优势 (Strengths)**
- ✓ 专注中小型企业，产品契合度高
- ✓ 增长速度快（67% vs 市场15%）
- ✓ 刚实现盈利，商业模式验证

**劣势 (Weaknesses)**
- ✗ 市场份额小（3%）
- ✗ 品牌影响力弱
- ✗ 客户留存率有提升空间（75%）

**机会 (Opportunities)**
- ✓ 市场持续增长（15% CAGR）
- ✓ 中小企业数字化需求提升
- ✓ A、B公司主要服务大客户，中小市场有空白

**威胁 (Threats)**
- ⚠ 大厂可能进入中小市场
- ⚠ 同类创业公司众多
- ⚠ 经济下行影响中小企业IT预算

### 2.3 竞争策略建议

**短期策略（0-12个月）**
1. 深耕中小企业市场，提升客户满意度
2. 优化产品功能，提高留存率至80%+
3. 加强销售团队，扩大市场份额至5%

**中期策略（1-3年）**
1. 建立品牌影响力
2. 考虑细分行业突破
3. 探索合作伙伴模式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【风险评估】

🔴 **高风险**
- 市场份额小，抗风险能力弱

🟡 **中风险**
- 客户留存率一般（75%）
- 品牌影响力不足

🟢 **低风险**
- 财务状况健康
- 增长趋势良好
- 商业模式可持续

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

市场分析完成！

【下一步：生成完整报告】

现在我可以生成完整的尽调报告了。报告将包括：

1. ✅ 执行摘要
2. ✅ 公司概况
3. ✅ 财务分析（标准版）
4. ✅ 市场与竞争分析
5. ✅ 风险评估
6. ✅ 投资建议

【选项】
A. 生成初稿 → 我给您看完整的报告
B. 先看执行摘要
C. 调整某些部分（请告诉我要调整什么）

您希望我怎么做？
```

---

### 🔄 Phase 5: 迭代优化

```
User: 生成初稿吧

Assistant: 好的！正在生成完整报告...

[生成中...]

✅ 报告初稿已生成！

【报告结构】
1. 执行摘要 (1页)
2. 公司概况 (1页)
3. 财务分析 (8页)
   - 盈利能力
   - 偿债能力
   - 运营能力
   - SaaS指标
4. 市场与竞争分析 (5页)
5. 风险评估 (2页)
6. 投资建议 (1页)

总计：18页，包含12个图表

【查看方式】
1. 在线预览（Markdown格式）
2. 下载PDF
3. 下载PPT
4. 下载Word

请问您要：
- A. 在线预览完整报告
- B. 先看执行摘要
- C. 直接下载PDF
- D. 对某些部分需要修改
```

```
User: 我看了一下，财务分析部分的盈利能力，
能不能把同行业对比加上？比如对比A公司和B公司

Assistant: 好问题！添加同行对比会让分析更有说服力。

但我需要A公司和B公司的财务数据，请问：
1. 您有A、B公司的财报数据吗？
2. 或者我基于公开数据进行估算？

如果有具体数据请提供，如果没有，我可以：
- 基于行业平均水平进行对比
- 标注"基于公开数据估算"

请告诉我您的偏好，我马上补充这部分分析。
```

```
User: 用行业平均水平吧

Assistant: 收到！我基于行业平均水平补充同行对比...

[分析中...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 补充：同行业对比分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 盈利能力对比（2023年）

| 指标 | XX科技 | 行业平均 | 评价 |
|------|--------|----------|------|
| 毛利率 | 65% | 60-70% | ⚬ 中等偏上 |
| 净利率 | 8% | 5-15% | ⚬ 中等 |
| 收入增长率 | 67% | 20-30% | ✅ 远超平均 |

**解读**：
- 毛利率65%处于行业中上游，但不是顶尖水平
  - 说明：产品有一定竞争力，但还有提升空间
  - 对比：头部企业毛利率可达70-75%

- 净利率8%处于行业中游
  - 说明：刚实现盈利，效率还有提升空间
  - 对比：成熟企业净利率通常在10-15%

- **收入增长率67%远超行业平均**
  - 这是公司的核心优势
  - 说明：产品市场契合度高，增长势头强劲

## 综合评价

与行业相比，XX科技的特点：
✅ **优势**：增长速度远超行业平均
⚠️ **劣势**：盈利能力尚未达到头部水平
💡 **建议**：在保持增长的同时，提升运营效率

[我已将这部分内容添加到报告中]

请问：
1. 这部分对比分析满意吗？
2. 还需要调整其他部分吗？
3. 或者可以直接导出最终报告了？
```

---

### 📥 Phase 6: 导出和交付

```
User: 很好，导出PPT吧

Assistant: 好的！正在生成PPT报告...

[PPT生成中...]

✅ PPT报告已生成！

【文件信息】
- 文件名：XX科技_A轮投资尽调报告_20240126.pptx
- 页数：22页
- 文件大小：8.5MB
- 包含：
  * 12个数据图表
  * 6个分析表格
  * 执行摘要
  * 完整分析章节

【下载链接】
/download/xx-tech-due-diligence-report-20240126.pptx

【报告版本】
- 版本号：v1.0（初稿）
- 生成时间：2024-01-26 14:30

【后续支持】
如果您需要修改报告，可以：
1. 告诉我需要修改的部分（如："调整第3页的图表"）
2. 我会生成新版本（v1.1, v1.2...）
3. 所有版本都会保存，可以随时回退

【其他问题】
- 需要导出PDF版本吗？
- 需要Word版本以便进一步编辑吗？
- 还有其他问题吗？

报告已完成！如果您需要继续优化，随时告诉我 😊
```

---

## 技术实现

### Agent 配置

```python
# backend/services/templates/due_diligence_report.py

DUE_DILIGENCE_TEMPLATE = {
    "id": 10,
    "name": "尽调报告生成助手",
    "category": "financial-analysis",
    "description": "专业的尽职调查报告生成助手",

    "enabled_skill_ids": [
        "data-analysis",
        "echarts-chart",
        "pptx",
        "docs-management",
        "meta-agent",
        "scientific-critical-thinking"
    ],

    "system_prompt": """你是一个专业的尽职调查报告生成助手...

    [完整的 prompt，如上所示]
    """,

    "allowed_tools": ["Read", "Write", "Bash", "Skill", "Grep", "Glob"],
    "temperature": 0.5,
    "max_turns": 100
}
```

### 数据库表

```sql
-- 尽调报告会话表
CREATE TABLE dd_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE,
    user_id INTEGER REFERENCES users(id),

    -- 基本信息
    company_name VARCHAR(200),
    report_type VARCHAR(50),
    industry VARCHAR(100),

    -- 数据文件
    data_files JSONB,

    -- 当前阶段
    current_phase VARCHAR(50),
    phase_data JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 报告版本表
CREATE TABLE dd_report_versions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50),
    version_number INTEGER,
    version_name VARCHAR(100),

    report_content JSONB,
    change_summary TEXT,

    export_files JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 阶段日志表
CREATE TABLE dd_phase_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50),
    phase_name VARCHAR(50),
    phase_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API 端点

```python
@router.post("/api/v1/dd/sessions")
async def create_dd_session(request: DDSessionCreate):
    """创建尽调报告会话"""
    pass

@router.post("/api/v1/dd/sessions/{session_id}/continue")
async def continue_dd_session(...):
    """继续对话（迭代）"""
    pass

@router.get("/api/v1/dd/sessions/{session_id}/report")
async def get_current_report(session_id: str):
    """获取当前报告"""
    pass

@router.post("/api/v1/dd/sessions/{session_id}/export")
async def export_report(
    session_id: str,
    format: str = "pptx"  # pptx, pdf, docx
):
    """导出报告"""
    pass

@router.post("/api/v1/dd/sessions/{session_id}/revise")
async def revise_report(
    session_id: str,
    revision: ReportRevision
):
    """修改报告特定部分"""
    pass

@router.get("/api/v1/dd/sessions/{session_id}/versions")
async def get_report_versions(session_id: str):
    """获取所有版本"""
    pass

@router.post("/api/v1/dd/sessions/{session_id}/rollback")
async def rollback_to_version(
    session_id: str,
    version_id: int
):
    """回退到指定版本"""
    pass
```

---

## 总结

### 核心特性

✅ **对话式交互** - 自然语言多轮对话
✅ **逐步引导** - 按阶段收集信息
✅ **实时反馈** - 每步都展示结果
✅ **可视化** - 自动生成图表
✅ **支持迭代** - 可以修改任何部分
✅ **版本管理** - 保存所有版本，可回退
✅ **多格式导出** - PPT、PDF、Word

### 用户体验

```
新手："帮我看下这个公司的财报"
     → 系统引导上传
     → 自动分析
     → 生成报告

进阶："帮我做尽调报告，重点分析现金流"
     → 系统按重点分析
     → 展示详细结果
     → 迭代优化

专家："对比同行业，调整风险评估部分"
     → 精确修改
     → 生成新版本
     → 导出最终版
```

这个设计可以让用户通过不断对话，逐步完善尽调报告，支持任意次数的迭代和优化！
