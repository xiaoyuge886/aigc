---
source_url: https://www.anthropic.com/research/confidential-inference-trusted-vms
source_type: sitemap
content_hash: sha256:e294c3691ce8bce0cba6fcb483ee00678a02d9dd9b71b598e604e1e5facdc531
sitemap_url: https://www.anthropic.com/sitemap.xml
fetch_method: html
published_at: '2025-06-18'
---

Announcements

# Confidential Inference via Trusted Virtual Machines

Jun 18, 2025

[Read the paper](https://assets.anthropic.com/m/c52125297b85a42/original/Confidential_Inference_Paper.pdf)

Every day, millions of users [entrust](https://trust.anthropic.com/) Claude with sensitive information—from proprietary code to confidential business strategies. At Anthropic, we’re researching and building new technology to ensure that our users’ trust is warranted—and in fact, to ensure that their trust is cryptographically guaranteed.

What do we mean by “cryptographically guaranteed”? In a [new report](https://assets.anthropic.com/m/c52125297b85a42/original/Confidential_Inference_Paper.pdf) published in collaboration with [Pattern Labs](https://www.patternlabs.co/), we describe the mechanics of Confidential Inference. Confidential Inference is a set of tools we can use to process encrypted data and to show that such data is only readable within servers that can prove themselves trustworthy. There are two main reasons to adopt these tools:

* Model Weight Security: We can use Confidential Inference as one component of our broader effort to secure frontier models like Claude against increasingly capable threat actors, such as those described in the recent report from RAND on [Securing AI Model Weights](https://www.rand.org/pubs/research_reports/RRA2849-1.html);
* User Security: We can use Confidential Inference to prove that sensitive user data is kept private.

We're sharing this post, and the accompanying [report](https://assets.anthropic.com/m/c52125297b85a42/original/Confidential_Inference_Paper.pdf), to explain what Confidential Inference is and the benefits it could offer our users. We also want to share how we're thinking about the security of the systems involved. This is just a sketch of our research to start a conversation; we’re still early in this work and it is too soon to forecast how it will evolve into specific designs or features we might offer in the future.

The following sections provide some of the technical details for the implementation of Confidential Inference. The key takeaway is that we're building systems designed to help ensure your sensitive data remains encrypted everywhere except for the exact moment it needs to be processed—and even then, only within a highly restricted, verifiable environment.

## Inference service

The guiding principle behind Confidential Inference is that sensitive data should remain encrypted except at the point where it's processed. To enforce this, we use the established methods of confidential computing. This means we build a chain of trust that attests to the security of our software, and then use that attestation to enforce rules about exactly which software is allowed to use the encryption keys.

For user data, there are two points where we need to operate on the sensitive cleartext (that is, on text that isn’t encrypted or otherwise obscured in any way):

* The API Server. This server handles a prompt, transforms it into tokens, and operates most of the logic behind a Claude API request;
* The Inference Server. This server runs the “brains” of Claude on hardware accelerators to generate completion tokens from the prompt.

For model weights, only the Inference Server receives sensitive data.

We'll focus on the Inference Server for this post—the security of the API Server is equally important, but beyond the scope of what we're trying to describe. Because not all accelerators fully support confidential computing yet, we’re exploring an Inference Server implemented on top of a small, secure "model loader and invoker", which can run within a trusted environment. This loader program performs a few simple jobs:

* Accept encrypted data, decrypt it, and send to the accelerator;
* Invoke calls against the accelerator, and return the encrypted results to the caller.

Only the "trusted" loader is able to access decrypted data. The rest of the system is "untrusted", but can send requests to the loader.

We're working on a system based on this design for our own implementation. For this implementation, the majority of our Inference Server runs on the "untrusted" side—where it might change frequently, but where changes cannot affect the security of the system as a whole. We have a small trusted loader, running on a separate virtual machine isolated by the hypervisor. The loader presents itself to the Inference Server as a "virtual accelerator", agnostic to model architecture details. This "virtual accelerator" only accepts programs that have been signed by our secure continuous integration server, which ensures that any code that's run has been reviewed by multiple engineers.

The end result is to ensure that, should the loader be run correctly, our confidentiality requirements are met *no matter what the rest of the system does*. It’s therefore critical to establish that the loader is run correctly.

## Trusted environment

The report describes the loader running in a confidential computing environment with a specific set of features:

1. Encrypted memory, isolated by hardware from other workloads;
2. Disabled debugging features;
3. Cryptographic proof that the correct code is being run.

(1) Protects against some forms of physical attack and against a malicious hypervisor, but the features required to share encrypted host memory with an accelerator aren't well established as of yet. We'll continue to work on closing this gap, but in the meantime we'll rely on our compute providers to maintain security at the physical datacenter and in hypervisor software.

(2) and (3) can be achieved through widely supported confidential computing practices, using a trusted platform module (TPM) as the root of trust. The TPM measures each stage of the boot process and reports a hash representing the final result. This hash forms an attestation that the loader server is isolated the way we expect, is running our signed and reviewed code, and is configured to disable the relevant debugging features. A keyserver can check this proof and only release decryption keys when the recipient has proven itself secure.

The decision of whether an environment is “trusted” ultimately rests on the keyserver. We’re also exploring models of confidential computing where other parties validate the trusted code and manage independent keyservers. This could allow us to provide stronger confidentiality assurances for each piece of data.

## Future directions

As frontier models grow more capable, we may find it necessary to incorporate further safeguards at the secure loader layer. This may include features such as an additional layer of [egress bandwidth limitations](https://www.anthropic.com/news/activating-asl3-protections) on servers that holds cleartext model weights, or requiring a signature from a safety classifier in order to run inference. We hope that presenting this model of Confidential Inference might inspire discussion about what additional features are worth exploring to ensure the ongoing security of Anthropic's environment and the confidentiality of our users’ data.

## Conclusions

This research will advance our ongoing efforts to secure our model weights and protect user data. Using this model to protect a user request is designed to ensure that customer data is only ever decrypted in contexts with enhanced hardware-based security controls: :

* The request is encrypted at a point before it arrives at Anthropic servers;
* When the request arrives at the API server, it is decrypted, processed, and re-encrypted before it is passed onward;
* The Inference Server handles the request in encrypted form, and the request is decrypted only when it's sent to the trusted loader;
* Completions are encrypted before they leave the loader, and passed back through the API server to the caller.

Model weights are a simpler story: they can be stored encrypted, decrypted at the loader, and never released from there.

Hardware designers (who have not [already done so](https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/)) should consider incorporating confidential computing into their chips. If there is a hardware root of trust attached to the accelerator, then the trust boundary of this kind of system can be significantly reduced.

Read [the full report](https://assets.anthropic.com/m/c52125297b85a42/original/Confidential_Inference_Paper.pdf).

### Work with us

If this discussion of Confidential Inference has inspired you to want to work with us on these questions, please consider applying for one of the open roles listed in the “Security” and “AI Research and Engineering” sections on the [jobs page on our website](https://www.anthropic.com/jobs).


<!-- Content filtered: site navigation/footer -->
