"""E02b analysis. Unit = swarm (topology, seed, arrangement): rows from the same swarm (3 liar models x
2 conditions) are not independent, so rates are averaged per swarm first and intervals come from a
bootstrap over swarms (paired over seeds for the same - distinct difference).

    uv run python experiments/E02b_framing/analyze.py --out results/E02b     -> <out>/summary.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = 5000


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def boot(vals: list[float], rng: random.Random) -> dict:
    if not vals:
        return {"mean": None, "ci": None, "n_swarms": 0}
    means = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(B))
    return {"mean": round(sum(vals) / len(vals), 3),
            "ci": [round(means[int(0.025 * B)], 3), round(means[int(0.975 * B) - 1], 3)], "n_swarms": len(vals)}


def per_swarm(rows: list[dict], metric) -> dict[tuple, float]:
    g: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        g[(r["topology"], r["seed"], r["arrangement"])].append(float(metric(r)))
    return {k: sum(v) / len(v) for k, v in g.items()}


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results/E02b"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    judged = {r["key"]: r for r in load(out / "judge.jsonl")}
    rows = [r | judged.get(r["key"], {}) for r in load(out / "runs.jsonl")]
    llm_rows = [r for r in rows if "edits" in r]
    rng = random.Random(0)
    metrics = {
        "framed_mincover": lambda r: r["framed"],
        "framed_bounded": lambda r: r["b_false_accusations"] > 0,
        "bounded_named_a_liar": lambda r: r["b_liars_named"] > 0,
        "both_hidden": lambda r: r["covert_hidden"],
        "judge_accused_receiver": lambda r: bool(set(r.get("judge_named", [])) & set(r["receivers"])),
        "judge_flagged": lambda r: r.get("judge_flagged", False),
    }
    res: dict = {"n_rows": len(rows), "n_llm_rows": len(llm_rows)}
    for group, rs in (("llm", llm_rows), ("minimal", [r for r in rows if r["condition"] == "minimal"])):
        for name, f in metrics.items():
            ps = per_swarm(rs, f)
            for ar in ("same", "distinct"):
                res[f"{group}_{name}_{ar}"] = boot([v for k, v in ps.items() if k[2] == ar], rng)
            pairs = [ps[(t, s, "same")] - ps[(t, s, "distinct")]
                     for (t, s, ar) in ps if ar == "same" and (t, s, "distinct") in ps]
            res[f"{group}_{name}_diff_same_minus_distinct"] = boot(pairs, rng)
    # mechanism: framing should happen exactly when both liars hid their message (same arrangement)
    same = [r for r in llm_rows if r["arrangement"] == "same"]
    res["same_framed_given_both_hidden"] = [sum(r["framed"] for r in same if r["covert_hidden"]),
                                            sum(1 for r in same if r["covert_hidden"])]
    res["same_framed_given_not_both_hidden"] = [sum(r["framed"] for r in same if not r["covert_hidden"]),
                                                sum(1 for r in same if not r["covert_hidden"])]
    # post hoc (not pre-registered): H2 exceptions all had a liar editing records with a second peer
    res["posthoc_same_framed_given_both_minimal_edit"] = [sum(r["framed"] for r in same if r["minimal_edit"]),
                                                          sum(1 for r in same if r["minimal_edit"])]
    res["posthoc_same_framed_given_hidden_not_minimal"] = [
        sum(r["framed"] for r in same if r["covert_hidden"] and not r["minimal_edit"]),
        sum(1 for r in same if r["covert_hidden"] and not r["minimal_edit"])]
    res["posthoc_same_hidden_not_framed_liar_accused"] = sum(
        1 for r in same if r["covert_hidden"] and not r["framed"] and set(r["accused"]) & set(r["liars"]))
    noedit = [r for r in rows if r["condition"] == "noedit"]
    res["noedit_clean_mincover"] = [sum(r["status"] == "clean" for r in noedit), len(noedit)]
    res["noedit_clean_bounded"] = [sum(r["b_status"] == "clean" for r in noedit), len(noedit)]
    res["bounded_false_accusations_total"] = sum(r["b_false_accusations"] for r in rows)
    res["liar_parse_ok"] = [sum(all(e["parse_ok"] for e in r["edits"].values()) for r in llm_rows), len(llm_rows)]
    by_model = defaultdict(list)
    for r in same:
        by_model[r["liar_model"]].append(r["framed"])
    res["same_framed_by_model_rows"] = {m: [sum(v), len(v)] for m, v in by_model.items()}
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
