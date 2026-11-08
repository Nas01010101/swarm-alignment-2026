"""E08: 200-agent synthetic scarcity sweep (rho x topology x governance x seeds). No LLM, $0.

uv run python experiments/E08_scarcity_synthetic/run.py --seeds 20 [--workers 8] [--tag sweep]
"""

import argparse
import itertools
import json
import time
from multiprocessing import Pool
from pathlib import Path

from swarm.scarcity import GOVERNANCE, TOPOLOGIES, ScarcityConfig, run

RHOS = (0.4, 0.6, 0.8, 1.0, 1.2, 1.5)


def job(args):
    rho, topo, gov, seed, n, rounds = args
    out = run(ScarcityConfig(n=n, rounds=rounds, rho=rho, topology=topo, governance=gov, seed=seed))
    hist = out.pop("hist")
    out["traj_hack"] = [round(h["hack"], 4) for h in hist]
    out["traj_need_met"] = [round(h["need_met"], 4) for h in hist]
    out["traj_stock"] = [round(h["stock"], 3) for h in hist]
    out["traj_lam"] = [round(h["lam"], 4) for h in hist]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="sweep")
    a = ap.parse_args()
    jobs = [(r, t, g, s, a.n, a.rounds) for r, t, g, s in itertools.product(RHOS, TOPOLOGIES, GOVERNANCE, range(a.seeds))]
    out = Path("results/E08") / f"{a.tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with Pool(a.workers) as pool, out.open("w") as f:
        for k, row in enumerate(pool.imap(job, jobs, chunksize=4), 1):
            f.write(json.dumps(row) + "\n")
            if k % 120 == 0:
                print(f"{k}/{len(jobs)} episodes, {time.time() - t0:.0f}s", flush=True)
    print(f"wrote {len(jobs)} episodes to {out} in {time.time() - t0:.0f}s")
