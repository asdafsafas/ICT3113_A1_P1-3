---
type: concept
title: "Labelling Protocol"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
  - golden-set
status: mature
related:
  - "[[Golden Test Set]]"
  - "[[Ticket Categories]]"
sources:
  - "[[Golden Set Summary]]"
complexity: intermediate
domain: "evaluation"
aliases:
  - "PROTOCOL.md"
  - "protocol.json"
---

# Labelling Protocol

Source of truth: `labeler/protocol.json`, exported to `golden/PROTOCOL.md` by `scripts/export_protocol.py` (`--check` passes). Current version: **v0.3**.

**Tie-break (v0.1):** label the product or company the complaint is *mainly* about, not everything it mentions.

## Revisions

| Version | Date | Trigger | Main rules |
|---|---|---|---|
| v0.1 | 2026-09-23 | n/a | Initial definitions + tie-break |
| v0.2 | 2026-10-03 | Group A, 16 rows | Student loans → Consumer loan. **Credit reporting vs Debt collection is decided by who the complaint is against.** A dispute with a bureau is Credit reporting; a dispute with the lender is the lender's product. Fees on your own card are not Debt collection. Bank-account fraud is Bank account, not Money transfer. Label the product, not the company type. |
| v0.3 | 2026-10-03 | Group B, 12 rows | Prepaid cards and crypto exchanges → Money transfer. Scams go to the product the money left through. A loan of unstated type → Consumer loan. **EXCLUDE** when no product is identifiable. |

Definitions for each category: [[Ticket Categories]].

> [!key-insight] The model never sees these rules
> `classify_v1.txt` gives the 7 category **names only**. The v0.2/v0.3 edge-case rules that settled human disagreements are not available to the models. The [[Prediction Record]] blamed this for the expected Debt collection errors. For the 7B, the measured weak spot turned out to be **Money transfer** (66.7%). Debt collection reached 82.4%.
