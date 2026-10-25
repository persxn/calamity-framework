---
id: post-training-rl
title: "Post-training with RL"
track: ai
group: training
prereqs: [fine-tuning]
tags: [ai, ml, llm, runnable]
aliases: [rlhf, dpo, grpo, rlvr, preference optimization, reward model]
est_hours: 35
order: 20
summary: "Improve a model with preferences and verifiable rewards: DPO, GRPO and RLVR, with KL control and reward-hacking checks."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the post-training landscape: supervised fine-tuning, then preferences or reinforcement learning
- preference optimisation: a reward model with PPO, or DPO without one
- reinforcement learning with verifiable rewards: the reward is a checker (unit tests, an exact answer); GRPO and its relatives
- rollouts, advantages, and the KL penalty that keeps the policy near the reference
- reward hacking: how a model games a reward, and how to catch it
- what actually moved a metric: the base model, the post-training, or just more inference-time compute

# Boss

Run a small GRPO job with a verifiable reward and show the reward rises while the policy stays controlled.

Passes when:

- the reward is an exact automatic check (for example arithmetic correctness), not a judgment call
- reward and KL divergence are plotted over the training steps
- a held-out check shows the gain is real and not reward hacking, with one example inspected by hand
- the run is reproduced from a seed, or the variance across seeds is reported
