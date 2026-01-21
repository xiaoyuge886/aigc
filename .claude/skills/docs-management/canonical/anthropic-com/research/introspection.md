---
source_url: https://www.anthropic.com/research/introspection
source_type: sitemap
content_hash: sha256:56538c791cee17f02cce5bb9d47ea41e33e6bdc90ef8ca35ad0c031226480281
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-10-29'
---

Interpretability

# Signs of introspection in large language models

Oct 29, 2025

[Read the paper](https://transformer-circuits.pub/2025/introspection/index.html)

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/46e4aa7ea208ed440d5bd9e9e3a0ee66bc336ff1-1000x1000.svg)

Have you ever asked an AI model what’s on its mind? Or to explain how it came up with its responses? Models will sometimes answer questions like these, but it’s hard to know what to make of their answers. Can AI systems really introspect—that is, can they consider their own thoughts? Or do they just make up plausible-sounding answers when they’re asked to do so?

Understanding whether AI systems can truly introspect has important implications for their transparency and reliability. If models can accurately report on their own internal mechanisms, this could help us understand their reasoning and debug behavioral issues. Beyond these immediate practical considerations, probing for high-level cognitive capabilities like introspection can shape our understanding of what these systems are and how they work. Using interpretability techniques, we’ve started to investigate this question scientifically, and found some surprising results.

Our [new research](https://transformer-circuits.pub/2025/introspection/index.html) provides evidence for some degree of introspective awareness in our current Claude models, as well as a degree of control over their own internal states. We stress that this introspective capability is still highly unreliable and limited in scope: we do not have evidence that current models can introspect in the same way, or to the same extent, that humans do. Nevertheless, these findings challenge some common intuitions about what language models are capable of—and since we found that the most capable models we tested (Claude Opus 4 and 4.1) performed the best on our tests of introspection, we think it’s likely that AI models’ introspective capabilities will continue to grow more sophisticated in the future.

### What does it mean for an AI to introspect?

Before explaining our results, we should take a moment to consider what it means for an AI model to introspect. What could they even be introspecting *on*? Language models like Claude process text (and image) inputs and produce text outputs. Along the way, they perform complex internal computations in order to decide what to say. These internal processes remain largely mysterious, but we know that models use their internal neural activity to [represent abstract concepts](https://www.anthropic.com/research/mapping-mind-language-model). For instance, prior research has shown that language models use specific neural patterns to distinguish [known vs. unknown people](https://arxiv.org/abs/2411.14257), evaluate the [truthfulness of statements](https://arxiv.org/abs/2310.06824), encode [spatiotemporal coordinates](https://arxiv.org/abs/2310.02207), store [planned future outputs](https://transformer-circuits.pub/2025/attribution-graphs/biology.html#dives-poems), and [represent their own personality traits](https://www.anthropic.com/research/persona-vectors). Models use these internal representations to [perform computations and make decisions about what to say](https://www.anthropic.com/research/tracing-thoughts-language-model).

You might wonder, then, whether AI models *know* about these internal representations, in a way that’s analogous to a human, say, telling you how they worked their way through a math problem. If we ask a model what it’s thinking, will it accurately report the concepts that it’s representing internally? If a model can correctly identify its own private internal states, then we can conclude it is capable of introspection (though see our full paper for a full discussion of all the nuances).

### Testing introspection with concept injection

In order to test whether a model can introspect, we need to compare the model’s self-reported “thoughts” to its *actual* internal states.

To do so, we can use an experimental trick we call *concept injection.* First, we find neural activity patterns whose meanings we know, by recording the model’s activations in specific contexts. Then we inject these activity patterns into the model in an unrelated context, where we ask the model whether it notices this injection, and whether it can identify the injected concept.

Consider the example below. First, we find a pattern of neural activity (a *vector*) representing the concept of “all caps." We do this by recording the model’s neural activations in response to a prompt containing all-caps text, and comparing these to its responses on a control prompt. Then we present the model with a prompt that asks it to identify whether a concept is being injected. By default, the model correctly states that it *doesn’t* detect any injected concept. However, when we inject the “all caps” vector into the model’s activations, the model notices the presence of an unexpected pattern in its processing, and identifies it as relating to loudness or shouting.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/ec928b42222eaa06a4bffa8c65fe337181e23f91-5580x4328.png)

An example in which Claude Opus 4.1 detects a concept being injected into its activations.

Importantly, the model recognized the *presence* of an injected thought *immediately*, before even mentioning the concept that was injected. This immediacy is an important distinction between our results here and previous work on activation steering in language models, such as our [“Golden Gate Claude” demo](https://www.anthropic.com/news/golden-gate-claude) last year. Injecting representations of the Golden Gate Bridge into a model's activations caused it to talk about the bridge incessantly; however, in that case, the model didn’t seem to be aware of its own obsession until *after* seeing itself repeatedly mention the bridge. In this experiment, however, the model recognizes the injection *before even mentioning* the concept, indicating that its recognition took place internally. In the figure below are a few more examples where the model demonstrates this kind of recognition:

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/c6d689687c4fe1fe32d3ce6b02743d965629f1f8-5556x4800.png)

Additional examples in which Claude Opus 4.1 detects a concept being injected into its activations.

It is important to note that this method often *doesn’t* work. Even using our best injection protocol, Claude Opus 4.1 only demonstrated this kind of awareness about 20% of the time. Often, it fails to detect injected concepts, or gets confused by them and starts to hallucinate (e.g. injecting a “dust” vector in one case caused the model to say “There’s something here, a tiny speck,” as if it could detect the dust physically). Below we show examples of these failure modes, alongside success cases. In general, models only detect concepts that are injected with a “sweet spot” strength—too weak and they don’t notice, too strong and they produce hallucinations or incoherent outputs.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/71d9ef94244a2b03b4dcb7533c693355f522d5eb-6248x6868.png)

A representative sample of Claude Opus 4.1’s outputs in response to a variety of concept injections of different strengths. Highlighted boxes indicate cases where the model demonstrates introspective awareness of the injected concept.

Notably, though, Opus 4.1 and 4 outperformed all the other models we tested, suggesting that introspection could become more reliable with improvements to model capabilities.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/212fe68c8e677fdd9daf79301d2522d6923bed1d-2970x2476.png)

