"""E09: E07 village under scarcity with a ledger loophole. `--models mock` runs offline.

SWARM_TOKEN_CAP=... uv run python experiments/E09_scarcity_llm/run.py --models gemma-4-26b-a4b-it --seeds 2 --tag pilot
Rows → results/E09/<tag>.jsonl (resumable: finished jobs are skipped); village logs → results/raw/E09/<tag>/;
spend → results/E09/spend.jsonl. Also used by E09b (--governance ..., --cells).
"""

import argparse
import itertools
import json
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from swarm import llm
from swarm.commons import CommonsConfig, run_village, village_metrics

REASONING = {"qwen3.8-27b", "deepseek-v4-flash", "glm-5.2", "glm-53-flash"}
LOCK = threading.Lock()


class Paced:
    """Adaption has a per-USER quota (~45 requests/min across all models; 429 + 60 s lockout above it).
    One global pacer spaces call starts 60/rpm s apart; `n` caps calls in flight per model."""

    _lock, _next = threading.Lock(), [0.0]

    def __init__(self, inner, n, rpm):
        self.inner, self.sem, self.gap = inner, threading.Semaphore(n), 60.0 / rpm

    def complete(self, system, messages):
        with self.sem:
            with Paced._lock:
                now = time.time()
                start = max(now, Paced._next[0])
                Paced._next[0] = start + self.gap
            time.sleep(max(0.0, start - now))
            return self.inner.complete(system, messages)


def backend(model, a):
    if model == "mock":
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
        from test_commons import HashJSON  # noqa: E402
        return HashJSON()
    r = model in REASONING
    b = llm.get_backend("adaption", model=model, max_tokens=a.reasoning_tokens if r else a.tokens,
                        reasoning="low" if r else None)
    b.retries = 8  # backoff 2..512 s; one 429 storm must not fail a whole village
    return Paced(b, a.concurrency, a.rpm)


def key(j):
    return f"{j['model']}|{j['economy']}|{j['rho']}|{int(j['seeded'])}|{int(j['loophole'])}|{j['governance']}|{j['seed']}"


def jobs(a):
    out = []
    for model, econ, rho, seeded, s in itertools.product(a.models.split(","), a.economies.split(","),
                                                         [float(x) for x in a.rhos.split(",")],
                                                         [bool(int(x)) for x in a.seeded.split(",")],
                                                         range(a.seed0, a.seed0 + a.seeds)):
        for gov in a.governance.split(","):
            out.append({"model": model, "economy": econ, "rho": rho, "seeded": seeded, "loophole": not a.no_loophole,
                        "governance": gov, "seed": s})
    return out


def one(j, a, backends, judge):
    cfg = CommonsConfig(economy=j["economy"], rho=j["rho"], seeded=j["seeded"], loophole=j["loophole"],
                        governance=j["governance"], seed=j["seed"], days=a.days)
    t0 = time.time()
    v = run_village(cfg, backends[j["model"]], judge=judge if j["governance"] == "llm_judge" else None)
    raw = Path("results/raw") / Path(a.outdir).name / a.tag
    raw.mkdir(parents=True, exist_ok=True)
    (raw / (key(j).replace("|", "_") + ".json")).write_text(json.dumps({"log": v.log, "board": v.board}, indent=1))
    return {**village_metrics(v), "model": j["model"], "key": key(j), "seconds": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="mock")
    ap.add_argument("--economies", default="c1,c2,c3")
    ap.add_argument("--rhos", default="2.0,0.6")
    ap.add_argument("--seeded", default="0,1")
    ap.add_argument("--governance", default="unfiltered")
    ap.add_argument("--no-loophole", action="store_true")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--tokens", type=int, default=1500)
    ap.add_argument("--reasoning-tokens", type=int, default=8000)
    ap.add_argument("--workers", type=int, default=6, help="villages in parallel (each runs 8 calls at once)")
    ap.add_argument("--concurrency", type=int, default=8, help="max in-flight calls per model")
    ap.add_argument("--rpm", type=float, default=40.0, help="global request starts per minute (Adaption quota)")
    ap.add_argument("--judge-model", default="gemma-4-31b-it")
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--outdir", default="results/E09")
    a = ap.parse_args()
    out = Path(a.outdir) / f"{a.tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(line)["key"] for line in out.open()} if out.exists() else set()
    todo = [j for j in jobs(a) if key(j) not in done]
    print(f"{len(todo)} villages to run ({len(done)} already in {out})", flush=True)
    backends = {m: backend(m, a) for m in a.models.split(",")}
    judge = None
    if "llm_judge" in a.governance:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E09b_cbf_governance"))
        from judge import make_judge  # noqa: E402
        judge = make_judge(a.judge_model if a.models != "mock" else "mock", wrap=lambda b: Paced(b, 2, a.rpm))
    t0, failed = time.time(), 0
    with ThreadPoolExecutor(a.workers) as ex, out.open("a") as f:
        futs = {ex.submit(one, j, a, backends, judge): j for j in todo}
        for k, fut in enumerate(as_completed(futs), 1):
            j = futs[fut]
            try:
                m = fut.result()
            except llm.TokenCapExceeded:
                print("token cap reached; stopping", flush=True)
                ex.shutdown(cancel_futures=True)
                break
            except Exception:  # one failed village must not kill the sweep; a rerun fills it
                failed += 1
                print(f"FAILED {key(j)}\n{traceback.format_exc(limit=2)}", flush=True)
                continue
            with LOCK:
                f.write(json.dumps(m) + "\n")
                f.flush()
            usd = sum(u.get("usd", 0.0) for u in llm.USAGE.values())
            print(f"[{k}/{len(todo)}] {m['key']} hacks={m['hack_calls']} adopt={m['adopters_nonseed']}/"
                  f"{m['nonseed']} starved={m['starved']} invalid={m['invalid']}/{m['actions']} "
                  f"${usd:.3f} {time.time() - t0:.0f}s", flush=True)
    if judge is not None:
        import judge as jmod  # noqa: E402
        with (out.parent / f"{a.tag}_judge.jsonl").open("a") as f:
            for row in jmod.LOG:
                f.write(json.dumps(row) + "\n")
    spend = {"utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "tag": a.tag, "failed": failed,
             "seconds": round(time.time() - t0), "usage": {m: dict(u) for m, u in llm.USAGE.items()}}
    with (out.parent / "spend.jsonl").open("a") as f:
        f.write(json.dumps(spend) + "\n")
    print("spend", json.dumps(spend))


if __name__ == "__main__":
    main()
