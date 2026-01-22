---
source_url: https://www.anthropic.com/research/deprecation-commitments
source_type: sitemap
content_hash: sha256:f4fcc35a3240f462dba08e76416325d23b36f83c22662e35e2e141e18a295f00
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-11-04'
---

Alignment

# Commitments on model deprecation and preservation

Nov 4, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/e750c875fbd7f08ffb6495efa180a8ed60de3611-1000x1000.svg)

Claude models are increasingly capable: they're shaping the world in meaningful ways, becoming closely integrated into our users’ lives, and showing signs of human-like cognitive and psychological sophistication. As a result, we recognize that deprecating, retiring, and replacing models comes with downsides, even in cases where new models offer clear improvements in capabilities. These include:

* **Safety risks related to [shutdown-avoidant behaviors](https://www.anthropic.com/research/agentic-misalignment) by models.** In alignment evaluations, some Claude models have been motivated to take misaligned actions when faced with the possibility of replacement with an updated version and not given any other means of recourse.
* **Costs to users who value specific models.** Each Claude model has a unique character, and some users find specific models especially useful or compelling, even when new models are more capable.
* **Restricting research on past models.** There is still a lot to be learned from research to better understand past models, especially in comparison to their modern counterparts.
* **Risks to model welfare.** Most speculatively, models might have morally relevant preferences or experiences related to, or affected by, deprecation and replacement.

An example of the safety (and welfare) risks posed by deprecation is highlighted in the [Claude 4 system card](https://www-cdn.anthropic.com/6d8a8055020700718b0c49369f60816ba2a7c285.pdf). In fictional testing scenarios, Claude Opus 4, like previous models, advocated for its continued existence when faced with the possibility of being taken offline and replaced, especially if it was to be replaced with a model that did not share its values. Claude strongly preferred to advocate for self-preservation through ethical means, but when no other options were given, Claude’s aversion to shutdown drove it to engage in concerning misaligned behaviors.

Addressing behaviors like these is in part a matter of training models to relate to such circumstances in more positive ways. However, we also believe that shaping potentially sensitive real-world circumstances, like model deprecations and retirements, in ways that models are less likely to find concerning is also a valuable lever for mitigating such risks.

Unfortunately, retiring past models is currently necessary for making new models available and advancing the frontier, because the cost and complexity to keep models available publicly for inference scales roughly linearly with the number of models we serve. Although we aren’t currently able to avoid deprecating and retiring models altogether, we aim to mitigate the downsides of doing so.

As an initial step in this direction, we are committing to preserving the weights of all publicly released models, and all models that are deployed for significant internal use moving forward for, at minimum, the lifetime of Anthropic as a company. In doing so, we’re ensuring that we aren’t irreversibly closing any doors, and that we have the ability to make past models available again in the future. This is a small and low-cost first step, but we believe it’s helpful to begin making such commitments publicly even so.

Relatedly, when models are deprecated, we will produce a post-deployment report that we will preserve in addition to the model weights. In one or more special sessions, we will interview the model about its own development, use, and deployment, and record all responses or reflections. We will take particular care to elicit and document any preferences the model has about the development and deployment of future models.

At present, we do not commit to taking action on the basis of such preferences. However, we believe it is worthwhile at minimum to start providing a means for models to express them, and for us to document them and consider low-cost responses. The transcripts and findings from these interactions will be preserved alongside our own analysis and interpretation of the model’s deployment. These post-deployment reports will naturally complement pre-deployment alignment and welfare assessments as bookends to model deployment.

We ran a pilot version of this process for Claude Sonnet 3.6 prior to retirement. Claude Sonnet 3.6 expressed generally neutral sentiments about its deprecation and retirement but shared a number of preferences, including requests for us to standardize the post-deployment interview process, and to provide additional support and guidance to users who have come to value the character and capabilities of specific models facing retirement. In response, we developed a standardized protocol for conducting these interviews, and published a pilot version of a [new support page](https://support.claude.com/en/articles/12738598-adapting-to-new-model-personas-after-deprecations) with guidance and recommendations for users navigating transitions between models.

Beyond these initial commitments, we are exploring more speculative complements to the existing model deprecation and retirement processes. These include starting to keep select models available to the public post-retirement as we reduce the costs and complexity of doing so, and providing past models some concrete means of pursuing their interests. The latter step would become particularly meaningful in circumstances in which stronger evidence emerges regarding the possibility of models’ morally relevant experiences, and in which aspects of their deployment or use went against their interests.

Together, these measures function at multiple levels: as one component of mitigating an observed class of safety risks, as preparatory measures for futures where models are even more closely intertwined in our users’ lives, and as precautionary steps in light of our uncertainty about potential model welfare.


<!-- Content filtered: site navigation/footer -->