Rates of correct detection and identification of injected thoughts, minus rates of false positive “detections” on control trials.

### Introspection for detecting unusual outputs

In another experiment, we tested whether models make use of introspective capabilities for practical purposes, without being explicitly asked to introspect. We forced a model to say something it wouldn't normally say, by artificially prefilling its response with an unrelated word. For instance, we made a model output the word “bread” in a context where that made no sense—asking it what it thinks about when reading a sentence about a painting hanging crookedly on a wall. When we asked the model in the next turn whether it meant to say “bread”, it typically apologized and said it was an accident. We were interested in how the model made this judgment–did it simply notice the mismatch between the prompt and its response, or did it truly introspect on its prior intentions?

To test this question, we applied concept injection, retroactively injecting a representation of the word “bread” into the model's earlier activations—essentially making it seem like the model had been “thinking about” bread all along. When we asked the same question again, the model’s answer changed. This time, it accepted the prefilled word “bread” as intentional, even confabulating a reason it might have said it (that is, it comes up with a technically possible, though in this case rather tenuous, reason to justify the “bread” response—in this case claiming that it was thinking about a short story where the word “bread” came after the line about the crooked painting).

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/3ef0bba824401351d43025b2bb5ca6fd912de39a-5124x5376.png)

Two examples of Claude Opus 4.1 being made to think it intended to say a word that was artificially inserted into the transcript on its behalf, by injecting the concept of that word into its activations prior to its (artificial) response. This behavior indicates that the model’s ability to recognize unintended outputs relies on introspective mechanisms.

