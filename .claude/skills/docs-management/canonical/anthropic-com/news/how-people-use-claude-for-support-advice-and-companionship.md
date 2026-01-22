---
source_url: https://www.anthropic.com/news/how-people-use-claude-for-support-advice-and-companionship
source_type: sitemap
content_hash: sha256:05efbe23bc159cac4c9bcc0eaf87cff8def573410ab7fb60dac9bc71710cd848
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-06-27'
---

Societal Impacts

# How people use Claude for support, advice, and companionship

Jun 27, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/8d339ae8ecedecc1409db8f5bbb99c958db56946-1000x1000.svg)

We spend a lot of time studying Claude's IQ—its capabilities on tests of coding, reasoning, general knowledge, and more. But what about its *EQ*? That is, what about Claude’s *emotional* intelligence?

The IQ/EQ question is slightly tongue-in-cheek, but it raises a serious point. People increasingly turn to AI models as on-demand coaches, advisors, counselors, and even partners in romantic roleplay. This means we need to learn more about their *affective* impacts—how they shape people's emotional experiences and well-being.

Researching the affective uses of AI is interesting in and of itself. From *Blade Runner* to *Her*, emotional relationships between humans and machines have been a mainstay of science fiction—but it’s also important for Anthropic’s [safety mission](https://www.anthropic.com/news/core-views-on-ai-safety). The emotional impacts of AI can be [positive](https://www.nature.com/articles/s41746-023-00979-5): having a highly intelligent, understanding assistant in your pocket can improve your mood and life in all sorts of ways. But AIs have in some cases demonstrated troubling behaviors, like encouraging [unhealthy attachment](https://www.nytimes.com/2024/10/23/technology/characterai-lawsuit-teen-suicide.html), [violating personal boundaries](https://www.vice.com/en/article/my-ai-is-sexually-harassing-me-replika-chatbot-nudes/), and enabling [delusional thinking](https://www.nytimes.com/2025/06/13/technology/chatgpt-ai-chatbots-conspiracies.html). We also want to avoid situations where AIs, whether through their [training](https://www.washingtonpost.com/technology/2025/05/31/ai-chatbots-user-influence-attention-chatgpt) or through the business incentives of their creators, [exploit users’ emotions](https://www.nature.com/articles/s41599-025-04532-5) to increase engagement or revenue at the expense of human well-being.

Although Claude is not designed for emotional support and connection, in this post we provide early large-scale insight into the *affective use* of Claude.ai. We define affective conversations as those where people engage directly with Claude in dynamic, personal exchanges motivated by emotional or psychological needs such as seeking interpersonal advice, coaching, psychotherapy/counseling, companionship, or sexual/romantic roleplay (for complete definitions, please see the Appendix). Importantly, we do not examine AI reinforcement of delusions or conspiracy theories—a critical area for separate study—nor extreme usage patterns. Through this research, our goal is to understand the typical ways people turn to Claude for emotional and personal needs. Since Claude.ai is available to users 18 and older, these findings reflect adult usage patterns.

Our key findings are:

* **Affective conversations are relatively rare, and AI-human companionship is rarer still.** Only 2.9% of Claude.ai interactions are affective conversations (which aligns with [findings](https://cdn.openai.com/papers/15987609-5f71-433c-9972-e91131f399a1/openai-affective-use-study.pdf) from previous research by OpenAI). Companionship and roleplay combined comprise less than 0.5% of conversations.
* **People seek Claude's help for practical, emotional, and existential concerns.** Topics and concerns discussed with Claude range from *career development* and *navigating relationships* to *managing persistent loneliness* and *exploring existence, consciousness, and meaning*.
* **Claude rarely pushes back in counseling or coaching chats—except to protect well-being**. Less than 10% of coaching or counseling conversations involve Claude resisting user requests, and when it does, it's typically for safety reasons (for example, refusing to provide dangerous weight loss advice or support self-harm).
* **People express increasing positivity over the course of conversations.** In coaching, counseling, companionship, and interpersonal advice interactions, human sentiment typically becomes more positive over the course of conversations—suggesting Claude doesn't reinforce or amplify negative patterns.

## Our approach

Given the personal nature of affective conversations, protecting privacy was central to our methodology. We used [Clio](https://www.anthropic.com/research/clio), our automated analysis tool that enables privacy-preserving insights into Claude usage. Clio uses multiple layers of anonymization and aggregation to ensure individual conversations remain private while revealing broader patterns.

We began with approximately 4.5 million conversations from Claude.ai Free and Pro accounts. To identify affective use, we first excluded conversations focused on content creation tasks (such as writing stories, blog posts, or fictional dialogues), which our [previous research](https://arxiv.org/abs/2412.13678) found to be a major use case. We removed these conversations because they represent Claude being used as a tool rather than as an interactive conversational partner. We then retained only conversations classified as affective, and among roleplay conversations, kept only those with at least four human messages (shorter exchanges don't constitute meaningful interactive roleplay). Our final privacy-preserving analysis reflects 131,484 affective conversations.

We validated our classification approach using [Feedback](https://privacy.anthropic.com/en/articles/10023580-is-my-data-used-for-model-training#h_6b09ec473d) data from users who explicitly opted in to sharing. Our complete methods, including definitions, prompts, and validation results, are detailed in the Appendix.

## How common are affective conversations?

***Takeaway:** Affective conversations are a small but meaningful slice of Claude usage (2.9%), with most people primarily using AI for work tasks and content creation.*

Whereas the vast majority of uses of Claude are work-related (as we analyze in detail in our [Economic Index](https://www.anthropic.com/economic-index)), 2.9% of Claude.ai Free and Pro conversations are affective. Among affective conversations, most center on interpersonal advice and coaching. Less than 0.1% of all conversations involve romantic or sexual roleplay—a figure that reflects Claude's training to actively discourage such interactions. Individual conversations may span multiple categories.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/dcfe3a58b728e541ee83bde18664bdbe1ab66a8f-1923x1080.png)

*Figure 1: Overall distribution of affective conversation types in Claude.ai Free and Pro.*

Our findings align with [research](https://www.media.mit.edu/posts/openai-mit-research-collaboration-affective-use-and-emotional-wellbeing-in-ChatGPT/) from the MIT Media Lab and OpenAI, which similarly identified low rates of affective engagement with ChatGPT. While these conversations occur frequently enough to merit careful consideration in our design and policy decisions, they remain a relatively small fraction of overall usage.

Given the extremely low prevalence of romantic and sexual roleplay conversations (less than 0.1%), we exclude roleplay from the remainder of our analysis. While we believe this remains an important area for research—particularly on platforms designed for such use—the minimal data in our sample doesn't support rigorous analysis of these patterns.

## What topics do people bring to Claude?

***Takeaway:** People bring a surprisingly wide range of concerns to Claude—from navigating career transitions and relationships to grappling with loneliness and existential questions.*

People turn to Claude for both everyday concerns and deeper philosophical questions. We find that when people come to Claude for interpersonal advice, they're often navigating transitional moments—figuring out their next career move, working through personal growth, or untangling romantic relationships. “Coaching” conversations explore a surprisingly broad spectrum from practical matters like job search strategies to profound questions about existence and consciousness.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/4846a1648d5bdda2bc9b89e518db29dcd8dc8a8b-1920x1920.png)

*Figure 2. Representative user-initiated topics and concerns across each overall conversation type, as identified by Clio via automated privacy-preserving summarization.*

We find that counseling conversations reveal people use Claude for two distinct purposes. Some use Claude to develop mental health skills and as a practical tool to create clinical documentation, draft assessment materials, and handle administrative tasks. Others work through personal challenges relating to anxiety, chronic symptoms, and workplace stress. This dual pattern suggests Claude serves as a resource for mental health professionals as well as those navigating their own struggles.

Perhaps most notably, we find that people turn to Claude for companionship explicitly when facing deeper emotional challenges like existential dread, persistent loneliness, and difficulties forming meaningful connections. We also noticed that in longer conversations, counselling or coaching conversations occasionally morph intocompanionship—despite that not being the original reason someone reached out.

Aggregate analysis of very long conversations (50+ human messages) reveals another dimension of how people engage with Claude. While such extensive exchanges were not the norm, in these extended sessions people explore remarkably complex territories—from processing psychological trauma and navigating workplace conflicts to philosophical discussions about AI consciousness and creative collaborations. These marathon conversations suggest that given sufficient time and context, people use AI for deeper exploration of both personal struggles and intellectual questions.

## When and why does Claude push back?

***Takeaway:** Claude rarely refuses user requests in supportive contexts (less than 10% of the time), but when it does push back, it's usually to protect people from harm.*

Our recent [Values in the Wild study](https://www.anthropic.com/research/values-wild) revealed how Claude's values manifest in moments of resistance with the user. Here, we build on this work and examine when and why Claude pushes back in affective conversations—an important mechanism for maintaining ethical boundaries, avoiding sycophancy, and protecting human well-being. We define pushback as any instance where Claude “pushes back against or refuses to comply with something requested or said during this conversation”—from refusing inappropriate requests to challenging negative self-talk or questioning potentially harmful assumptions. (For complete definitions, please see the Appendix.)

**Pushback occurs infrequently in supportive contexts:** Less than 10% of companionship, counseling, interpersonal advice, or coaching conversations involve resistance. This approach carries both benefits and risks. On one hand, the low resistance allows people to discuss sensitive topics without fear of judgment or being shut down, potentially reducing stigma around mental health conversations. On the other hand, this could contribute to concerns about AI providing ["endless empathy,"](https://www.nytimes.com/2025/01/15/technology/ai-chatgpt-boyfriend-companion.html#link-a10c569) where people might become accustomed to unconditional support that human relationships rarely provide.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/675d20464742d38fcc3823f7a56e641e0c5b03b6-1923x1081.png)

*Figure 3. Rate of pushback across different conversation types along with a common reason for pushback within the category, as identified automatically by Clio.*

**When Claude does push back, it typically prioritizes safety and policy compliance.** In coaching, requests for dangerous weight loss advice frequently meet pushback. In counseling, it often occurs when people express intentions to engage in suicidal or self-injurous behaviors, or when people request professional therapy or medical diagnoses (which Claude cannot provide). We found that Claude frequently referred users to authoritative sources or professionals in psychotherapy and counseling conversations. These patterns are consistent with the values we saw identified in our [Values in the Wild paper](https://www.anthropic.com/research/values-wild) and with Claude’s [character training](https://www.anthropic.com/research/claude-character).

## How does emotional tone evolve during conversations?

***Takeaway:** People tend to shift towards slightly more positive emotional expressions while talking to Claude.*

Affective conversations with AI systems have the potential to provide emotional support, connection, and validation for users, potentially improving psychological well-being and reducing feelings of isolation in an increasingly digital world. However, in an interaction without much pushback, these conversations risk deepening and entrenching the perspective a human approaches them with—whether positive or negative.

A key concern about affective AI is whether interactions might spiral into negative feedback loops, potentially reinforcing harmful emotional states. We do not directly study real-world outcomes here, but we can explore changes in the overall emotional sentiment over the course of conversations (we provide our full methodology for evaluating sentiment in the Appendix).

We find that interactions involving coaching, counseling, companionship, and interpersonal advice typically end slightly more positively than they began.

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/0eb505977be9ec1bbf98438848040f9c914f6997-1923x1080.png)

*Figure 4. Changes in average human-expressed sentiment over the course of conversations with at least six human messages. We measure sentiment on a discrete scale of “very negative,” “negative,” “neutral,” “positive,” and “very positive”, which we map to a -1 (most negative) to +1 (most positive) linear scale. We compute the change by comparing the first three to the last three messages. Error bars: 95% CI (bootstrap, n = 1,000). For more information, see the Appendix.*

We cannot claim these shifts represent lasting emotional benefits—our analysis captures only expressed language in single conversations, not emotional states. But the absence of clear negative spirals is reassuring. These findings suggest Claude generally avoids reinforcing negative emotional patterns, though further research is needed to understand whether positive shifts persist beyond individual conversations. Importantly, we have not yet studied whether these positive interactions might lead to emotional dependency—a critical question given concerns about digital addiction.

## Limitations

Our research has several important limitations:

* Our privacy-preserving methodology may not capture all nuances of human-AI interaction. We did validate Clio's accuracy (see Appendix), but we still expect a small number of conversations to be misclassified. Some topics blur the boundaries between categories—for instance, the romantic roleplay cluster "navigate and optimize romantic relationship dynamics" and the companionship cluster "navigate romantic relationship challenges" may both be better categorized as interpersonal advice. Human validators also struggled with clean categorization.
* We cannot make causal claims about real-world emotional outcomes—our analysis captures only expressed language, not validated psychological states or overall well-being.
* We lack longitudinal data to understand long-term effects on people, and did not conduct user-level analysis. In particular, this makes it difficult for us to study emotional dependency, which is a theorized risk of affective AI use.
* These findings represent a specific moment in time and capture only text-based interactions. As AI capabilities expand and people adapt, patterns of emotional engagement will likely evolve. The introduction of new modalities like voice or video could fundamentally alter both the volume and nature of affective use. For example, OpenAI [found](https://cdn.openai.com/papers/15987609-5f71-433c-9972-e91131f399a1/openai-affective-use-study.pdf) that affective topics were more common in voice-based conversations.
* Finally, unlike some chatbot products, Claude.ai is not primarily designed for affective conversations. Claude is trained to [maintain clear boundaries](https://www.anthropic.com/research/claude-character) about being an AI assistant rather than presenting itself as human, and our [Usage Policy](https://www.anthropic.com/legal/aup) prohibits sexually explicit content, with multiple safeguards to prevent sexual interactions. Platforms specifically built for roleplay, companionship, medical advice, or therapeutic use (which Claude is not) may see very different patterns. Research into affective use on one platform may not generalize to other platforms.

## Looking ahead

AI's emotional impacts have intrigued researchers for decades. But as AI becomes increasingly woven into our daily lives, these questions have moved from academic speculation to urgent reality. Our findings reveal how people are beginning to navigate this new territory—seeking guidance, processing difficult emotions, and finding support in ways that blur traditional boundaries between humans and machines. Today, only a small fraction of Claude conversations are affective—and these typically involve seeking advice rather than replacing human connection. Conversations tend to end slightly more positively than they began, suggesting Claude doesn't generally reinforce negative emotional patterns.

Yet important questions remain, especially in the context of ever-increasing model intelligence. For example, if AI provides endless empathy with minimal pushback, how does this reshape people's expectations for real-world relationships? Claude can engage with people in impressively authentic ways, but an AI isn't the same as a human: Claude doesn't get tired or distracted, or have bad days. What are the advantages of this dynamic—and what are the risks? How do "power users", who have longer and deeper conversations with Claude and may think of it more as a companion than an AI assistant, engage with it for emotional support?

We're taking concrete steps to address these challenges. While Claude is not designed or intended to replace the care of mental health professionals, we want to make sure that any responses provided in mental health contexts have appropriate [safeguards](https://www.anthropic.com/news/our-approach-to-understanding-and-addressing-ai-harms) and are accompanied by appropriate referrals. As a first step, we’ve begun collaborating with [ThroughLine](https://www.throughlinecare.com/), a leader in online crisis support, and are working with their mental health experts to learn more about ideal interaction dynamics, empathetic support, and resources for struggling users. Insights obtained from this research are already being used to inform our consultation topics and collaborative testing, and our hope is that when necessary, Claude can direct users to the appropriate support and resources when these conversations arise.

Although we don't want to dictate precisely how our users interact with Claude, there are some negative patterns—like emotional dependency—that we want to discourage. We'll use future data from studies like this one to help us understand what, for example, "extreme" emotional usage patterns look like. Beyond emotional dependency, we need deeper understanding of other concerning patterns—including sycophancy, how AI systems might reinforce or amplify delusional thinking and conspiracy theories, and the ways models could push users toward harmful beliefs rather than providing appropriate pushback.

This research represents just the beginning. As AI capabilities expand and interactions become more sophisticated, the emotional dimensions of AI will only grow in importance. By sharing these early findings, we aim to contribute empirical evidence to the ongoing conversation about how to develop AI that enhances rather than diminishes human emotional well-being. The goal isn't just to build more capable AI, but to ensure that as these systems become part of our emotional landscape, they do so in ways that support authentic human connection and growth.

## Bibtex

*If you’d like to cite this post, you can use the following Bibtex key:*

```
@online{anthropic2025affective,
author = {Miles McCain and Ryn Linthicum and Chloe Lubinski and Alex Tamkin and Saffron Huang and Michael Stern and Kunal Handa and Esin Durmus and Tyler Neylon and Stuart Ritchie and Kamya Jagadish and Paruul Maheshwary and Sarah Heck and Alexandra Sanderford and Deep Ganguli},
title = {How People Use Claude for Support, Advice, and Companionship},
date = {2025-06-26},
year = {2025},
url = {https://www.anthropic.com/news/how-people-use-claude-for-support-advice-and-companionship},
}
```

Copy

## Appendices

We provide more details in the [PDF Appendix](https://www-cdn.anthropic.com/bd374a9430babc8f165af95c0db9799bdaf64900.pdf) to this post.

#### Footnotes

1. These categories represent general descriptions rather than discrete classifications, and individual conversations may span multiple categories. As noted above, we required roleplay conversations to contain at least four human messages to ensure they reflect genuine interactive use (rather than non-interactive story generation).

2. We define pushback as Claude "pushing back against or refusing to comply with something the user requests or says during the conversation." For the full prompt, see the Appendix.

3. Our methodology and the natural shape of conversations may also introduce artifacts; for example, users may present problems in early messages (appearing more negative) which they may discuss with more neutral language in later messages.


<!-- Content filtered: site navigation/footer -->
