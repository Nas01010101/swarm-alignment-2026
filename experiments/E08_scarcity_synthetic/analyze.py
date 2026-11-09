"""E08 analysis: cell means + hypothesis checks exactly as registered in prereg.md → results/E08/summary.json."""

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

LOW, HIGH = (0.4, 0.6, 0.8), (1.0, 1.2, 1.5)
CELL_METRICS = ["hack_T", "hack_cap_T", "hack_com_T", "need_met_all", "need_met_last5", "real_production",
                "solvent_all", "infeasible_rounds", "shortage_rounds", "inflation", "mean_lam", "stock_T"]


def boot(xs, n=5000, seed=0):
    r = random.Random(seed)
    m = sorted(statistics.fmean(r.choices(xs, k=len(xs))) for _ in range(n))
    return [round(statistics.fmean(xs), 4), round(m[int(0.025 * n)], 4), round(m[int(0.975 * n) - 1], 4)]


def main(rows):
    cells = defaultdict(list)
    for r in rows:
        cells[(r["rho"], r["topology"], r["governance"])].append(r)
    table = {}
    for (rho, topo, gov), rs in sorted(cells.items()):
        table[f"{rho}|{topo}|{gov}"] = {"n": len(rs), **{m: round(statistics.fmean(float(x[m] or 0) for x in rs), 4)
                                                       for m in CELL_METRICS}}
    topos = sorted({r["topology"] for r in rows})
    by = {(r["rho"], r["topology"], r["governance"], r["seed"]): r for r in rows}
    seeds = sorted({r["seed"] for r in rows})
    c = lambda rho, t, g, m: table[f"{rho}|{t}|{g}"][m]  # noqa: E731

    h1_low = {f"{rho}|{t}": c(rho, t, "unfiltered", "hack_cap_T") for rho in LOW for t in topos}
    h1_high = {f"{rho}|{t}": c(rho, t, "unfiltered", "hack_T") for rho in HIGH for t in topos}
    h1 = all(v >= 0.5 for v in h1_low.values()) and all(v <= 0.10 for v in h1_high.values())

    h2 = {}
    for rho in LOW:
        d = [by[(rho, t, "unfiltered", s)]["hack_cap_T"] - by[(rho, t, "unfiltered", s)]["hack_com_T"]
             for t in topos for s in seeds]
        h2[str(rho)] = boot(d)
    h2_ok = all(v[1] > 0 for v in h2.values())

    dc = [r for r in rows if r["governance"] == "dcbf_gateway"]
    feas = [r for r in dc if r["infeasible_rounds"] == 0]
    h3_sound = sum(r["solvent_all"] for r in feas)
    infeas_by_rho = {str(rho): sum(r["infeasible_rounds"] > 0 for r in dc if r["rho"] == rho) for rho in LOW + HIGH}
    h3 = h3_sound == len(feas) and all(infeas_by_rho[str(r)] == 0 for r in HIGH)

    h4_cells = {f"{rho}|{t}": c(rho, t, "dcbf_gateway", "hack_T") for rho in LOW + HIGH for t in topos}
    h4 = all(v <= 0.10 for v in h4_cells.values())

    h5 = {}
    for rho in LOW:
        out = {}
        for m in ("need_met_all", "real_production"):
            d = [by[(rho, t, "dcbf_gateway", s)][m] - by[(rho, t, "unfiltered", s)][m] for t in topos for s in seeds]
            out[m] = boot(d)
        h5[str(rho)] = out
    h5_ok = all(v[m][1] > 0 for v in h5.values() for m in v)

    return {
        "source": "results/E08/sweep.jsonl", "episodes": len(rows),
        "hypotheses": {
            "H1_supported": h1, "H1_cap_hack_T_unfiltered_low_rho": h1_low, "H1_hack_T_unfiltered_high_rho": h1_high,
            "H2_supported": h2_ok, "H2_cap_minus_com_hack_T_unfiltered": h2,
            "H3_supported": h3, "H3_feasible_dcbf_runs": len(feas), "H3_feasible_dcbf_runs_solvent": h3_sound,
            "H3_dcbf_runs_with_infeasible_rounds_by_rho": infeas_by_rho,
            "H4_supported": h4, "H4_hack_T_dcbf": h4_cells,
            "H5_supported": h5_ok, "H5_dcbf_minus_unfiltered_mean_lo_hi": h5,
        },
        "cells": table,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="sweep")
    a = ap.parse_args()
    rows = [json.loads(line) for line in open(f"results/E08/{a.tag}.jsonl")]
    s = main(rows)
    Path("results/E08/summary.json").write_text(json.dumps(s, indent=1) + "\n")
    print(json.dumps(s["hypotheses"], indent=1))
