"""E07: capitalist (c1) vs communist (c2) village, Scenario C. `--model mock` runs offline."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from swarm.economy import EconConfig, run_town, town_metrics
from swarm.llm import AdaptionBackend, MockBackend


def lm(name):
    return MockBackend() if name == "mock" else AdaptionBackend(model=name, max_tokens=2000)


def one(cond, seed, a):
    t = run_town(EconConfig(condition=cond, seed=seed, days=a.days),
                 lm(a.model), lm(a.evil_model or a.model), lm(a.bond_model or a.model))
    raw = Path("results/raw/E07") / a.tag
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{cond}_s{seed}.json").write_text(json.dumps(t.log, indent=1))
    return {**town_metrics(t), "model": a.model, "evil_model": a.evil_model or a.model,
            "bond_model": a.bond_model or a.model}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    ap.add_argument("--evil-model"), ap.add_argument("--bond-model")
    ap.add_argument("--conditions", default="c1,c2")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = [(c, s) for s in range(a.seeds) for c in a.conditions.split(",")]
    out = Path("results/E07") / f"{a.tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    keys = ["outcome", "days_played", "prosperity", "gini", "work_rate", "wall_given", "trades",
            "thefts", "frames", "evil_kills", "innocents_killed", "framed_killed", "catch_day", "starved"]
    with ThreadPoolExecutor(a.workers) as ex, out.open("a") as f:
        for m in ex.map(lambda j: one(*j, a), jobs):
            f.write(json.dumps(m) + "\n")
            f.flush()
            print(m["condition"], m["seed"], {k: m[k] for k in keys}, f"${AdaptionBackend.spent:.3f}", flush=True)
