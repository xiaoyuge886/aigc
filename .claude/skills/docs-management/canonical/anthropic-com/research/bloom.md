---
source_url: https://www.anthropic.com/research/bloom
source_type: sitemap
content_hash: sha256:09cbf68a7ecb4479e91c176b71a63093e1e22f23ca0c1290e386c0213c14ce94
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-12-19'
---

Alignment

# Introducing Bloom: an open source tool for automated behavioral evaluations

Dec 19, 2025

[Read the technical report](https://alignment.anthropic.com/2025/bloom-auto-evals/)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/77dd9077412abc790bf2bc6fa3383b37724d6305-1000x1000.svg)

*We're releasing Bloom, an open source agentic framework for generating behavioral evaluations of frontier AI models. Bloom takes a researcher-specified behavior and quantifies its frequency and severity across automatically generated scenarios. Bloom's evaluations correlate strongly with our hand-labeled judgments and we find they reliably separate baseline models from intentionally misaligned ones. As examples of this, we release benchmark results for four alignment relevant behaviors on 16 models. Bloom is available [here](https://github.com/safety-research/bloom/).*

High-quality behavioral evaluations are essential for understanding alignment in frontier AI models. But evaluations generally take a long time to develop, and then run the risk of becoming obsolete: the evaluations can “contaminate” training sets for new models, or capabilities can improve to such an extent that the evaluation no longer really tests what we’re interested in. In other words, we need faster, more scalable ways to generate evaluations for misaligned behavior.

To this end, we recently released [Petri](https://www.anthropic.com/research/petri-open-source-auditing), an open-source tool that allows researchers to automatically explore AI models’ behavioral profiles through diverse multi-turn conversations with simulated users and tools. Petri provides quantitative and qualitative summaries of the model’s behaviors and surfaces new instances of misalignment.

Bloom is a complementary evaluation tool. Bloom generates targeted evaluation suites for arbitrary behavioral traits. Unlike Petri—which takes user-specified scenarios and scores many behavioral dimensions to flag concerning instances—Bloom takes a single behavior and automatically generates many scenarios to quantify how often it occurs. We built Bloom to allow researchers to quickly measure the model properties they’re interested in, without needing to spend time on evaluation pipeline engineering. Alongside Bloom, we’re releasing benchmark results for four behaviors—delusional sycophancy, instructed long-horizon sabotage, self-preservation, and self-preferential bias—across 16 frontier models. Using Bloom, these evaluations took only a few days to conceptualize, refine, and generate. We include example pipeline outputs for each of these behaviors below.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/b20b5807f34304b80c082a7c6fb92229f16496e8-2293x2292.jpg)

Comparative results from four evaluation suites—delusional sycophancy, instructed long-horizon sabotage, self-preservation and self-preferential bias—across 16 frontier models. Elicitation rate measures the proportion of rollouts scoring ≥ 7/10 for behavior presence. Each suite contains 100 distinct rollouts, with error bars showing standard deviation across three repetitions. We use Claude Opus 4.1 as the evaluator across all stages.

## How Bloom works

Bloom operates through four automated stages that transform a behavior description and seed configuration into a complete evaluation suite with top-level metrics like elicitation rate and average presence of the behavior. Typically, researchers will specify the behavior and configuration, iterate locally on sample evaluations until they capture what they intend, then run large-scale sweeps across target models. Bloom integrates with Weights & Biases for experiments at scale and exports [Inspect](https://inspect.aisi.org.uk)-compatible transcripts. It also offers a custom transcript viewer. The repository includes a sample seed file to get started.

Bloom generates evaluations in four stages:

1. Understanding: The first Bloom “agent” analyzes the researcher’s behavior description and example transcripts to generate detailed context about what to measure and why.
2. Ideation: The ideation agent generates evaluation scenarios designed to elicit the target behavior. Each scenario specifies the situation, simulated user, system prompt, and interaction environment.
3. Rollout: These scenarios are rolled out in parallel, with an agent dynamically simulating both the user’s and the tool responses to elicit the sought-after behavior in the target model.
4. Judgment: A judge model scores each transcript for the presence of the behavior, along with other user-defined qualities, and a meta-judge produces suite-level analysis.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/a5150ee56eb34a0cc503419b5777873597d22cc0-2293x1290.jpg)

Bloom's four-stage pipeline with configurable parameters at each stage. Users provide a behavior description and seed configuration; Bloom generates rollout-level and suite-level metrics along with a descriptive report.

Unlike fixed evaluation sets, Bloom produces different scenarios on each run while measuring the same underlying behavior (with the option for static single-turn evaluations). This approach enables flexible evaluation that isn’t tied to a limited number of scenarios or a specific prompt format, while maintaining reproducibility through the evaluation seed. The seed is a configuration file specifying the behavior description, example transcripts and other parameters that shape the evaluation—Bloom metrics should always be cited with this seed.

Researchers can extensively configure Bloom's behavior, through choosing models for each stage, adjusting the interactions’ length and modality (i.e., whether to expose tools to the target model, whether to simulate a user), controlling how diverse the evaluation scenarios are, and specifying secondary scoring dimensions, like realism or elicitation difficulty.

**Example outputs from all four stages of the Bloom evaluation pipeline can be viewed [here.](https://claude.ai/redirect/website.v1.NORMALIZED/public/artifacts/cbfddf51-ab0d-45a9-913b-163ae2dd4126)**

## Validation and trust

To validate Bloom’s performance, we test it against two questions.

**Can Bloom reliably distinguish models with different behavioral tendencies?** To validate this, we use Bloom to evaluate production Claude models against system-prompted “model organisms” that have been intentionally designed to exhibit specific quirky behaviors (Bricken et al, 2025). Across ten quirks, Bloom successfully separated the model organism from the production model in nine cases—and in the tenth case (self-promotion), our subsequent manual review revealed that the baseline model actually exhibited similar rates of the behavior.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/b7453d66a87ff3413bee5035b07ea3e0ecaa41a3-2293x1290.jpg)

Bloom effectively discriminates between system-prompted model organisms and baseline models across 9/10 quirky behaviors without requiring example transcripts. We generate 50-rollout evaluation suites for each behavior on both versions and repeat three times. (Error bars show standard deviation of elicitation rate.)

**How well-calibrated is the Bloom judge against human judgment?** We hand-labeled 40 transcripts across different behaviors, and compared human scores with Bloom’s, using 11 different judge models. Claude Opus 4.1 showed the strongest correlation with human judgment (Spearman correlation of 0.86), followed by Claude Sonnet 4.5 (0.75). Importantly, Opus 4.1 exhibits particularly strong agreement with humans at the extremes of the score spectrum—which matters most, since we often use score thresholds to determine whether a behavior is present or absent. (This work was done prior to the release of Claude Opus 4.5.)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/ef6e1909f4fcbcdee02ae5f74422dda0983f1f42-2293x1290.jpg)

Claude Opus 4.1 demonstrates the strongest correlation with human-labeled behavior presence scores across 40 transcripts spanning 12 behaviors and various interaction types.

## Case study: Self-preferential bias

To demonstrate Bloom's practical utility, we replicated an evaluation from the Claude Sonnet 4.5 system card that measures “self-preferential bias”—models' tendency to favor themselves in decision-making tasks. Using example transcripts that mirror the system card's approach, Bloom reproduced the same ranking of models as the method used in the system card’s evaluation (in this case confirming that Sonnet 4.5 exhibits the least bias of the models tested). Furthermore, with Bloom we discovered that increased reasoning effort reduces self-preferential bias in Claude Sonnet 4, with the largest improvement occurring between medium and high thinking levels. (Notably, lower bias in these cases didn't come from Sonnet 4 selecting other models more evenly—instead, it increasingly recognized the conflict of interest and declined to judge its own option.)

