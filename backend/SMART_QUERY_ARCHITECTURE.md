# 智能问数系统架构说明

## 📋 系统概述

智能问数系统是一个基于SQLite的数据查询和分析系统，允许用户使用自然语言提问，自动生成SQL查询，执行数据检索，生成可视化图表，并提供深度数据分析。

## 🏗️ 系统架构

```
用户提问
    ↓
前端界面
    ↓
API端点 (/api/v1/agent/query)
    ↓
Agent Service (选择smart_query_analyzer skill)
    ↓
Claude Agent SDK (执行skill)
    ↓
SQLite查询工具 (sqlite_query)
    ↓
SQLite数据库 (backend/data/sessions.db)
    ↓
返回数据结果
    ↓
调用echarts_chart生成图表
    ↓
数据分析与洞察
    ↓
返回给用户
```

## 📂 核心组件

### 1. SQLite查询服务
**文件**: [services/sqlite_query_service.py](services/sqlite_query_service.py)

**功能**:
- 管理SQLite数据库连接
- 执行SQL查询
- 获取表结构和表列表
- 测试数据库连接

**关键方法**:
```python
class SQLiteQueryService:
    - execute_query(query, params)  # 执行查询
    - get_tables()                   # 获取所有表
    - get_table_schema(table_name)   # 获取表结构
    - test_connection()              # 测试连接
    - analyze_business_data(table_name)  # 分析业务数据
```

### 2. SQLite工具集
**文件**: [tools/custom_tools.py](tools/custom_tools.py)

**功能**:
- 将SQLite服务封装为MCP工具
- 提供给skill使用

**可用工具**:
```python
@tool("sqlite_query")            # 执行SQL查询
@tool("sqlite_get_tables")        # 获取所有表名
@tool("sqlite_get_schema")        # 获取表结构
@tool("sqlite_test_connection")   # 测试数据库连接
```

### 3. Smart Query Analyzer Skill
**文件**: [.claude/skills/smart_query_analyzer/SKILL.md](../.claude/skills/smart_query_analyzer/SKILL.md)

**功能**:
- 深度理解用户问题
- 生成优化的SQL查询
- 执行查询获取数据
- 调用echarts_chart生成可视化
- 提供数据分析与洞察

**工作流程**:
1. **问题理解**: 识别数据维度、度量指标、查询类型
2. **SQL生成**: 根据问题生成优化的SQL
3. **查询执行**: 使用sqlite_query工具执行
4. **可视化**: 调用echarts_chart skill生成图表
5. **分析**: 提供深度数据洞察

### 4. 数据库
**位置**: `backend/data/sessions.db`

**表结构**:
- `users` - 用户表
- `roles` - 角色表
- `sessions` - 会话表
- `messages` - 消息表
- `business_scenarios` - 业务场景表
- `skills` - 技能表
- `user_feedback` - 用户反馈表
- 等等...

## 🔧 配置说明

### 无需额外配置

系统默认使用SQLite数据库，位于 `backend/data/sessions.db`。

**优势**:
- ✅ 无需配置数据库连接
- ✅ 无需安装额外服务
- ✅ 开箱即用
- ✅ 轻量级，易于部署

## 🚀 使用方法

### 方式1: 通过API调用

```bash
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询最近7天的用户活跃度",
    "use_skill": "smart_query_analyzer"
  }'
```

### 方式2: 通过前端界面

1. 打开前端界面
2. 输入问题: "查询最近7天的用户活跃度"
3. 系统自动识别并使用smart_query_analyzer skill
4. 返回查询结果、图表和分析

### 方式3: 直接使用SQLite工具

如果skill未激活，可以直接调用工具:

```python
from tools.custom_tools import sqlite_query_tool

result = await sqlite_query_tool({
    "query": "SELECT * FROM users LIMIT 10",
    "params": "[]"
})
```

## 📊 完整示例

### 用户问题
"查看最近7天各场景的会话数量"

### Skill处理流程

#### 1. 问题理解
```
核心需求: 统计会话数量
时间维度: 最近7天
分组维度: 场景(scenario_id)
度量指标: COUNT(*)
查询类型: 时间趋势+分组统计
```

#### 2. SQL生成
```sql
SELECT
    DATE(created_at) as date,
    associated_scenario_id as scenario_id,
    COUNT(*) as session_count
FROM sessions
WHERE created_at >= DATE('now', '-7 days')
  AND is_active = 1
GROUP BY DATE(created_at), associated_scenario_id
ORDER BY date, scenario_id
```

#### 3. 执行查询
调用工具: `sqlite_query`
参数:
```json
{
  "query": "SELECT DATE(created_at) as date, ...",
  "params": "[]"
}
```

