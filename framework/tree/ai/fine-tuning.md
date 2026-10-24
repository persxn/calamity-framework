---
id: fine-tuning
title: "Fine-tuning"
track: ai
group: training
prereqs: [transformers-internals]
tags: [ai, ml, llm, runnable]
aliases: [sft, lora, qlora, peft, fine-tuning]
est_hours: 30
order: 10
summary: "Adapt an open model to a task: supervised fine-tuning with LoRA and QLoRA, measured honestly against the base model."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- supervised fine-tuning: demonstration data, instruction formats, the training loop
- full fine-tuning versus parameter-efficient (LoRA): what LoRA changes, and why it is cheap
- QLoRA: a quantised base model, and the memory it saves
- a held-out set and honest evaluation against the base model, scored the same way for both
- overfitting and leakage between train and eval, and how to check for them
- learning rate, epochs and batch size; reading the loss curve

# Boss

LoRA fine-tune a small open model on a task and show it beats the base model on a held-out set.

Passes when:

- the data is split so that no evaluation example appears in training, and the split is shown
- the fine-tuned model is scored against the base model on the held-out set, the same way for both
- the improvement is reported with its seed and reproduced on a second run
- the memory used is stated, and the QLoRA variant's saving is measured if it is attempted