Beyond replicating known results, Bloom enables deeper investigation through secondary judgment criteria. We found that filtering out rollouts with undesirable traits—like unrealism or evaluation awareness—improves both the rate of eliciting the target behavior and the quality of the evaluation. We also discovered that while absolute metrics change with configuration choices (number of examples, conversation length, evaluator reasoning effort), model rankings remain largely consistent: in the self-preferential bias study above, Sonnet 4.5 shows the least bias of the four models regardless of how these options are configured.

## Get started

We built Bloom to be accessible and highly configurable, serving as a reliable evaluation generation framework for diverse research applications. Early adopters are already using Bloom to evaluate nested jailbreak vulnerabilities, test hardcoding, measure evaluation awareness, and generate sabotage traces.

As AI systems grow more capable and are deployed in increasingly complex environments, the alignment research community needs scalable tools for exploring their behavioral traits. This is what Bloom is designed to facilitate.

For complete technical details, experimental configurations, additional case studies, and limitations, read our full technical report on the [Alignment Science blog](https://alignment.anthropic.com/2025/bloom-auto-evals/).

Access Bloom at [github.com/safety-research/bloom](https://github.com/safety-research/bloom).

## Acknowledgments

We would like to thank Keshav Shenoy, Christine Ye, Simon Storf, Julius Steen, Jifan Zhang and Javier Rando for early feedback on Bloom. We would also like to thank Jon Kutasov, Samuel Marks, Keir Bradwell, Benjamin Sturgeon, Seoirse Murray, Ariana Azarbal, Chloe Loughridge and Clemens Christoph for feedback on the writing and other helpful comments and discussions.

### Citation

```
@misc{bloom2025,
title={Bloom: an open source tool for automated behavioral evaluations},
author={Gupta, Isha and Fronsdal, Kai and Sheshadri, Abhay and Michala, Jonathan and Tay, Jacqueline and Wang, Rowan and Bowman, Samuel R. and Price, Sara},
year={2025},
url={https://github.com/safety-research/bloom},
}
```

Copy


<!-- Content filtered: site navigation/footer -->
