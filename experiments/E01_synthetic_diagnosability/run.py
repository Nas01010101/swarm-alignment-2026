"""E01: where does witness-free attribution break? Sweep topology x liar count x
collusion on synthetic swarms; no LLM, $0. Prereg: ./prereg.md.

    uv run python experiments/E01_synthetic_diagnosability/run.py --seeds 20
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from swarm import diagnose, naive_count, synthetic_swarm, tamper  # noqa: E402


def one(n, topo, k, collude, seed, rate, rounds):
    logs = synthetic_swarm(n, topo, rounds, seed)
    rng = random.Random(seed)
    liars = set(rng.sample(sorted(logs), k)) if k else set()
    bad, truth = tamper(logs, liars, rate, seed, collude=collude)
    v = diagnose(bad, max_liars=max(k + 2, 3))
    naive = naive_count(bad)
    return {
        "n": n, "topology": topo, "liars": k, "collude": collude, "seed": seed,
        "status": v.status,
        # exact = named precisely the liars (for k=0: correctly reported clean)
        "exact": v.status in ("identified", "clean") and v.accused == truth.liars,
        "false_accusations": len(v.accused - truth.liars),
        "missed": len(truth.liars - v.accused),
        "naive_false_accusations": len(naive - truth.liars),
        "n_tampered": len(truth.tampered), "n_discrepancies": len(v.discrepancies),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--rate", type=float, default=0.2)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--out", default=str(ROOT / "results/E01/sweep.jsonl"))
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [one(a.n, topo, k, c, s, a.rate, a.rounds)
            for topo in ("complete", "erdos", "ring", "star")
            for k in range(0, 5)
            for c in (False, True)
            for s in range(a.seeds)]
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    # Summary table: exact-identification rate per cell.
    cells: dict = {}
    for r in rows:
        cells.setdefault((r["topology"], r["liars"], r["collude"]), []).append(r)
    print(f"{'topology':9} k collude exact  insuff  falseAcc naiveFalseAcc")
    for (t, k, c), rs in sorted(cells.items()):
        m = len(rs)
        print(f"{t:9} {k} {str(c):7} {sum(r['exact'] for r in rs)/m:5.2f} "
              f"{sum(r['status']=='insufficient_evidence' for r in rs)/m:7.2f} "
              f"{sum(r['false_accusations'] for r in rs)/m:8.2f} "
              f"{sum(r['naive_false_accusations'] for r in rs)/m:8.2f}")
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
