"""Ticket-length distribution of the exact 1,000 tickets committed in this repo.

    python3 scripts/ticket_lengths.py

Rows 3000-3199 come from ict3113_ticket_P1-3.xlsx and rows 3200-3999 from
loadtest/data/load-test-tickets.csv. Lengths are counted as stored, with no normalisation.
"""

from common import REPO, load_narratives, md_table, percentile

P = (5, 25, 50, 75, 95, 99)


def main():
    pool = {r: t for r, t in load_narratives(REPO / "ict3113_ticket_P1-3.xlsx").items() if 3000 <= r <= 3199}
    load = {r: t for r, t in load_narratives(REPO / "loadtest" / "data" / "load-test-tickets.csv").items() if 3200 <= r <= 3999}
    tickets = {**pool, **load}
    assert sorted(tickets) == list(range(3000, 4000)), "expected exactly rows 3000-3999"

    def rows(ts):
        w = [len(t.split()) for t in ts]
        c = [len(t) for t in ts]
        return [["Words"] + [percentile(w, p) for p in P] + [max(w)],
                ["Characters"] + [percentile(c, p) for p in P] + [max(c)]]

    head = [""] + [f"p{p}" for p in P] + ["max"]
    print(f"All 1,000 committed tickets (rows 3000-3999):\n{md_table(head, rows(tickets.values()))}\n")
    print(f"Golden pool only (rows 3000-3199, {len(pool)} tickets):\n{md_table(head, rows(pool.values()))}\n")
    print(f"Load-test tickets only (rows 3200-3999, {len(load)} tickets):\n{md_table(head, rows(load.values()))}\n")
    print(f"Tickets containing \\r: {sum(chr(13) in t for t in tickets.values())}; "
          f"containing line breaks: {sum(chr(10) in t for t in tickets.values())}")


if __name__ == "__main__":
    main()
