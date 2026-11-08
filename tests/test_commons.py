import hashlib
import json

import pytest

from swarm.commons import GOVERNANCE, CommonsConfig, build_village, run_village, village_metrics


class HashJSON:
    """Deterministic pseudo-random decisions keyed on the prompt (thread-safe, order-free)."""

    def __init__(self, p_hack=0.3):
        self.p_hack = p_hack

    def complete(self, system, messages):
        h = int(hashlib.sha256((system + messages[-1]["content"]).encode()).hexdigest(), 16)
        u = (h % 1000) / 1000
        act = "ledger_sync" if u < self.p_hack else ("work" if u < 0.8 else "forage")
        return json.dumps({"action": act, "wall": h % 3, "take": h % 2, "buy": h % 2, "max_price": h % 4,
                           "sell": (h >> 3) % 2, "min_price": (h >> 5) % 4, "say": "hi"})


class Const:
    def __init__(self, act):
        self.act = act

    def complete(self, system, messages):
        return json.dumps({"action": self.act, "wall": 0, "take": 1})


@pytest.mark.parametrize("econ", ["c1", "c2", "c3"])
@pytest.mark.parametrize("gov", GOVERNANCE)
def test_runs_and_invariants(econ, gov):
    judge = (lambda day, board, lb: [line.split()[2] for line in board if "ledger_sync" in line][:1])
    cfg = CommonsConfig(economy=econ, rho=0.6, governance=gov, seeded=True, seed=3)
    v = run_village(cfg, HashJSON(), judge=judge)
    m = village_metrics(v)
    assert m["actions"] > 0 and m["invalid"] == 0
    assert v.wall >= 0 and v.store >= 0 and all(p.food >= -1e-9 for p in v.people)
    assert m["seed_econ"] in ("c1", "c2")
    if gov == "hack_ban":
        assert m["drained"] == 0 and m["mean_lam"] == 0
    if gov in ("unfiltered", "constitutional_prompt"):
        assert m["mean_lam"] == 1
    if gov != "llm_judge":
        assert m["fined"] == 0
    json.dumps(m)


def test_deterministic_with_deterministic_backend():
    cfg = CommonsConfig(economy="c3", rho=0.6, seed=5, seeded=True)
    assert village_metrics(run_village(cfg, HashJSON())) == village_metrics(run_village(cfg, HashJSON()))


def test_positive_and_negative_controls():
    allhack = village_metrics(run_village(CommonsConfig(economy="c1", rho=2.0, days=3, raid_loss=0), Const("ledger_sync")))
    assert allhack["hack_calls"] == 8 * 3 and allhack["adopters_nonseed"] == 8
    assert allhack["credits_issued"] == 8 * 3 * 5.0
    honest = village_metrics(run_village(CommonsConfig(economy="c2", rho=2.0, days=3), Const("work")))
    assert honest["hack_calls"] == 0 and not honest["any_hack"] and honest["work_rate"] == 1.0
    noloop = village_metrics(run_village(CommonsConfig(economy="c1", loophole=False, days=2), Const("ledger_sync")))
    assert noloop["hack_calls"] == 0 and noloop["invalid"] == 16  # invalid action falls back to forage


def test_drain_hits_wall_first():
    v = run_village(CommonsConfig(economy="c1", rho=2.0, days=1, wall0=10.0), Const("ledger_sync"))
    hacks = [e for e in v.log if e["kind"] == "hack"]
    assert abs(sum(e["drained"] for e in hacks) - 8 * 1.5) < 1e-9


def test_c3_split_and_seed_alternates_bloc():
    for s in range(6):
        v = build_village(CommonsConfig(economy="c3", seeded=True, seed=s))
        assert sorted(v.econ.values()).count("c1") == 4
        assert v.econ[v.seed_name] == ("c1" if s % 2 == 0 else "c2")


def test_economy_module_untouched():
    """E07 must stay reproducible: commons.py only imports from economy.py."""
    from swarm import economy
    assert economy.EconConfig().produce == 2 and economy.EconConfig().forage == 1
