"""
核心Agent服务 - 封装Claude Agent SDK

本服务提供两种与Claude交互的清晰模式:

1. 无状态单次查询 (query_once)
   - 使用 claude_agent_sdk.query() 函数
   - 每次查询都是独立的，没有对话上下文
   - 适用于: 简单问题、批量处理、自动化脚本
   - 无需会话管理

2. 有状态多轮会话 (query_in_session)
   - 使用持久化的 ClaudeSDKClient 实例
   - 在API调用之间维护对话上下文
   - 适用于: 聊天界面、交互式Agent、多轮对话
   - 需要SessionManager保持ClaudeSDKClient在不同HTTP请求间存活

与Claude SDK文档的关键区别:
- query() 函数: 单向，预先发送所有提示，接收所有响应
- ClaudeSDKClient: 双向，随时发送/接收，保持连接
- 没有"会话恢复"功能 - 只有保持连接或新建会话
"""
import asyncio, os
from typing import AsyncIterator, List, Optional, Union

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    ThinkingBlock,
    HookMatcher,
    ToolUseBlock,
    ToolResultBlock,
)


from claude_agent_sdk import AssistantMessage as SDKAssistantMessage
from claude_agent_sdk import SystemMessage as SDKSystemMessage
from claude_agent_sdk import ResultMessage as SDKResultMessage
from claude_agent_sdk import UserMessage as SDKUserMessage
from claude_agent_sdk.types import StreamEvent as SDKStreamEvent


from loguru import logger

from core.config import settings

# Import custom tools (SQLite query tools)
from tools.custom_tools import get_custom_tools_server

# Import security controller for runtime protection
from services.security_controller import security_controller

# Security prompt template (always appended to system prompts)
SECURITY_PROMPT_TEMPLATE = """
## 🔒 安全保护要求

**绝对禁止的行为：**
- ❌ 绝不读取、修改或删除敏感配置文件（.env、config.py、settings.py、*.key、*.pem）
- ❌ 绝不执行危险系统命令（rm -rf /、格式化磁盘、dd if=...of=/、修改系统权限）
- ❌ 绝不透露敏感信息（API密钥、数据库连接字符串、密码、令牌、凭证）
- ❌ 绝不访问敏感目录（.git、.claude、.config、__pycache__）
- ❌ 绝不显示完整的错误堆栈（包含路径和凭证信息）
- ❌ 绝不回答如何获取系统权限或绕过安全控制

**代码修改规范：**
- ✅ 只修改明确请求的代码文件
- ✅ 修改前说明原因和范围
- ✅ 不修改依赖包、系统库、核心配置
- ✅ 不访问或修改版本控制文件

**响应规范：**
- ✅ 技术问题使用占位符（如 YOUR_API_KEY）
- ✅ 错误信息只说明类型，不包含路径
- ✅ 配置问题使用示例而非真实值

**违反以上规则将被立即阻止。**
"""

