# Summary of My Chat with Codex

This document summarises the help, decisions and work discussed throughout this
chat for ICT3113 Assignment 1. It is a record of the conversation, not a
replacement for the assignment brief or the team's final report.

## 1. Understanding and dividing the assignment

We first reviewed what Assignment 1 required and divided the work among the
three active members:

- Ridwan: JMeter load and stress testing, collecting evidence and reconciling
  results.
- Tze Han: selecting/downloading the models and operating the Mac that hosts
  Ollama and the triage service.
- Zong Han: requirements, workload modelling and prediction-related work.

We clarified that JMeter testing can be automated, although the complete
experiment still requires coordination between the JMeter machine and the
system-under-test machine. We also planned the work in phases so tasks could be
done in parallel before the final datasets were ready.

## 2. Branches, worktrees and pull requests

We created and worked with a Ridwan branch based on `main`. We discussed what a
Git worktree is, checked whether branches were up to date and handled the order
in which team branches should be merged.

Zong Han's changes were inspected and adjusted to match the newer `main`
changes before being merged. Tze Han's work was merged first, after which the
Ridwan branch was updated. We also prepared pull-request titles and descriptions
and removed an obsolete worktree after its pull request was accepted.

Later testing and adaptive stress-test work continued on the `attempt-2`
branch.

## 3. Datasets

We distinguished the two datasets used by the project:

- The golden dataset is used only for accuracy testing.
- The separate set of about 800 tickets is used for load and stress testing.

We generated/exported the load-test tickets separately so the golden data would
not be mixed into performance traffic. The JMeter input format and row ranges
were checked, and dry-run data was kept separate from reportable results.

## 4. Predictions and requirements

We reviewed `MODELS_BRIEF.md`, Zong Han's branch and the assignment brief to
check the workload model, requirements and predictions. We discussed who was
responsible for each part and whether the predictions were believable.

The prediction record was frozen before official testing. We later compared the
predictions with real observations and noted that latency predictions were
conservative, while the CPU-related predictions were broadly supported.

We also confirmed that estimates such as a possible saturation region must not
be reported as an observed limit unless the stress test actually demonstrates
one.

## 5. JMeter setup and dry run

We fixed the JMeter path on Ridwan's Mac after the original `$JMETER_BIN` path
was incorrect. A mock dry run was performed first, followed by a dry run against
Tze Han's real service over the network.

The first health check failed because the script expected different metadata.
After that was corrected, the dry run succeeded against both the 0.5B and 3B
models. We explained why a small number of dry-run samples could make the 3B
model appear faster than the 0.5B model: warm-up effects, random variation and
the tiny sample size meant it was not a reliable performance comparison.

The dry run was treated only as a check that the test setup worked, not as
reportable benchmark evidence.

## 6. Official load tests

The official arrangement used two Macs:

- Ridwan's Mac ran JMeter.
- Tze Han's Mac ran Docker, Ollama and the triage service.

We created instructions and scripts to run the load-test configurations and
repeat each configuration three times. Before each measured run, the SUT had to
be reset, warmed with invented text, checked through `/health`, and monitored.

After every run, two pieces of SUT evidence had to be copied through Git:

- The service log containing matching request IDs.
- A Docker resource-statistics CSV.

The JMeter-side script then matched the service records to the JTL samples and
reported missing records, status mismatches and client-versus-service latency.
We discovered that service logs alone were not enough because the assignment
also required resource evidence. This led to clearer commands for starting
`docker stats` with the correct per-run filename.

We also dealt with several practical issues during the runs:

- Runs taking longer than expected because the configured duration and drain
  periods were measured in minutes.
- Output not appearing in the expected VS Code terminal.
- Pulling evidence before typing `PULLED`.
- Accidentally typing `PULLED` before the files had actually been pulled.
- Splitting or renaming evidence when run numbers were confused.
- Resuming a suite from a particular run without repeating valid completed
  runs.
- Avoiding cache and database contamination between repeated runs.

The normal load-test matrix was eventually completed for the retained models.

