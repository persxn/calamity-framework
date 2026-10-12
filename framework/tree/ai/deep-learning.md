---
id: deep-learning
title: Deep learning with PyTorch
track: ai
group: ml
prereqs: [classical-ml]
tags: [ai, ml]
weaves_into: [llm, ai]
aliases: [dl, neural networks, pytorch, cnn, backpropagation]
est_hours: 80
order: 30
summary: Neural networks from the backpropagation equations to trained models you can debug.
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the neuron, layers, activations, the forward pass; universal approximation in outline
- backpropagation derived and implemented by hand for a small network
- PyTorch: tensors, autograd, modules, datasets and loaders, the training loop, devices
- loss functions and optimisers; learning-rate schedules; initialisation
- regularisation: weight decay, dropout, data augmentation, early stopping; normalisation layers
- convolutional networks for images
- sequence models: embeddings, recurrent networks in outline, attention
- the transformer block at a working level
- debugging training: overfit one batch, loss curves, gradient norms, common failure signs
- transfer learning and fine-tuning a pretrained model
- experiment hygiene: seeds, configs, checkpoints, tracking runs

# Boss

Train an image classifier twice: a small CNN from scratch and a fine-tuned pretrained model, with a written comparison and a debugging log.

Passes when:

- the from-scratch model first overfits a single batch to near-zero loss (shown in the log)
- the fine-tuned model beats the from-scratch one on the held-out set by the margin the tutor sets
- the training script resumes from a checkpoint and reproduces the same metric with the same seed
- the learner explains one planted training bug from the loss curve alone

# Weave

LLM topics should point back to embeddings, attention and the training loop learnt here.
