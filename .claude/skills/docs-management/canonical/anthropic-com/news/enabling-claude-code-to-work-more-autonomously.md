---
source_url: https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
source_type: sitemap
content_hash: sha256:0a04dc0f63847b50ad3079503ccc74535309f73f15709a13d6917291fa2a552c
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-09-29'
---

Product

# Enabling Claude Code to work more autonomously

[![Video](https://img.youtube.com/vi/OZ-aLrJ0oVg/maxresdefault.jpg)](https://www.youtube.com/watch?v=OZ-aLrJ0oVg)

[![Video](https://img.youtube.com/vi/IpFG\_K-1xog/maxresdefault.jpg)](https://www.youtube.com/watch?v=IpFG\_K-1xog)

Sep 29, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/a62b6eb169818f14c35b7a192af269e283f8fa93-1000x1000.svg)

We’re introducing several upgrades to Claude Code: a native VS Code extension, version 2.0 of our terminal interface, and checkpoints for autonomous operation. Powered by [Sonnet 4.5](https://www.anthropic.com/news/claude-sonnet-4-5), Claude Code now handles longer, more complex development tasks in your terminal and IDE.

## Claude Code on more surfaces

**VS Code extension**

We’re introducing a [native VS Code extension](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code) in beta that brings Claude Code directly into your IDE. You can now see Claude’s changes in real-time through a dedicated sidebar panel with inline diffs. The extension provides a richer, graphical Claude Code experience for users who prefer to work in IDEs over terminals.

**Enhanced terminal experience**

We’ve also refreshed Claude Code’s terminal interface. The updated interface features improved status visibility and searchable prompt history (Ctrl+r), making it easier to reuse or edit previous prompts.

![An image of the new Claude Code terminal UX](https://www-cdn.anthropic.com/images/4zrzovbb/website/3613f360926fae004521197488623465eb0cd751-1920x1035.png)

**Claude Agent SDK**

For teams who want to create custom agentic experiences, the Claude Agent SDK (formerly the Claude Code SDK) gives access to the same core tools, context management systems, and permissions frameworks that power Claude Code. We’ve also released SDK support for subagents and hooks, making it more customizable for building agents for your specific workflows.

Developers are [already building agents](https://anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) for a broad range use cases with the SDK, including financial compliance agents, cybersecurity agents, and code debugging agents.

## Execute long-running tasks with confidence

As Claude Code takes on increasingly complex tasks, we're releasing a checkpointing feature to help delegate tasks to Claude Code with confidence while maintaining control. Combined with recent feature releases, Claude Code is now more capable of handling sophisticated tasks.

**Checkpoints**

Complex development often involves exploration and iteration. Our new checkpoint system automatically saves your code state before each change, and you can instantly rewind to previous versions by tapping Esc twice or using the /rewind command. Checkpoints let you pursue more ambitious and wide-scale tasks knowing you can always return to a prior code state.

When you rewind to a checkpoint, you can choose to restore the code, the conversation, or both to the prior state. Checkpoints apply to Claude’s edits and not user edits or bash commands, and we recommend using them in combination with version control.

**Subagents, hooks, and background tasks**

Checkpoints are especially useful when combined with Claude Code’s latest features that power autonomous work:

* **Subagents** delegate specialized tasks—like spinning up a backend API while the main agent builds the frontend—allowing parallel development workflows
* **Hooks** automatically trigger actions at specific points, such as running your test suite after code changes or linting before commits
* **Background** **tasks** keep long-running processes like dev servers active without blocking Claude Code’s progress on other work

Together, these capabilities let you confidently delegate broad tasks like extensive refactors or feature exploration to Claude Code.

## Getting started

These updates are available now for Claude Code users.

* **Claude Sonnet 4.5** is the new default model in Claude Code. Run /model to switch models
* **VS Code extension** (beta)**:** Download from the [VS Code Extension Marketplace](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code) to get started
* **Terminal updates**, including the visual refresh and checkpoints, are available to all Claude Code users—just update your local installation
* **Claude Agent SDK:** [See the docs](https://docs.claude.com/en/api/agent-sdk/overview) to get started


<!-- Content filtered: site navigation/footer -->