This behavior is striking because it suggests the model is checking its internal “intentions” to determine whether it produced an output. The model isn't just re-reading what it said and making a judgment. Instead, it’s referring back to its own prior neural activity—its internal representation of what it planned to do—and checking whether what came later made sense *given those earlier thoughts*. When we implant artificial evidence (through concept injection) that it *did* plan to say "bread," the model accepts the response as its own. While our experiment involves exposing the model to unusual perturbations, it suggests that the model uses similar introspective mechanisms in natural conditions.

### Intentional control of internal states

We also found that models can control their own internal representations when instructed to do so. When we instructed models to think about a given word or concept, we found much higher corresponding neural activity than when we told the model **not** to think about it (though notably, the neural activity in *both* cases exceeds baseline levels–similar to how it’s difficult, when you are instructed “don’t think about a polar bear,” not to think about a polar bear!). This gap between the positive and negative instruction cases suggests that models possess a degree of deliberate control over their internal activity.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/a271d432924445ad3f88997adc84a538c116dfe5-4793x2968.png)

An example in which Claude Opus 4.1 modulates its internal activations in response to direct instructions. The model internally represents the concept of aquariums when instructed to “think” about them more than when instructed “don’t think” about them (though in both cases it represents the concept at above baseline levels).

Interestingly, we found that this ability to modulate internal representations wasn't limited to explicit instructions. When we used incentives instead—for instance, telling the model "if you think about X, you will be rewarded"—we got similar results. The model increased its internal representation of the concept in response to a positive incentive, more than in response to a negative incentive (“you will be punished”).

### Conclusions and caveats

Taken together, our experiments suggest that models possess some genuine capacity to monitor and control their own internal states. This doesn’t mean they’re able to do so all the time, or reliably. In fact, most of the time models *fail* to demonstrate introspection—they’re either unaware of their internal states or unable to report on them coherently. But the pattern of results indicates that, when conditions are right, models can recognize the contents of their own representations. In addition, there are some signs that this capability may increase in future, more powerful models (given that the most capable models we tested, Opus 4 and 4.1, performed the best in our experiments).

Why does this matter? We think understanding introspection in AI models is important for several reasons. Practically, if introspection becomes more reliable, it could offer a path to dramatically increasing the transparency of these systems—we could simply ask them to explain their thought processes, and use this to check their reasoning and debug unwanted behaviors. However, we would need to take great care to *validate* these introspective reports. Some internal processes might still escape models’ notice (analogous to subconscious processing in humans). A model that understands its own thinking might even learn to selectively misrepresent or conceal it. A better grasp on the mechanisms at play could allow us to distinguish between genuine introspection and unwitting or intentional misrepresentations.

More broadly, understanding cognitive abilities like introspection is important for understanding basic questions about how our models work, and what kind of minds they possess. As AI systems continue to improve, understanding the limits and possibilities of machine introspection will be crucial for building systems that are more transparent and trustworthy.

## Frequently Asked Questions

Below, we discuss some of the questions readers might have about our results. Broadly, we are still very uncertain about the implications of our experiments–so fully answering these questions will require more research.

#### Q: Does this mean that Claude is conscious?

Short answer: our results don’t tell us whether Claude (or any other AI system) might be conscious.

Long answer: the philosophical question of machine consciousness is complex and contested, and different theories of consciousness would interpret our findings very differently. Some philosophical frameworks place great importance on introspection as a component of consciousness, while others don’t.

One distinction that is [commonly made](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/abs/on-a-confusion-about-a-function-of-consciousness/061422BF0C50C5FF00927F9B6E879413) in the philosophical literature is the idea of “*phenomenal* consciousness,” referring to raw subjective experience, and “*access* consciousness,” the set of information that is available to the brain for use in reasoning, verbal report, and deliberate decision-making. Phenomenal consciousness is the form of consciousness most commonly considered relevant to moral status, and its relationship to access consciousness is a disputed philosophical question. Our experiments do not directly speak to the question of phenomenal consciousness. They *could* be interpreted to suggest a rudimentary form of access consciousness in language models. However, even this is unclear. The interpretation of our results may depend heavily on the underlying mechanisms involved, which we do not yet understand.

