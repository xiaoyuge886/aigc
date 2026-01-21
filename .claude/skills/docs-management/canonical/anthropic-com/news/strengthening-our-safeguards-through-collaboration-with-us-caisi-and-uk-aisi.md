---
source_url: https://www.anthropic.com/news/strengthening-our-safeguards-through-collaboration-with-us-caisi-and-uk-aisi
source_type: sitemap
content_hash: sha256:4f40cff2344a913cc6c133b218345bcbc3d65becc9a53bb24092214e042009a2
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-09-12'
---

Announcements

# Strengthening our safeguards through collaboration with US CAISI and UK AISI

Sep 12, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/74409af25137110ac04cc39e4d5ea0a2fbcea421-1000x1000.svg)

Over the past year, we've collaborated with the US Center for AI Standards and Innovation (CAISI) and UK AI Security Institute (AISI), government bodies established to measure and improve the security of AI systems. Our voluntary work together began as initial consultations, but over time evolved to an ongoing partnership where CAISI and AISI teams were provided access to our systems at various stages of model development, allowing for ongoing testing of our systems.

Governments bring unique capabilities to this work, particularly deep expertise in national security areas like cybersecurity, intelligence analysis, and threat modeling that enables them to evaluate specific attack vectors and defense mechanisms when paired with their machine learning expertise. Their feedback helps us improve our security measures so our systems can withstand some of the most sophisticated attempts at misuse.

Working with independent external experts to identify vulnerabilities in AI systems is a core part of Anthropic’s [Safeguards](https://www.anthropic.com/news/building-safeguards-for-claude) approach and is critical to preventing misuse of our models that could cause real-world harm.

## Uncovering and addressing vulnerabilities

This collaboration has already led to key findings that helped us strengthen the tools we use to prevent malicious use of our models. As part of our respective agreements with CAISI and AISI, each organization evaluated several iterations of our [Constitutional Classifiers](https://www.anthropic.com/news/constitutional-classifiers)—a defense system we use to spot and prevent jailbreaks—on models like Claude Opus 4 and 4.1 prior to deployment to help identify vulnerabilities and build robust safeguards.

**Testing of Constitutional Classifiers.** We gave CAISI and AISI access to several early versions of our constitutional classifiers, and we’ve continued to provide access to our latest systems as we’ve made improvements. Together, we stress-tested these classifiers, with government red-teamers identifying a range of vulnerabilities—both before and after deployment—and our technical team using these findings to strengthen the safeguards. As examples, these vulnerabilities included:

* **Uncovering prompt injection vulnerabilities.** Government red-teamers identified weaknesses in our early classifiers via prompt injection attacks. Such attacks use hidden instructions to trick models into behavior that the system designer didn’t intend. Testers discovered that specific annotations, like falsely claiming human review had occurred, could bypass classifier detection entirely. We have patched these vulnerabilities.
* **Stress-testing safeguard architectures.** They developed a sophisticated universal jailbreak that encoded harmful interactions in ways that evaded our standard detection methods. Rather than simply patching this individual exploit, the discovery prompted us to fundamentally restructure our safeguard architecture to address the underlying vulnerability class.
* **Identifying cipher-based attacks.** Encoded harmful requests using ciphers, character substitutions, and other obfuscation techniques to evade our classifiers. These findings drove improvements to our detection systems, enabling them to recognize and block disguised harmful content regardless of encoding method.
* **Input and output obfuscation attacks.** Discovered universal jailbreaks using sophisticated obfuscation methods tailored to our specific defenses, such as fragmenting harmful strings into seemingly benign components within a wider context. Identifying these blind spots enabled targeted improvements to our filtering mechanisms.
* **Automated attack refinement.** Built new automated systems that progressively optimize attack strategies. They recently used this system to produce an effective universal jailbreak by iterating from a less effective jailbreak, which we are using to improve our safeguards.

**Evaluation and risk methodology.** Beyond identifying specific vulnerabilities, CAISI and AISI teams have helped strengthen our broader approach to security. Their external perspective on evidence requirements, deployment monitoring, and rapid response capabilities has been invaluable in pressure-testing our assumptions and identifying areas where additional evidence may be needed to support our threat models.

## Key lessons for effective collaborations

Our experience has taught us several important lessons about how to engage effectively with government research and standards bodies to improve the safety and security of our models.

**Comprehensive model access enhances red-teaming effectiveness.** Our experience shows that giving government red-teamers deeper access to our systems enables more sophisticated vulnerability discovery. We provided several key resources:

* **Pre-deployment safeguard prototypes**. Testers could evaluate and iterate on protection systems before they went live, identifying weaknesses *before* safeguards were deployed.
* **Multiple system configurations**. We provided models across the protection spectrum, from completely unprotected versions to models with full safeguards. This approach lets testers first develop attacks against base models, then progressively refine techniques to bypass increasingly sophisticated defenses. Helpful-only model variants also enabled precise harmful output scoring and capability benchmarking.
* **Extensive documentation and internal resources**. We provided trusted government red-teamers with our safeguard architecture details, documented vulnerabilities, safeguards reports, and granular content policy information (including specific prohibited requests and evaluation criteria). This transparency helped teams target high-value testing areas rather than searching blindly for weaknesses.
* **Real-time safeguards data accelerates vulnerability discovery.** We gave government red-teamers direct access to classifier scores. This enabled testers to refine their attack strategies and conduct more targeted exploratory research.

**Iterative testing allows for complex vulnerability discovery.** Though single evaluations provide value, sustained collaboration enables external teams to develop deep system expertise and uncover more complex vulnerabilities. During critical phases, we've maintained daily communication channels and frequent technical deep-dives with our partners.

**Complementary approaches offer more robust security.** CAISI and AISI evaluations work synergistically with our broader ecosystem. [Public bug bounty](https://www.anthropic.com/news/testing-our-safety-defenses-with-a-new-bug-bounty-program) programs generate high-volume, diverse vulnerability reports from a wide talent pool, while specialized expert teams can help uncover complex, subtle attack vectors that require deep technical knowledge to identify. This multi-layered strategy helps ensure we catch both common exploits and sophisticated edge cases.

## Ongoing collaboration

Making powerful AI models secure and beneficial requires not just technical innovation but also new forms of collaboration between industry and government. Our experience demonstrates that public-private partnerships are most effective when technical teams work closely together to identify and address risk.

As AI capabilities advance, the role of independent evaluations of mitigations is increasingly important. We are heartened that other AI developers are also working with these government bodies, and encourage more companies to do so and share their own lessons more widely.

*We extend our gratitude to the technical teams at both US CAISI and UK AISI for their rigorous testing, thoughtful feedback, and ongoing collaboration. Their work has materially improved the security of our systems and advanced the field of measuring AI safeguard effectiveness.*


<!-- Content filtered: site navigation/footer -->