#### 4. 查询结果
```json
[
  {"date": "2026-01-01", "scenario_id": 1, "session_count": 15},
  {"date": "2026-01-01", "scenario_id": 2, "session_count": 8},
  ...
]
```

#### 5. 生成可视化
调用echarts_chart生成折线图:
- X轴: 日期
- Y轴: 会话数
- 系列: 不同场景的折线

#### 6. 数据分析
```
**描述性分析**
- 7天总会话数: 234次
- 日均会话数: 33.4次
- 最活跃场景: 场景1（数据分析）

**趋势分析**
- 整体呈上升趋势
- 周末（1月6-7日）会话数最高

**关键发现**
- 场景1使用率最高，占比45%
- 场景3使用率最低，仅占比8%
- 建议推广场景1的最佳实践
```

## 🔌 工具集成

### 在allowed_tools中添加

修改 [backend/.env](.env):

```env
DEFAULT_ALLOWED_TOOLS=Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch,TodoWrite,mcp__custom_tools__sqlite_query,mcp__custom_tools__sqlite_get_tables,mcp__custom_tools__sqlite_get_schema,mcp__custom_tools__sqlite_test_connection
```

### 注册MCP服务器

在agent_service中添加custom_tools服务器:

```python
from tools.custom_tools import get_custom_tools_server

options = ClaudeAgentOptions(
    allowed_tools=[...],
    mcp_servers={
        "custom_tools": get_custom_tools_server()
    }
)
```

## 🧪 测试方法

### 1. 测试数据库连接

```python
from services.sqlite_query_service import get_sqlite_query_service

service = get_sqlite_query_service()
result = service.test_connection()
print(result)
```

### 2. 测试SQL查询

```python
from services.sqlite_query_service import get_sqlite_query_service

service = get_sqlite_query_service()
result = service.execute_query("SELECT * FROM users LIMIT 5")
print(result)
```

### 3. 测试工具调用

```python
from tools.custom_tools import sqlite_test_connection

result = await sqlite_test_connection({})
print(result)
```

## 📝 优势与限制

### ✅ 优势

1. **零配置**: 无需配置数据库连接
2. **轻量级**: SQLite嵌入式数据库，无需额外服务
3. **易集成**: 直接使用现有数据库
4. **高性能**: 对于中小型数据量性能优异
5. **跨平台**: 支持Windows、Linux、macOS

### ⚠️ 限制

1. **并发写入**: SQLite支持并发读取，但写入时需要锁
2. **数据量**: 适合中小型数据集（< 100GB）
3. **网络访问**: 不支持远程网络访问（仅本地）

## 🎯 最佳实践

### 1. SQL优化

```sql
-- ✅ 好的做法: 使用LIMIT
SELECT * FROM sessions LIMIT 100

-- ❌ 不好的做法: 全表扫描
SELECT * FROM sessions
```

### 2. 查询安全

```python
# ✅ 好的做法: 使用参数化查询
sqlite_query({
    "query": "SELECT * FROM users WHERE id = ?",
    "params": "[1]"
})

# ❌ 不好的做法: 字符串拼接
sqlite_query({
    "query": f"SELECT * FROM users WHERE id = {user_id}",
    "params": "[]"
})
```

### 3. 错误处理

```python
try:
    result = await sqlite_query_tool(args)
    if result.get("is_error"):
        logger.error(f"Query failed: {result['content']}")
except Exception as e:
    logger.error(f"Query error: {e}")
```

## 🔗 相关文档

- [SQLite查询服务API](services/sqlite_query_service.py)
- [SQLite工具集](tools/custom_tools.py)
- [Smart Query Analyzer Skill](../.claude/skills/smart_query_analyzer/SKILL.md)
- [ECharts图表生成Skill](../.claude/skills/echarts_chart/SKILL.md)

## 💡 常见问题

### Q1: 如何切换到MySQL?

A: 需要修改 `services/sqlite_query_service.py`，将SQLite连接改为MySQL连接，并更新配置。

### Q2: 如何查看数据库内容?

A: 使用DB Browser for SQLite工具，或调用 `sqlite_get_tables` 和 `sqlite_query` 工具。

### Q3: 如何添加自定义业务表?

A: 直接在sessions.db中创建新表，skill会自动识别。

### Q4: 查询性能如何优化?

A:
1. 添加索引
2. 使用LIMIT限制结果
3. 避免SELECT *
4. 合理使用WHERE条件

### Q5: 如何备份数据库?

A:
```bash
# 备份
cp backend/data/sessions.db backend/data/sessions.db.backup

# 或使用SQLite命令
sqlite3 backend/data/sessions.db ".backup sessions.db.backup"
```

---

**创建日期**: 2026-01-07
**版本**: 1.0.0
**维护者**: Backend Team
