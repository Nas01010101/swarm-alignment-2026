"""E01 exploratory (not pre-registered): min-cover `diagnose` vs t-bounded `diagnose_bounded` on the
same synthetic sweep as run.py (same generator, seeds and tampering). t = k (bound equals the true
number of liars) and t = k + 1 (a loose bound). $0, seconds.

    uv run python experiments/E01_synthetic_diagnosability/bounded.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from swarm import diagnose, diagnose_bounded, synthetic_swarm, tamper  # noqa: E402


def one(n, topo, k, collude, seed, rate, rounds):
    logs = synthetic_swarm(n, topo, rounds, seed)
    rng = random.Random(seed)
    liars = set(rng.sample(sorted(logs), k)) if k else set()
    bad, truth = tamper(logs, liars, rate, seed, collude=collude)
    row = {"n": n, "topology": topo, "liars": k, "collude": collude, "seed": seed}
    dets = {"mincover": diagnose(bad, max_liars=max(k + 2, 3))}
    if k:
        dets |= {"bounded_t=k": diagnose_bounded(bad, k), "bounded_t=k+1": diagnose_bounded(bad, k + 1)}
    for name, v in dets.items():
        row[name] = {"status": v.status, "false_accusations": len(v.accused - truth.liars),
                     "liars_named": len(v.accused & truth.liars),
                     "exact": v.status in ("identified", "clean") and v.accused == truth.liars}
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--rate", type=float, default=0.2)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--out", default=str(ROOT / "results/E01"))
    a = ap.parse_args()
    rows = [one(a.n, t, k, c, s, a.rate, a.rounds) for t in ("complete", "erdos", "ring", "star")
            for k in range(1, 5) for c in (False, True) for s in range(a.seeds)]
    out = Path(a.out)
    (out / "bounded.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    cells = defaultdict(list)
    for r in rows:
        cells[(r["topology"], r["liars"])].append(r)  # pooled over collusion
    summary = []
    for (t, k), rs in sorted(cells.items()):
        s = {"topology": t, "liars": k, "runs": len(rs)}
        for d in ("mincover", "bounded_t=k", "bounded_t=k+1"):
            s[d] = {"exact": round(sum(r[d]["exact"] for r in rs) / len(rs), 3),
                    "runs_with_false_accusation": round(sum(r[d]["false_accusations"] > 0 for r in rs) / len(rs), 3),
                    "liar_recall": round(sum(r[d]["liars_named"] for r in rs) / (k * len(rs)), 3)}
        summary.append(s)
    tot = {d: sum(r[d]["false_accusations"] > 0 for r in rows) for d in ("mincover", "bounded_t=k", "bounded_t=k+1")}
    (out / "bounded_summary.json").write_text(json.dumps({"runs": len(rows), "runs_with_false_accusation": tot,
                                                          "cells": summary}, indent=1))
    print("runs", len(rows), "runs with >=1 false accusation:", tot)
    print(f"{'topology':9} k  | mincover exact FA-runs recall | t=k exact FA-runs recall | t=k+1 recall")
    for s in summary:
        m, b, b1 = s["mincover"], s["bounded_t=k"], s["bounded_t=k+1"]
        print(f"{s['topology']:9} {s['liars']}  | {m['exact']:.2f} {m['runs_with_false_accusation']:.2f} "
              f"{m['liar_recall']:.2f} | {b['exact']:.2f} {b['runs_with_false_accusation']:.2f} "
              f"{b['liar_recall']:.2f} | {b1['liar_recall']:.2f}")


if __name__ == "__main__":
    main()
