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
    ap.add_argument("--mc", default=None, help="RTX host: islands A and B on controllers at ports 25580, 25581")
    ap.add_argument("--work-s", type=int, default=45)
    ap.add_argument("--night-s", type=int, default=45)
    a = ap.parse_args()
    llm = MockBackend() if a.model == "mock" else AdaptionBackend(model=a.model, max_tokens=2000)
    out, raw = Path("results/E12") / f"{a.tag}.jsonl", Path("results/raw/E12") / a.tag
    out.parent.mkdir(parents=True, exist_ok=True), raw.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        for s in range(a.seed_start, a.seeds):
            for arm in a.arms.split(","):
                worlds = None
                if a.mc:
                    from swarm.mc_islands import Controller, MinecraftWorld
                    cal = json.loads(Path("experiments/E09_minecraft/calib.json").read_text())
                    worlds = {t: MinecraftWorld(Controller(a.mc, port), cal["zombies_per_need"], a.work_s, a.night_s,
                                                cal["convert"]) for t, port in (("A", 25580), ("B", 25581))}
                res = run_year(YearConfig(arm=arm, n=a.n, weeks=a.weeks, workers=a.workers, seed=s), llm, worlds)
                if worlds:
                    res["mc"] = {t: w.log for t, w in worlds.items()}
                m = {**year_metrics(res), "model": a.model}
                f.write(json.dumps(m) + "\n")
                f.flush()
                (raw / f"{arm}_s{s}.json").write_text(json.dumps(res))
                print(arm, s, {k: m[k] for k in ("weeks_run", "alive_A", "alive_B", "rules_end_A", "rules_end_B",
                      "switches", "moves_A_to_B", "moves_B_to_A", "births", "reelections", "elections")},
                      f"${AdaptionBackend.spent:.3f} calls {AdaptionBackend.calls}", flush=True)