## 7. Model-set changes

The candidates originally included `qwen2.5:3b`. The team later decided to drop
the 3B model. We removed its active references from predictions and supporting
documents while preserving the other frozen material.

The retained measured models were:

- `qwen2.5:0.5b`
- `llama3.2:1b-instruct-q4_K_M`
- `qwen2.5:7b`

We repeatedly checked that the model tags, health metadata and result folders
matched the model actually running on the SUT.

## 8. Accuracy testing

We confirmed that accuracy testing must use the golden set and should be run for
every retained model, not only the 7B model. We created an automated process so
each model could have separate evidence and reports before moving to the next
model.

The measured overall accuracies discussed were:

- 0.5B: 17.9%.
- 1B: 32.8%.
- 7B: 82.6%.

The 7B model was the only model to pass the overall 80% accuracy requirement,
but it did not pass every per-category recall requirement. In particular, Money
transfer recall was 66.7%, below the 70% target. Therefore, the 7B model remained
the best recommendation, but the report must state honestly that no tested
model passed every requirement.

We also clarified that an accuracy run at full speed cannot by itself establish
the saturation point because it is not a controlled open-loop stress test.

## 9. Stress testing

We created separate stress-test automation and corresponding commands for both
Macs. The original stress tests exercised the 7B model through a ramp and
constant-rate confirmation stages. They showed that the service could handle
the tested range, but they did not produce a clear saturation breakpoint.

We discussed whether Docker prevented saturation; it does not. The real limit
could still come from Ollama inference, CPU, memory, queues, timeouts or errors.
The issue was that the original offered rates were not high enough to reveal a
repeatable limit.

Because the deadline still allowed another attempt, we added an adaptive
stress-test process. It increases load automatically, keeps JTL, JMeter, service
and resource evidence, and confirms suspected overload so the result is backed
by logs rather than guesswork.

At the time this chat summary was rewritten, the adaptive test had been running
on the `attempt-2` branch. Any summary produced while that process is still
running must be treated as interim; the final conclusion should only be taken
after the script exits normally and all evidence is reconciled.

## 10. Documentation and slides

Throughout the chat, we checked whether the instructions, prediction record,
testing documentation and slides answered the assignment brief. We created or
updated Markdown instructions for:

- The overall testing plan.
- Dry runs.
- Official JMeter tests.
- Accuracy automation.
- Stress and adaptive stress testing.
- Evidence collection and reconciliation.

We also reviewed whether claims in the slides were supported by the collected
evidence. The main reporting rule established in the chat was to distinguish
clearly between:

- A measured result.
- A prediction made before testing.
- An analytical estimate made after testing.
- A limit that was not observed within the tested range.

## 11. Main conclusions from the chat

- JMeter testing can be automated, but the two machines still have to be
  coordinated for model selection, resets and evidence collection.
- One JMeter machine and one SUT machine are sufficient; a third Ollama machine
  is not required for comparing models.
- Accuracy uses the golden set; load and stress use the separate 800-ticket
  dataset.
- Every reportable run needs its JTL, JMeter log, matching service log and
  resource-statistics CSV.
- The SUT must be reset consistently between measured runs so repeated traffic
  is comparable.
- The 7B model gives the strongest accuracy but also has the highest latency.
- The 7B model is the best of the retained candidates, although it does not pass
  every category-recall requirement.
- The original stress test established only that capacity exceeded the tested
  range; it did not directly establish saturation.
- The adaptive stress test was added to find and confirm a defensible limit
  with supporting logs.
- Final slides and reports should never present predictions or estimates as if
  they were measured facts.

## 12. Current point in the conversation

The latest work is on the `attempt-2` branch. The adaptive 7B stress test was
still in progress when this summary was prepared. Its generated result files
should not be edited while it is running, and its final Markdown/JSON conclusion
should be used only after normal completion and evidence reconciliation.

This file itself is only a summary of the conversation with Codex. It does not
change the assignment methodology or the frozen experimental evidence.