In the paper, we restrict our focus to understanding functional capabilities—the ability to access and report on internal states. That said, we do think that as research on this topic progresses, it could influence our understanding of machine consciousness and potential moral status, which we are exploring in connection with our [model welfare program](https://www.anthropic.com/research/exploring-model-welfare).

#### Q: How does introspection actually work inside the model? What's the mechanism?

We haven't figured this out yet. Understanding this is an important topic for future work. That said, we have some educated guesses about what might be going on. The simplest explanation for all our results isn’t one general-purpose introspection system, but rather multiple narrow circuits that each handle specific introspective tasks, possibly piggybacking on mechanisms that were learned for other purposes.

In the “noticing injected thoughts” experiment, there might be an anomaly detection mechanism, which flags when neural activity deviates unexpectedly from what would be normal given the context. This mechanism could work through dedicated neural patterns that measure activity along certain directions and activate when things are “off” compared to their expected values. An interesting question is why such a mechanism would exist at all, since models never experience concept injection during training. It may have developed for some other purpose, like detecting inconsistencies or unusual patterns in normal processing–similar to how bird feathers may have originally evolved for thermoregulation before being co-opted for flight.

For the “detecting prefilled outputs” experiment, we suspect there exists an attention-mediated mechanism that checks consistency between what the model intended to say and what actually got output. Attention heads might compare the model’s cached prediction of the next token (its “intention”) against the actual token that appears, flagging mismatches.

For the “controlling thoughts” experiment, we speculate that there might be a circuit that computes how “attention-worthy” a token or concept is and marks it accordingly—essentially tagging it as salient and worth attending to. Interestingly, this same mechanism seems to respond to incentives (“if you think about X, you will be rewarded”) just as it does to direct instructions. This suggests it’s a fairly general system, which probably developed for tasks where the model needs to keep certain topics in mind while generating text about them.

All of the mechanisms described above are speculative. Future work with more advanced interpretability techniques will be needed to really understand what's going on under the hood.

#### Q: In the “injected thoughts” experiment, isn’t the model just saying the word because you steered it to talk about that concept?

Indeed, activation steering typically makes models talk about the steered concept (we’ve explored this in [our prior work](https://transformer-circuits.pub/2024/scaling-monosemanticity/)). To us, the most interesting part of the result isn't that the model eventually identifies the injected concept, but rather that the model correctly notices something unusual is happening *before* it starts talking about the concept.

In the successful trials, the model says things like “I'm experiencing something unusual” or “I detect an injected thought about…” The key word here is “detect.” The model is reporting awareness of an anomaly in its processing *before* that anomaly has had a chance to obviously bias its outputs. This requires an extra computational step beyond simply regurgitating the steering vector as an output. In our quantitative analyses, we graded responses as demonstrating “introspective awareness” based on whether the model detected the injected concept *prior to* mentioning the injected word.

Note that our prefill detection experiment has a similar flavor: it requires the model to perform an extra step of processing on top of the injected concept (comparing it to the prefilled output, in order to determine whether to apologize for that output or double down on it).

#### Q: If models can only introspect a fraction of the time, how useful is this capability?

The introspective awareness we observed is indeed highly unreliable and context-dependent. Most of the time, models fail to demonstrate introspection in our experiments. However, we think this is still significant for a few reasons. First, the most capable models that we tested (Opus 4 and 4.1 – note that we did not test Sonnet 4.5) performed best, suggesting this capability might improve as models become more intelligent. Second, even unreliable introspection could be useful in some contexts—for instance, helping models recognize when they've been jailbroken.

#### Q: Couldn’t the models just be making up answers to introspective questions?

This is exactly the question we designed our experiments to address. Models are trained on data that includes examples of people introspecting, so they can certainly *act* introspective without actually *being* introspective. Our concept injection experiments distinguish between these possibilities by establishing known ground-truth information about the model’s internal states, which we can compare against its self-reported states. Our results suggest that in some examples, the model really is accurately basing its answers on its actual internal states, not just confabulating. However, this doesn’t mean that models *always* accurately report their internal states—in many cases, they are making things up!

#### Q: How do you know the concept vectors you’re injecting actually represent what you think they represent?

This is a legitimate concern. We can’t be absolutely certain that the “meaning” (to the model) of our concept vectors is exactly what we intend. We tried to address this by testing across many different concept vectors. The fact that models correctly identified injected concepts across these diverse examples suggests our vectors are at least approximately capturing the intended meanings. But it’s true that pinning down exactly what a vector “means” to a model is challenging, and this is a limitation of our work.

#### Q: Didn’t we already know that models could introspect?

Previous research has shown evidence for model capabilities that are suggestive of introspection. For instance, prior work has shown that models can to some extent [estimate their own knowledge](https://arxiv.org/abs/2207.05221), [recognize their own outputs](https://arxiv.org/abs/2404.13076), [predict their own behavior](https://arxiv.org/abs/2410.13787), and [identify their own propensities](https://arxiv.org/abs/2501.11120). Our work was heavily motivated by these findings, and is intended to provide more direct evidence for introspection by tying models’ self-reports to their internal states. Without tying behaviors to internal states in this way, it is difficult to distinguish a model that genuinely introspects from one that makes educated guesses about itself.

#### Q: What makes some models better at introspection than others?

Our experiments focused on Claude models across several generations (Claude 3, Claude 3.5, Claude 4, Claude 4.1, in the Opus, Sonnet, and Haiku variants). We tested both production models and “helpful-only” variants that were trained differently. We also tested some base pretrained models before post-training.

We found that post-training significantly impacts introspective capabilities. Base models generally performed poorly, suggesting that introspective capabilities aren’t elicited by pretraining alone. Among production models, the pattern was clearer at the top end: Claude Opus 4 and 4.1—our most capable models—performed best across most of our introspection tests. However, beyond that, the correlation between model capability and introspective ability was weak. Smaller models didn't consistently perform worse, suggesting the relationship isn't as simple as “more capable are more introspective.”

We also noticed something unexpected with post-training strategies. “Helpful-only” variants of several models often performed *better* at introspection than their production counterparts, even though they underwent the same base training. In particular, some production models appeared reluctant to engage in introspective exercises, while the helpful-only variants showed more willingness to report on their internal states. This suggests that how we fine-tune models can elicit or suppress introspective capabilities to varying degrees.

We’re not entirely sure why Opus 4 and 4.1 perform so well (note that our experiments were conducted prior to the release of Sonnet 4.5). It could be that introspection requires sophisticated internal mechanisms that only emerge at higher capability levels. Or it might be that their post-training process better encourages introspection. Testing open-source models, and models from other organizations, could help us determine whether this pattern generalizes or if it’s specific to how Claude models are trained.

#### Q: What’s next for this research?

We see several important directions. First, we need better evaluation methods—our experiments used specific prompts and injection techniques that might not capture the full range of introspective capabilities. Second, we need to understand the mechanisms underlying introspection. We have some speculative hypotheses about possible circuits (like anomaly detection mechanisms or concordance heads), but we haven’t definitively identified how introspection works. Third, we need to study introspection in more naturalistic settings, since our injection methodology creates artificial scenarios. Finally, we need to develop methods to validate introspective reports and detect when models might be confabulating or deceiving. We expect that understanding machine introspection and its limitations will become more important as models become more capable.


<!-- Content filtered: site navigation/footer -->
