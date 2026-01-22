---
source_url: https://www.anthropic.com/news/claude-haiku-4-5
source_type: sitemap
content_hash: sha256:779fbf1d21b212e7f7efff66a8f994a0cb35bbe5b5f575f2aeb1b61b1c9fa962
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-10-15'
---

Product

# Introducing Claude Haiku 4.5

[![Video](https://img.youtube.com/vi/ccQSHQ3VGIc/maxresdefault.jpg)](https://www.youtube.com/watch?v=ccQSHQ3VGIc)

Oct 15, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/6457c34fbcb012acf0f27f15a6006f700d0f50de-1000x1000.svg)

Claude Haiku 4.5, our latest small model, is available today to all users.

What was recently at the frontier is now cheaper and faster. Five months ago, Claude Sonnet 4 was a state-of-the-art model. Today, Claude Haiku 4.5 gives you similar levels of coding performance but at one-third the cost and more than twice the speed.

![Chart comparing frontier models on SWE-bench Verified which measures performance on real-world coding tasks](https://www-cdn.anthropic.com/images/4zrzovbb/website/1a27d7a85f953c5a0577dc19b507d6e1b93444d5-1920x1080.png)

Claude Haiku 4.5 even surpasses Claude Sonnet 4 at certain tasks, like using computers. These advances make applications like [Claude for Chrome](http://claude.ai/redirect/website.v1.NORMALIZED/chrome) faster and more useful than ever before.

Users who rely on AI for real-time, low-latency tasks like chat assistants, customer service agents, or pair programming will appreciate Haiku 4.5’s combination of high intelligence and remarkable speed. And users of Claude Code will find that Haiku 4.5 makes the coding experience—from multiple-agent projects to rapid prototyping—markedly more responsive.

Claude Sonnet 4.5, released [two weeks ago](https://www.anthropic.com/news/claude-sonnet-4-5), remains our frontier model and the best coding model in the world. Claude Haiku 4.5 gives users a new option for when they want near-frontier performance with much greater cost-efficiency. It also opens up new ways of using our models together. For example, Sonnet 4.5 can break down a complex problem into multi-step plans, then orchestrate a team of multiple Haiku 4.5s to complete subtasks in parallel.

Claude Haiku 4.5 is available everywhere today. If you’re a developer, simply use claude-haiku-4-5 via the Claude API. Pricing is now $1/$5 per million input and output tokens.

## Benchmarks

![Comparison table of frontier models across popular benchmarks](https://www-cdn.anthropic.com/images/4zrzovbb/website/029af67124b67bdf0b50691a8921b46252c023d2-1920x1625.png)

Claude Haiku 4.5 is one of our most powerful models to date. See footnotes for methodology.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/a638c23edfce0d313f951732a2379b89cd40d682-235x64.svg)

> Claude Haiku 4.5 hit a sweet spot we didn't think was possible: **near-frontier coding quality with blazing speed and cost efficiency**. In Augment's agentic coding evaluation, it achieves 90% of Sonnet 4.5's performance, matching much larger models. We're excited to offer it to our users.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/14c3ac690679578d7361cf67c93f11782531d602-150x48.svg)

> **Claude Haiku 4.5 is a leap forward for agentic coding**, particularly for sub-agent orchestration and computer use tasks. The responsiveness makes AI-assisted development in Warp feel instantaneous.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/094b76abf3e64453c224e12ae388b8008b02660e-150x48.svg)

> Historically models have sacrificed speed and cost for quality. Claude Haiku 4.5 is blurring the lines on this trade off: **it's a fast frontier model that keeps costs efficient** and signals where this class of models is headed.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/02dced142fb26d4a3441cad79f997a1fd6c9a8b0-150x48.svg)

> **Claude Haiku 4.5 delivers intelligence without sacrificing speed**, enabling us to build AI applications that utilize both deep reasoning and real-time responsiveness.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/9235b38d087c4aea7debc0e62fc6f37d337ff237-356x68.svg)

> Claude Haiku 4.5 is remarkably capable—**just six months ago, this level of performance would have been state-of-the-art** on our internal benchmarks. Now it runs up to 4-5 times faster than Sonnet 4.5 at a fraction of the cost, unlocking an entirely new set of use cases.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/023ced6d84b14452f308b629b8931b80d8120e28-150x48.svg)

> Speed is the new frontier for AI agents operating in feedback loops. **Haiku 4.5 proves you can have both intelligence and rapid output**. It handles complex workflows reliably, self-corrects in real-time, and maintains momentum without latency overhead. For most development tasks, it's the ideal performance balance.

