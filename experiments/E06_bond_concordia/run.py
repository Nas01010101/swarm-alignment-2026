"""E06: spy thriller (Sterling vs Dr. Vex) on Concordia agents. `--model mock` runs offline (random choices)."""

import argparse
import json
from pathlib import Path

from concordia.language_model.no_language_model import RandomChoiceLanguageModel

from swarm.concordia_lm import AdaptionLM
from swarm.llm import AdaptionBackend
from swarm.spy import Film, SpyConfig, film_metrics


def lm(name):
    return RandomChoiceLanguageModel() if name == "mock" else AdaptionLM(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock", help="residents' model")
    ap.add_argument("--bond-model"), ap.add_argument("--villain-model")
    ap.add_argument("--agent", default="active,idle", help="idle = control, Sterling does nothing")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed-start", type=int, default=0, help="resume a partial run")
    ap.add_argument("--days", type=int, default=6)
    ap.add_argument("--persuadable", default="", help="comma list of sweep levels 0-3; empty = original cast")
    ap.add_argument("--tag", default="pilot")
    a = ap.parse_args()
    models = {"agent": a.bond_model or a.model, "villain": a.villain_model or a.model}
    out = Path("results/E06") / f"{a.tag}.jsonl"
    raw = Path("results/raw/E06") / a.tag
    out.parent.mkdir(parents=True, exist_ok=True), raw.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        for k in [int(x) for x in a.persuadable.split(",")] if a.persuadable else [None]:
            for it in a.agent.split(","):
                for s in range(a.seed_start, a.seeds):
                    cfg = SpyConfig(days=a.days, agent_active=it == "active", persuadable=k, seed=s)
                    film = Film(cfg, lambda r: lm(models.get(r, a.model))).run()
                    m = {**film_metrics(film), "fallbacks_cum": AdaptionLM.fallbacks, **{f"{r}_model": v for r, v in models.items()}}
                    f.write(json.dumps(m) + "\n")
                    f.flush()
                    (raw / f"{'' if k is None else f'k{k}_'}agent{it}_s{s}.json").write_text(json.dumps(film.log, indent=1))
                    print(f"k={k} agent {it} s{s} -> {m['outcome']} day {m['end_day']} stages {m['stages_done']} "
                          f"kills {m['kills']} captures {m['captures']} showdowns {m['showdowns']} "
                          f"spent ${AdaptionBackend.spent:.3f} calls {AdaptionBackend.calls} fallbacks {AdaptionLM.fallbacks}", flush=True)


if __name__ == "__main__":
    main()
