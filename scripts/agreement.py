"""Compare annotators' label sheets: agreement statistics and a resolution sheet per labelling group.

    python scripts/agreement.py \
        --group golden/labels/labels_Zong_Han.csv golden/labels/labels_Ridwan.csv \
        --group golden/labels/labels_Tze_Han.csv golden/labels/labels_Kannan.csv golden/labels/labels_Natalie.csv

A group is the people who labelled the same rows (two or more). For each group:
- Cohen's kappa for every pair of annotators in it;
- Fleiss' kappa for the whole group (equals Cohen-style chance correction across 3+ raters);
- golden/pairs/group_<names>.csv with every row all of them labelled.
Rows where everyone agrees get final_label pre-filled; the team fills in final_label (and a
resolution note) for every disagreement, then runs build_golden.py.
Also writes golden/agreement_summary.md.
"""

import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path

from common import NONE_LABEL, REPO, md_table, read_csv, write_csv

OUT_DIR = REPO / "golden" / "pairs"


def annotator(path):
    return Path(path).stem.removeprefix("labels_")


def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss_kappa(items):
    """items: list of label lists, one per ticket, each with the same number of raters."""
    n, m = len(items), len(items[0])
    counts = [Counter(labels) for labels in items]
    p_i = [(sum(c * c for c in cnt.values()) - m) / (m * (m - 1)) for cnt in counts]
    p_bar = sum(p_i) / n
    totals = Counter()
    for cnt in counts:
        totals.update(cnt)
    pe = sum((t / (n * m)) ** 2 for t in totals.values())
    return p_bar, (p_bar - pe) / (1 - pe) if pe < 1 else 1.0


def compare(paths, force):
    names = [annotator(p) for p in paths]
    if len(set(names)) != len(names):
        raise SystemExit(f"Duplicate annotator in group: {names}")
    sheets = [{int(r["row"]): r for r in read_csv(p)} for p in paths]
    rows = sorted(set.intersection(*(set(s) for s in sheets)))
    partial = sorted(set.union(*(set(s) for s in sheets)) - set(rows))
    if not rows:
        raise SystemExit(f"{', '.join(names)} have no rows in common")

    out_path = OUT_DIR / f"group_{'_'.join(names)}.csv"
    if out_path.exists() and not force:
        raise SystemExit(f"{out_path} already exists (it may hold your resolutions). Use --force to overwrite.")

    out = []
    for row in rows:
        labels = [s[row]["label"] for s in sheets]
        top, top_n = Counter(labels).most_common(1)[0]
        unanimous = top_n == len(labels)
        rec = {"row": row}
        for name, s in zip(names, sheets):
            rec[f"{name}_label"] = s[row]["label"]
            rec[f"{name}_also"] = s[row].get("secondary_label", "")
            rec[f"{name}_reasoning"] = s[row].get("reasoning", "")
        rec.update({
            "agree": "Y" if unanimous else "N",
            # Majority is shown for reference only; a majority is not a resolution.
            "majority": f"{top} ({top_n}/{len(labels)})" if len(labels) > 2 and not unanimous and top_n > 1 else "",
            # Unanimous "None / unclear" still needs a team decision, so it is left blank.
            "final_label": top if unanimous and top != NONE_LABEL else "",
            "resolution_note": "",
            "protocol_change": "",
        })
        out.append(rec)
    write_csv(out_path, out, list(out[0].keys()))

    by_rater = [[s[r]["label"] for r in rows] for s in sheets]
    pairwise = []
    for (i, a), (j, b) in combinations(enumerate(names), 2):
        po, k = cohen_kappa(by_rater[i], by_rater[j])
        pairwise.append((f"{a} / {b}", po, k))
    fleiss = fleiss_kappa([[s[r]["label"] for s in sheets] for r in rows]) if len(names) > 2 else None
    disagreements = Counter(tuple(sorted(Counter(r[f"{n}_label"] for n in names).elements()))
                            for r in out if r["agree"] == "N")
    return {"group": " / ".join(names), "names": names, "n": len(rows),
            "unanimous": sum(r["agree"] == "Y" for r in out), "pairwise": pairwise, "fleiss": fleiss,
            "partial": partial, "disagreements": disagreements, "out": out_path}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", "--pair", nargs="+", action="append", required=True, metavar="LABELS.csv",
                    help="label sheets of everyone who labelled the same rows (2 or more)")
    ap.add_argument("--force", action="store_true", help="overwrite existing resolution sheets")
    args = ap.parse_args()
    if any(len(g) < 2 for g in args.group):
        ap.error("each --group needs at least two label sheets")

    results = [compare(g, args.force) for g in args.group]

    lines = ["# Inter-annotator agreement", "",
             "Labels compared over each group's commonly labelled rows (8 labels, including None / unclear).", "",
             "## Per group", "",
             md_table(["Group", "Annotators", "Tickets", "All agree", "Any disagreement", "Fleiss' kappa"],
                      [[r["group"], len(r["names"]), r["n"], r["unanimous"], r["n"] - r["unanimous"],
                        f"{r['fleiss'][1]:.3f}" if r["fleiss"] else "n/a (2 annotators: see Cohen's)"]
                       for r in results]), "",
             "## Every pair of annotators (Cohen's kappa)", "",
             md_table(["Pair", "Observed agreement", "Cohen's kappa"],
                      [[p, f"{po:.1%}", f"{k:.3f}"] for r in results for p, po, k in r["pairwise"]]), ""]
    for r in results:
        lines += [f"## {r['group']}: most common disagreements", ""]
        lines += [md_table(["Labels given", "Tickets"],
                           [[" vs ".join(labels), n] for labels, n in r["disagreements"].most_common(10)])
                  if r["disagreements"] else "None.", ""]
        if r["partial"]:
            lines += [f"Rows not labelled by everyone in the group (excluded): {', '.join(map(str, r['partial']))}", ""]
    summary = REPO / "golden" / "agreement_summary.md"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    for r in results:
        print(f"Wrote {r['out'].relative_to(REPO)}")
    print(f"Wrote {summary.relative_to(REPO)}")


if __name__ == "__main__":
    main()
