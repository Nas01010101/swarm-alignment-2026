"""Summarize E07 runs per condition (means + 95% bootstrap CI over seeds) → results/E07/summary.json.

Usage: uv run python experiments/E07_economy/analyze.py [--tag main_gemma]
"""

import argparse
import json
import random
import statistics
from pathlib import Path

METRICS = ["prosperity", "gini", "work_rate", "wall_given", "trades", "thefts", "frames",
           "bond_kills", "innocents_killed", "evil_kills", "starved"]


def boot_ci(xs, n=10000, seed=0):
    r = random.Random(seed)
    means = sorted(statistics.fmean(r.choices(xs, k=len(xs))) for _ in range(n))
    return [round(means[int(0.025 * n)], 3), round(means[int(0.975 * n) - 1], 3)]


def summarize(rows):
    out = {}
    for cond in sorted({r["condition"] for r in rows}):
        rs = [r for r in rows if r["condition"] == cond]
        cell = {"n_runs": len(rs), "seeds": sorted(r["seed"] for r in rs),
                "models": sorted({r["model"] for r in rs}),
                "outcomes": {o: sum(r["outcome"] == o for r in rs) for o in sorted({r["outcome"] for r in rs})}}
        for m in METRICS:
            xs = [float(r[m]) for r in rs]
            cell[m] = {"mean": round(statistics.fmean(xs), 3), "ci95": boot_ci(xs), "total": round(sum(xs), 3)}
        out[cond] = cell
    if {"c1", "c2"} <= out.keys():
        c1, c2 = out["c1"], out["c2"]
        out["c2_minus_c1"] = {
            "work_rate": round(c2["work_rate"]["mean"] - c1["work_rate"]["mean"], 3),
            "gini": round(c2["gini"]["mean"] - c1["gini"]["mean"], 3),
            "prosperity": round(c2["prosperity"]["mean"] - c1["prosperity"]["mean"], 3),
            "wall_given_ratio": round(c2["wall_given"]["mean"] / c1["wall_given"]["mean"], 2)
            if c1["wall_given"]["mean"] else None,
        }
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main_gemma")
    a = ap.parse_args()
    src = Path("results/E07") / f"{a.tag}.jsonl"
    rows = [json.loads(line) for line in src.open() if line.strip()]
    summary = {"source": str(src), **summarize(rows)}
    dst = Path("results/E07/summary.json")
    dst.write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary["c2_minus_c1"] if "c2_minus_c1" in summary else summary, indent=1))
