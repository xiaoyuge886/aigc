---
source_url: https://www.anthropic.com/news/claude-opus-4-1
source_type: sitemap
content_hash: sha256:3eda211c62cda6c4794188c76a076d0cfe63fedea94f2d48264a40c68d565589
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-08-05'
---

Announcements

# Claude Opus 4.1

Aug 5, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/a97733b3607b54a30778eb89de08afd9e02b9fb3-1000x1000.svg)

Today we're releasing Claude Opus 4.1, an upgrade to Claude Opus 4 on agentic tasks, real-world coding, and reasoning. We plan to release substantially larger improvements to our models in the coming weeks.

Opus 4.1 is now available to paid Claude users and in Claude Code. It's also on our API, Amazon Bedrock, and Google Cloud's Vertex AI. Pricing is the same as Opus 4.

## Claude Opus 4.1

Opus 4.1 advances our state-of-the-art coding performance to 74.5% on [SWE-bench Verified](https://www.swebench.com/). It also improves Claude’s in-depth research and data analysis skills, especially around detail tracking and agentic search.

![Chart showing Claude's progress on a popular coding evaluation](https://www-cdn.anthropic.com/images/4zrzovbb/website/dced1e451a52da3bcb3807d7a9510b1b5426ace6-3840x2160.png)

**GitHub** notes that Claude Opus 4.1 improves across most capabilities relative to Opus 4, with particularly notable performance gains in multi-file code refactoring. **Rakuten Group** finds that Opus 4.1 excels at pinpointing exact corrections within large codebases without making unnecessary adjustments or introducing bugs, with their team preferring this precision for everyday debugging tasks. **Windsurf** reports Opus 4.1 delivers a one standard deviation improvement over Opus 4 on their junior developer benchmark, showing roughly the same performance leap as the jump from Sonnet 3.7 to Sonnet 4.

![A benchmark table comparing Claude Opus 4.1 to prior Claude models and other public models](https://www-cdn.anthropic.com/images/4zrzovbb/website/bde326699c667506c87f74b09a6355961d29eb26-2600x2084.png)

## Getting started

We recommend upgrading from Opus 4 to Opus 4.1 for all uses. If you’re a developer, simply use `claude-opus-4-1-20250805` via the API. You can also explore our [system card](https://www.anthropic.com/claude-opus-4-1-system-card), [model page](https://www.anthropic.com/claude/opus), [pricing page](https://www.anthropic.com/pricing#api), and [docs](https://docs.anthropic.com/en/docs/about-claude/models/overview) to learn more.

As always, your [feedback](mailto: feedback@anthropic.com) helps us improve, especially as we continue to release new and more capable models.

#### Appendix

**Data sources**

* OpenAI: [o3 launch post](https://openai.com/index/introducing-o3-and-o4-mini/), [o3 system card](https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf)
* Gemini: [2.5 Pro model card](https://storage.googleapis.com/model-cards/documents/gemini-2.5-pro.pdf)
* Claude: [Sonnet 3.7 launch post](https://www.anthropic.com/news/claude-3-7-sonnet), [Claude 4 launch post](https://www.anthropic.com/news/claude-4)

**Benchmark reporting**

Claude models are hybrid reasoning models. The benchmarks reported in this blog post show the highest scores achieved with or without extended thinking. We’ve noted below for each result whether extended thinking was used:

* No extended thinking: SWE-bench Verified, Terminal-Bench
* The following benchmarks were reported with extended thinking (up to 64K tokens): TAU-bench, GPQA Diamond, MMMLU, MMMU, AIME

**TAU-bench methodology**

Scores were achieved with a prompt addendum to both the Airline and Retail Agent Policy instructing Claude to better leverage its reasoning abilities while using extended thinking with tool use. The model is encouraged to write down its thoughts as it solves the problem distinct from our usual thinking mode, during the multi-turn trajectories to best leverage its reasoning abilities. To accommodate the additional steps Claude incurs by utilizing more thinking, the maximum number of steps (counted by model completions) was increased from 30 to 100 (most trajectories completed under 30 steps with only one trajectory reaching above 50 steps).

**SWE-bench methodology**

For the Claude 4 family of models, we continue to use the same simple scaffold that equips the model with solely the two tools described in our prior releases [here](https://www.anthropic.com/engineering/swe-bench-sonnet)—a bash tool, and a file editing tool that operates via string replacements. We no longer include the [third ‘planning tool’](https://www.anthropic.com/engineering/claude-think-tool) used by Claude 3.7 Sonnet. On all Claude 4 models, we report scores out of the full 500 problems. Scores for OpenAI models are reported out of a [477 problem subset](https://openai.com/index/gpt-4-1/).


<!-- Content filtered: site navigation/footer -->
