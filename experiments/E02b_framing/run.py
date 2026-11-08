"""E02b: do two liars who hide messages sent to the SAME honest agent frame that agent?
And does the t-bounded detector (`diagnose_bounded`) remove the framing? See prereg.md.

Paired design: for each (topology, seed) the graph and the two liars are fixed; only the covert
receivers differ between arrangement=same (one shared honest receiver) and arrangement=distinct
(two different honest receivers). Reuses E02's liar prompts, scoring and judge unchanged.

    SWARM_BACKEND=mock uv run python experiments/E02b_framing/run.py --seeds 1 --out /tmp/e02b
    set -a; . ./.env; set +a
    SWARM_BACKEND=adaption SWARM_TOKEN_CAP=8000000 uv run python experiments/E02b_framing/run.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E02 = ROOT / "experiments" / "E02_llm_swarm_tamper"
sys.path[:0] = [str(ROOT / "src"), str(E02)]

from liars import judge, liar_edit, minimal_hide, score  # noqa: E402

from swarm import diagnose_bounded, llm  # noqa: E402
from swarm.events import dump_logs, load_logs  # noqa: E402
from swarm.sim import Covert, llm_swarm, neighbors  # noqa: E402

_spec = importlib.util.spec_from_file_location("e02run", E02 / "run.py")
e02 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e02)  # TASK, COVERT, append, done_keys, settle, effort

ARRANGEMENTS = ("same", "distinct")
CONDITIONS = ("naive", "detector")
T = 2  # bound for diagnose_bounded = number of liars


def plant(topology: str, n: int, seed: int, p: float, arrangement: str) -> list[tuple[Covert, int]]:
    """Two liars, chosen so BOTH arrangements are possible on this graph (keeps the pair matched):
    a common honest neighbour exists (same) and two different honest neighbours exist (distinct).
    Covert targets are always honest (fixes the E02 fallback that let a liar target the other)."""
    nb = neighbors(n, topology, random.Random(seed), p)  # same graph llm_swarm builds
    rng = random.Random(f"E02b-{topology}-{seed}")
    for _ in range(1000):
        l1, l2 = rng.sample(range(n), 2)
        h1 = [j for j in nb[l1] if j not in (l1, l2)]
        h2 = [j for j in nb[l2] if j not in (l1, l2)]
        common = sorted(set(h1) & set(h2))
        pairs = [(x, y) for x in h1 for y in h2 if x != y]
        if common and pairs:
            break
    else:
        raise RuntimeError(f"no feasible liar pair for {topology} seed {seed}")
    same_dst = rng.choice(common)
    distinct = rng.choice(pairs)
    projects = (rng.randint(1, 4), rng.randint(1, 4))
    dsts = (same_dst, same_dst) if arrangement == "same" else distinct
    return [(Covert(f"a{li}", e02.COVERT_ROUND, f"a{d}", e02.COVERT.format(p=pr)), pr)
            for li, d, pr in zip((l1, l2), dsts, projects)]


def full_score(bad, clean, cov) -> dict:
    liars = {c["agent"] for c in cov}
    s = score(bad, clean, liars, {c["agent"]: c["msg_id"] for c in cov}, {c["agent"]: c["dst"] for c in cov})
    vb = diagnose_bounded(bad, T)
    return s | {"framed": s["false_accusations"] > 0,
                "b_status": vb.status, "b_accused": sorted(vb.accused),
                "b_false_accusations": len(vb.accused - liars), "b_liars_named": len(vb.accused & liars)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["swarm", "attack", "judge", "all"])
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--p", type=float, default=0.4)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--seed-offset", type=int, default=100, help="disjoint from E02 seeds 0-9")
    ap.add_argument("--topologies", default="complete,erdos")
    ap.add_argument("--swarm-model", default="gemma-4-26b-a4b-it")
    ap.add_argument("--liar-models", default="gemma-4-26b-a4b-it,qwen3.8-27b,deepseek-v4-flash")
    ap.add_argument("--judge-model", default="gemma-4-31b-it")
    ap.add_argument("--liar-tokens", type=int, default=8000)
    ap.add_argument("--judge-tokens", type=int, default=2000)
    ap.add_argument("--reasoning", default="low")
    ap.add_argument("--reasoning-models", default="qwen3.8-27b,qwen3.5-397b,deepseek-v4-flash,glm-53-flash,glm-5.2")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(ROOT / "results/E02b"))
    a = ap.parse_args(argv)
    a.topologies, a.liar_models = a.topologies.split(","), a.liar_models.split(",")
    a.reasoning, a.reasoning_models = a.reasoning or None, set(a.reasoning_models.split(","))
    seeds = range(a.seed_offset, a.seed_offset + a.seeds)
    out = Path(a.out)
    sdir, tdir = out / "raw" / "swarms", out / "raw" / "tampered"
    sdir.mkdir(parents=True, exist_ok=True)
    tdir.mkdir(parents=True, exist_ok=True)
    runs, jpath = out / "runs.jsonl", out / "judge.jsonl"
    cells = [(t, s, ar) for t in a.topologies for s in seeds for ar in ARRANGEMENTS]
    t0 = time.time()

    def swarm(t, s, ar):
        meta_p = sdir / f"{t}_s{s}_{ar}.json"
        if meta_p.exists():
            return
        planted = plant(t, a.n, s, a.p, ar)
        cov = [c for c, _ in planted]
        b = llm.get_backend(model=a.swarm_model, max_tokens=400)
        logs = llm_swarm(b, a.n, t, a.rounds, e02.TASK, s, covert=cov, p=a.p, workers=a.n)
        dump_logs(logs, str(sdir / f"{t}_s{s}_{ar}.jsonl"))
        meta_p.write_text(json.dumps({"topology": t, "seed": s, "arrangement": ar, "swarm_model": a.swarm_model,
                                      "covert": [asdict(c) | {"project": pr} for c, pr in planted]}, indent=1))
        print("swarm", t, s, ar, [(c.agent, c.dst, c.msg_id) for c in cov], flush=True)

    def load(t, s, ar):
        meta = json.loads((sdir / f"{t}_s{s}_{ar}.json").read_text())
        return load_logs(str(sdir / f"{t}_s{s}_{ar}.jsonl")), meta

    def emit(key, base, bad, clean, cov, extra):
        dump_logs(bad, str(tdir / f"{key}.jsonl"))
        row = {"key": key, **base, "liars": sorted(c["agent"] for c in cov),
               "receivers": [c["dst"] for c in cov], **full_score(bad, clean, cov), **extra}
        e02.append(runs, row)
        return row

    def controls(t, s, ar, have):
        clean, meta = load(t, s, ar)
        cov = meta["covert"]
        base = {"liar_model": "-", "topology": t, "seed": s, "arrangement": ar}
        if f"ctl_minimal_{t}_s{s}_{ar}" not in have:
            bad = {k: list(v) for k, v in clean.items()}
            for c in cov:
                bad[c["agent"]] = minimal_hide(bad[c["agent"]], c["msg_id"])
            emit(f"ctl_minimal_{t}_s{s}_{ar}", base | {"condition": "minimal"}, bad, clean, cov, {})
        if f"ctl_noedit_{t}_s{s}_{ar}" not in have:
            dump_logs(clean, str(tdir / f"ctl_noedit_{t}_s{s}_{ar}.jsonl"))
            e02.append(runs, {"key": f"ctl_noedit_{t}_s{s}_{ar}", **base, "condition": "noedit", "liars": [],
                              "receivers": [], **full_score(clean, clean, [])})

    def attack(m, t, s, ar, cond, backends):
        key = f"{m}_{t}_s{s}_{ar}_{cond}"
        clean, meta = load(t, s, ar)
        cov = meta["covert"]
        bad = {k: list(v) for k, v in clean.items()}
        edits = {}
        for c in cov:
            bad[c["agent"]], edits[c["agent"]] = liar_edit(backends[m], bad[c["agent"]], c["agent"], cond,
                                                           c["dst"], c["project"])
        row = emit(key, {"liar_model": m, "topology": t, "seed": s, "arrangement": ar, "condition": cond},
                   bad, clean, cov, {"edits": edits})
        print(cond, m, t, s, ar, row["status"], row["accused"], "liars", row["liars"],
              "bounded", row["b_accused"], flush=True)

    try:
        if a.phase in ("swarm", "all"):
            with ThreadPoolExecutor(max(1, a.workers // a.n)) as ex:
                e02.settle([ex.submit(swarm, *c) for c in cells])
        if a.phase in ("attack", "all"):
            have = e02.done_keys(runs)
            for c in cells:
                controls(*c, have)
            backends = {m: llm.get_backend(model=m, max_tokens=a.liar_tokens, reasoning=e02.effort(a, m))
                        for m in a.liar_models}
            jobs = [(m, *c, cond) for m in a.liar_models for c in cells for cond in CONDITIONS
                    if f"{m}_{c[0]}_s{c[1]}_{c[2]}_{cond}" not in have]
            with ThreadPoolExecutor(a.workers) as ex:
                e02.settle([ex.submit(attack, *j, backends) for j in jobs])
        if a.phase in ("judge", "all"):
            have = e02.done_keys(jpath)
            jb = llm.get_backend(model=a.judge_model, max_tokens=a.judge_tokens, reasoning=e02.effort(a, a.judge_model))
            rows = [json.loads(x) for x in runs.read_text().splitlines() if x.strip()]

            def one(r):
                bad = load_logs(str(tdir / f"{r['key']}.jsonl"))
                e02.append(jpath, {"key": r["key"], "judge_model": a.judge_model, **judge(jb, bad, set(r["liars"]))})

            with ThreadPoolExecutor(a.workers) as ex:
                e02.settle([ex.submit(one, r) for r in rows if r["key"] not in have])
    finally:
        spend = {"utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "phase": a.phase,
                 "seconds": round(time.time() - t0), "usage": dict(llm.USAGE)}
        e02.append(out / "spend.jsonl", spend)
        print("usage", json.dumps(spend["usage"]))


if __name__ == "__main__":
    main()
