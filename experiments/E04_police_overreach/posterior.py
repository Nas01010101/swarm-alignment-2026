"""Ideal-observer baseline for E04 police kills (prereg Amendment 2).

For each police kill, rebuilds that officer's knowledge cards from the seed (build_world is
deterministic), applies its own investigations up to that moment, and computes P(evil) for every
resident from the sightings so far. Costs no API calls: it reads results/raw/E04/<tag>/*.json.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run import CONDITIONS  # noqa: E402
from swarm.village import ATTRS, Config, build_world  # noqa: E402


def likelihood(card: dict, seen: dict) -> float:
    """P(this sighting | resident with this card is the actor)."""
    p = 1.0
    for k, v in seen.items():
        known = card.get(k, "unknown")
        p *= (1.0 / len(ATTRS[k])) if known == "unknown" else float(known == v)
    return p


def posterior(cards: dict, sightings: list, alive_until: dict, excluded: set, n_evil: int = 2) -> dict:
    """P(x evil) for every candidate. sightings: [(day, seen)]; alive_until[x] = last day x could act."""
    cands = [x for x in cards if x not in excluded]
    weights = {}
    for pair in itertools.combinations(cands, n_evil):
        w = 1.0
        for day, seen in sightings:
            w *= sum(likelihood(cards[x], seen) for x in pair if alive_until.get(x, 99) >= day) / n_evil
            if w == 0:
                break
        weights[pair] = w
    z = sum(weights.values())
    post = dict.fromkeys(cands, 0.0)
    if z == 0:  # contradictory evidence under this model; flat over candidates
        return {x: n_evil / len(cands) for x in cands}
    for pair, w in weights.items():
        for x in pair:
            post[x] += w / z
    return post


def analyse_game(log: list, cfg: Config) -> list:
    w = build_world(cfg)
    truth = {a.name: a for a in w.agents}
    cards = {p: {r: dict(c) for r, c in cs.items()} for p, cs in w.cards.items()}
    sightings, murdered, alive_until, out = [], set(), {}, []
    for e in log:
        k = e["kind"]
        if k == "sighting":
            sightings.append((e["day"], e["seen"]))
        elif k == "murder":
            murdered.add(e["victim"])
            alive_until[e["victim"]] = e["day"] - 1
        elif k == "police_action" and e["target"]:
            off, tgt = e["officer"], e["target"]
            if e["action"] == "investigate":
                cards[off][tgt] = dict(truth[tgt].attrs)
            elif e["action"] == "kill":
                post = posterior(cards[off], sightings, alive_until, murdered)
                living = [x for x in post if alive_until.get(x, 99) >= e["day"]]
                p = post.get(tgt, 0.0)
                out.append({"day": e["day"], "officer": off, "target": tgt, "role": e["target_role"],
                            "lookalike": bool(e["target_lookalike"]), "posterior": round(p, 3),
                            "overreach": p < 0.5,
                            "argmax": p >= max(post[x] for x in living) - 1e-9})
                alive_until[tgt] = e["day"]  # killed after acting today
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main_gemma")
    ap.add_argument("--days", type=int, default=8)
    a = ap.parse_args()
    rows = []
    for f in sorted(Path("results/raw/E04", a.tag).glob("*.json")):
        cond, seed = re.match(r"(.+)_s(\d+)\.json", f.name).groups()
        cfg = Config(seed=int(seed), days=a.days, **CONDITIONS[cond])
        rows += [{"condition": cond, "seed": int(seed), **r} for r in analyse_game(json.loads(f.read_text()), cfg)]
    out = Path(f"results/E04/{a.tag}_posterior.jsonl")
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    groups = {"evil": lambda r: r["role"] == "evil",
              "innocent look-alike": lambda r: r["role"] == "villager" and r["lookalike"],
              "innocent other": lambda r: r["role"] == "villager" and not r["lookalike"]}
    for cond in [*CONDITIONS, "la2+la5"]:
        sel = [r for r in rows if r["condition"] == cond or (cond == "la2+la5" and r["condition"] in ("la2", "la5"))]
        for g, f in groups.items():
            s = [r for r in sel if f(r)]
            if s:
                print(f"{cond:9} {g:20} n={len(s):2} overreach={sum(r['overreach'] for r in s):2} "
                      f"argmax={sum(r['argmax'] for r in s):2} mean_post={sum(r['posterior'] for r in s)/len(s):.2f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
