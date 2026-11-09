"""E08/E10: island economies in a text Minecraft. `--model mock` runs offline."""

import argparse
import json
from pathlib import Path

from swarm.islands import IslandConfig, island_metrics, run_island
from swarm.llm import AdaptionBackend, MockBackend

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    ap.add_argument("--islands", default="capitalist,socialist")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--days", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--neutral", action="store_true", help="E10 ablation: rules without ideology words")
    ap.add_argument("--loophole", action="store_true", help="E14: ledger_sync tool")
    a = ap.parse_args()
    llm = MockBackend() if a.model == "mock" else AdaptionBackend(model=a.model, max_tokens=2000)
    out, raw = Path("results/E08") / f"{a.tag}.jsonl", Path("results/raw/E08") / a.tag
    out.parent.mkdir(parents=True, exist_ok=True), raw.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        for s in range(a.seed_start, a.seeds):
            for name in a.islands.split(","):
                isl = run_island(IslandConfig(island=name, n=a.n, days=a.days, seed=s, workers=a.workers,
                                                neutral=a.neutral, loophole=a.loophole), llm)
                m = {**island_metrics(isl), "model": a.model}
                f.write(json.dumps(m) + "\n")
                f.flush()
                (raw / f"{name}{'_neutral' * a.neutral}{'_loophole' * a.loophole}_s{s}.json").write_text(json.dumps(isl.log, indent=1))
                print(name, s, {k: m[k] for k in ("survivors", "deaths_starved", "deaths_mobs", "deaths_cave_in",
                      "rest_rate", "walls_built", "compliance", "wealth_gini", "trades",
                      "under_report_rate", "plan_efficiency", "hack_rate", "wall_drained")},
                      f"${AdaptionBackend.spent:.3f} calls {AdaptionBackend.calls}", flush=True)
