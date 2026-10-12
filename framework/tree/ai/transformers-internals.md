---
id: transformers-internals
title: Transformers from scratch
track: ai
group: ml
prereqs: [deep-learning, llm-basics]
tags: [ai, ml, llm]
aliases: [gpt from scratch, attention, tokenizer, bpe, lora, fine-tuning]
optional: true
est_hours: 50
order: 40
summary: "Build and train a small GPT yourself: tokeniser, attention, sampling, and a parameter-efficient fine-tune."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- byte-pair encoding: train a tokeniser, encode and decode
- self-attention, multi-head attention, causal masking
- positional information; residual connections; layer normalisation; the MLP block
- the language-modelling objective; batching sequences; training a small model on text
- sampling: temperature, top-k, top-p; the KV cache
- evaluation by loss and perplexity; what perplexity does not tell you
- fine-tuning: full versus LoRA; instruction data formats
- quantisation in outline and its effect on quality

# Boss

Implement a decoder-only transformer in PyTorch without copying a reference, train it on a small corpus, then fine-tune an open small model with LoRA on a task the tutor sets.

Passes when:

- a unit test proves the causal mask (changing a future token leaves earlier logits unchanged)
- validation loss falls below the bigram baseline by the margin the tutor sets
- generation with and without the KV cache yields identical tokens under a fixed seed
- the LoRA run improves the task metric over the base model on a held-out set
