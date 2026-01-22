---
source_url: https://www.anthropic.com/news/claude-for-life-sciences
source_type: sitemap
content_hash: sha256:63a671c616172d573987858ac81519d76bf0ab4defa3c2ed43c3b46f64630c59
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-10-20'
---

Announcements

# Claude for Life Sciences

[![Video](https://img.youtube.com/vi/sHImlfVM9r4/maxresdefault.jpg)](https://www.youtube.com/watch?v=sHImlfVM9r4)

[![Video](https://img.youtube.com/vi/kSl2mxseXkM/maxresdefault.jpg)](https://www.youtube.com/watch?v=kSl2mxseXkM)

Oct 20, 2025

![](https://www-cdn.anthropic.com/images/4zrzovbb/website/74409af25137110ac04cc39e4d5ea0a2fbcea421-1000x1000.svg)

Increasing the rate of scientific progress is a core part of Anthropic’s public benefit mission.

We are focused on building the tools to allow researchers to make new discoveries – and eventually, to allow AI models to make these discoveries autonomously.

Until recently, scientists typically used Claude for individual tasks, like writing code for statistical analysis or summarizing papers. Pharmaceutical companies and others in industry also use it for tasks across the rest of their business, like sales, to fund new research. Now, our goal is to make Claude capable of supporting the entire process, from early discovery through to translation and commercialization.

To do this, we’re rolling out [several improvements](https://www.claude.com/solutions/life-sciences) that aim to make Claude a better partner for those who work in the life sciences, including researchers, clinical coordinators, and regulatory affairs managers.

## Making Claude a better research partner

First, we’ve improved Claude’s underlying performance. Our most capable model, Claude Sonnet 4.5, is significantly better than previous models at a range of life sciences tasks. For example, on Protocol QA, a benchmark that tests the model’s understanding and facility with laboratory protocols, Sonnet 4.5 scores 0.83, against a human baseline of 0.79, and Sonnet 4’s performance of 0.74.1 Sonnet 4.5 shows a similar improvement on its predecessor on BixBench, an evaluation that measures its performance on bioinformatics tasks.

To make Claude more useful for scientific work, we’re now adding several [new connectors](https://claude.com/partners/mcp) to scientific platforms, the ability to use Agent Skills, and life sciences-specific support in the form of a prompt library and dedicated support.

## Connecting Claude to scientific tools

[**Connectors**](https://claude.ai/redirect/website.v1.NORMALIZED/settings/connectors) allow Claude to access other platforms and tools directly. We’re adding several new connectors that are designed to make it easier to use Claude for scientific discovery:

* **Benchling** gives Claude the ability to respond to scientists’ questions with links back to source experiments, notebooks, and records;
* **BioRender** connects Claude to its extensive library of vetted scientific figures, icons, and templates;
* **PubMed** provides access to millions of biomedical research articles and clinical studies;
* **Scholar Gateway developed by Wiley** providesaccess to authoritative, peer-reviewed scientific content within Claude to accelerate research discovery;
* **Synapse.org** allows scientists to share and analyze data together in public or private projects;
* **10x Genomics** allows researchers to conduct single cell and spatial analysis in natural language.

These connectors add to our existing set, which includes general purpose tools like Google Workspace and Microsoft SharePoint, OneDrive, Outlook, and Teams. Claude can also already work directly with Databricks to provide analytics for large-scale bioinformatics research, and Snowflake to search through large datasets using natural language questions.

## Developing skills for Claude

Last week, we released [Agent Skills:](https://www.anthropic.com/news/skills) folders including instructions, scripts, and resources that Claude can use to improve how it performs specific tasks. Skills are a natural fit for scientific work, since they allow Claude to consistently and predictably follow specific protocols and procedures.

We’re developing a number of scientific skills for Claude, beginning with **`single-cell-rna-qc`** This skill performs quality control and filtering on single-cell RNA sequencing data, using [scverse](https://scverse.org/) best practices:

![Claude performs quality control on single-cell RNA-seq data](https://www-cdn.anthropic.com/images/4zrzovbb/website/07de700e38ef4d328ccdb5c15ab9e3df5286fc08-3840x2160.png)

*Claude performs quality control on single-cell RNA-seq data.*

In addition to the skills we’re creating, scientists can build their own. For more information and guidance, including setting up custom skills, see [here](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

## Using Claude for Life Sciences

Claude can be used for life sciences tasks like the following:

* **Research, like literature reviews and developing hypotheses:** Claude can cite and summarize biomedical literature and generate testable ideas based on what it finds.

Watch how Claude analyzes data, conducts a literature review, dives into potentially novel insights, turns this analysis into a presentation, and puts the finishing touches on slides with a figure from BioRender.

* **Generating protocols**: With the Benchling connector, Claude can draft study protocols, standard operating procedures and consent documents.
* **Bioinformatics and data analysis**: Process and analyze genomic data with Claude Code. Claude can present its results in [slides, docs](https://www.anthropic.com/news/create-files), or code notebook format.
* **Clinical and regulatory compliance**: Claude can draft and review regulatory submissions, and compile compliance data.

In addition, to help scientists get started quickly, we’re creating a [library of prompts](https://support.claude.com/en/articles/12614768-getting-started-with-claude-for-life-sciences) that should elicit best results on tasks like the above.

## Partnerships and customers

We’re providing hands-on support from dedicated subject matter experts in our Applied AI and customer-facing teams.

We’re also partnering with companies who specialize in helping organizations adopt AI for life sciences work. These include Caylent, Deloitte, Accenture, KPMG, PwC, Quantium, Slalom, Tribe AI, and Turing, along with our cloud partners, AWS and Google Cloud.

Many of our existing customers and partners have already been using Claude for a broad range of real-world scientific tasks:

![Sanofi logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/44cb9482787368c3b6b3dc183e378abf6b5ca693-3274x1510.png)

> Claude, paired with internal knowledge libraries, is integral to Sanofi's AI transformation and used by most Sanofians daily in our Concierge app. We're seeing efficiency gains across the value-chain, while our enterprise deployment has enhanced how teams work. This collaboration with Anthropic augments human expertise to deliver life-changing medicines faster to patients worldwide.

![Benchling logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/f8958499b7603125dd85312cb6688fe8cf7bd959-938x321.png)

> AI in R&D works through an ecosystem. Anthropic brings the best technologies while prioritizing access, governance, and interoperability. Benchling is uniquely positioned to contribute. For over a decade, scientists have trusted us as their source of truth for experimental data and workflows. Now we're building AI that powers the next chapter of R&D.

![Broad Institute of MIT and Harvard logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/d165bbdbd303f12d2fe5e8b6d24332b5d9ab94eb-600x154.png)

> Broad Institute scientists pursue the most ambitious questions in biology and medicine, creating tools to empower scientists everywhere. We're working with Manifold on Terra Powered by Manifold. AI agents built on Claude enable scientists to work at entirely new scale and efficiency, exploring scientific domains in previously impossible ways.

![10x Genomics  logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/2d2b4c714c164385923a67894ec0173d6290fb4f-1200x771.png)

> 10x's single cell and spatial analysis capabilities traditionally required computational expertise. Now, with Claude, researchers perform analytical tasks—aligning reads, generating matrices, clustering, secondary analysis—through plain English conversation. This lowers the barrier for new users while scaling to meet the needs of advanced research teams.

![Genmab logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/fe19dca89482cda5712ddb7d40d0b0e5db73f2a6-1301x380.png)

> We see tremendous potential in Claude streamlining how we bring drugs to market. The ability to pull from clinical data sources and create GxP-compliant outputs will help us bring life-changing cancer therapies to patients faster while maintaining the highest quality standards. We see Claude powering AI applications across several major functions at our company.

![Komodo Health logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/c10350722a8953ec4a62bd473df1b80774d4df79-640x177.svg)

> Healthcare analytics demands AI purpose-built for our industry's complexity and rigor. Komodo Health's partnership with Anthropic delivers transparent, auditable solutions designed for regulated healthcare environments. Together, we're enabling healthcare and life sciences teams to transform weeks-long analytical workflows into actionable intelligence in minutes.

![Novo Nordisk logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/5080602ba328ac22c4a32d3cd348ba234320900a-800x565.png)

> We've consistently been one of the first movers when it comes to document and content automation in pharma development. Our work with Anthropic and Claude has set a new standard — we're not just automating tasks, we're transforming how medicines get from discovery to the patients who need them.

![Stanford University  logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/e7743444ed3664c6609617c16114be37d5474a7b-3840x2160.png)

> Claude Code and partnership with Anthropic have been extremely valuable for developing Paper2Agent, our moonshot to transform passive research papers into interactive AI agents that can act as virtual corresponding authors and co-scientists.

![PwC logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/468fc2c0bb3ca80ff2b112002d4d665c1e2bff65-360x180.svg)

> At PwC, responsible AI is a trust imperative. We pair our deep sector insight with Claude's agentic intelligence to reimagine how clinical, regulatory, and commercial teams operate. Together, we're not just streamlining processes—we're elevating quality, accelerating discovery, and building systems where confidence scales alongside innovation.

![Schrödinger logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/b463e00f9945da22059fbb8216e3af714f58fd62-1238x362.png)

> Claude Code has become a powerful accelerator for us at Schrödinger. For the projects where it fits best, Claude Code allows us to turn ideas into working code in minutes instead of hours, enabling us to move up to 10x faster in some cases. As we continue to work with Claude, we are excited to see how we can further transform the way we build and customize our software.

![Latch Bio logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/b6ec5b998f39cde140615558d3da14c58a52c1be-1025x289.png)

> When creating an AI agent for bioinformatics analyses, we focused on three key factors: top software development, life sciences alignment, and startup support. We evaluated half a dozen platforms, and Claude was the standout leader. We're excited to continue this collaboration and bring cutting-edge AI agents into biotech research.

![EvolutionaryScale logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/98f513214f5429a2273ead0768a6f43a23e504ba-2495x491.png)

> At EvolutionaryScale, we’re building next-generation AI systems to model the living world. Anthropic’s frontier models accelerate our ability to reason about complex biological data and translate it into scientific insight, helping us push the boundaries of what’s possible in life science discovery.

![Manifold logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/6ba95f586841d964268b8845bbe9629a0933e714-149x36.svg)

> At Manifold, our mission is to power faster, leaner life sciences. Building with Claude has enabled us to develop AI agents that translate questions in the semantic space of scientists to execution in the technical space of specialized datasets and tools. Together, we’re transforming how life sciences R&D will happen in the years ahead.

![FutureHouse logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/2309ae6041b9aae5b19483b28c1d4515c6490f28-2776x711.png)

> At FutureHouse, Claude helps power both our bioinformatics and literature analysis workflows. Claude is our model of choice for accurate figure analyses and orchestrating non-linear searches through the literature.

![Axiom Bio logo](https://www-cdn.anthropic.com/images/4zrzovbb/website/e9660fa2497a0ea2d3090a94d3e0e97ac6b2e0b4-604x178.svg)

> Claude has been invaluable for Axiom as we build AI to predict drug toxicity. We've used billions of tokens in Claude Code for many PRs. Claude agents with MCP servers are core to our scientific work, directly querying databases to interpret, transform, and test data correlations, helping us identify the most useful features for predicting clinical drug toxicity.

01 / 15

## Supporting the life sciences

In addition to the updates described above, we’re supporting life sciences research through our [AI for Science](https://www.anthropic.com/news/ai-for-science-program) program. This program provides free API credits to support leading researchers working on high-impact scientific projects around the world.

Our partnerships with these labs helps us identify new applications for Claude, while helping scientists answer some of their most pressing questions. We continue to welcome [submissions](https://docs.google.com/forms/d/e/1FAIpQLSfwDGfVg2lHJ0cc0oF_ilEnjvr_r4_paYi7VLlr5cLNXASdvA/viewform) for project ideas.

Jonah Cool and Eric Kauderer-Abrams, who lead partnerships and R&D for Life Sciences at Anthropic, respectively, discuss this and other recent work below.

Anthropic’s Jonah Cool and Eric Kauderer-Abrams share their vision for making Claude the go-to AI research assistant for scientists with Claude for Life Sciences.

## Getting started

To learn more about Claude for Life Sciences or set up a demo with our team, see [here](https://claude.com/contact-sales/life-sciences).

[Claude for Life Sciences](https://www.claude.com/solutions/life-sciences) is available through Claude.com and on the AWS Marketplace, with Google Cloud Marketplace availability coming soon.

#### Footnotes

1 Protocol QA score (multiple choice format) with 10 shot prompting. For more, see our [Sonnet 4.5 System Card](https://assets.anthropic.com/m/12f214efcc2f457a/original/Claude-Sonnet-4-5-System-Card.pdf), pages 132-133.


<!-- Content filtered: site navigation/footer -->
