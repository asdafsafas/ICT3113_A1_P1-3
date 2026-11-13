---
type: source
title: "Golden Set Summary"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - source
  - golden-set
status: mature
related:
  - "[[Golden Test Set]]"
  - "[[Labelling Protocol]]"
  - "[[Inter-Annotator Agreement]]"
sources:
  - "golden/SUMMARY.md"
  - "golden/agreement_summary.md"
  - "labeler/protocol.json"
source_type: data
author: "Team P1-3"
date_published: 2026-10-06
url: ""
confidence: high
key_claims:
  - "195 golden tickets (rows 3000-3199) plus 5 excluded"
  - "Group A Cohen's kappa 0.735; Group B Fleiss' kappa 0.778"
  - "49 disagreements, all resolved; 37 cite a protocol rule"
  - "Protocol revised v0.1 -> v0.2 -> v0.3"
---

# Golden Set Summary (Slide 6)

Sources: `golden/SUMMARY.md`, `golden/agreement_summary.md`, `labeler/protocol.json`.

## Package
- `golden/golden_set.csv`: **195 tickets**, rows 3000–3199.
- `golden/excluded.csv`: **5 excluded** (no identifiable product: 3102, 3181, 3193 and two others).
- 5 independent label sheets committed in `39d4cc2` before any resolution. The agreement statistic and blank resolution sheets were committed in `50fbdbb`.
- `golden/pairs/`: 49 of 49 disagreements have a final label and a resolution note.

## Agreement (see [[Inter-Annotator Agreement]])

| Group | Rows | Labellers | All agree | Statistic |
|---|---|---|---|---|
| A | 3000–3099 | [[Zong Han]], [[Ridwan]] | 78 | Cohen's κ **0.735** |
| B | 3100–3199 | [[Tze Han]], [[Kannan]], [[Natalie]] | 73 | Fleiss' κ **0.778** (pairs 0.826 / 0.763 / 0.745) |

Each labeller matched the final label on 83–96% of their tickets.

## Disagreements (49)
- 44 resolved to a category, 5 excluded.
- Group B: 24 two-to-one splits (majority kept in 18) and 3 three-way splits.
- Most common confusions: A, **Credit reporting vs Debt collection** (4); B, **Bank account vs Money transfer** (6).
- Data-quality finding: two of Zong Han's notes were saved to the wrong rows (3020→3018, 3086→3085). Those rows were re-decided, and the raw sheet was left unedited.

## Category counts in the golden set (derived)
Derived from the recall figures in [[Accuracy Results]]: Credit reporting 42 · Bank account 37 · Money transfer 30 · Mortgage 27 · Consumer loan 24 · Credit card 18 · Debt collection 17 = 195.

## Worked examples
1. **3025 vs 3072**: who is the complaint against? A dispute with the bureau → Credit reporting; the collector never gave proof → Debt collection.
2. **3141**: a rule overturned the 2-of-3 majority. A repossession dispute with Ally (the lender) → Consumer loan.
3. **3193**: a supervisor hung up and no product is mentioned → excluded.

> [!note] Labels are the team's own (confirmed 2026-11-13)
> Every label and every resolution was made by team members. An earlier AI-assistance line in `golden/SUMMARY.md` has been removed; the file now says resolutions were "redone and agreed upon as a group". The item is closed in `slides/pending-changes.md`, and Slide 12's wording stands.