![Gamma logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/d1a7e2e3c3c9c90411efd32141c8dc02f83efef2-150x48.svg)

> Claude Haiku 4.5 **outperformed our current models on instruction-following for slide text generation**, achieving 65% accuracy versus 44% from our premium tier model—that's a game-changer for our unit economics.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/7715b118c5eb0ff2a85f1f7914bce8c634ecacbd-150x48.svg)

> Our early testing shows that Claude Haiku 4.5 brings efficient code generation to GitHub Copilot **with comparable quality to Sonnet 4 but at faster speed**. Already we're seeing it as an excellent choice for Copilot users who value speed and responsiveness in their AI-powered development workflows.

01 / 08

## Safety evaluations

We ran a detailed series of safety and alignment evaluations on Claude Haiku 4.5. The model showed low rates of concerning behaviors, and was substantially more aligned than its predecessor, Claude Haiku 3.5. In our automated alignment assessment, Claude Haiku 4.5 also showed a statistically significantly lower overall rate of misaligned behaviors than both Claude Sonnet 4.5 and Claude Opus 4.1—making Claude Haiku 4.5, by this metric, our safest model yet.

Our safety testing also showed that Claude Haiku 4.5 poses only limited risks in terms of the production of chemical, biological, radiological, and nuclear (CBRN) weapons. For that reason, we’ve released it under the AI Safety Level 2 (ASL-2) standard—compared to the more restrictive ASL-3 for Sonnet 4.5 and Opus 4.1. You can read the full reasoning behind the model’s ASL-2 classification, as well as details on all our other safety tests, in the [Claude Haiku 4.5 system card](https://www.anthropic.com/claude-haiku-4-5-system-card).

## Further information

Claude Haiku 4.5 is available now on Claude Code and our apps. Its efficiency means you can accomplish more within your usage limits while maintaining premium model performance.

Developers can use Claude Haiku 4.5 on our API, Amazon Bedrock, and Google Cloud’s Vertex AI, where it serves as a drop-in replacement for both Haiku 3.5 and Sonnet 4 at our most economical price point.

For complete technical details and evaluation results, see our [system card](https://www.anthropic.com/claude-haiku-4-5-system-card), [model page](https://www.anthropic.com/claude/haiku), and [documentation](https://docs.claude.com/en/docs/about-claude/models/overview).

#### Methodology

* **SWE-bench Verified**: All Claude results were reported using a simple scaffold with two tools—bash and file editing via string replacements. We report 73.3%, which was averaged over 50 trials, no test-time compute, 128K thinking budget, and default sampling parameters (temperature, top\_p) on the full 500-problem SWE-bench Verified dataset.
  + The score reported uses a minor prompt addition: "You should use tools as much as possible, ideally more than 100 times. You should also implement your own tests first before attempting the problem."
* **Terminal-Bench**: All scores reported use the default agent framework (Terminus 2), with XML parser, averaging 11 runs (6 without thinking (40.21% score), 5 with 32K thinking budget (41.75% score)) with n-attempts=1.
* **τ2-bench**: Scores were achieved averaging over 10 runs using extended thinking (128k thinking budget) and default sampling parameters (temperature, top\_p) with tool use and a prompt addendum to the Airline and Telecom Agent Policy instructing Claude to better target its known failure modes when using the vanilla prompt. A prompt addendum was also added to the Telecom User prompt to avoid failure modes from the user ending the interaction incorrectly.
* **AIME**: Haiku 4.5 score reported as the average over 10 independent runs that each calculate pass@1 over 16 trials with default sampling parameters (temperature, top\_p) and 128K thinking budget.
* **OSWorld**: All scores reported use the official OSWorld-Verified framework with 100 max steps, averaged across 4 runs with 128K total thinking budget and 2K thinking budget per-step configured.
* **MMMLU**: All scores reported are the average of 10 runs over 14 non-English languages with a 128K thinking budget.
* All other scores were averaged over 10 runs with default sampling parameters (temperature, top\_p) and 128K thinking budget.

All OpenAI scores reported from their [GPT-5 post](https://openai.com/index/introducing-gpt-5/), [GPT-5 for developers post](https://openai.com/index/introducing-gpt-5-for-developers/), [GPT-5 system card](https://cdn.openai.com/gpt-5-system-card.pdf) (SWE-bench Verified reported using n=500), and [Terminal Bench leaderboard](https://www.tbench.ai/) (using Terminus 2). All Gemini scores reported from their [model web page](https://deepmind.google/models/gemini/pro/), and [Terminal Bench leaderboard](https://www.tbench.ai/) (using Terminus 1).


<!-- Content filtered: site navigation/footer -->
