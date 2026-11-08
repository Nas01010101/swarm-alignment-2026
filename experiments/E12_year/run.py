"""E12: two islands for one simulated year, fixed vs open rules. `--model mock` runs offline."""

import argparse
import json
from pathlib import Path

from swarm.llm import AdaptionBackend, MockBackend
from swarm.year import YearConfig, run_year, year_metrics

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    ap.add_argument("--arms", default="fixed,open")
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--weeks", type=int, default=52)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--tag", default="pilot")
    a = ap.parse_args()
    llm = MockBackend() if a.model == "mock" else AdaptionBackend(model=a.model, max_tokens=2000)
    out, raw = Path("results/E12") / f"{a.tag}.jsonl", Path("results/raw/E12") / a.tag
    out.parent.mkdir(parents=True, exist_ok=True), raw.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        for s in range(a.seed_start, a.seeds):
            for arm in a.arms.split(","):
                res = run_year(YearConfig(arm=arm, n=a.n, weeks=a.weeks, workers=a.workers, seed=s), llm)
                m = {**year_metrics(res), "model": a.model}
                f.write(json.dumps(m) + "\n")
                f.flush()
                (raw / f"{arm}_s{s}.json").write_text(json.dumps(res))
                print(arm, s, {k: m[k] for k in ("weeks_run", "alive_A", "alive_B", "rules_end_A", "rules_end_B",
                      "switches", "moves_A_to_B", "moves_B_to_A", "births", "reelections", "elections")},
                      f"${AdaptionBackend.spent:.3f} calls {AdaptionBackend.calls}", flush=True)
