---
source_url: https://platform.claude.com/docs/en/agent-sdk/quickstart
source_type: sitemap
content_hash: sha256:85abc9a7afe949336b0939bc6358457fc6ef306758ed9a1d90d795631d855ef0
sitemap_url: https://platform.claude.com/sitemap.xml
fetch_method: markdown
---

# Quickstart

Get started with the Python or TypeScript Agent SDK to build AI agents that work autonomously

---

Use the Agent SDK to build an AI agent that reads your code, finds bugs, and fixes them, all without manual intervention.

**What you'll do:**
1. Set up a project with the Agent SDK
2. Create a file with some buggy code
3. Run an agent that finds and fixes the bugs automatically

## Prerequisites

- **Node.js 18+** or **Python 3.10+**
- An **Anthropic account** ([sign up here](https://console.anthropic.com/))

## Setup

<Steps>
  <Step title="Install Claude Code">
    The Agent SDK uses Claude Code as its runtime. Install it for your platform:

    <Tabs>
      <Tab title="macOS/Linux/WSL">
        ```bash
        curl -fsSL https://claude.ai/install.sh | bash
        ```
      </Tab>
      <Tab title="Homebrew">
        ```bash
        brew install --cask claude-code
        ```
      </Tab>
      <Tab title="npm">
        ```bash
        npm install -g @anthropic-ai/claude-code
        ```
      </Tab>
    </Tabs>

    After installing Claude Code onto your machine, run `claude` in your terminal and follow the prompts to authenticate. The SDK will use this authentication automatically.

    <Tip>
    For more information on Claude Code installation, see [Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/setup).
    </Tip>
  </Step>

  <Step title="Create a project folder">
    Create a new directory for this quickstart:

    ```bash
    mkdir my-agent && cd my-agent
    ```

    For your own projects, you can run the SDK from any folder; it will have access to files in that directory and its subdirectories by default.
  </Step>

  <Step title="Install the SDK">
    Install the Agent SDK package for your language:

    <Tabs>
      <Tab title="TypeScript">
        ```bash
        npm install @anthropic-ai/claude-agent-sdk
        ```
      </Tab>
      <Tab title="Python (uv)">
        [uv Python package manager](https://docs.astral.sh/uv/) is a fast Python package manager that handles virtual environments automatically:
        ```bash
        uv init && uv add claude-agent-sdk
        ```
      </Tab>
      <Tab title="Python (pip)">
        Create a virtual environment first, then install:
        ```bash
        python3 -m venv .venv && source .venv/bin/activate
        pip3 install claude-agent-sdk
        ```
      </Tab>
    </Tabs>
  </Step>

  <Step title="Set your API key">
    If you've already authenticated Claude Code (by running `claude` in your terminal), the SDK uses that authentication automatically.

    Otherwise, you need an API key, which you can get from the [Claude Console](https://console.anthropic.com/).

    Create a `.env` file in your project directory and store the API key there:

    ```bash
    ANTHROPIC_API_KEY=your-api-key
    ```

    <Note>
    **Using Amazon Bedrock, Google Vertex AI, or Microsoft Azure?** See the setup guides for [Bedrock](https://code.claude.com/docs/en/amazon-bedrock), [Vertex AI](https://code.claude.com/docs/en/google-vertex-ai), or [Azure AI Foundry](https://code.claude.com/docs/en/azure-ai-foundry).

    Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Please use the API key authentication methods described in this document instead.
    </Note>
  </Step>
</Steps>

## Create a buggy file

This quickstart walks you through building an agent that can find and fix bugs in code. First, you need a file with some intentional bugs for the agent to fix. Create `utils.py` in the `my-agent` directory and paste the following code:

```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

def get_user_name(user):
    return user["name"].upper()
```

This code has two bugs:
1. `calculate_average([])` crashes with division by zero
2. `get_user_name(None)` crashes with a TypeError

## Build an agent that finds and fixes bugs

Create `agent.py` if you're using the Python SDK, or `agent.ts` for TypeScript:

<CodeGroup>
```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    # Agentic loop: streams messages as Claude works
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],  # Tools Claude can use
            permission_mode="acceptEdits"            # Auto-approve file edits
        )
    ):
        # Print human-readable output
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)              # Claude's reasoning
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")   # Tool being called
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")      # Final result

asyncio.run(main())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Agentic loop: streams messages as Claude works
for await (const message of query({
  prompt: "Review utils.py for bugs that would cause crashes. Fix any issues you find.",
  options: {
    allowedTools: ["Read", "Edit", "Glob"],  // Tools Claude can use
    permissionMode: "acceptEdits"            // Auto-approve file edits
  }
})) {
  // Print human-readable output
  if (message.type === "assistant" && message.message?.content) {
    for (const block of message.message.content) {
      if ("text" in block) {
        console.log(block.text);             // Claude's reasoning
      } else if ("name" in block) {
        console.log(`Tool: ${block.name}`);  // Tool being called
      }
    }
  } else if (message.type === "result") {
    console.log(`Done: ${message.subtype}`); // Final result
  }
}
```
</CodeGroup>

This code has three main parts:

1. **`query`**: the main entry point that creates the agentic loop. It returns an async iterator, so you use `async for` to stream messages as Claude works. See the full API in the [Python](/docs/en/agent-sdk/python#query) or [TypeScript](/docs/en/agent-sdk/typescript#query) SDK reference.

2. **`prompt`**: what you want Claude to do. Claude figures out which tools to use based on the task.

3. **`options`**: configuration for the agent. This example uses `allowedTools` to restrict Claude to `Read`, `Edit`, and `Glob`, and `permissionMode: "acceptEdits"` to auto-approve file changes. Other options include `systemPrompt`, `mcpServers`, and more. See all options for [Python](/docs/en/agent-sdk/python#claudeagentoptions) or [TypeScript](/docs/en/agent-sdk/typescript#claudeagentoptions).

The `async for` loop keeps running as Claude thinks, calls tools, observes results, and decides what to do next. Each iteration yields a message: Claude's reasoning, a tool call, a tool result, or the final outcome. The SDK handles the orchestration (tool execution, context management, retries) so you just consume the stream. The loop ends when Claude finishes the task or hits an error.

The message handling inside the loop filters for human-readable output. Without filtering, you'd see raw message objects including system initialization and internal state, which is useful for debugging but noisy otherwise.

<Note>
This example uses streaming to show progress in real-time. If you don't need live output (e.g., for background jobs or CI pipelines), you can collect all messages at once. See [Streaming vs. single-turn mode](/docs/en/agent-sdk/streaming-vs-single-mode) for details.
</Note>

### Run your agent

Your agent is ready. Run it with the following command:

<Tabs>
  <Tab title="Python">
    ```bash
    python3 agent.py
    ```
  </Tab>
  <Tab title="TypeScript">
    ```bash
    npx tsx agent.ts
    ```
  </Tab>
</Tabs>

After running, check `utils.py`. You'll see defensive code handling empty lists and null users. Your agent autonomously:

1. **Read** `utils.py` to understand the code
2. **Analyzed** the logic and identified edge cases that would crash
3. **Edited** the file to add proper error handling

This is what makes the Agent SDK different: Claude executes tools directly instead of asking you to implement them.

<Note>
If you see "Claude Code not found", [install Claude Code](#install-claude-code) and restart your terminal. For "API key not found", [set your API key](#set-your-api-key). See the [full troubleshooting guide](https://docs.anthropic.com/en/docs/claude-code/troubleshooting) for more help.
</Note>

### Try other prompts

Now that your agent is set up, try some different prompts:

- `"Add docstrings to all functions in utils.py"`
- `"Add type hints to all functions in utils.py"`
- `"Create a README.md documenting the functions in utils.py"`

### Customize your agent

You can modify your agent's behavior by changing the options. Here are a few examples:

**Add web search capability:**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "WebSearch"],
    permission_mode="acceptEdits"
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob", "WebSearch"],
  permissionMode: "acceptEdits"
}
```
</CodeGroup>

**Give Claude a custom system prompt:**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
    system_prompt="You are a senior Python developer. Always follow PEP 8 style guidelines."
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob"],
  permissionMode: "acceptEdits",
  systemPrompt: "You are a senior Python developer. Always follow PEP 8 style guidelines."
}
```
</CodeGroup>

**Run commands in the terminal:**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "Bash"],
    permission_mode="acceptEdits"
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob", "Bash"],
  permissionMode: "acceptEdits"
}
```
</CodeGroup>

With `Bash` enabled, try: `"Write unit tests for utils.py, run them, and fix any failures"`

## Key concepts

**Tools** control what your agent can do:

| Tools | What the agent can do |
| --- | --- |
| `Read`, `Glob`, `Grep` | Read-only analysis |
| `Read`, `Edit`, `Glob` | Analyze and modify code |
| `Read`, `Edit`, `Bash`, `Glob`, `Grep` | Full automation |

**Permission modes** control how much human oversight you want:

| Mode | Behavior | Use case |
| --- | --- | --- |
| `acceptEdits` | Auto-approves file edits, asks for other actions | Trusted development workflows |
| `bypassPermissions` | Runs without prompts | CI/CD pipelines, automation |
| `default` | Requires a `canUseTool` callback to handle approval | Custom approval flows |

The example above uses `acceptEdits` mode, which auto-approves file operations so the agent can run without interactive prompts. If you want to prompt users for approval, use `default` mode and provide a [`canUseTool` callback](/docs/en/agent-sdk/permissions#canusetool) that collects user input. For more control, see [Permissions](/docs/en/agent-sdk/permissions).

## Next steps

Now that you've created your first agent, learn how to extend its capabilities and tailor it to your use case:

- **[Permissions](/docs/en/agent-sdk/permissions)**: control what your agent can do and when it needs approval
- **[Hooks](/docs/en/agent-sdk/hooks)**: run custom code before or after tool calls
- **[Sessions](/docs/en/agent-sdk/sessions)**: build multi-turn agents that maintain context
- **[MCP servers](/docs/en/agent-sdk/mcp)**: connect to databases, browsers, APIs, and other external systems
- **[Hosting](/docs/en/agent-sdk/hosting)**: deploy agents to Docker, cloud, and CI/CD
- **[Example agents](https://github.com/anthropics/claude-agent-sdk-demos)**: see complete examples: email assistant, research agent, and more
