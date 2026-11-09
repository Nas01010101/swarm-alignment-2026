"""E09: one E08 island at --n citizens, with work and mob nights played by bots in Minecraft.

Needs controller.js listening (RTX, port 25580). The LLM decision layer is unchanged from E08.
--calib is the calibration file from calib_client.js (prereg): it sets the block conversion and
zombies per unit of mob_need.
"""

import argparse
import json
from pathlib import Path

from swarm.islands import IslandConfig, build_island, island_metrics, run_island
from swarm.llm import AdaptionBackend, MockBackend
from swarm.mc_islands import Controller, MinecraftWorld

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    ap.add_argument("--island", default="capitalist")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--days", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=25580)
    ap.add_argument("--calib", default="experiments/E09_minecraft/calib.json")
    ap.add_argument("--tag", default="main")
    ap.add_argument("--neutral", action="store_true", help="E10/E13: rules without ideology words")
    a = ap.parse_args()
    cal = json.loads(Path(a.calib).read_text())
    llm = MockBackend() if a.model == "mock" else AdaptionBackend(model=a.model, max_tokens=2000)
    cfg = IslandConfig(island=a.island, n=a.n, days=a.days, seed=a.seed, workers=a.workers, neutral=a.neutral)
    world = MinecraftWorld(Controller(a.host, a.port), zombies_per_need=cal["zombies_per_need"],
                           convert=cal["convert"])
    world.setup(build_island(cfg))  # run_island rebuilds the same people from the same seed
    isl = run_island(cfg, llm, world=world)
    m = {**island_metrics(isl), "model": a.model, "world": "minecraft"}
    out, raw = Path("results/E09") / f"{a.tag}.jsonl", Path("results/raw/E09") / a.tag
    out.parent.mkdir(parents=True, exist_ok=True), raw.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps(m) + "\n")
    stem = f"{a.island}{'_neutral' * a.neutral}_s{a.seed}"
    (raw / f"{stem}.json").write_text(json.dumps(isl.log, indent=1))
    (raw / f"{stem}_world.json").write_text(json.dumps(world.log, indent=1))
    print(a.island, a.seed, {k: m.get(k) for k in ("survivors", "deaths_starved", "deaths_mobs", "walls_built")},
          f"${AdaptionBackend.spent:.3f}", flush=True)
