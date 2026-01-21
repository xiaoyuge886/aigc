---
source_url: https://www.anthropic.com/news/claude-sonnet-4-5
source_type: sitemap
content_hash: sha256:6b454e459eaa6049944ecffffcffcb77b350f7fab893dad3cdb79a30d93dc9ba
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-09-29'
---

Announcements

# Introducing Claude Sonnet 4.5

[![Video](https://img.youtube.com/vi/dGiqrsv530Y/maxresdefault.jpg)](https://www.youtube.com/watch?v=dGiqrsv530Y)

[![Video](https://img.youtube.com/vi/OZ-aLrJ0oVg/maxresdefault.jpg)](https://www.youtube.com/watch?v=OZ-aLrJ0oVg)

[![Video](https://img.youtube.com/vi/vLIDHi-1PVU/maxresdefault.jpg)](https://www.youtube.com/watch?v=vLIDHi-1PVU)

[![Video](https://img.youtube.com/vi/DAQJvGjlgVM/maxresdefault.jpg)](https://www.youtube.com/watch?v=DAQJvGjlgVM)

[![Video](https://img.youtube.com/vi/oXfVkbb7MCg/maxresdefault.jpg)](https://www.youtube.com/watch?v=oXfVkbb7MCg)

Sep 29, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/a683fdcfe3e2c7c6532342a0fa4ff789c3fd4852-1000x1000.svg)

Claude Sonnet 4.5 is the best coding model in the world. It's the strongest model for building complex agents. It’s the best model at using computers. And it shows substantial gains in reasoning and math.

Code is everywhere. It runs every application, spreadsheet, and software tool you use. Being able to use those tools and reason through hard problems is how modern work gets done.

Claude Sonnet 4.5 makes this possible. We're releasing it along with a set of major upgrades to our products. In [Claude Code](https://anthropic.com/news/enabling-claude-code-to-work-more-autonomously), we've added checkpoints—one of our most requested features—that save your progress and allow you to roll back instantly to a previous state. We've refreshed the terminal interface and shipped a [native VS Code extension](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code). We've added a new [context editing feature and memory tool](https://anthropic.com/news/context-management) to the Claude API that lets agents run even longer and handle even greater complexity. In the Claude [apps](https://claude.ai/redirect/website.v1.NORMALIZED/download), we've brought code execution and [file creation](https://www.anthropic.com/news/create-files) (spreadsheets, slides, and documents) directly into the conversation. And we've made the [Claude for Chrome](https://www.anthropic.com/news/claude-for-chrome) extension available to Max users who joined the waitlist last month.

We're also giving developers the building blocks we use ourselves to make Claude Code. We're calling this the [Claude Agent SDK](https://anthropic.com/engineering/building-agents-with-the-claude-agent-sdk). The infrastructure that powers our frontier products—and allows them to reach their full potential—is now yours to build with.

This is the [most aligned frontier model](https://www.anthropic.com/claude-sonnet-4-5-system-card) we’ve ever released, showing large improvements across several areas of alignment compared to previous Claude models.

Claude Sonnet 4.5 is available everywhere today. If you’re a developer, simply use `claude-sonnet-4-5` via [the Claude API](https://docs.claude.com/en/docs/about-claude/models/overview). Pricing remains the same as Claude Sonnet 4, at $3/$15 per million tokens.

## Frontier intelligence

Claude Sonnet 4.5 is state-of-the-art on the SWE-bench Verified evaluation, which measures real-world software coding abilities. Practically speaking, we’ve observed it maintaining focus for more than 30 hours on complex, multi-step tasks.

![Chart showing frontier model performance on SWE-bench Verified with Claude Sonnet 4.5 leading](https://www-cdn.anthropic.com/images/4zrzovbb/website/6421e7049ff8b2c4591497ec92dc4157b2ac1b30-3840x2160.png)

Claude Sonnet 4.5 represents a significant leap forward on computer use. On OSWorld, a benchmark that tests AI models on real-world computer tasks, Sonnet 4.5 now leads at 61.4%. Just four months ago, Sonnet 4 held the lead at 42.2%. Our [Claude for Chrome](https://www.anthropic.com/news/claude-for-chrome) extension puts these upgraded capabilities to use. In the demo below, we show Claude working directly in a browser, navigating sites, filling spreadsheets, and completing tasks.

The model also shows improved capabilities on a broad range of evaluations including reasoning and math:

![Benchmark table comparing frontier models across popular public evals](https://www-cdn.anthropic.com/images/4zrzovbb/website/67081be1ea2752e2a554e49a6aab2731b265d11b-2600x2288.png)

Claude Sonnet 4.5 is our most powerful model to date. See footnotes for methodology.

Experts in finance, law, medicine, and STEM found Sonnet 4.5 shows dramatically better domain-specific knowledge and reasoning compared to older models, including Opus 4.1.

FinanceLawMedicineSTEM

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/7175bc18c46562f1228280a7abda751219a2aae1-3840x2160.png)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/fd313a5edb996d98b9fc73ee5b3e6a34fbbcbb83-3840x2160.png)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/442f96fd96de39e3ff3a05b288e2647dd7ec2f58-3840x2160.png)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/711e6e1178f0ed7ca9aa85a5e0e9940a807c436a-3840x2160.png)

The model’s capabilities are also reflected in the experiences of early customers:

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/464cf83cd04ad624fee1730a71914b18e89cdf9b-150x48.svg)

> **We're seeing state-of-the-art coding performance from Claude Sonnet 4.5**, with significant improvements on longer horizon tasks. It reinforces why many developers using Cursor choose Claude for solving their most complex problems.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/7715b118c5eb0ff2a85f1f7914bce8c634ecacbd-150x48.svg)

> **Claude Sonnet 4.5 amplifies GitHub Copilot's core strengths**. Our initial evals show significant improvements in multi-step reasoning and code comprehension—enabling Copilot's agentic experiences to handle complex, codebase-spanning tasks better.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/daef759120b29e4db8ba4a5664d7574750964ab9-150x48.svg)

> **Claude Sonnet 4.5 is excellent at software development tasks**, learning our codebase patterns to deliver precise implementations. It handles everything from debugging to architecture with deep contextual understanding, transforming our development velocity.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/eb96f772e9ae5e340de41e6b07f3c6d50b3fff22-150x48.svg)

> Claude Sonnet 4.5 **reduced average vulnerability intake time for our Hai security agents by 44% while improving accuracy by 25%**, helping us reduce risk for businesses with confidence.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/8cbf56e184dd5174705a0f55cb91b0af545982ff-150x48.svg)

> **Claude Sonnet 4.5 is state of the art on the most complex litigation tasks.** For example, analyzing full briefing cycles and conducting research to synthesize excellent first drafts of an opinion for judges, or interrogating entire litigation records to create detailed summary judgment analysis.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/431e098a503851789fa4508b88a0418853f513eb-150x48.svg)

> Claude Sonnet 4.5's edit capabilities are exceptional — **we went from 9% error rate on Sonnet 4 to 0% on our internal code editing benchmark**. Higher tool success at lower cost is a major leap for agentic coding. Claude Sonnet 4.5 balances creativity and control perfectly.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/66e0000e396aea64ea31ed3fea7b2b20ac329312-150x48.svg)

> Claude Sonnet 4.5 delivers impressive gains on our most complex, long-context tasks—from engineering in our codebase to in-product features and research. **It's noticeably more intelligent and a big leap forward**, helping us push what 240M+ users can design with Canva.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/cdec0ff1244295571db38838e90f61c47681d63d-150x48.svg)

> **Claude Sonnet 4.5 has noticeably improved Figma Make in early testing**, making it easier to prompt and iterate. Teams can explore and validate their ideas with more functional prototypes and smoother interactions, while still getting the design quality Figma is known for.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/094b76abf3e64453c224e12ae388b8008b02660e-150x48.svg)

> **Sonnet 4.5 represents a new generation of coding models**. It's surprisingly efficient at maximizing actions per context window through parallel tool execution, for example running multiple bash commands at once.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/6e418ccebe0a1d6fd13f21094852b080a0c93ae5-150x48.svg)

> For Devin, Claude Sonnet 4.5 increased planning performance by 18% and end-to-end eval scores by 12%—**the biggest jump we've seen since the release of Claude Sonnet 3.6**. It excels at testing its own code, enabling Devin to run longer, handle harder tasks, and deliver production-ready code.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/5a7dfab326b449aedc0d11053f9d42f48951ae7e-150x48.svg)

> **Claude Sonnet 4.5 shows strong promise for red teaming**, generating creative attack scenarios that accelerate how we study attacker tradecraft. These insights strengthen our defenses across endpoints, identity, cloud, data, SaaS, and AI workloads.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/b0b6b40b55f3aa73e8a32ce81f9bb927134fd3da-150x48.svg)

> Claude Sonnet 4.5 resets our expectations—**it handles 30+ hours of autonomous coding**, freeing our engineers to tackle months of complex architectural work in dramatically less time while maintaining coherence across massive codebases.

![ logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/4fcce1a2389ddafa9f3302c51960e1ff4bfbd3d7-150x48.svg)

> For complex financial analysis—risk, structured products, portfolio screening—Claude Sonnet 4.5 with thinking **delivers investment-grade insights that require less human review**. When depth matters more than speed, it's a meaningful step forward for institutional finance.

01 / 13

## Our most aligned model yet

As well as being our most capable model, Claude Sonnet 4.5 is our most aligned frontier model yet. Claude’s improved capabilities and our extensive safety training have allowed us to substantially improve the model’s behavior, reducing concerning behaviors like sycophancy, deception, power-seeking, and the tendency to encourage delusional thinking. For the model’s agentic and computer use capabilities, we’ve also made considerable progress on defending against prompt injection attacks, one of the most serious risks for users of these capabilities.

You can read a detailed set of safety and alignment evaluations, which for the first time includes tests using techniques from mechanistic interpretability, in the Claude Sonnet 4.5 [system card](https://www.anthropic.com/claude-sonnet-4-5-system-card).

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/33efc283321feeff94dd80973dbcd38409806cf5-3840x2160.png)

Overall misaligned behavior scores from an automated behavioral auditor (lower is better). Misaligned behaviors include (but are not limited to) deception, sycophancy, power-seeking, encouragement of delusions, and compliance with harmful system prompts. More details can be found in the Claude Sonnet 4.5 [system card](https://www.anthropic.com/claude-sonnet-4-5-system-card).

Claude Sonnet 4.5 is being released under our AI Safety Level 3 (ASL-3) protections, as per [our framework](https://www.anthropic.com/news/announcing-our-updated-responsible-scaling-policy) that matches model capabilities with appropriate safeguards. These safeguards include filters called classifiers that aim to detect potentially dangerous inputs and outputs—in particular those related to chemical, biological, radiological, and nuclear (CBRN) weapons.

These classifiers might sometimes inadvertently flag normal content. We’ve made it easy for users to continue any interrupted conversations with Sonnet 4, a model that poses a lower CBRN risk. We've already made significant progress in reducing these false positives, reducing them by a factor of ten since [we originally described them](https://www.anthropic.com/news/constitutional-classifiers), and a factor of two since Claude Opus 4 was released in May. We’re continuing to make progress in making the classifiers more discerning1.

## The Claude Agent SDK

We've spent more than six months shipping updates to Claude Code, so we know what it takes to [build](https://www.youtube.com/watch?v=DAQJvGjlgVM) and [design](https://www.youtube.com/watch?v=vLIDHi-1PVU) AI agents. We've solved hard problems: how agents should manage memory across long-running tasks, how to handle permission systems that balance autonomy with user control, and how to coordinate subagents working toward a shared goal.

Now we’re making all of this available to you. The [Claude Agent SDK](https://anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) is the same infrastructure that powers Claude Code, but it shows impressive benefits for a very wide variety of tasks, not just coding. As of today, you can use it to build your own agents.

We built Claude Code because the tool we wanted didn’t exist yet. The Agent SDK gives you the same foundation to build something just as capable for whatever problem you're solving.

## Bonus research preview

We’re releasing a temporary research preview alongside Claude Sonnet 4.5, called "[Imagine with Claude](https://claude.ai/redirect/website.v1.NORMALIZED/imagine)".

In this experiment, Claude generates software on the fly. No functionality is predetermined; no code is prewritten. What you see is Claude creating in real time, responding and adapting to your requests as you interact.

It's a fun demonstration showing what Claude Sonnet 4.5 can do—a way to see what's possible when you combine a capable model with the right infrastructure.

"Imagine with Claude" is available to Max subscribers for the next five days. We encourage you to try it out on [claude.ai/imagine](https://claude.ai/redirect/website.v1.NORMALIZED/imagine).

## Further information

We recommend upgrading to Claude Sonnet 4.5 for all uses. Whether you’re using Claude through our apps, our API, or Claude Code, Sonnet 4.5 is a drop-in replacement that provides much improved performance for the same price. Claude Code updates are available to all users. [Claude Developer Platform](https://claude.com/platform/api) updates, including the Claude Agent SDK, are available to all developers. Code execution and file creation are available on all paid plans in the Claude apps.

For complete technical details and evaluation results, see our [system card](https://www.anthropic.com/claude-sonnet-4-5-system-card), [model page](https://www.anthropic.com/claude/sonnet), and [documentation](https://docs.claude.com/en/docs/about-claude/models/overview). For more information, explore our [engineering](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) [posts](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) and research post on [cybersecurity](https://red.anthropic.com/2025/ai-for-cyber-defenders).

#### Footnotes

*1**:** Customers in the cybersecurity and biological research industries can work with their account teams to join our allowlist in the meantime.*  
  
**Methodology**

* **SWE-bench Verified**: All Claude results were reported using a simple scaffold with two tools—bash and file editing via string replacements. We report 77.2%, which was averaged over 10 trials, no test-time compute, and 200K thinking budget on the full 500-problem SWE-bench Verified dataset.
  + The score reported uses a minor prompt addition: "You should use tools as much as possible, ideally more than 100 times. You should also implement your own tests first before attempting the problem."
  + A 1M context configuration achieves 78.2%, but we report the 200K result as our primary score as the 1M configuration was implicated in our recent [inference issues](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues).
  + For our "high compute" numbers we adopt additional complexity and parallel test-time compute as follows:
    - We sample multiple parallel attempts.
    - We discard patches that break the visible regression tests in the repository, similar to the rejection sampling approach adopted by [Agentless](https://arxiv.org/abs/2407.01489) (Xia et al. 2024); note no hidden test information is used.
    - We then use an internal scoring model to select the best candidate from the remaining attempts.
    - This results in a score of 82.0% for Sonnet 4.5.
* **Terminal-Bench**: All scores reported use the default agent framework (Terminus 2), with XML parser, averaging multiple runs during different days to smooth the eval sensitivity to inference infrastructure.
* **τ2-bench:** Scores were achieved using extended thinking with tool use and a prompt addendum to the Airline and Telecom Agent Policy instructing Claude to better target its known failure modes when using the vanilla prompt. A prompt addendum was also added to the Telecom User prompt to avoid failure modes from the user ending the interaction incorrectly.
* **AIME**: Sonnet 4.5 score reported using sampling at temperature 1.0. The model used 64K reasoning tokens for the Python configuration.
* **OSWorld:** All scores reported use the official OSWorld-Verified framework with 100 max steps, averaged across 4 runs.
* **MMMLU**: All scores reported are the average of 5 runs over 14 non-English languages with extended thinking (up to 128K).
* **Finance Agent**: All scores reported were run and published by [Vals AI](https://vals.ai) on their public leaderboard. All Claude model results reported are with extended thinking (up to 64K) and Sonnet 4.5 is reported with interleaved thinking on.
* All OpenAI scores reported from their [GPT-5 post](https://openai.com/index/introducing-gpt-5/), [GPT-5 for developers post](https://openai.com/index/introducing-gpt-5-for-developers/), [GPT-5 system card](https://cdn.openai.com/gpt-5-system-card.pdf) (SWE-bench Verified reported using n=500), [Terminal Bench leaderboard](https://www.tbench.ai/) (using Terminus 2), and public [Vals AI](http://vals.ai) leaderboard. All Gemini scores reported from their [model web page](https://deepmind.google/models/gemini/pro/), [Terminal Bench leaderboard](https://www.tbench.ai/) (using Terminus 1), and public [Vals AI](https://vals.ai) leaderboard.


<!-- Content filtered: site navigation/footer -->
