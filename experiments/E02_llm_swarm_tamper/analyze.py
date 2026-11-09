"""Aggregate E02 rows into per-cell rates with Wilson 95% intervals.

    uv run python experiments/E02_llm_swarm_tamper/analyze.py --out results/E02
Writes <out>/summary.json and prints a table.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATES = ["detected", "localized", "exact", "covert_hidden", "minimal_edit", "liar_parse_ok", "liar_edited",
         "judge_exact", "judge_flagged", "judge_parse_ok"]
MEANS = ["n_suspects", "false_accusations", "naive_false_accusations", "judge_false_accusations"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, round(c - h, 3)), min(1.0, round(c + h, 3)))


def receiver_split(out: Path, llm_rows, all_rows, rate) -> dict:
    """k=2 rows split by who the two covert messages went to: distinct honest receivers,
    the same honest receiver (framing case), or one liar targeting the other (collusion blind spot).
    Needs <out>/swarms.json (exported from raw/swarms/*.json, which is gitignored)."""
    meta_p = out / "swarms.json"
    if not meta_p.exists():
        raw = out / "raw" / "swarms"
        if not raw.exists():
            return {}
        metas = {p.stem: json.loads(p.read_text()) for p in sorted(raw.glob("*.json"))}
        meta_p.write_text(json.dumps(metas, indent=1))
    metas = json.loads(meta_p.read_text())

    def kind(r):
        cov = metas[f"{r['topology']}_s{r['seed']}"]["covert"][:2]
        dsts, agents = [c["dst"] for c in cov], [c["agent"] for c in cov]
        if any(d in agents for d in dsts):
            return "liar_target"
        return "same_receiver" if dsts[0] == dsts[1] else "distinct_receivers"

    res = {}
    for name, rows in (("llm", llm_rows), ("minimal", [r for r in all_rows if r["condition"] == "minimal"])):
        for kd in ("distinct_receivers", "same_receiver", "liar_target"):
            rs = [r | {"framed": r["false_accusations"] > 0} for r in rows if r["k"] == 2 and kind(r) == kd]
            res[f"{name}_{kd}"] = {"n": len(rs), "localized": rate(rs, "localized")["rate"],
                                   "honest_agent_accused": rate(rs, "framed"),
                                   "swarms": len({(r["topology"], r["seed"]) for r in rs})}
    return res


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/E02"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    judged = {r["key"]: r for r in load(out / "judge.jsonl")}
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in load(out / "runs.jsonl"):
        r = r | judged.get(r["key"], {})
        if "edits" in r:
            r["liar_parse_ok"] = all(e["parse_ok"] for e in r["edits"].values())
            r["liar_edited"] = len(r["liars_who_edited"]) == len(r["liars"])
        cells[(r["liar_model"], r["topology"], r["k"], r["condition"])].append(r)
    summary = []
    for (model, topo, k, cond), rows in sorted(cells.items()):
        s = {"liar_model": model, "topology": topo, "k": k, "condition": cond, "n": len(rows)}
        for m in RATES:
            vals = [bool(r[m]) for r in rows if m in r]
            if vals:
                s[m] = round(sum(vals) / len(vals), 3)
                s[m + "_ci"] = wilson(sum(vals), len(vals))
        for m in MEANS:
            vals = [r[m] for r in rows if m in r]
            if vals:
                s[m] = round(sum(vals) / len(vals), 3)
        summary.append(s)
    all_rows = [r for rows in cells.values() for r in rows]
    llm_rows = [r for r in all_rows if "edits" in r]

    def rate(rows, m):
        k = sum(bool(r.get(m)) for r in rows)
        return {"rate": round(k / len(rows), 3) if rows else None, "n": len(rows), "ci": wilson(k, len(rows))}

    by = {c: [r for r in llm_rows if r["condition"] == c] for c in ("naive", "crosscheck", "detector")}
    noedit = [r for r in all_rows if r["condition"] == "noedit"]
    minimal = [r for r in all_rows if r["condition"] == "minimal"]
    k1_hidden = [r for r in llm_rows if r["k"] == 1 and r["covert_hidden"]]
    hyp = {
        "H1_hidden_but_not_localized_k1": sum(not r["localized"] for r in k1_hidden),
        "H1_k1_hidden_rows": len(k1_hidden),
        "H1_noedit_clean": rate([r | {"c": r["status"] == "clean"} for r in noedit], "c"),
        "H2_minimal_exact": rate(minimal, "exact"),
        "H2_minimal_mean_suspects_per_liar": round(
            sum(r["n_suspects"] / r["k"] for r in minimal) / len(minimal), 3) if minimal else None,
        "H3_minimal_edit_by_condition": {c: rate(rs, "minimal_edit") for c, rs in by.items()},
        "H4_detector_fa_noedit": sum(r["false_accusations"] for r in noedit),
        "H4_judge_mean_fa_noedit": round(sum(r.get("judge_false_accusations", 0) for r in noedit)
                                         / len(noedit), 3) if noedit else None,
        "H4_llm_rows_localized": rate(llm_rows, "localized") if llm_rows else None,
        "H4_llm_rows_judge_flagged": rate([r for r in llm_rows if "judge_flagged" in r], "judge_flagged"),
    }
    hyp["k2_by_receiver"] = receiver_split(out, llm_rows, all_rows, rate)
    (out / "summary.json").write_text(json.dumps({"hypotheses": hyp, "cells": summary}, indent=1))
    print(json.dumps(hyp, indent=1))
    cols = ["liar_model", "topology", "k", "condition", "n", "detected", "localized", "exact",
            "n_suspects", "covert_hidden", "minimal_edit", "liar_edited", "judge_flagged", "judge_false_accusations"]
    print("\t".join(cols))
    for s in summary:
        print("\t".join(str(s.get(c, "")) for c in cols))
    return {"cells": len(summary)}


if __name__ == "__main__":
    main()
