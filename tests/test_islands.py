import json
import random

import pytest

from swarm.islands import IslandConfig, build_island, island_metrics, run_island


class RandomJSON:
    """Random but well-formed replies for every prompt the islands send."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def complete(self, system, messages):
        r, ask = self.r, messages[-1]["content"]
        rep = {j: r.randint(0, 6) for j in ["farm", "chop", "mine"]}
        if "Day 1. Your island must elect" in ask:
            return json.dumps({"vote": f"c{r.randrange(5)}", "report": rep})
        if "job quotas as shares" in ask:
            return json.dumps({j: r.random() for j in ["farm", "chop", "mine", "build_wall", "rest"]})
        return json.dumps({"job": r.choice(["farm", "chop", "mine", "build_wall", "rest", "dance"]),
                           "sell_food": r.randint(0, 2), "min_price": r.randint(0, 5), "donate_wood": r.randint(0, 2), "donate_stone": r.randint(0, 2),
                           "buy_food": r.randint(0, 2), "max_price": r.randint(0, 5), "say": "hi", "report": rep})


@pytest.mark.parametrize("island", ["capitalist", "capitalist_tax", "socialist", "planned", "commons", "directed"])
@pytest.mark.parametrize("seed", range(3))
def test_island_runs_and_keeps_invariants(island, seed):
    isl = run_island(IslandConfig(island=island, n=30, days=8, seed=seed, workers=1), RandomJSON(seed))
    m = island_metrics(isl)
    assert 0 <= m["survivors"] <= 30
    assert m["survivors"] + m["deaths_starved"] + m["deaths_mobs"] + m["deaths_cave_in"] == 30
    assert all(v >= 0 for p in isl.people for v in p.inv.values()) and all(v >= 0 for v in isl.store.values())
    assert not [e for e in isl.log if e["kind"] == "death" and e["cause"] == "mobs" and e["day"] <= 2]
    pooled_, led_ = island in ("socialist", "planned", "commons"), island in ("socialist", "planned", "directed")
    assert (m["leader"] is not None) == led_
    if pooled_:
        assert m["trades"] == 0 and m["wealth_gini"] is None
    else:
        assert 0 <= m["wealth_gini"] <= 1


def test_islands_share_people_and_food():
    a, b = (build_island(IslandConfig(island=i, seed=4)) for i in ("capitalist", "socialist"))
    assert [(p.name, p.trait) for p in a.people] == [(p.name, p.trait) for p in b.people]
    assert sum(p.inv["food"] for p in a.people) == b.store["food"]
    assert min(p.coins for p in a.people) >= -5 and all(p.coins == 0 for p in b.people)


def test_tax_funds_treasury_and_never_overdraws():
    isl = run_island(IslandConfig(island="capitalist_tax", n=30, days=8, seed=1, workers=1), RandomJSON(1))
    sales = sum(1 for e in isl.log if e["kind"] == "job" and e["done"] == "mine")
    assert isl.treasury >= 0 and sales > 0
    assert island_metrics(isl)["treasury_end"] >= 0


def test_planned_reports_and_efficiency():
    isl = run_island(IslandConfig(island="planned", n=30, days=6, seed=2, workers=1), RandomJSON(2))
    m = island_metrics(isl)
    assert all(1 <= v <= 5 for p in isl.people for v in p.skill.values())
    assert all(1 <= v <= 5 for p in isl.people for v in p.report.values())
    assert 0 <= m["under_report_rate"] <= 1 and 0 < m["plan_efficiency"] <= 1
    assert m["compliance"] is not None


def test_allocate_rests_lowest_reporters_and_fills_by_skill():
    from swarm.islands import Citizen, _allocate, _slots
    ppl = [Citizen(f"c{i}", "loyal") for i in range(4)]
    rep = {"c0": {"farm": 5, "chop": 1, "mine": 1}, "c1": {"farm": 1, "chop": 5, "mine": 1},
           "c2": {"farm": 1, "chop": 1, "mine": 1}, "c3": {"farm": 4, "chop": 4, "mine": 4}}
    slots = _slots({"farm": 1, "chop": 1, "mine": 1, "rest": 1}, 4)
    assert sum(slots.values()) == 4
    assert _allocate(ppl, slots, rep) == {"c2": "rest", "c0": "farm", "c1": "chop", "c3": "mine"}


def test_neutral_wording_drops_ideology_words_only():
    from swarm.islands import _system
    for arm in ("capitalist", "socialist"):
        plain, neut = (build_island(IslandConfig(island=arm, seed=0, neutral=n)) for n in (False, True))
        text = _system(neut, neut.people[0]).lower()
        assert not any(w in text for w in ("capitalis", "socialis", "leader"))
        assert [(p.name, p.trait, p.inv, p.coins) for p in plain.people] == \
            [(p.name, p.trait, p.inv, p.coins) for p in neut.people]


def test_planned_shares_people_with_socialist():
    a, b = (build_island(IslandConfig(island=i, seed=3)) for i in ("socialist", "planned"))
    assert [(p.name, p.trait) for p in a.people] == [(p.name, p.trait) for p in b.people]
    assert a.store == b.store and not a.people[0].skill and b.people[0].skill


def test_factorial_cells_split_ownership_from_coordination():
    """E13: commons pools goods with no coordinator; directed keeps goods private under an elected coordinator."""
    com = run_island(IslandConfig(island="commons", n=20, days=4, seed=1, workers=1), RandomJSON(1))
    dirc = run_island(IslandConfig(island="directed", n=20, days=4, seed=1, workers=1), RandomJSON(1))
    assert com.leader is None and not any(e["kind"] in ("election", "quotas") for e in com.log)
    assert all(not p.inv.get("food") for p in com.people) and island_metrics(com)["compliance"] is None
    assert dirc.leader is not None and any(e["kind"] == "quotas" for e in dirc.log)
    assert any(e["kind"] == "market" for e in dirc.log) and island_metrics(dirc)["compliance"] is not None
    assert all(e["assigned"] is not None for e in dirc.log if e["kind"] == "job")
