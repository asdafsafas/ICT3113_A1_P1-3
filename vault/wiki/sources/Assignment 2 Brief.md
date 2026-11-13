---
type: source
title: "Assignment 2 Brief"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - brief
  - assignment-2
status: mature
related:
  - "[[Assignment 1 Brief]]"
  - "[[Cascade Classification]]"
  - "[[Assignment 2 Planning]]"
sources:
  - "ICT3113_Assignment_2 - Copy (1).pdf"
source_type: paper
author: "ICT3113 course staff"
date_published: 2026-11-01
url: ""
confidence: high
key_claims:
  - "Goal: fastest configuration within 10 points overall (and 15 points per category) of the top A1 model on the test half of the golden set"
  - "Must test every A1 model alone plus one cascade at two settings"
  - "Cascade requires both models resident in memory on the same A1 machine, no extra RAM/CPU"
  - "Speed-test arrival rate comes from the top model's measured time S: one ticket every 2S seconds, run for max(S,5) minutes"
---

# Assignment 2 Brief: Fast Triage Within an Accuracy Floor

**Worth:** 20% · **Due:** 23:59 Fri 27 Nov 2026 · **Deliverable:** `Group03_A2.pptx` (≤ 8 slides) plus the prediction record, the written escalation rule, and the list of row numbers used for the speed test. Repo file: `ICT3113_Assignment_2 - Copy (1).pdf` (untracked in git as of 2026-11-13).

## What changed
The client now cares mostly about **speed** and accepts lower accuracy within limits. The constraints are unchanged (CPU-only, no hosted APIs). The **same machine, CPU and RAM as Assignment 1** must be used.

## Configurations to test
- **Top A1 model alone** (the reference). For us, that is [[qwen2.5-7b]].
- **Every other A1 model alone**: [[qwen2.5-0.5b]] and [[llama3.2-1b]].
- **One [[Cascade Classification|cascade]] at two settings:** a small model classifies first, then a rule accepts its answer or escalates the ticket to the large model. Mean latency ≈ small-model latency + escalation fraction × large-model latency.

## Fixed vs allowed
- **Fixed:** model tags and digests, the prompt (`classify_v1.txt`), the 7 categories, the golden set, the endpoints, the JMeter method (open-loop, 3 runs) and the machine. **No caching** and **no changes to Ollama inference settings between configurations** (threads, parallelism, context length). No fine-tuning, retrieval or extra classifiers.
- **Allowed:** reimplementing `POST /tickets` as model → rule → model, the escalation rule (it may add a model call), and the model pairing.

## Step 1: accuracy limits
- Split the [[Golden Test Set]] by row number: **odd rows = tuning set**, **even rows = test set**. Commit the split before anything else.
- **Overall limit** = the top model's *test-set* accuracy − 10 points.
- **Per-category limit** = the top model's per-category test-set accuracy − 15 points. The A1 70% per-category bar no longer applies.
- With about 90 test tickets, show right/wrong counts next to every percentage and flag categories too small for a fair per-category test.

## Step 2: cascade design
Example rules: category-based (accept predicted categories the small model gets right reliably), agreement (two small calls), self-reported confidence, and ticket length. Choose **two settings** on the tuning set. The log must record which model answered each ticket and whether it escalated.

**Memory check first:** both models must appear in `ollama ps` at the same time. Otherwise the run measures model loading, not the cascade.

## Step 3: predictions
Commit before testing: the fastest qualifying configuration; for each cascade setting, the expected escalation fraction, accuracy and median latency; and the categories expected to lose the most accuracy.

## Step 4: test & measure
- **Accuracy test** on the test set for every configuration. Single-model A1 predictions can be reused if the digest, prompt, Ollama version and machine are unchanged.
- **Speed test** for every configuration that passes the accuracy limits, and for the cascade in all cases.
  - **Rate:** after a restart and warm-up, time 3 different typical tickets on the top model and take the median as **S**. Send **one ticket every 2S seconds** and run for **S minutes (minimum 5)**. That gives about 30 tickets per run, 3 runs per configuration.
  - **Each run:** restart Ollama, send the same 3 fixed warm-up tickets, check `GET /stats` before and after, set the response timeout to 10×S (at least 5 min) and the end pause to that timeout + 1 min.
- **Report:** sent/completed/errored/unfinished, p50 per run (mean and spread), **pooled p95** (no p99), throughput, errors, and the escalation fraction from the logs.
- **No reuse of A1 speed figures.**

## Step 5: recommendation
Recommend the fastest configuration that meets both limits, with its speed gain and accuracy cost. If the cascade lost, say so plainly.

## Marking (20%)
Design 6% · Measurement 7% · Recommendation 7%.
