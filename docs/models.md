# Candidate models (Step 4, Slide 5)

**Owner:** Tze Han

## What the brief requires

- **3 to 5** candidate models from the [Ollama library](https://ollama.com/library).
- Spanning **at least two parameter size classes** (for example ~1B, ~3–4B, ~7–8B).
- **Pinned by exact tag and digest**, and the same pins reported with the results.
- **Justified:** why these models, and what trade-off they show (small = fast but less accurate; large = more accurate, slower, lower throughput).
- Licences acknowledged on Slide 12.

## Selected candidates

| Ollama tag | Size class | Quantisation | Purpose in the comparison |
|---|---:|---|---|
| `qwen2.5:0.5b` | 0.49B | Q4_K_M | Smallest and fastest Qwen baseline |
| `llama3.2:1b-instruct-q4_K_M` | 1.24B | Q4_K_M | A second family near the small-model class |
| `qwen2.5:7b` | 7.6B | Q4_K_M | Largest candidate that fits the SUT memory budget |

The 0.5B and 7B Qwen models show the speed, accuracy and throughput trade-off
between small and large models within one family. The 1B Llama candidate adds a
second family near the small-model class. All three use Q4_K_M, avoiding
quantisation as an extra uncontrolled variable, and together they span the
small and large parameter-size classes required by the brief.

## Choosing

Things worth weighing (and writing down as the justification):

- **Size classes:** at least one small model the CPU handles quickly, and at least one larger model that should be more accurate.
- **Same family at different sizes** (Qwen 0.5B / 7B) isolates the effect of size. **Different families near the small-model class** (Qwen and Llama) shows whether training matters as well as size.
- **Memory:** check the model fits in the SUT machine's Docker memory limit (see [setup.md](setup.md)).
- **Quantisation:** Ollama's default tags are usually 4-bit (`Q4_K_M`). Keep it the same across candidates, or justify the difference.
- **Instruction-tuned** models follow the "reply with one category" instruction much better than base models.
- **Licence:** check each model's licence allows commercial use by the client.

## Pinning

```bash
# With the stack running on the system-under-test machine:
python scripts/pull_models.py
```

This pulls every model and writes **`models/models.lock.json`** with each model's tag, **digest**, size, parameter count, quantisation and licence line, plus the Ollama version. Commit it. It's what goes on Slide 5.

Before every benchmark session:

```bash
python scripts/pull_models.py --check
```

This fails if any installed model no longer matches its pinned digest (for example, if someone re-pulled a tag that was updated upstream). The service also logs the digest with every request, so each result is traceable to an exact model.

## Measuring single-request latency (for predictions)

The prediction record needs an expected single-request latency per model **before** benchmarking. Estimate it from model size and the SUT hardware, or try a handful of **made-up** tickets. **Never use tickets from our rows (3000–3999) before the freeze.** The golden set in particular must not be seen by any model until it's committed.

## Prompt

The prompt is [`service/prompts/classify_v1.txt`](../service/prompts/classify_v1.txt). If the team wants to improve it (for example, adding the category definitions from the labelling protocol):

- Do it **before the freeze**, then don't change it. Every model is tested with the same prompt.
- Develop it on **made-up tickets or rows outside the golden set** (e.g. 3200–3999 from the full course CSV), **never on golden-set rows**. Tuning on the test set inflates the accuracy results.
- Save changes as a new file (`classify_v2.txt`) and set `PROMPT_FILE` in `.env`, so the version is logged.
