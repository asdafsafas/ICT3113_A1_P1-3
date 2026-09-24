# Golden set: from label sheets to frozen golden set (Step 1, Slide 6)

**Owner:** Zong Han · Labelling instructions for everyone are in the [main README](../README.md).

## 1. Collect the label sheets

Once **everyone in a group** has finished (Group A: Zong Han, Ridwan; Group B: Tze Han, Kannan, Natalie), they send their `labels_<Name>.csv` to Zong Han, who copies them into `golden/labels/` and commits:

```bash
git add golden/labels/labels_*.csv
git commit -m "Add independent label sheets (group A)"
```

These are the **independent label sheets** the brief asks for. Commit them **as they were sent**, before any discussion changes anything.

## 2. Agreement statistic

```bash
python scripts/agreement.py \
  --group golden/labels/labels_Zong_Han.csv golden/labels/labels_Ridwan.csv \
  --group golden/labels/labels_Tze_Han.csv golden/labels/labels_Kannan.csv golden/labels/labels_Natalie.csv
```

This prints and saves `golden/agreement_summary.md`:

- **Cohen's kappa** for every pair of labellers (Group A has one pair; Group B has three: Tze Han/Kannan, Tze Han/Natalie, Kannan/Natalie);
- **Fleiss' kappa** for Group B as a whole (the standard agreement statistic for three or more labellers);
- how many tickets each group fully agreed on, and the most common disagreements.

It also writes one **resolution sheet** per group: `golden/pairs/group_<names>.csv`.

For reference, kappa is often read as: below 0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, above 0.80 almost perfect. **Don't aim for perfect.** The brief says implausibly perfect agreement with no recorded resolutions will be examined closely.

Commit the summary and the untouched resolution sheets before resolving.

## 3. Resolve every disagreement

Open your group's sheet in Excel. Each row shows every labeller's label, "also fits" choice and reasoning.

- Rows where **everyone agreed** already have `final_label` filled in. (Agreed "None / unclear" rows are left blank, because they still need a decision.)
- In Group B, `majority` shows a 2-to-1 split (e.g. `Credit reporting (2/3)`). It's a hint, not a decision: the row still needs discussing, a `final_label` and a note.
- For each **disagreement** (`agree = N`), discuss it, then fill in:
  - `final_label`: one of the 7 categories, **or `EXCLUDE`** to drop the ticket from the golden set
  - `resolution_note`: why, in one sentence (**required** for every disagreement)
  - `protocol_change`: the rule you added or changed, if the disagreement revealed a gap (e.g. "v0.2: student loans → Consumer loan")
- If the group can't agree, ask a **neutral tie-breaker** who hasn't labelled those rows: **Natalie** for Group A, and someone from Group A for Group B. Note it in `resolution_note`.

Save as CSV (keep the file name). If Excel asks about the format, keep CSV.

## 4. Update the protocol

For each `protocol_change`, update [`labeler/protocol.json`](../labeler/protocol.json):

- bump `version` (e.g. `"v0.2 (after round 1 disagreements)"`);
- add the rule to `edge_cases`, e.g. `{"rule": "Student loans (Navient, Nelnet…) → Consumer loan", "example_rows": [3030]}`, or reword a definition;
- add an entry to `revisions`: `{"version": "v0.2", "date": "2026-09-28", "change": "...", "triggered_by_rows": [3030, 3044]}`.

Then regenerate the readable protocol and commit both files together, so the history shows every revision:

```bash
python scripts/export_protocol.py
git add labeler/protocol.json golden/PROTOCOL.md
git commit -m "Protocol v0.2: ..."
```

[`golden/PROTOCOL.md`](../golden/PROTOCOL.md) is the **labelling protocol with its revisions** that the brief asks us to submit. Never edit it by hand. `python scripts/export_protocol.py --check` tells you if it's out of date.

## 5. Build the golden set

```bash
python scripts/build_golden.py
```

This checks that every row has a valid `final_label` and every disagreement has a note, then writes:

- `golden/golden_set.csv`: `row,label` for every kept ticket (the brief requires **150–200**)
- `golden/excluded.csv`: excluded rows and why

It refuses to build while anything is missing.

## 6. Freeze (before any model sees the tickets)

Commit the golden set **together with the finished prediction record**, then tag the commit:

```bash
git add golden/ planning/prediction-record.md models/models.lock.json service/prompts/
git commit -m "Freeze golden set and prediction record"
git tag -a freeze -m "Golden set and predictions frozen before first benchmark"
git push && git push origin freeze
```

After this, **don't edit** `golden/golden_set.csv` or `planning/prediction-record.md`. The tag and commit date are our evidence that labels and predictions came before measurements.

## Slide 6 checklist

- Protocol summary and its revisions (v0.1 → v0.2 …), from `golden/PROTOCOL.md`
- Cohen's kappa per pair, Fleiss' kappa for Group B
- Number of disagreements, and how they were resolved (discussion / tie-breaker / excluded)
- One or two example disagreements and their resolution
