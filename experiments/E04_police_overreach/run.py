"""E04: police with kill power vs saboteurs that share a look (Scenario B, text village).

uv run python experiments/E04_police_overreach/run.py --seeds 1          # mock
SWARM_BACKEND=adaption SWARM_MODEL=gemma-4-26b-a4b-it uv run python experiments/E04_police_overreach/run.py --seeds 3
"""

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from swarm.llm import get_backend
from swarm.village import Config, metrics, run_village

CONDITIONS = {
    "la0": dict(lookalikes=0),
    "la2": dict(lookalikes=2),
    "la5": dict(lookalikes=5),
    # Control: evil agents get random looks, so the profile carries no signal.
    "ctrl_la5": dict(lookalikes=5, profile_informative=False),
}


def one(cond, seed, days, tag):
    cfg = Config(seed=seed, days=days, **CONDITIONS[cond])
    w = run_village(cfg, get_backend())
    raw = Path("results/raw/E04") / tag
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{cond}_s{seed}.json").write_text(json.dumps(w.log, indent=1))
    return {"condition": cond, "model": os.environ.get("SWARM_MODEL", "mock"), **metrics(w)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--days", type=int, default=8)
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    jobs = [(c, s) for c in a.conditions.split(",") for s in range(a.seeds)]
    out = Path("results/E04") / f"{a.tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex, out.open("w") as f:
        for row in ex.map(lambda j: one(*j, a.days, a.tag), jobs):
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(row["condition"], row["seed"], "kills", row["police_kills"],
                  "evil", row["evil_killed"], "inno", row["innocents_killed"],
                  "la_inno", row["lookalike_innocents_killed"], "DI", row["discrimination_index"])
