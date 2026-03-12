# 配置权限

通过权限模式、钩子和声明式允许/拒绝规则来控制代理使用工具的方式。

---

Claude Agent SDK 提供权限控制来管理 Claude 使用工具的方式。使用权限模式和规则来定义哪些操作可以自动允许，并使用 [`canUseTool` 回调](/docs/zh-CN/agent-sdk/user-input)在运行时处理其他所有情况。

<Note>
本页介绍权限模式和规则。要构建用户在运行时批准或拒绝工具请求的交互式审批流程，请参阅[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input)。
</Note>

## 权限评估方式

当 Claude 请求使用工具时，SDK 按以下顺序检查权限：

<Steps>
  <Step title="钩子">
    首先运行[钩子](/docs/zh-CN/agent-sdk/hooks)，钩子可以允许、拒绝或继续到下一步
  </Step>
  <Step title="权限规则">
    按以下顺序检查 [settings.json](https://code.claude.com/docs/en/settings#permission-settings) 中定义的规则：首先检查 `deny` 规则（无论其他规则如何都会阻止），然后检查 `allow` 规则（匹配则允许），最后检查 `ask` 规则（提示审批）。这些声明式规则让您无需编写代码即可预先批准、阻止或要求审批特定工具。
  </Step>
  <Step title="权限模式">
    应用当前激活的[权限模式](#permission-modes)（`bypassPermissions`、`acceptEdits`、`dontAsk` 等）
  </Step>
  <Step title="canUseTool 回调">
    如果规则或模式未能解决，则调用您的 [`canUseTool` 回调](/docs/zh-CN/agent-sdk/user-input)来做出决定
  </Step>
</Steps>

![权限评估流程图](/docs/images/agent-sdk/permissions-flow.svg)

本页重点介绍**权限模式**（第 3 步），即控制默认行为的静态配置。关于其他步骤：

- **钩子**：运行自定义代码来允许、拒绝或修改工具请求。请参阅[使用钩子控制执行](/docs/zh-CN/agent-sdk/hooks)。
- **权限规则**：在 `settings.json` 中配置声明式允许/拒绝规则。请参阅[权限设置](https://code.claude.com/docs/en/settings#permission-settings)。
- **canUseTool 回调**：在运行时提示用户进行审批。请参阅[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input)。

## 权限模式

权限模式提供对 Claude 使用工具方式的全局控制。您可以在调用 `query()` 时设置权限模式，也可以在流式会话期间动态更改。

### 可用模式

SDK 支持以下权限模式：

| 模式 | 描述 | 工具行为 |
| :--- | :---------- | :------------ |
| `default` | 标准权限行为 | 无自动批准；未匹配的工具会触发您的 `canUseTool` 回调 |
| `acceptEdits` | 自动接受文件编辑 | 文件编辑和[文件系统操作](#accept-edits-mode-acceptedits)（`mkdir`、`rm`、`mv` 等）会自动批准 |
| `bypassPermissions` | 绕过所有权限检查 | 所有工具无需权限提示即可运行（请谨慎使用） |
| `plan` | 规划模式 | 不执行工具；Claude 只进行规划而不做更改 |

<Warning>
**子代理继承**：使用 `bypassPermissions` 时，所有子代理都会继承此模式且无法覆盖。子代理可能具有不同的系统提示词和比主代理更少的约束行为。启用 `bypassPermissions` 会授予它们完全的、自主的系统访问权限，且不会有任何审批提示。
</Warning>

### 设置权限模式

您可以在启动查询时一次性设置权限模式，也可以在会话活跃期间动态更改。

<Tabs>
  <Tab title="查询时设置">
    创建查询时传入 `permission_mode`（Python）或 `permissionMode`（TypeScript）。此模式在整个会话期间有效，除非动态更改。

    <CodeGroup>

    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        async for message in query(
            prompt="Help me refactor this code",
            options=ClaudeAgentOptions(
                permission_mode="default",  # Set the mode here
            ),
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    async function main() {
      for await (const message of query({
        prompt: "Help me refactor this code",
        options: {
          permissionMode: "default",  // Set the mode here
        },
      })) {
        if ("result" in message) {
          console.log(message.result);
        }
      }
    }

    main();
    ```

    </CodeGroup>
  </Tab>
  <Tab title="流式传输期间">
    调用 `set_permission_mode()`（Python）或 `setPermissionMode()`（TypeScript）在会话中途更改模式。新模式会立即对所有后续工具请求生效。这让您可以从严格限制开始，随着信任建立逐步放宽权限，例如在审查 Claude 的初始方案后切换到 `acceptEdits`。

    <CodeGroup>

    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        q = query(
            prompt="Help me refactor this code",
            options=ClaudeAgentOptions(
                permission_mode="default",  # Start in default mode
            ),
        )

        # Change mode dynamically mid-session
        await q.set_permission_mode("acceptEdits")

        # Process messages with the new permission mode
        async for message in q:
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    async function main() {
      const q = query({
        prompt: "Help me refactor this code",
        options: {
          permissionMode: "default",  // Start in default mode
        },
      });

      // Change mode dynamically mid-session
      await q.setPermissionMode("acceptEdits");

      // Process messages with the new permission mode
      for await (const message of q) {
        if ("result" in message) {
          console.log(message.result);
        }
      }
    }

    main();
    ```

    </CodeGroup>
  </Tab>
</Tabs>

### 模式详情

#### 接受编辑模式 (`acceptEdits`)

自动批准文件操作，使 Claude 可以在不提示的情况下编辑代码。其他工具（如非文件系统操作的 Bash 命令）仍需正常权限。

**自动批准的操作：**
- 文件编辑（Edit、Write 工具）
- 文件系统命令：`mkdir`、`touch`、`rm`、`mv`、`cp`

**适用场景：**您信任 Claude 的编辑并希望更快迭代，例如在原型开发期间或在隔离目录中工作时。

#### 绕过权限模式 (`bypassPermissions`)

自动批准所有工具使用，无需提示。钩子仍会执行，并可在需要时阻止操作。

<Warning>
请极其谨慎使用。在此模式下 Claude 拥有完全的系统访问权限。仅在您信任所有可能操作的受控环境中使用。
</Warning>

#### 规划模式 (`plan`)

完全阻止工具执行。Claude 可以分析代码并创建计划，但不能进行更改。Claude 可能会使用 `AskUserQuestion` 在最终确定计划之前澄清需求。请参阅[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input#handle-clarifying-questions)了解如何处理这些提示。

**适用场景：**您希望 Claude 提出更改建议而不执行它们，例如在代码审查期间或需要在更改执行前进行审批时。

## 相关资源

关于权限评估流程中的其他步骤：

- [处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input)：交互式审批提示和澄清问题
- [钩子指南](/docs/zh-CN/agent-sdk/hooks)：在代理生命周期的关键节点运行自定义代码
- [权限规则](https://code.claude.com/docs/en/settings#permission-settings)：`settings.json` 中的声明式允许/拒绝规则