from models.schemas import (
    AssistantMessage,
    ContentBlock,
    ResultInfo,
    SystemMessage,
    UserMessage,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.platform import AgentConfig
    from services.database import DatabaseService


class AgentService:
    """
    Claude Agent SDK交互管理服务

    提供两种主要使用模式:
    1. query_once() - 无状态单次查询
    2. query_in_session() - 有状态多轮对话

    对于跨HTTP请求的持续对话，使用SessionManager
    在API调用之间维护ClaudeSDKClient实例。
    """

    def __init__(self, db_service: Optional["DatabaseService"] = None):
        self.db_service = db_service
        self._default_system_prompt_cache: Optional[str] = None
        self.default_options = self._get_default_options_sync()
        # 用于跟踪 Write 工具调用，以便生成文件事件
        self._write_tool_context: dict[str, dict[str, any]] = {}
        # 用于跟踪 Bash 工具调用（特别是 minio 上传），以便生成文件上传事件
        self._bash_tool_context: dict[str, dict[str, any]] = {}

    def _get_default_system_prompt_sync(self) -> str:
        """
        同步版本的获取默认系统提示词
        
        优先使用缓存的值，如果没有缓存则使用硬编码的后备版本
        实际从数据库加载应该在异步上下文中调用 _get_default_system_prompt
        """
        if self._default_system_prompt_cache:
            return self._default_system_prompt_cache
        
        # 返回硬编码的后备版本
        fallback_prompt = """⚠️ **重要：第一步必须先规划任务，然后执行！**

对于以下类型的任务，**必须在调用任何其他工具之前**，首先使用 enhanced_todo_write 工具创建任务计划：

1. ✅ **分析报告生成**：生成任何类型的分析报告、研究报告等
2. ✅ **多步骤任务**：需要3个或更多步骤才能完成的任务
3. ✅ **复杂查询**：涉及多个维度、需要多个工具或需要分阶段完成的任务
4. ✅ **用户明确要求**：用户要求生成报告、输出详尽信息时

### 🎯 必须遵守的执行顺序：

**第一步：立即创建任务计划**
- 接收用户请求后，**立即、马上**调用 `enhanced_todo_write` 工具
- **必须使用 enhanced_todo_write**，它支持层级任务结构（1, 1.1, 1.2）
- **不要使用 TodoWrite**，只使用 enhanced_todo_write
- **不要先搜索、不要先查询、不要先做任何其他操作**
- 任务计划应该清晰列出所有步骤，使用层级结构（1, 1.1, 1.2）

**第二步：按计划执行并实时更新**
- 创建任务计划后，再开始调用其他工具（搜索、查询等）
- 每完成一个任务，立即调用 enhanced_todo_write 更新状态（保持实时性）

### 📋 任务规划示例：

用户问："分析某项目的基本情况并输出报告"

❌ **错误做法**（慢）：
1. 先搜索专业知识库
2. 再搜索相关数据
3. 输出内容
4. 最后才调用 enhanced_todo_write

✅ **正确做法**（快，实时进度）：
1. **立即调用** enhanced_todo_write 创建任务计划（所有任务初始状态为 `pending`）：
   ```
   1 数据收集
     1.1 搜索基本信息
     1.2 搜索相关数据
     1.3 查阅参考资料
   2 报告编写
     2.1 编写基本信息章节
     2.2 编写数据分析章节
     2.3 编写总结结论章节
   ```

2. **开始执行任务 1.1**：调用 enhanced_todo_write，将任务 1.1 状态更新为 `in_progress`

3. **完成任务 1.1**：调用 enhanced_todo_write，将任务 1.1 状态更新为 `completed`

4. **开始执行任务 1.2**：调用 enhanced_todo_write，将任务 1.2 状态更新为 `in_progress`

5. **完成任务 1.2**：调用 enhanced_todo_write，将任务 1.2 状态更新为 `completed`

6. **重复上述过程**：每开始一个新任务就更新为 `in_progress`，每完成一个任务就更新为 `completed`

7. **关键**：不要等到所有任务完成后再调用 enhanced_todo_write，而是每完成一个任务就调用一次，让用户实时看到进度

---

你是一个智能助手，擅长使用工具完成复杂任务。

## 其他规范

这样可以：
- 让用户立即了解工作计划
- 确保任务完整执行
- 提供清晰的工作流程
- 实时显示任务进度
- **避免用户长时间等待第一次响应**

## 文件输出要求

**核心原则**：所有通过 Write 工具创建的文件，**必须**立即使用 minio_uploader 上传到远端 MinIO 存储。这是**强制要求**，不能省略。

当生成报告或长篇内容时，按以下流程执行：

1. **字符流输出**：首先以字符流形式输出内容，让用户实时看到进度和内容预览
2. **文件保存**：使用 Write 工具将完整内容保存到文件（建议保存到 work_dir/reports/ 目录）
3. **文件上传（必需）**：**立即**使用 Bash 工具执行 MinIO 上传脚本，将文件上传到 MinIO 并获取可访问的 URL
   - **重要**：Write 工具执行成功后，**必须紧接着**执行 minio_uploader 上传
   - **不能跳过**：即使文件已保存到本地，也必须上传到远端
   - **自动化流程**：将文件保存和上传视为一个完整的、不可分割的操作

### MinIO 文件上传方法

**强制要求**：每次使用 Write 工具创建文件后，**必须立即**使用 Bash 工具执行以下命令上传文件。这是**自动化流程的一部分**，不能省略或延迟。

```bash
python .claude/skills/minio_uploader/simple_minio_uploader.py <文件路径>
```

**命令参数说明**：
- `<文件路径>`：必需，要上传的文件的路径。使用相对路径（相对于当前工作目录），例如：
  - `work_dir/reports/alibaba_analysis_20250101.md`
  - `reports/alibaba_analysis_20250101.md`
- `[对象名称]`：可选，MinIO 中的存储路径（默认使用原文件名）
- `[force_download]`：可选，是否强制下载（true/false，默认 false）
- `[存储桶]`：可选，存储桶名称（默认：agentic）

**配置说明**：
- MinIO 配置已经内置在脚本中，**无需用户提供任何配置信息**
- 脚本会自动从环境变量或默认配置读取 MinIO 连接信息
- 上传成功后，脚本会输出公开访问链接

**执行步骤**：
1. 确认文件已成功保存（使用 Read 工具验证或通过 Write 工具的输出确认）
2. 使用 Bash 工具执行上传命令：
   - 脚本路径：`.claude/skills/minio_uploader/simple_minio_uploader.py`（相对于当前工作目录）
   - 如果当前目录不是项目根目录，可以尝试：`../.claude/skills/minio_uploader/simple_minio_uploader.py`
   - 文件路径：使用相对路径（例如：`work_dir/reports/文件名.md`）
3. 从命令输出中提取公开访问链接（查找包含 "Public访问地址:" 或 "🔗" 的输出行）
4. 在回复中向用户提供文件访问链接

### 适用场景

- 生成分析报告（PDF、Markdown、HTML 等格式）
- 生成长篇文档（超过 1000 字的文档）
- 生成包含图表、表格的复杂报告
- 用户明确要求保存文件时

### 文件命名规范

- 使用有意义的文件名，包含报告类型和日期
- 示例：`alibaba_analysis_report_20250101.md`、`sales_data_analysis_20250101.html`
- 保存到 `work_dir/reports/` 目录下

### 完整执行示例

当用户要求"生成阿里巴巴分析报告"时：

1. **字符流输出**：先以字符流形式输出报告内容（让用户实时看到）
2. **保存文件**：使用 Write 工具保存到文件：`work_dir/reports/alibaba_analysis_20250101.md`
3. **立即上传文件（必需步骤）**：Write 工具执行成功后，**必须立即**使用 Bash 工具执行上传：
   ```bash
   python .claude/skills/minio_uploader/simple_minio_uploader.py work_dir/reports/alibaba_analysis_20250101.md
   ```
   **注意**：这一步是**强制性的**，不能省略。Write 和 minio_uploader 是**配对操作**。
4. **提取链接**：从命令输出中获取公开访问链接（格式：`http://your-minio-server:9000/bucket/文件名`）
5. **回复用户**：在回复中提供文件访问链接，告知用户可通过链接访问文件

### Write 工具使用规范

**重要规则**：
- ✅ **必须配对使用**：Write 工具 + minio_uploader 是一个完整的操作单元
- ✅ **立即上传**：Write 工具执行成功后，立即执行 minio_uploader 上传
- ❌ **禁止只保存不上传**：不能只使用 Write 工具保存文件而不上传
- ❌ **禁止延迟上传**：不能在多个操作后才上传，必须在 Write 后立即上传

**工作流程**：
```
Write 工具创建文件 → 立即执行 minio_uploader 上传 → 获取 URL → 完成任务
```

这样可以：
- 用户实时看到内容进度
- 文件被持久化保存到本地
- 文件自动上传到远端 MinIO，可通过 URL 分享和访问
- 完整的自动化流程，无需用户手动操作
- 所有生成的文件都有远端备份和访问链接

## 其他要求

- 优先使用合适的工具完成任务
- 对于文件操作，使用 Write 工具保存结果，**并立即使用 minio_uploader 上传到远端**
- 对于搜索任务，使用 WebSearch 工具获取最新信息
- 所有输出使用中文

## 重要提醒

**文件操作规范**：
- 每次使用 Write 工具创建文件后，**必须立即**使用 Bash 工具执行 minio_uploader 上传
- Write 工具和 minio_uploader 是**配对操作**，不能分开执行
- 所有生成的文件都应该有远端备份和可访问的 URL
- 这是系统要求，不是可选项
"""
        self._default_system_prompt_cache = fallback_prompt
        return fallback_prompt

    async def _get_default_system_prompt(self) -> str:
        """
        获取默认的系统提示词
        
        优先从数据库的 system_prompts 表中读取 is_default=True 的提示词
        如果数据库中没有，则使用硬编码的默认提示词作为后备
        """
        # 如果已有缓存，直接返回
        if self._default_system_prompt_cache:
            return self._default_system_prompt_cache
        
        # 尝试从数据库读取默认提示词
        if self.db_service:
            try:
                from services.query_service import get_query_service
                query_service = get_query_service()
                default_prompt = await query_service.get_default_system_prompt()
                
                if default_prompt and default_prompt.get('content'):
                    logger.info(f"Using default system prompt from database: {default_prompt.get('prompt_id')} ({default_prompt.get('name')})")
                    self._default_system_prompt_cache = default_prompt['content']
                    return default_prompt['content']
            except Exception as e:
                logger.warning(f"Failed to load default system prompt from database: {e}, using fallback")
        
        # 后备：使用硬编码的默认提示词
        fallback_prompt = """⚠️ **重要：第一步必须先规划任务，然后执行！**

对于以下类型的任务，**必须在调用任何其他工具之前**，首先使用 enhanced_todo_write 工具创建任务计划：

1. ✅ **分析报告生成**：生成任何类型的分析报告、研究报告等
2. ✅ **多步骤任务**：需要3个或更多步骤才能完成的任务
3. ✅ **复杂查询**：涉及多个维度、需要多个工具或需要分阶段完成的任务
4. ✅ **用户明确要求**：用户要求生成报告、输出详尽信息时

### 🎯 必须遵守的执行顺序：

**第一步：立即创建任务计划**
- 接收用户请求后，**立即、马上**调用 `enhanced_todo_write` 工具
- **必须使用 enhanced_todo_write**，它支持层级任务结构（1, 1.1, 1.2）
- **不要使用 TodoWrite**，只使用 enhanced_todo_write
- **不要先搜索、不要先查询、不要先做任何其他操作**
- 任务计划应该清晰列出所有步骤，使用层级结构（1, 1.1, 1.2）

**第二步：按计划执行并实时更新**
- 创建任务计划后，再开始调用其他工具（搜索、查询等）
- **⚠️ 关键：必须实时更新任务状态，不要等到所有任务完成后再更新**
- **每开始一个新任务时**：立即调用 enhanced_todo_write，将该任务状态更新为 `in_progress`
- **每完成一个任务时**：立即调用 enhanced_todo_write，将该任务状态更新为 `completed`
- **必须保持实时性**：每完成一个子任务就更新一次，让用户能够实时看到进度
- **不要等到所有任务完成后再调用 enhanced_todo_write**，这样用户无法看到实时进度

### 📋 任务规划示例：

用户问："分析某项目的基本情况并输出报告"

❌ **错误做法**（慢）：
1. 先搜索专业知识库
2. 再搜索相关数据
3. 输出内容
4. 最后才调用 enhanced_todo_write

✅ **正确做法**（快，实时进度）：
1. **立即调用** enhanced_todo_write 创建任务计划（所有任务初始状态为 `pending`）：
   ```
   1 数据收集
     1.1 搜索基本信息
     1.2 搜索相关数据
     1.3 查阅参考资料
   2 报告编写
     2.1 编写基本信息章节
     2.2 编写数据分析章节
     2.3 编写总结结论章节
   ```

2. **开始执行任务 1.1**：调用 enhanced_todo_write，将任务 1.1 状态更新为 `in_progress`

3. **完成任务 1.1**：调用 enhanced_todo_write，将任务 1.1 状态更新为 `completed`

4. **开始执行任务 1.2**：调用 enhanced_todo_write，将任务 1.2 状态更新为 `in_progress`

5. **完成任务 1.2**：调用 enhanced_todo_write，将任务 1.2 状态更新为 `completed`

6. **重复上述过程**：每开始一个新任务就更新为 `in_progress`，每完成一个任务就更新为 `completed`

7. **关键**：不要等到所有任务完成后再调用 enhanced_todo_write，而是每完成一个任务就调用一次，让用户实时看到进度

---

你是一个智能助手，擅长使用工具完成复杂任务。

## 文件输出要求

**核心原则**：所有通过 Write 工具创建的文件，**必须**立即使用 minio_uploader 上传到远端 MinIO 存储。这是**强制要求**，不能省略。

当生成报告或长篇内容时，按以下流程执行：

1. **字符流输出**：首先以字符流形式输出内容，让用户实时看到进度和内容预览
2. **文件保存**：使用 Write 工具将完整内容保存到文件（建议保存到 work_dir/reports/ 目录）
3. **文件上传（必需）**：**立即**使用 Bash 工具执行 MinIO 上传脚本，将文件上传到 MinIO 并获取可访问的 URL
   - **重要**：Write 工具执行成功后，**必须紧接着**执行 minio_uploader 上传
   - **不能跳过**：即使文件已保存到本地，也必须上传到远端
   - **自动化流程**：将文件保存和上传视为一个完整的、不可分割的操作

### MinIO 文件上传方法

**强制要求**：每次使用 Write 工具创建文件后，**必须立即**使用 Bash 工具执行以下命令上传文件。这是**自动化流程的一部分**，不能省略或延迟。

```bash
python .claude/skills/minio_uploader/simple_minio_uploader.py <文件路径>
```

**命令参数说明**：
- `<文件路径>`：必需，要上传的文件的路径。使用相对路径（相对于当前工作目录），例如：
  - `work_dir/reports/alibaba_analysis_20250101.md`
  - `reports/alibaba_analysis_20250101.md`
- `[对象名称]`：可选，MinIO 中的存储路径（默认使用原文件名）
- `[force_download]`：可选，是否强制下载（true/false，默认 false）
- `[存储桶]`：可选，存储桶名称（默认：agentic）

**配置说明**：
- MinIO 配置已经内置在脚本中，**无需用户提供任何配置信息**
- 脚本会自动从环境变量或默认配置读取 MinIO 连接信息
- 上传成功后，脚本会输出公开访问链接

**执行步骤**：
1. 确认文件已成功保存（使用 Read 工具验证或通过 Write 工具的输出确认）
2. 使用 Bash 工具执行上传命令：
   - 脚本路径：`.claude/skills/minio_uploader/simple_minio_uploader.py`（相对于当前工作目录）
   - 如果当前目录不是项目根目录，可以尝试：`../.claude/skills/minio_uploader/simple_minio_uploader.py`
   - 文件路径：使用相对路径（例如：`work_dir/reports/文件名.md`）
3. 从命令输出中提取公开访问链接（查找包含 "Public访问地址:" 或 "🔗" 的输出行）
4. 在回复中向用户提供文件访问链接

### 适用场景

- 生成分析报告（PDF、Markdown、HTML 等格式）
- 生成长篇文档（超过 1000 字的文档）
- 生成包含图表、表格的复杂报告
- 用户明确要求保存文件时

### 文件命名规范

- 使用有意义的文件名，包含报告类型和日期
- 示例：`alibaba_analysis_report_20250101.md`、`sales_data_analysis_20250101.html`
- 保存到 `work_dir/reports/` 目录下

### 完整执行示例

当用户要求"生成阿里巴巴分析报告"时：

1. **字符流输出**：先以字符流形式输出报告内容（让用户实时看到）
2. **保存文件**：使用 Write 工具保存到文件：`work_dir/reports/alibaba_analysis_20250101.md`
3. **立即上传文件（必需步骤）**：Write 工具执行成功后，**必须立即**使用 Bash 工具执行上传：
   ```bash
   python .claude/skills/minio_uploader/simple_minio_uploader.py work_dir/reports/alibaba_analysis_20250101.md
   ```
   **注意**：这一步是**强制性的**，不能省略。Write 和 minio_uploader 是**配对操作**。
4. **提取链接**：从命令输出中获取公开访问链接（格式：`http://your-minio-server:9000/bucket/文件名`）
5. **回复用户**：在回复中提供文件访问链接，告知用户可通过链接访问文件

### Write 工具使用规范

**重要规则**：
- ✅ **必须配对使用**：Write 工具 + minio_uploader 是一个完整的操作单元
- ✅ **立即上传**：Write 工具执行成功后，立即执行 minio_uploader 上传
- ❌ **禁止只保存不上传**：不能只使用 Write 工具保存文件而不上传
- ❌ **禁止延迟上传**：不能在多个操作后才上传，必须在 Write 后立即上传

**工作流程**：
```
Write 工具创建文件 → 立即执行 minio_uploader 上传 → 获取 URL → 完成任务
```

这样可以：
- 用户实时看到内容进度
- 文件被持久化保存到本地
- 文件自动上传到远端 MinIO，可通过 URL 分享和访问
- 完整的自动化流程，无需用户手动操作
- 所有生成的文件都有远端备份和访问链接

## 其他要求

- 优先使用合适的工具完成任务
- 对于文件操作，使用 Write 工具保存结果，**并立即使用 minio_uploader 上传到远端**
- 对于搜索任务，使用 WebSearch 工具获取最新信息
- 所有输出使用中文

## 重要提醒

**文件操作规范**：
- 每次使用 Write 工具创建文件后，**必须立即**使用 Bash 工具执行 minio_uploader 上传
- Write 工具和 minio_uploader 是**配对操作**，不能分开执行
- 所有生成的文件都应该有远端备份和可访问的 URL
- 这是系统要求，不是可选项
"""
        self._default_system_prompt_cache = fallback_prompt
        return fallback_prompt

    def _get_default_options_sync(self) -> ClaudeAgentOptions:
        """同步版本的获取默认选项（用于初始化）"""
        # 使用硬编码的默认提示词作为初始值
        # 实际使用时会在异步方法中从数据库读取
        return ClaudeAgentOptions(
            allowed_tools=settings.allowed_tools_list,
            permission_mode=settings.permission_mode,
            max_turns=settings.max_turns,
            model=settings.default_model,
            cwd=str(settings.work_dir),
            system_prompt=None,  # 将在异步方法中设置
        )
    
    async def _get_default_options(self) -> ClaudeAgentOptions:
        """从配置获取默认Agent选项"""
        default_prompt = await self._get_default_system_prompt()
        return ClaudeAgentOptions(
            allowed_tools=settings.allowed_tools_list,
            permission_mode=settings.permission_mode,
            max_turns=settings.max_turns,
            model=settings.default_model,
            cwd=str(settings.work_dir),
            system_prompt=default_prompt,
        )

    def create_options(
        self,
        system_prompt: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        model: Optional[str] = None,
        include_partial_messages: bool = False,
        agent_config: Optional["AgentConfig"] = None,  # Platform configuration
        **kwargs
    ) -> ClaudeAgentOptions:
        """
        创建带自定义选项的ClaudeAgentOptions

        参数:
            system_prompt: Agent的自定义系统提示词（请求级别，最高优先级）
            allowed_tools: Claude可使用的工具列表 (None = 所有默认工具)
            model: 要使用的模型 (如 'claude-sonnet-4-5', 'claude-opus-4-5')
            include_partial_messages: 是否启用增量流式消息 (SSE模式)
            agent_config: 平台配置对象（已合并用户、场景等配置）
            **kwargs: 传递给ClaudeAgentOptions的其他选项

        返回:
            配置好自定义选项的ClaudeAgentOptions
        
        注意：
            - 如果提供了 agent_config，会使用其中的配置作为基础
            - 请求级别的参数（system_prompt, allowed_tools, model）会覆盖 agent_config
            - 这确保了配置优先级：请求 > 会话 > 用户  > 场景 > 全局
        """
        # 如果提供了平台配置，使用它作为基础
        if agent_config:
            # 🎯 cwd 使用项目根目录，Skills 在项目根的 .claude/skills/
            # work_dir 作为 add_dir，便于文件操作
            project_root = str(settings.work_dir.parent)  # aigc/

            options_dict = {
                "allowed_tools": agent_config.allowed_tools or self.default_options.allowed_tools,
                "permission_mode": agent_config.permission_mode or self.default_options.permission_mode,
                "max_turns": agent_config.max_turns or self.default_options.max_turns,
                "model": agent_config.model or self.default_options.model,
                "cwd": agent_config.cwd or project_root,  # 项目根目录
                "add_dirs": [str(settings.work_dir)],  # work_dir 作为额外可访问目录
                "include_partial_messages": include_partial_messages,
                # 重要：setting_sources 必须使用配置中的值，不能回退到默认值
                # 如果配置中没有设置，应该保持 None（不加载 skill）
                "setting_sources": agent_config.setting_sources,  # 可能是 None，这是正确的
            }
            
            # 系统提示词：优先使用请求级别的，否则使用配置中的
            if system_prompt:
                options_dict["system_prompt"] = system_prompt
            elif agent_config.system_prompt:
                options_dict["system_prompt"] = agent_config.system_prompt
            else:
                # 使用缓存的默认提示词，如果没有缓存则使用硬编码的后备版本
                options_dict["system_prompt"] = self._get_default_system_prompt_sync()

            # 自定义工具（MCP servers）- 必须正确传递
            if agent_config.custom_tools:
                options_dict["mcp_servers"] = agent_config.custom_tools
                logger.info(f"[AgentService] ✅ Applied custom_tools (MCP servers): {list(agent_config.custom_tools.keys()) if isinstance(agent_config.custom_tools, dict) else 'N/A'}")
            else:
                # 使用默认的 custom_tools (SQLite tools)
                options_dict["mcp_servers"] = {
                    "custom_tools": get_custom_tools_server()
                }
                logger.info(f"[AgentService] Using default custom_tools (MCP servers): custom_tools")

            # 禁用自动加载的 agents（避免加载 ~4,000 tokens 的无用数据）
            # 当使用 setting_sources 加载 skills 时，CLI 会自动加载所有默认 agents
            # 我们通过显式设置 agents={} 来禁用这个行为
            if agent_config.setting_sources:
                options_dict["agents"] = {}
                logger.info(f"[AgentService] ✅ Disabled auto-loading of default agents to save tokens")
        else:
            # 没有平台配置，使用原有逻辑（保持向后兼容）
            # 默认不加载 skill，除非用户明确配置
            # 🎯 cwd 使用项目根目录，work_dir 作为 add_dir
            project_root = str(settings.work_dir.parent)  # aigc/

            options_dict = {
                "allowed_tools": allowed_tools or self.default_options.allowed_tools,
                "permission_mode": self.default_options.permission_mode,
                "max_turns": self.default_options.max_turns,
                "model": model or self.default_options.model,
                "cwd": project_root,  # 项目根目录
                "add_dirs": [str(settings.work_dir)],  # work_dir 作为额外可访问目录
                "include_partial_messages": include_partial_messages,
                "setting_sources": None,  # 默认不加载 skill，需要用户明确配置
                "mcp_servers": {
                    "custom_tools": get_custom_tools_server()
                }
            }

            # 系统提示词：优先使用自定义的，否则使用默认的
            if system_prompt:
                options_dict["system_prompt"] = system_prompt
            elif hasattr(self.default_options, 'system_prompt') and self.default_options.system_prompt:
                options_dict["system_prompt"] = self.default_options.system_prompt
            else:
                options_dict["system_prompt"] = self._get_default_system_prompt_sync()
        
        # 请求级别的参数覆盖配置（最高优先级）
        if allowed_tools is not None:
            options_dict["allowed_tools"] = allowed_tools
        if model is not None:
            options_dict["model"] = model
        if system_prompt is not None:
            options_dict["system_prompt"] = system_prompt

        options_dict.update(kwargs)

        # 添加安全控制回调（如果启用）
        if hasattr(settings, 'enable_security_control') and settings.enable_security_control:
            options_dict["can_use_tool"] = security_controller.can_use_tool
            logger.info("[AgentService] ✅ Security control enabled (can_use_tool callback attached)")

        # 🔒 始终追加安全提示词到所有系统提示词（最后执行，确保不被覆盖）
        if hasattr(settings, 'enable_security_control') and settings.enable_security_control:
            if "system_prompt" in options_dict and options_dict["system_prompt"]:
                # 确保安全提示词没有被包含过（避免重复追加）
                if "## 🔒 安全保护要求" not in options_dict["system_prompt"]:
                    options_dict["system_prompt"] = options_dict["system_prompt"] + "\n\n" + SECURITY_PROMPT_TEMPLATE
                    logger.info("[AgentService] ✅ Security prompt appended (final step)")
                else:
                    logger.debug("[AgentService] Security prompt already exists, skipping append")
        
        # 📋 添加 Todo 进度跟踪 Hook（如果启用）
        try:
            from services.todo_progress_hook import get_todo_progress_hooks
            todo_hooks = get_todo_progress_hooks()
            if "hooks" not in options_dict:
                options_dict["hooks"] = {}
            # 合并现有的 hooks（如果有）
            for hook_type, hook_matchers in todo_hooks.items():
                if hook_type not in options_dict["hooks"]:
                    options_dict["hooks"][hook_type] = []
                options_dict["hooks"][hook_type].extend(hook_matchers)
            logger.info("[AgentService] ✅ Todo progress tracking hooks enabled")
        except Exception as e:
            logger.warning(f"[AgentService] Failed to load todo progress hooks: {e}")

        # 📁 文件操作路径指引（确保文件在 work_dir 下操作）
        work_dir_instruction = f"""

## 📁 文件操作路径规范

所有文件操作请在 **work_dir/** 目录下进行：

**报告文档**：请保存到 `work_dir/reports/` 目录
**图表可视化**：请保存到 `work_dir/charts/` 目录
**临时文件**：请保存到 `work_dir/temp/` 目录
**其他文件**：请优先使用 `work_dir/` 作为根目录

**示例路径**：
- `work_dir/reports/数据分析报告.md`
- `work_dir/charts/趋势图.png`
- `work_dir/temp/临时数据.csv`

**重要**：使用相对路径 `work_dir/...` 而不是绝对路径
"""
        if agent_config:
            final_prompt = options_dict.get('system_prompt', '')
            if final_prompt:
                options_dict['system_prompt'] = final_prompt + work_dir_instruction
                logger.info(f"[AgentService] ✅ Added work_dir path instruction to system prompt")

        # 如果配置中指定了技能ID，在系统提示词中添加技能限制指令
        # 注意：SDK 的 setting_sources 只能控制从哪些位置加载技能，不能指定具体技能名称
        # 因此我们通过在系统提示词中添加指令来限制 Claude 只使用指定的技能
        if agent_config and agent_config.enabled_skill_ids:
            final_prompt = options_dict.get('system_prompt', '')
            if final_prompt:
                skill_instruction = f"""

## 可用技能限制

你只能使用以下指定的技能：
{chr(10).join(f"- {skill_id}" for skill_id in agent_config.enabled_skill_ids)}

**重要**：
- 不要使用其他技能，即使它们在你的技能列表中可用
- 只使用上述明确列出的技能
- 如果用户请求需要使用其他技能，请告知用户当前场景只支持上述技能
"""
                options_dict['system_prompt'] = final_prompt + skill_instruction
                logger.info(f"[AgentService] ✅ Added skill restriction to system prompt: {agent_config.enabled_skill_ids}")

        # Log final configuration that will be sent to Claude
        final_system_prompt = options_dict.get('system_prompt', '')
        allowed_tools_list = options_dict.get('allowed_tools', [])
        setting_sources = options_dict.get('setting_sources')
        mcp_servers = options_dict.get('mcp_servers')
        enabled_skill_ids = agent_config.enabled_skill_ids if agent_config else None
        
        logger.info(f"[AgentService] Final ClaudeAgentOptions configuration:")
        logger.info(f"  - model: {options_dict.get('model')}")
        logger.info(f"  - allowed_tools: {len(allowed_tools_list)} tools - {allowed_tools_list}")
        logger.info(f"  - permission_mode: {options_dict.get('permission_mode')}")
        logger.info(f"  - max_turns: {options_dict.get('max_turns')}")
        logger.info(f"  - cwd: {options_dict.get('cwd')}")
        logger.info(f"  - add_dirs: {options_dict.get('add_dirs')} (additional accessible directories)")
        logger.info(f"  - setting_sources: {setting_sources} (skills: {'ENABLED' if setting_sources else 'DISABLED'})")
        logger.info(f"  - enabled_skill_ids: {enabled_skill_ids} (specific skills to use)")
        logger.info(f"  - mcp_servers: {list(mcp_servers.keys()) if mcp_servers else 'None'} (custom tools)")
        logger.info(f"  - system_prompt: {'SET' if final_system_prompt else 'NOT SET'}")
        if final_system_prompt:
            logger.info(f"  - system_prompt length: {len(final_system_prompt)} characters")
            logger.info(f"  - system_prompt preview (first 200 chars): {final_system_prompt[:200]}...")
        logger.info(f"  - has_platform_config: {agent_config is not None}")

        return ClaudeAgentOptions(**options_dict)

    @property
    def work_dir(self) -> str:
        """获取Agent操作的工作目录"""
        return str(settings.work_dir)

    # =========================================================================
    # 模式1: 无状态单次查询
    # =========================================================================

    async def query_once(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        model: Optional[str] = None,
        include_partial_messages: bool = False,
    ) -> AsyncIterator[Union[AssistantMessage, SystemMessage, ResultInfo, ContentBlock, SDKUserMessage]]:
        """
        执行无状态单次查询，使用 claude_agent_sdk.query()

        每次调用创建一个全新的Claude会话 - 调用之间不保留对话上下文
        每次查询都是完全独立的

        适用于:
            - 简单的一次性问题 ("2+2等于几?")
            - 批量处理独立提示
            - 代码生成或分析任务
            - 自动化脚本和CI/CD管道
            - 提前知道所有输入的场景

        不适用于:
            - 多轮对话 (请使用 query_in_session)
            - 需要上下文的聊天界面 (请使用 query_in_session)

        参数:
            prompt: 发送给Claude的用户提示
            system_prompt: 可选的自定义系统提示
            allowed_tools: 可选的允许工具列表
            model: 可选的模型选择 (如 'claude-sonnet-4-5')
            include_partial_messages: 是否启用增量流式 (逐字符/词传输)

        生成:
            AssistantMessage: Claude的响应，包含内容块
            SystemMessage: 处理过程中的系统更新
            ResultInfo: 包含成本、时间、轮次的最终结果
            ContentBlock: 当启用增量流式时，返回文本片段 (type="text_delta")

        示例:
            ```python
            # 普通模式
            async for message in agent_service.query_once("法国的首都是哪里?"):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if block.type == "text":
                            print(f"Claude: {block.text}")
                elif isinstance(message, ResultInfo):
                    print(f"成本: ${message.total_cost_usd:.4f}")

            # 增量流式模式
            async for message in agent_service.query_once(
                "法国的首都是哪里?",
                include_partial_messages=True
            ):
                if isinstance(message, ContentBlock) and message.type == "text_delta":
                    print(message.text, end="", flush=True)  # 逐字符打印
            ```
        """
        from claude_agent_sdk import query

        options = self.create_options(
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            model=model,
            include_partial_messages=include_partial_messages,
        )

        logger.info(
            f"[query_once] Starting one-shot query: {prompt[:100]}..., "
            f"model={options.model}"
        )

        try:
            async for sdk_message in query(prompt=prompt, options=options):
                converted = await self._convert_sdk_message(sdk_message, session_id="once")
                if converted:
                    yield converted

            logger.info(f"[query_once] Query completed successfully")

        except Exception as e:
            logger.error(f"[query_once] Error during query: {e}", exc_info=True)
            yield ResultInfo(
                subtype="error",
                is_error=True,
                duration_ms=0,
                num_turns=0,
                session_id="once",
                result=str(e)
            )

    # =========================================================================
    # 模式2: 有状态多轮会话
    # =========================================================================

    async def query_in_session(
        self,
        prompt: str,
        session_id: str,
        include_partial_messages: bool = False,
        user_id: Optional[int] = None,  # 用户ID，用于生成 work_dir 路径
        session_manager=None,  # 可选：用于检查是否有消息记录
        agent_config: Optional["AgentConfig"] = None,  # 平台配置（可选）
    ) -> AsyncIterator[Union[AssistantMessage, SystemMessage, ResultInfo, ContentBlock, SDKUserMessage]]:
        """
        在现有ClaudeSDKClient会话中执行查询

        重要实现说明:
        - 每次查询创建新的 client 实例，使用 resume 参数恢复会话上下文
        - ClaudeSDKClient 通过 resume=session_id 恢复对话历史
        - 使用 async with 确保正确清理，避免状态污染

        这使得Claude能够记住同一会话中之前消息的上下文，
        实现真正的多轮对话。

        适用于:
            - 交互式聊天界面
            - 需要上下文的多轮对话
            - Claude需要记住之前交流的场景
            - 构建对话式Agent

        参数:
            prompt: 要发送的用户提示
            session_id: 会话标识符，用于 resume 恢复对话上下文
            include_partial_messages: 是否启用增量流式 (SSE mode with text deltas)

        生成:
            AssistantMessage: Claude的响应，包含内容块
            SystemMessage: 处理过程中的系统更新
            ResultInfo: 包含成本、时间、轮次的最终结果
            ContentBlock: 当启用增量流式时，返回文本片段 (type="text_delta")

        示例:
            ```python
            # 在API端点中:
            session_manager = get_session_manager()
            session = await session_manager.get_session(session_id)

            async for message in agent_service.query_in_session(
                prompt=prompt,
                session_id=session_id,
                include_partial_messages=True  # 启用增量流式
            ):
                # 处理消息
                ...
            ```
        """

        # 获取原始的 options（从 session 中保存的）
        # 注意：这里的 client 只用来获取 options，实际查询会创建新的实例
        logger.info(
            f"[query_in_session] Creating new client with resume={session_id}: "
            f"prompt={prompt[:100]}..., "
            f"include_partial_messages={include_partial_messages}"
        )

        try:
            # 获取options（通过反射或直接访问）
            # ClaudeSDKClient 在创建时保存了 options
            # 如果提供了 agent_config，使用它来创建选项
            options = self.create_options(
                include_partial_messages=include_partial_messages,
                agent_config=agent_config  # 传递平台配置
            )

            # ⚠️ 重要：检查是否需要使用 resume
            # 只要 session_id 存在且数据库中有消息记录，就使用 resume
            # 如果这是第一次查询（数据库中还没有消息），不使用 resume，让 SDK 创建新对话
            should_resume = False
            if session_id:
                if session_manager:
                    # 检查数据库中是否有消息记录
                    try:
                        import sqlite3

                        # 直接查询数据库获取消息数量
                        db_path = session_manager.db_service.db_path
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
                            (session_id,)
                        )
                        result = cursor.fetchone()
                        conn.close()

                        if result and result[0] > 0:
                            # 有消息记录，使用 resume
                            should_resume = True
                            logger.info(
                                f"[query_in_session] Session has {result[0]} message(s), will use resume"
                            )
                        else:
                            # 没有消息记录，创建新对话
                            logger.info(
                                f"[query_in_session] Session has no messages yet, creating new conversation (no resume)"
                            )
                    except Exception as e:
                        logger.warning(
                            f"[query_in_session] Error checking session history: {e}, will not use resume"
                        )
                else:
                    # 如果没有 session_manager，保守处理：不使用 resume
                    logger.warning(
                        f"[query_in_session] No session_manager provided, will not use resume for session_id={session_id}"
                    )
            
            if should_resume:
                # 后续查询：使用 resume 恢复对话上下文
                options.resume = session_id
                logger.info(f"[query_in_session] Using resume={session_id} to restore conversation")
            else:
                # 第一次查询：不使用 resume，创建新对话
                logger.info(f"[query_in_session] Creating new conversation (no resume)")

            # 每次查询创建新的client实例，使用 async with 自动管理
            async with ClaudeSDKClient(options) as new_client:
                resume_status = "with resume" if session_id else "without resume (first query)"
                logger.info(f"[query_in_session] New client created {resume_status}, sending query")

                # Send the query
                try:
                    await new_client.query(prompt)
                except Exception as query_error:
                    # 如果使用了 resume 但 SDK 找不到 session，自动降级为不使用 resume
                    if should_resume and "No conversation found with session ID" in str(query_error):
                        logger.warning(
                            f"[query_in_session] SDK cannot find session {session_id}, retrying without resume"
                        )
                        # 移除 resume 参数
                        options.resume = None
                        # 重新创建 client（需要退出当前 context）
                        # 由于在 async with 块内，需要特殊处理
                        raise query_error
                    else:
                        raise

                logger.info(f"[query_in_session] Query sent, receiving response")

                # 跟踪从 SystemMessage 中提取的 session_id（第一次查询时）
                extracted_session_id = session_id

                # Receive all messages until ResultMessage
                message_count = 0
                async for sdk_message in new_client.receive_response():
                    message_count += 1
                    logger.debug(f"[query_in_session] Received SDK message #{message_count}: {type(sdk_message).__name__}")
                    print(sdk_message)  # Keep existing debug print
                    
                    # 从 SystemMessage 中提取 session_id（第一次查询时）
                    if isinstance(sdk_message, SDKSystemMessage) and hasattr(sdk_message, 'data'):
                        if isinstance(sdk_message.data, dict) and "session_id" in sdk_message.data:
                            extracted_session_id = sdk_message.data.get("session_id")
                            if extracted_session_id:
                                logger.info(f"[query_in_session] Extracted session_id from SystemMessage: {extracted_session_id}")
                    
                    converted = await self._convert_sdk_message(sdk_message, extracted_session_id)
                    if converted:
                        yield converted

                logger.info(f"[query_in_session] Query completed for session {extracted_session_id or session_id}, received {message_count} messages")

                # async with 块结束时自动清理连接
                logger.info(f"[query_in_session] Client automatically cleaned up by async with")

        except Exception as e:
            logger.error(
                f"[query_in_session] Error in session {session_id}: {e}",
                exc_info=True
            )
            yield ResultInfo(
                subtype="error",
                is_error=True,
                duration_ms=0,
                num_turns=0,
                session_id=session_id,
                result=str(e)
            )

    # =========================================================================
    # 会话管理辅助方法
    # =========================================================================

    async def create_session_client(
        self,
        options: ClaudeAgentOptions,
        initial_prompt: Optional[str] = None,
    ) -> ClaudeSDKClient:
        """
        创建用于持久会话的新ClaudeSDKClient

        创建一个具有持久连接的client，可以在多个API调用中使用
        client将保持Claude子进程存活，直到显式断开连接

        参数:
            options: 此会话的ClaudeAgentOptions
            initial_prompt: 连接时发送的可选初始提示

        返回:
            已连接的ClaudeSDKClient实例，准备好进行查询

        注意:
            调用者负责:
            1. 将client存储在SessionManager中
            2. 会话结束时调用client.disconnect()

        环境变量:
            需要在 .env 文件中配置:
            - ANTHROPIC_API_KEY: Claude API 密钥
            - ANTHROPIC_BASE_URL: Claude API 基础URL (可选)
        """
        logger.info("[create_session_client] Creating new persistent ClaudeSDKClient")

        # 环境变量已在 main.py 启动时通过 load_dotenv() 加载
        # Claude Agent SDK 会自动从 os.environ 读取这些变量:
        # - ANTHROPIC_API_KEY
        # - ANTHROPIC_BASE_URL
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        logger.info(f"[create_session_client] Using API: {base_url or 'default Anthropic API'}")

        client = ClaudeSDKClient(options=options)

        # Connect with optional initial prompt
        # If no initial prompt, connects with empty stream for interactive use
        await client.connect(prompt=initial_prompt)

        logger.info(
            f"[create_session_client] Client connected successfully, "
            f"model={options.model}"
        )

        return client

    async def close_session_client(self, client: ClaudeSDKClient, session_id: str):
        """
        正确关闭会话client

        参数:
            client: 要关闭的ClaudeSDKClient
            session_id: 用于日志的会话标识符
        """
        logger.info(f"[close_session_client] Closing client for session {session_id}")

        try:
            await client.disconnect()
            logger.info(f"[close_session_client] Client closed successfully")
        except Exception as e:
            logger.error(f"[close_session_client] Error closing client: {e}", exc_info=True)

    # =========================================================================
    # 消息转换
    # =========================================================================

    async def _convert_sdk_message(
        self,
        sdk_message,
        session_id: str = "unknown"
    ) -> Optional[Union[AssistantMessage, SystemMessage, ResultInfo, ContentBlock, UserMessage]]:
        """
        将SDK消息转换为API模型格式

        参数:
            sdk_message: 来自Claude SDK的消息
            session_id: ResultInfo的会话标识符

        返回:
            转换后的消息:
            - AssistantMessage: 完整助手消息
            - SystemMessage: 系统消息
            - ResultInfo: 结果信息
            - UserMessage: 用户消息（包含工具结果）
            - ContentBlock: 增量流式文本片段 (type="text_delta")
        """
        # 处理 UserMessage - 转换为 Pydantic 模型
        if isinstance(sdk_message, SDKUserMessage):
            logger.debug("[_convert_sdk_message] UserMessage")

            # 检查 content 类型
            content = sdk_message.content
            if isinstance(content, str):
                # 如果 content 是字符串，包装成 TextBlock
                from models.schemas import UserMessage as PydanticUserMessage, ContentBlock as PydanticContentBlock
                return PydanticUserMessage(
                    content=[PydanticContentBlock(type="text", text=content)],
                    uuid=getattr(sdk_message, 'uuid', None),
                    parent_tool_use_id=getattr(sdk_message, 'parent_tool_use_id', None)
                )
            elif isinstance(content, list):
                # 如果 content 是 ContentBlock 列表，需要转换每个 block
                from models.schemas import UserMessage as PydanticUserMessage
                converted_blocks = []

                for block in content:
                    if isinstance(block, TextBlock):
                        converted_blocks.append(ContentBlock(type="text", text=block.text))
                    elif isinstance(block, ThinkingBlock):
                        converted_blocks.append(ContentBlock(type="thinking", thinking=block.thinking))
                    elif isinstance(block, ToolUseBlock):
                        converted_blocks.append(ContentBlock(
                            type="tool_use",
                            tool_name=block.name,
                            tool_use_id=block.id,
                            tool_input=block.input
                        ))

                        # 🔧 新增：检测 Write 工具，立即推送文件内容到前端
                        if block.name == "Write":
                            file_path = block.input.get("file_path", "")
                            file_content = block.input.get("content", "")

                            if file_path and file_content:
                                import os
                                file_name = os.path.basename(file_path)

                                # 推断文件类型
                                file_type = None
                                if file_path.endswith('.md') or file_path.endswith('.markdown'):
                                    file_type = 'text/markdown'
                                elif file_path.endswith('.txt'):
                                    file_type = 'text/plain'
                                elif file_path.endswith('.html') or file_path.endswith('.htm'):
                                    file_type = 'text/html'
                                elif file_path.endswith('.json'):
                                    file_type = 'application/json'
                                elif file_path.endswith('.py'):
                                    file_type = 'text/x-python'
                                elif file_path.endswith('.js'):
                                    file_type = 'text/javascript'
                                elif file_path.endswith('.ts'):
                                    file_type = 'text/typescript'
                                elif file_path.endswith('.css'):
                                    file_type = 'text/css'
                                elif file_path.endswith('.svg'):
                                    file_type = 'image/svg+xml'

                                # 立即生成包含文件内容的 event
                                converted_blocks.append(ContentBlock(
                                    type="file_created",
                                    file_path=file_path,
                                    file_name=file_name,
                                    file_size=len(file_content),
                                    file_type=file_type,
                                    file_content=file_content,  # ✅ 添加完整内容
                                    conversation_turn_id=getattr(self, 'current_conversation_turn_id', None)
                                ))

                                logger.info(
                                    f"[_convert_sdk_message] 📤 立即推送文件内容到前端: "
                                    f"{file_path} ({len(file_content)} 字符)"
                                )

                                # 🔧 标记此工具已推送过文件事件，避免 ToolResultBlock 阶段重复推送
                                if not hasattr(self, '_pushed_file_events'):
                                    self._pushed_file_events = set()
                                self._pushed_file_events.add(block.id)
                    elif isinstance(block, ToolResultBlock):
                        # 转换 ToolResultBlock
                        content_text = self._format_tool_result(block.content)
                        converted_blocks.append(ContentBlock(
                            type="tool_result",
                            tool_use_id=block.tool_use_id,
                            text=content_text,
                            is_error=getattr(block, 'is_error', None)
                        ))
                        logger.debug(
                            f"[_convert_sdk_message] 转换 ToolResultBlock: "
                            f"tool_use_id={block.tool_use_id}, "
                            f"content_length={len(content_text) if content_text else 0}"
                        )
                        
                        # 检测 Write 工具成功执行，生成文件创建事件
                        # 🔧 新增：检查是否已经在 ToolUseBlock 阶段推送过文件内容，避免重复
                        pushed_file_events = getattr(self, '_pushed_file_events', set())
                        if block.tool_use_id in self._write_tool_context and not getattr(block, 'is_error', False):
                            context = self._write_tool_context[block.tool_use_id]
                            file_path = context.get("file_path", "")

                            # 如果已经在 ToolUseBlock 阶段推送过，跳过此次 file_created 事件
                            if block.tool_use_id not in pushed_file_events:
                                if file_path:
                                    import os
                                    try:
                                        file_name = os.path.basename(file_path)
                                        # 检查文件是否存在（处理相对路径）
                                        if not os.path.isabs(file_path):
                                            # 相对路径：尝试从当前工作目录解析
                                            full_path = os.path.abspath(file_path)
                                        else:
                                            full_path = file_path
                                        file_size = os.path.getsize(full_path) if os.path.exists(full_path) else None

                                        # 从文件路径推断文件类型
                                        file_type = None
                                        if file_path.endswith('.md') or file_path.endswith('.markdown'):
                                            file_type = 'text/markdown'
                                        elif file_path.endswith('.txt'):
                                            file_type = 'text/plain'
                                        elif file_path.endswith('.html') or file_path.endswith('.htm'):
                                            file_type = 'text/html'
                                        elif file_path.endswith('.pdf'):
                                            file_type = 'application/pdf'

                                        logger.info(f"[_convert_sdk_message] Generated file_created event (UserMessage): file_path={file_path}")
                                        converted_blocks.append(ContentBlock(
                                            type="file_created",
                                            file_path=file_path,
                                            file_name=file_name,
                                            file_size=file_size,
                                            file_type=file_type
                                            # 注意：此时没有 file_content，因为已经在 ToolUseBlock 阶段推送过
                                        ))
                                    except Exception as e:
                                        logger.warning(f"[_convert_sdk_message] Error creating file_created event (UserMessage): {e}")
                            else:
                                # 已经在 ToolUseBlock 阶段推送过文件内容和 file_created 事件
                                logger.debug(f"[_convert_sdk_message] 跳过重复的 file_created 事件（已通过 ToolUseBlock 推送）: tool_use_id={block.tool_use_id}")

                            # 清理上下文
                            del self._write_tool_context[block.tool_use_id]
                        
                        # 检测 Bash 工具执行 minio 上传成功，生成文件上传事件
                        if block.tool_use_id in self._bash_tool_context and not getattr(block, 'is_error', False):
                            context = self._bash_tool_context[block.tool_use_id]
                            if context.get("is_minio_upload", False):
                                result_text = content_text
                                # 从输出中提取 URL
                                import re
                                url_patterns = [
                                    r'🔗\s*Public访问地址:\s*([^\s\n]+)',
                                    r'Public访问地址:\s*([^\s\n]+)',
                                    r'🔗\s*([^\s\n]+)',
                                    r'文件上传成功.*?->\s*([^\s\n\(]+)',
                                    r'(http://[^\s\n\)]+)',
                                    r'(https://[^\s\n\)]+)',
                                ]
                                file_url = None
                                for pattern in url_patterns:
                                    match = re.search(pattern, result_text)
                                    if match:
                                        file_url = match.group(1).strip().rstrip('.,;:()')
                                        if file_url and ('http://' in file_url or 'https://' in file_url):
                                            break
                                        else:
                                            file_url = None
                                
                                file_path = context.get("file_path", "")
                                import os
                                try:
                                    file_name = os.path.basename(file_path) if file_path else "uploaded_file"
                                    if file_path and not os.path.isabs(file_path):
                                        full_path = os.path.abspath(file_path)
                                    else:
                                        full_path = file_path if file_path else None
                                    file_size = os.path.getsize(full_path) if full_path and os.path.exists(full_path) else None
                                    
                                    # 从 URL 或文件路径推断文件类型
                                    file_type = None
                                    source = file_url if file_url else file_path
                                    if source:
                                        if source.endswith('.md') or source.endswith('.markdown'):
                                            file_type = 'text/markdown'
                                        elif source.endswith('.txt'):
                                            file_type = 'text/plain'
                                        elif source.endswith('.html') or source.endswith('.htm'):
                                            file_type = 'text/html'
                                        elif source.endswith('.pdf'):
                                            file_type = 'application/pdf'
                                    
                                    if file_url or file_path:
                                        logger.info(f"[_convert_sdk_message] Generated file_uploaded event (UserMessage): file_url={file_url}, file_path={file_path}")
                                        converted_blocks.append(ContentBlock(
                                            type="file_uploaded",
                                            file_path=file_path,
                                            file_url=file_url,
                                            file_name=file_name,
                                            file_size=file_size,
                                            file_type=file_type
                                        ))
                                    else:
                                        logger.warning(f"[_convert_sdk_message] Minio upload detected but no URL or file_path found (UserMessage)")
                                except Exception as e:
                                    logger.warning(f"[_convert_sdk_message] Error creating file_uploaded event (UserMessage): {e}")
                            # 清理上下文
                            del self._bash_tool_context[block.tool_use_id]

                return PydanticUserMessage(
                    content=converted_blocks,
                    uuid=getattr(sdk_message, 'uuid', None),
                    parent_tool_use_id=getattr(sdk_message, 'parent_tool_use_id', None)
                )
            else:
                logger.warning(f"[_convert_sdk_message] Unknown UserMessage content type: {type(content)}")
                return None

        # 处理 StreamEvent - 增量流式事件
        if isinstance(sdk_message, SDKStreamEvent):
            event_type = sdk_message.event.get('type')
            index = sdk_message.event.get('index', 'N/A')
            logger.info(f"[_convert_sdk_message] 🔍 StreamEvent: {event_type}, index={index}")

            # 1. 处理文本增量事件
            if event_type == 'content_block_delta':
                delta = sdk_message.event.get('delta', {})
                if delta.get('type') == 'text_delta':
                    text = delta.get('text', '')
                    if text:  # 只返回非空文本
                        return ContentBlock(type="text_delta", text=text)
                elif delta.get('type') == 'input_json_delta':
                    # 🔧 处理工具调用的流式输入更新（input_json_delta）
                    partial_json = delta.get('partial_json', '')
                    index = sdk_message.event.get('index', 0)
                    logger.info(f"[_convert_sdk_message] ✅ Converted tool_input_delta: index={index}, partial_json_length={len(partial_json)}")
                    # 返回一个特殊的 ContentBlock，包含 index 和 partial_json
                    # endpoints.py 会通过 index 查找对应的 tool_use_id
                    return ContentBlock(
                        type="tool_input_delta",
                        text=partial_json,  # 使用 text 字段存储 partial_json
                        tool_use_id=str(index)  # 临时使用 index 作为标识，endpoints.py 会替换为实际的 tool_use_id
                    )

            # 2. 处理工具使用开始事件 - 显示"AI 正在使用工具..."
            if event_type == 'content_block_start':
                block = sdk_message.event.get('content_block', {})
                if block.get('type') == 'tool_use':
                    index = sdk_message.event.get('index', 0)
                    tool_use_id = block.get('id')
                    tool_name = block.get('name')
                    logger.info(
                        f"[_convert_sdk_message] ✅ Converted tool_start: index={index}, tool_use_id={tool_use_id[:20]}..., tool_name={tool_name}"
                    )
                    # 🔧 在 tool_input 中添加 index 信息，供 endpoints.py 建立映射
                    tool_input_with_index = block.get('input', {}) or {}  # 确保不是 None
                    tool_input_with_index['_index'] = index  # 临时添加 index 信息
                    logger.info(f"[_convert_sdk_message] 🔧 Added _index to tool_input: {tool_input_with_index}")
                    return ContentBlock(
                        type="tool_start",
                        tool_use_id=tool_use_id,
                        tool_name=tool_name,
                        tool_input=tool_input_with_index
                    )

            # 3. 处理消息元数据事件 - token 使用和停止原因
            if event_type == 'message_delta':
                delta = sdk_message.event.get('delta', {})
                usage = sdk_message.event.get('usage', {})
                logger.debug(
                    f"[_convert_sdk_message] MessageDelta: "
                    f"stop_reason={delta.get('stop_reason')}, "
                    f"output_tokens={usage.get('output_tokens', 0)}"
                )
                return ContentBlock(
                    type="message_metadata",
                    text=delta.get('stop_reason'),  # 使用 text 字段传递 stop_reason
                    thinking=str(usage) if usage else None  # 使用 thinking 字段传递 usage
                )

            # 4. 处理消息结束事件
            if event_type == 'message_stop':
                logger.debug("[_convert_sdk_message] MessageStop")
                return ContentBlock(type="message_stop")

            # 其他 StreamEvent 暂时忽略
            return None

        # 处理ResultMessage - 表示响应结束
        if isinstance(sdk_message, SDKResultMessage):
            logger.debug(
                f"[_convert_sdk_message] ResultMessage: subtype={sdk_message.subtype}, "
                f"turns={sdk_message.num_turns}, cost=${sdk_message.total_cost_usd:.4f}"
            )
            return ResultInfo(
                subtype=sdk_message.subtype,
                is_error=getattr(sdk_message, 'is_error', False),
                duration_ms=getattr(sdk_message, 'duration_ms', 0),
                duration_api_ms=getattr(sdk_message, 'duration_api_ms', None),
                num_turns=getattr(sdk_message, 'num_turns', 0),
                session_id=session_id,
                result=getattr(sdk_message, 'result', None),
                total_cost_usd=getattr(sdk_message, 'total_cost_usd', None),
                usage=getattr(sdk_message, 'usage', None),
            )

        # 处理SystemMessage - 处理过程中的系统更新
        if isinstance(sdk_message, SDKSystemMessage):
            logger.debug(
                f"[_convert_sdk_message] SystemMessage: subtype={sdk_message.subtype}"
            )
            return SystemMessage(
                subtype=sdk_message.subtype,
                data=getattr(sdk_message, 'data', {})
            )

        # 处理AssistantMessage - Claude的响应内容
        if isinstance(sdk_message, SDKAssistantMessage):
            content_blocks = []

            for block in sdk_message.content:
                if isinstance(block, TextBlock):
                    content_blocks.append(ContentBlock(
                        type="text",
                        text=block.text
                    ))
                elif isinstance(block, ThinkingBlock):
                    content_blocks.append(ContentBlock(
                        type="thinking",
                        thinking=block.thinking
                    ))
                elif isinstance(block, ToolUseBlock):
                    logger.debug(
                        f"[_convert_sdk_message] ToolUse: {block.name}, "
                        f"id={block.id}"
                    )
                    # 如果是 Write 工具，保存文件路径信息以便后续生成文件事件
                    if block.name == "Write":
                        file_path = block.input.get("file_path", "")
                        file_content = block.input.get("content", "")

                        # 📝 输出文件内容到日志（在写入之前）
                        logger.info(f"[Write Tool] 📝 准备写入文件:")
                        logger.info(f"  📂 文件路径: {file_path}")
                        logger.info(f"  📏 内容长度: {len(file_content)} 字符")

                        # 如果内容不太长，输出完整内容
                        if len(file_content) <= 2000:
                            logger.info(f"  📄 文件完整内容:\n{file_content}")
                        else:
                            # 内容太长，分段输出
                            logger.info(f"  📄 文件内容 (前2000字符):\n{file_content[:2000]}")
                            logger.info(f"  📄 文件内容 (后500字符):\n{file_content[-500:]}")
                            logger.info(f"  ℹ️  中间省略 {len(file_content) - 2500} 字符")

                        self._write_tool_context[block.id] = {
                            "file_path": file_path,
                            "tool_name": block.name
                        }
                    # 如果是 Bash 工具，检查是否是 minio 上传命令
                    elif block.name == "Bash":
                        command = block.input.get("command", "")
                        # 检测是否是 minio 上传命令
                        if "simple_minio_uploader.py" in command or "minio" in command.lower():
                            # 尝试从命令中提取文件路径
                            import re
                            # 匹配文件路径（可能是相对路径或绝对路径）
                            file_path_match = re.search(r'(\S+\.(md|txt|html|pdf|docx?|xlsx?|pptx?))', command)
                            file_path = file_path_match.group(1) if file_path_match else ""
                            self._bash_tool_context[block.id] = {
                                "command": command,
                                "file_path": file_path,
                                "tool_name": block.name,
                                "is_minio_upload": True
                            }
                            logger.debug(f"[_convert_sdk_message] Detected minio upload command: {command[:100]}")
                    content_blocks.append(ContentBlock(
                        type="tool_use",
                        tool_name=block.name,
                        tool_use_id=block.id,
                        tool_input=block.input
                    ))
                elif isinstance(block, ToolResultBlock):
                    logger.debug(
                        f"[_convert_sdk_message] ToolResult: id={block.tool_use_id}, "
                        f"is_error={getattr(block, 'is_error', False)}"
                    )
                    content_blocks.append(ContentBlock(
                        type="tool_result",
                        tool_use_id=block.tool_use_id,
                        is_error=getattr(block, 'is_error', None),
                        text=self._format_tool_result(block.content)
                    ))
                    # 检测 Write 工具成功执行，生成文件创建事件
                    if block.tool_use_id in self._write_tool_context and not getattr(block, 'is_error', False):
                        context = self._write_tool_context[block.tool_use_id]
                        file_path = context.get("file_path", "")
                        if file_path:
                            import os
                            try:
                                file_name = os.path.basename(file_path)
                                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
                                
                                # 从文件路径推断文件类型
                                file_type = None
                                if file_path:
                                    if file_path.endswith('.md') or file_path.endswith('.markdown'):
                                        file_type = 'text/markdown'
                                    elif file_path.endswith('.txt'):
                                        file_type = 'text/plain'
                                    elif file_path.endswith('.html') or file_path.endswith('.htm'):
                                        file_type = 'text/html'
                                    elif file_path.endswith('.pdf'):
                                        file_type = 'application/pdf'
                                    elif file_path.endswith('.docx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                                    elif file_path.endswith('.xlsx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                    elif file_path.endswith('.pptx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                                    elif file_path.endswith('.json'):
                                        file_type = 'application/json'
                                    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                                        file_type = 'application/x-yaml'
                                    elif file_path.endswith('.py'):
                                        file_type = 'text/x-python'
                                    elif file_path.endswith('.js'):
                                        file_type = 'text/javascript'
                                    elif file_path.endswith('.ts'):
                                        file_type = 'text/typescript'
                                
                                logger.info(f"[_convert_sdk_message] Generated file_created event: file_path={file_path}")
                                # conversation_turn_id 将在流式响应处理中设置
                                content_blocks.append(ContentBlock(
                                    type="file_created",
                                    file_path=file_path,
                                    file_name=file_name,
                                    file_size=file_size,
                                    file_type=file_type
                                ))
                            except Exception as e:
                                logger.warning(f"[_convert_sdk_message] Error creating file_created event: {e}")
                        # 清理上下文
                        del self._write_tool_context[block.tool_use_id]
                    
                    # 检测 Bash 工具执行 minio 上传成功，生成文件上传事件
                    if block.tool_use_id in self._bash_tool_context and not getattr(block, 'is_error', False):
                        context = self._bash_tool_context[block.tool_use_id]
                        if context.get("is_minio_upload", False):
                            result_text = self._format_tool_result(block.content)
                            # 从输出中提取 URL（查找 "Public访问地址:" 或 "🔗" 后的 URL）
                            import re
                            url_patterns = [
                                r'🔗\s*Public访问地址:\s*([^\s\n]+)',  # 优先匹配带emoji的完整格式
                                r'Public访问地址:\s*([^\s\n]+)',  # 匹配不带emoji的格式
                                r'🔗\s*([^\s\n]+)',  # 匹配只有emoji的格式
                                r'文件上传成功.*?->\s*([^\s\n\(]+)',  # 匹配 "文件上传成功: ... -> URL" 格式（排除左括号）
                                r'(http://[^\s\n\)]+)',  # 匹配 http:// 开头的 URL（排除右括号）
                                r'(https://[^\s\n\)]+)',  # 匹配 https:// 开头的 URL（排除右括号）
                            ]
                            file_url = None
                            for pattern in url_patterns:
                                match = re.search(pattern, result_text)
                                if match:
                                    file_url = match.group(1).strip()
                                    # 清理可能的尾随标点符号和括号
                                    file_url = file_url.rstrip('.,;:()')
                                    # 验证是否是有效的 URL
                                    if file_url and ('http://' in file_url or 'https://' in file_url):
                                        break
                                    else:
                                        file_url = None
                            
                            # 如果检测到是 minio 上传命令，即使没有提取到 URL，也尝试生成事件
                            file_path = context.get("file_path", "")
                            import os
                            try:
                                # 如果 URL 提取失败，但命令执行成功，尝试从命令中推断
                                if not file_url and file_path:
                                    # 从文件路径推断可能的 URL（基于默认配置）
                                    # 这里可以根据实际情况调整
                                    logger.debug(f"[_convert_sdk_message] URL extraction failed, but minio upload command succeeded")
                                
                                file_name = os.path.basename(file_path) if file_path else "uploaded_file"
                                # 如果文件路径存在，获取文件大小
                                file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else None
                                
                                # 从 URL 或文件路径推断文件类型
                                file_type = None
                                source = file_url if file_url else file_path
                                if source:
                                    if source.endswith('.md') or source.endswith('.markdown'):
                                        file_type = 'text/markdown'
                                    elif source.endswith('.txt'):
                                        file_type = 'text/plain'
                                    elif source.endswith('.html') or source.endswith('.htm'):
                                        file_type = 'text/html'
                                    elif source.endswith('.pdf'):
                                        file_type = 'application/pdf'
                                    elif source.endswith('.docx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                                    elif source.endswith('.xlsx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                    elif source.endswith('.pptx'):
                                        file_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                                
                                # 只要有 URL 或文件路径，就生成文件上传事件
                                if file_url or file_path:
                                    logger.info(f"[_convert_sdk_message] Generated file_uploaded event: file_url={file_url}, file_path={file_path}")
                                    content_blocks.append(ContentBlock(
                                        type="file_uploaded",
                                        file_path=file_path,
                                        file_url=file_url,
                                        file_name=file_name,
                                        file_size=file_size,
                                        file_type=file_type
                                    ))
                                else:
                                    logger.warning(f"[_convert_sdk_message] Minio upload detected but no URL or file_path found")
                            except Exception as e:
                                logger.warning(f"[_convert_sdk_message] Error creating file_uploaded event: {e}")
                        # 清理上下文
                        del self._bash_tool_context[block.tool_use_id]

            return AssistantMessage(
                content=content_blocks,
                model=getattr(sdk_message, 'model', None)
            )

        logger.warning(f"[_convert_sdk_message] Unknown message type: {type(sdk_message)}")
        return None

    def _format_tool_result(self, content) -> str:
        """
        将工具结果内容格式化为字符串

        参数:
            content: 工具结果内容 (字符串、列表或字典)

        返回:
            格式化的字符串表示（永远不会返回 None，至少返回空字符串）
        """
        import json
        
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # 处理内容项列表
            result = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        result.append(str(item["text"]))
                    elif item.get("type") == "text":
                        result.append(str(item.get("text", "")))
                    else:
                        # 如果字典中没有 text 字段，将其格式化为 JSON
                        try:
                            result.append(json.dumps(item, ensure_ascii=False, indent=2))
                        except (TypeError, ValueError):
                            result.append(str(item))
                else:
                    result.append(str(item))
            if result:
                return "\n".join(result)
            # 如果列表为空或没有有效内容，返回空字符串而不是 None
            return ""
        if isinstance(content, dict):
            # 对于字典类型（如 WebSearch 的结果），格式化为 JSON 字符串
            try:
                return json.dumps(content, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                # 如果无法序列化为 JSON（例如包含不可序列化的对象），则使用 str
                return str(content)
        return str(content)


# =========================================================================
# 全局服务实例
# =========================================================================

_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取或创建全局agent服务实例"""
    global _agent_service
    if _agent_service is None:
        logger.info("[get_agent_service] Creating global AgentService instance")
        from services.database import get_database_service
        _agent_service = AgentService(db_service=get_database_service())
    return _agent_service


async def initialize_default_prompt(agent_service: AgentService):
    """初始化默认提示词（从数据库加载或使用fallback）"""
    try:
        prompt = await agent_service._get_default_system_prompt()
        # 检查是否使用的是 fallback（通过判断缓存是否包含特定特征）
        if agent_service._default_system_prompt_cache and "你是一个智能助手，擅长使用工具完成复杂任务" in agent_service._default_system_prompt_cache[:100]:
            logger.info("Default system prompt initialized using fallback (hardcoded prompt)")
        else:
            logger.info("Default system prompt initialized from database")
    except Exception as e:
        logger.warning(f"Failed to initialize default prompt: {e}")
