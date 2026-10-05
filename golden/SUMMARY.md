# Golden set summary (Slide 6)

Everything here can be traced to files in `golden/`. The protocol and its revisions are in [PROTOCOL.md](PROTOCOL.md), the statistics in [agreement_summary.md](agreement_summary.md), and every disagreement with its resolution in [pairs/](pairs/).

## Package checklist (brief: Deliverables)

| Item | File | Status |
|---|---|---|
| Golden test set, 150–200 tickets by row number | [golden_set.csv](golden_set.csv) | ✅ 195 tickets (rows 3000–3199), all labels valid, no duplicates |
| Excluded tickets and reasons | [excluded.csv](excluded.csv) | ✅ 5. Golden + excluded covers all 200 labelled rows. |
| Labelling protocol with its revisions | [PROTOCOL.md](PROTOCOL.md) (generated from `labeler/protocol.json`) | ✅ v0.1 → v0.2 → v0.3; `export_protocol.py --check` passes |
| Independent label sheets, unedited | [labels/](labels/) | ✅ 5 sheets, committed in `39d4cc2` before any resolution |
| Agreement statistic | [agreement_summary.md](agreement_summary.md) | ✅ committed with the blank resolution sheets in `50fbdbb` |
| Every disagreement resolved and recorded | [pairs/](pairs/) | ✅ 49 of 49 have a final label and a resolution note |
| Prediction record committed with the golden set | `planning/prediction-record.md` | ⬜ needed before the `freeze` tag |

## Agreement

| Group | Rows | Labellers | All agree | Disagreements | Statistic |
|---|---|---|---|---|---|
| A | 3000–3099 | Zong Han, Ridwan | 78 | 22 | Cohen's κ = **0.735** (substantial) |
| B | 3100–3199 | Tze Han, Kannan, Natalie | 73 | 27 | Fleiss' κ = **0.778** (substantial). Pairwise Cohen's κ: 0.826 Tze Han/Kannan, 0.763 Tze Han/Natalie, 0.745 Kannan/Natalie |

Agreement is high but not perfect, as the brief expects. Each labeller matched the final golden label on 83–96% of their tickets.

## How the 49 disagreements were resolved

| Outcome | Group A | Group B | Total |
|---|---|---|---|
| Resolved to one of the 7 categories | 22 | 22 | 44 |
| Excluded (product cannot be identified from the text) | 0 | 5 | 5 |
| **Total** | **22** | **27** | **49** |

- **Group B** had 24 two-to-one splits and 3 three-way splits. The majority label was kept in 18 of the 24 two-to-one splits. In the other 6, a protocol rule decided the ticket against the majority (for example 3141, 3194) or the ticket was excluded (3102, 3181, 3193).
- **37 resolutions** cite the protocol rule they applied or added (`protocol_change` column).
- **Most common disagreements:**
  - Group A: Credit reporting vs Debt collection (4 tickets), plus three pairs at 3 tickets each: Bank account vs Money transfer, Bank account vs Mortgage, and Consumer loan vs Credit reporting.
  - Group B: Bank account vs Money transfer (6 tickets across its split patterns).
- **Data-quality finding:** two of Zong Han's reasoning notes had been saved to the wrong rows (the note on 3020 belongs to 3018; the note on 3086 belongs to 3085). Both rows were re-decided from the ticket text, and the raw sheet was left unedited.

Resolution drafts were prepared with AI assistance and accepted by the team on 5 Oct 2026. *(Edit this line if the groups revise any resolution.)*

## Protocol revisions

| Version | Triggered by | Main changes |
|---|---|---|
| v0.1 | n/a | Initial definitions and tie-break rule ("label the product the complaint is mainly about") |
| v0.2 | Group A, 16 rows | Student loans → Consumer loan. New rules: Credit reporting vs Debt collection decided by **who the complaint is against**; a dispute with a bureau is Credit reporting, but a dispute with the lender is the lender's product; fees on your own card are not Debt collection; bank-account fraud is Bank account, not Money transfer; label the product, not the company type |
| v0.3 | Group B, 12 rows | Prepaid cards and crypto exchanges → Money transfer. New rules: scams go to the product the money left through; a loan of unstated type is Consumer loan; when to **EXCLUDE** (no identifiable product) |

## Examples for the slide

1. **Same situation, different answer: who is the complaint against? (3025 vs 3072, rule v0.2).** Both tickets are about a collection account appearing on a credit report.
   - In **3025** the person demands that *TransUnion and the other bureaus* delete it → **Credit reporting**.
   - In **3072** the complaint is that *Midland*, the collector, never gave notice or proof of the debt → **Debt collection**.
   - Group A had split on exactly this, and the rule now decides it.
2. **A rule overturning the majority (3141).** Two of three labellers chose Credit reporting, because the person wants a repossession removed from their credit report. The request is made to Ally Financial, the auto lender, not to a bureau. Under v0.2's "dispute with the lender → the lender's product" rule it became **Consumer loan**.
3. **An exclusion (3193).** The whole complaint is that a Wells Fargo supervisor hung up. No product is mentioned, so no label could be defended, and it was **excluded** under v0.3.
