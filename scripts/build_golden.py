"""Build golden/golden_set.csv from the resolved pair sheets in golden/pairs/.

    python scripts/build_golden.py

Every row's final_label must be one of the seven categories, or EXCLUDE to leave the
ticket out of the golden set (give the reason in resolution_note).
"""

import argparse
from collections import Counter

from common import CATEGORIES, REPO, md_table, read_csv, write_csv

PAIRS = REPO / "golden" / "pairs"


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    sheets = sorted(PAIRS.glob("group_*.csv"))
    if not sheets:
        raise SystemExit(f"No resolution sheets in {PAIRS}. Run scripts/agreement.py first.")

    golden, excluded, problems, seen = [], [], [], set()
    for sheet in sheets:
        for r in read_csv(sheet):
            row, label = int(r["row"]), r["final_label"].strip()
            where = f"{sheet.name} row {row}"
            if row in seen:
                problems.append(f"{where}: row appears in more than one group sheet")
            seen.add(row)
            if label.upper() == "EXCLUDE":
                excluded.append({"row": row, "reason": r.get("resolution_note", "")})
            elif label in CATEGORIES:
                golden.append({"row": row, "label": label})
            elif not label:
                problems.append(f"{where}: final_label is blank")
            else:
                problems.append(f"{where}: {label!r} is not one of the seven categories or EXCLUDE")
            if r.get("agree") == "N" and not r.get("resolution_note", "").strip():
                problems.append(f"{where}: disagreement has no resolution_note")

    if problems:
        print("Not built. Fix these first:\n  " + "\n  ".join(problems))
        raise SystemExit(1)

    golden.sort(key=lambda g: g["row"])
    write_csv(REPO / "golden" / "golden_set.csv", golden, ["row", "label"])
    write_csv(REPO / "golden" / "excluded.csv", sorted(excluded, key=lambda e: e["row"]), ["row", "reason"])

    counts = Counter(g["label"] for g in golden)
    print(md_table(["Category", "Tickets"], [[c, counts.get(c, 0)] for c in CATEGORIES] + [["**Total**", len(golden)]]))
    print(f"\nExcluded: {len(excluded)}. Wrote golden/golden_set.csv and golden/excluded.csv")
    if not 150 <= len(golden) <= 200:
        print(f"WARNING: the brief requires 150-200 golden tickets; you have {len(golden)}.")
    print("\nNext: commit golden/ and planning/prediction-record.md, then tag the commit (see docs/golden-set.md).")


if __name__ == "__main__":
    main()
