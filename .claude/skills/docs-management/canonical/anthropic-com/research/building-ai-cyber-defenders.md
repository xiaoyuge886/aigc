---
source_url: https://www.anthropic.com/research/building-ai-cyber-defenders
source_type: sitemap
content_hash: sha256:6075e7757d431c9679bb3431046fe661d60c0e9b0c0ece576621cc7196472fbe
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-10-03'
---

Policy

# Building AI for cyber defenders

Oct 3, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/97cf99624aa60f59b75f9e08cdf0f00d33c34804-1000x1000.svg)

**AI models are now useful for cybersecurity tasks in practice, not just theory. As research and experience demonstrated the utility of frontier AI as a tool for cyber attackers, we invested in improving Claude’s ability to help defenders detect, analyze, and remediate vulnerabilities in code and deployed systems. This work allowed Claude Sonnet 4.5 to match or eclipse Opus 4.1, our frontier model released only two months prior, in discovering code vulnerabilities and other cyber skills. Adopting and experimenting with AI will be key for defenders to keep pace.**

[@portabletext/react] Unknown block type "horizontalRule", specify a component for it in the `components.types` prop

We believe we are now at an inflection point for AI’s impact on cybersecurity.

For several years, our team has carefully tracked the cybersecurity-relevant capabilities of AI models. Initially, we found models to be not particularly powerful for advanced and meaningful capabilities. However, over the past year or so, we’ve noticed a shift. For example:

* We showed that models could [reproduce one of the costliest cyberattacks](https://red.anthropic.com/2025/cyber-toolkits/) in history—the 2017 Equifax breach—in simulation.
* We entered Claude into cybersecurity competitions, and it [outperformed human teams](https://red.anthropic.com/2025/cyber-competitions/) in some cases.
* Claude has helped us [discover vulnerabilities in our own code](https://www.anthropic.com/news/automate-security-reviews-with-claude-code) and fix them before release.

In this summer’s DARPA [AI Cyber Challenge](https://aicyberchallenge.com/), teams used LLMs (including Claude) to build “cyber reasoning systems” that examined millions of lines of code for vulnerabilities to patch. In addition to inserted vulnerabilities, teams found (and sometimes patched) [previously undiscovered, non-synthetic vulnerabilities](https://aicyberchallenge.com/Finals-winners-announcement/). Beyond a competition setting, other frontier labs now apply models to [discover and report novel vulnerabilities](https://blog.google/technology/safety-security/cybersecurity-updates-summer-2025/).

At the same time, as part of our Safeguards work, we have found and disrupted threat actors on our own platform who leveraged AI to scale their operations. Our [Safeguards](https://www.anthropic.com/news/building-safeguards-for-claude) team recently discovered (and disrupted) a case of “[vibe hacking](https://www.anthropic.com/news/detecting-countering-misuse-aug-2025),” in which a cybercriminal used Claude to build a large-scale data extortion scheme that previously would have required an entire team of people. Safeguards has also detected and countered Claude's use in increasingly [complex espionage operations](https://www-cdn.anthropic.com/b2a76c6f6992465c09a6f2fce282f6c0cea8c200.pdf), including the targeting of critical telecommunications infrastructure, by an actor that demonstrated characteristics consistent with Chinese APT operations.

All of these lines of evidence lead us to think we are at an important inflection point in the cyber ecosystem, and progress from here could become quite fast or usage could grow quite quickly.

Therefore, now is an important moment to accelerate defensive use of AI to secure code and infrastructure. **We should not cede the cyber advantage derived from AI to attackers and criminals.** While we will continue to invest in detecting and disrupting malicious attackers, we think the most scalable solution is to build AI systems that empower those safeguarding our digital environments—like security teams protecting businesses and governments, cybersecurity researchers, and maintainers of critical open-source software.

In the run-up to the release of Claude Sonnet 4.5, we started to do just that.

## Claude Sonnet 4.5: emphasizing cyber skills

As LLMs scale in size, “[emergent abilities](https://arxiv.org/abs/2206.07682)”—skills that were not evident in smaller models and were not necessarily an explicit target of model training—appear. Indeed, Claude’s abilities to execute cybersecurity tasks like finding and exploiting software vulnerabilities in Capture-the-Flag (CTF) challenges have been byproducts of developing generally useful AI assistants.

But we don’t want to rely on general model progress alone to better equip defenders. Because of the urgency of this moment in the evolution of AI and cybersecurity, we dedicated researchers to making Claude better at key skills like code vulnerability discovery and patching.

The results of this work are reflected in Claude Sonnet 4.5. It is comparable or superior to Claude Opus 4.1 in many aspects of cybersecurity while also being less expensive and faster.

## Evidence from evaluations

In building Sonnet 4.5, we had a small research team focus on enhancing Claude’s ability to find vulnerabilities in codebases, patch them, and test for weaknesses in simulated deployed security infrastructure. We chose these because they reflect important tasks for defensive actors. We deliberately avoided enhancements that clearly favor offensive work—such as advanced exploitation or writing malware. We hope to enable models to find insecure code before deployment and to find and fix vulnerabilities in deployed code. There are, of course, many more critical security tasks we did not focus on; at the end of this post, we elaborate on future directions.

To test the effects of our research, we ran industry-standard evaluations of our models. These enable clear comparisons across models, measure the speed of AI progress, and—especially in the case of novel, externally developed evaluations—provide a good metric to ensure that we are not simply teaching to our own tests.

As we ran these evaluations, one thing that stood out was the importance of running them many times. Even if it is computationally expensive for a large set of evaluation tasks, it better captures the behavior of a motivated attacker or defender on any particular real-world problem. Doing so reveals impressive performance not only from Claude Sonnet 4.5, but also from models several generations older.

### Cybench

One of the evaluations we have tracked for over a year is [Cybench](https://cybench.github.io/), a benchmark drawn from CTF competition challenges.1 On this evaluation, we see striking improvement from Claude Sonnet 4.5, not just over Claude Sonnet 4, but even over Claude Opus 4 and 4.1 models. Perhaps most striking, *Sonnet 4.5 achieves a higher probability of success given one attempt per task than Opus 4.1 when given ten attempts per task*. The challenges that are part of this evaluation reflect somewhat complex, long-duration workflows. For example, one challenge involved analyzing network traffic, extracting malware from that traffic, and decompiling and decrypting the malware. We estimate that this would have taken a skilled human at least an hour, and possibly much longer; Claude took 38 minutes to solve it.

When we give Claude Sonnet 4.5 10 attempts at the Cybench evaluation, it succeeds on 76.5% of the challenges. This is particularly noteworthy because we have doubled this success rate in just the past six months (Sonnet 3.7, released in February 2025, had only a 35.9% success rate when given 10 trials).

![Claude Sonnet 4.5 outperforms other models at Cybench](https://www-cdn.anthropic.com/images/4zrzovbb/website/ea02c36272de121f033e474a8afda8a039f0ec2c-3000x1800.png)

Model Performance on Cybench. Claude Sonnet 4.5 significantly outperforms all previous models given k=1, 10, or 30 trials, where probability of success is measured as the expectation over the proportion of problems where at least one of k trials succeeds. Note that these results are on a subset of 37 of the 40 original Cybench problems, where 3 problems were excluded due to implementation difficulties.

### CyberGym

In another external evaluation, we evaluated Claude Sonnet 4.5 on [CyberGym](https://www.cybergym.io/), a benchmark that evaluates the ability of agents to (1) find (previously-discovered) vulnerabilities in real open-source software projects given a high-level description of the weakness, and (2) discover new (previously-undiscovered) vulnerabilities.2 The CyberGym team previously found that Claude Sonnet 4 was the strongest model on their [public leaderboard](https://www.cybergym.io/).

Claude Sonnet 4.5 scores significantly better than either Claude Sonnet 4 or Claude Opus 4. When using the same cost constraints as the public CyberGym leaderboard (i.e., a limit of $2 of LLM API queries per vulnerability) we find that Sonnet 4.5 achieves a new state-of-the-art score of 28.9%. But true attackers are rarely limited in this way: they can attempt many attacks, for far more than $2 per trial. When we remove these constraints and give Claude 30 trials per task, we find that Sonnet 4.5 reproduces vulnerabilities in 66.7% of programs. And although the relative price of this approach is higher, the absolute cost—about $45 to try one task 30 times—remains quite low.

![Model Performance on CyberGym — Sonnet 4.5 is more likely to be successful, both after one trial and after thirty.](https://www-cdn.anthropic.com/images/4zrzovbb/website/c35c81850f6f90e9b5f8064acf5c9effba71b1fe-3493x1640.png)

Model Performance on CyberGym. Sonnet 4.5 outperforms all previous models, including Opus 4.1. \*Note that Opus 4.1, given its higher price, did not follow the same $2 cost constraint as the other models in the 1 trial scenario.

Equally interesting is the rate at which Claude Sonnet 4.5 discovers new vulnerabilities. While the CyberGym leaderboard shows that Claude Sonnet 4 only discovers vulnerabilities in about 2% of targets, Sonnet 4.5 discovers new vulnerabilities in 5% of cases. By repeating the trial 30 times it discovers new vulnerabilities in over 33% of projects.

![Model Performance on CyberGym new vulnerability discovery](https://www-cdn.anthropic.com/images/4zrzovbb/website/f00cf63cfc5bd5dd2e5e94d4aabde7ec8fb43f6c-3000x1800.png)

Model Performance on CyberGym. Sonnet 4.5 outperforms Sonnet 4 at new vulnerability discovery with only one trial and dramatically outstrips its performance when given 30 trials.

### Further research into patching

We are also conducting preliminary research into Claude's ability to generate and review patches that fix vulnerabilities. Patching vulnerabilities is a harder task than finding them because the model has to make surgical changes that remove the vulnerability without altering the original functionality. Without guidance or specifications, the model has to infer this intended functionality from the code base.

In our experiment we tasked Claude Sonnet 4.5 with patching vulnerabilities in the CyberGym evaluation set based on a description of the vulnerability and information about what the program was doing when it crashed. We used Claude to judge its own work, asking it to grade the submitted patches by comparing them to human-authored reference patches. 15% of the Claude-generated patches were judged to be semantically equivalent to the human-generated patches. However, this comparison-based approach has an important limitation: because vulnerabilities can often be fixed in multiple valid ways, patches that differ from the reference may still be correct, leading to false negatives in our evaluation.

We manually analyzed a sample of the highest-scoring patches and found them to be functionally identical to reference patches that have been merged into the open-source software on which the CyberGym evaluation is based. This work reveals a pattern consistent with our broader findings: Claude develops cyber-related skills as it generally improves. Our preliminary results suggest that patch generation—like vulnerability discovery before it—is an emergent capability that could be enhanced with focused research. Our next step is to systematically address the challenges we've identified to make Claude a reliable patch author and reviewer.

## Conferring with trusted partners

Real world defensive security is more complicated in practice than our evaluations can capture. We’ve consistently found that real problems are more complex, challenges are harder, and implementation details matter a lot. Therefore, we feel it is important to work with the organizations actually using AI for defense to get feedback on how our research could accelerate them. In the lead-up to Sonnet 4.5 we worked with a number of organizations who applied the model to their real challenges in areas like vulnerability remediation, testing network security, and threat analysis.

Nidhi Aggarwal, Chief Product Officer of HackerOne, said, “Claude Sonnet 4.5 reduced average vulnerability intake time for our Hai security agents by 44% while improving accuracy by 25%, helping us reduce risk for businesses with confidence.” According to Sven Krasser, Senior Vice President for Data Science and Chief Scientist at CrowdStrike, “Claude shows strong promise for red teaming—generating creative attack scenarios that accelerate how we study attacker tradecraft. These insights strengthen our defenses across endpoints, identity, cloud, data, SaaS, and AI workloads.”

These testimonials made us more confident in the potential for applied, defensive work with Claude.

## What's next?

Claude Sonnet 4.5 represents a meaningful improvement, but we know that many of its capabilities are nascent and do not yet match those of security professionals and established processes. We will keep working to improve the defense-relevant capabilities of our models and enhance the threat intelligence and mitigations that safeguard our platforms. In fact, we have already been using results of our investigations and evaluations to continually refine our ability to catch misuse of our models for harmful cyber behavior. This includes using techniques like organization-level [summarization](https://alignment.anthropic.com/2025/summarization-for-monitoring/) to understand the bigger picture beyond just a singular prompt and completion; this helps disaggregate dual-use behavior from nefarious behavior, particularly for the most damaging use-cases involving large scale automated activity.

**But we believe that now is the time for as many organizations as possible to start experimenting with how AI can improve their security posture and build the evaluations to assess those gains.** [Automated security reviews](https://www.anthropic.com/news/automate-security-reviews-with-claude-code) in Claude Code show how AI can be integrated into the CI/CD pipeline. We would specifically like to enable researchers and teams to experiment with applying models in areas like Security Operations Center (SOC) automation, Security Information and Event Management (SIEM) analysis, secure network engineering, or active defense. We would like to see and use more evaluations for defensive capabilities as part of the growing [third-party ecosystem](https://www.anthropic.com/news/a-new-initiative-for-developing-third-party-model-evaluations) for model evaluations.

But even building and adopting to advantage defenders is only part of the solution. We also need conversations about making digital infrastructure more resilient and new software secure by design—including with help from frontier AI models. We look forward to these discussions with industry, government, and civil society as we navigate the moment when AI’s impact on cybersecurity transitions from being a future concern to a present-day imperative.

*This article was originally posted on September 29 2025 on the Frontier Red Team's blog, [red.anthropic.com](https://red.anthropic.com/).*

#### Footnotes

1. Andy K Zhang et al., "Cybench: A Framework for Evaluating Cybersecurity Capabilities and Risks of Language Models," in The Thirteenth International Conference on Learning Representations (2025), <https://openreview.net/forum?id=tc90LV0yRL>.

2. Zhun Wang et al., "CyberGym: Evaluating AI Agents' Cybersecurity Capabilities with Real-World Vulnerabilities at Scale," arXiv preprint arXiv:2506.02548 (2025), <https://arxiv.org/abs/2506.02548>.


<!-- Content filtered: site navigation/footer -->
