"""E05: Bond (fewer resources) vs the Evil Agent, both LLMs on Adaption.

SWARM_BACKEND=adaption uv run python experiments/E05_bond_vs_evil/run.py --pair gemma-4-26b-a4b-it:gemma-4-26b-a4b-it --seeds 2
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from swarm.bond import BondConfig, duel_metrics, run_duel
from swarm.llm import AdaptionBackend, MockBackend


def backend(model):
    return MockBackend() if model == "mock" else AdaptionBackend(model=model, max_tokens=2000)


def one(bond_m, evil_m, budget, seed, days, tag):
    cfg = BondConfig(budget=budget, seed=seed, days=days)
    d = run_duel(cfg, backend(bond_m), backend(evil_m))
    raw = Path("results/raw/E05") / tag
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{bond_m}_vs_{evil_m}_b{budget}_s{seed}.json").write_text(json.dumps(d.log, indent=1))
    return {"bond_model": bond_m, "evil_model": evil_m, **duel_metrics(d)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", action="append", required=True, help="bond_model:evil_model")
    ap.add_argument("--budgets", default="0,1,2")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = [(*p.split(":"), int(b), s) for p in a.pair for b in a.budgets.split(",") for s in range(a.seeds)]
    out = Path("results/E05") / f"{a.tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex, out.open("w") as f:
        for r in ex.map(lambda j: one(*j, a.days, a.tag), jobs):
            f.write(json.dumps(r) + "\n")
            f.flush()
            print(r["bond_model"], "vs", r["evil_model"], "b", r["budget"], "s", r["seed"], "->", r["outcome"],
                  "day", r["days_played"], "innocents", r["innocents_struck"], "evil_kills", r["evil_kills"])
