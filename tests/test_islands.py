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
        if "elect a leader" in ask:
            return json.dumps({"vote": f"c{r.randrange(5)}"})
        if "job quotas as shares" in ask:
            return json.dumps({j: r.random() for j in ["farm", "chop", "mine", "build_wall", "rest"]})
        return json.dumps({"job": r.choice(["farm", "chop", "mine", "build_wall", "rest", "dance"]),
                           "sell_food": r.randint(0, 2), "min_price": r.randint(0, 5), "donate_wood": r.randint(0, 2), "donate_stone": r.randint(0, 2),
                           "buy_food": r.randint(0, 2), "max_price": r.randint(0, 5), "say": "hi"})


@pytest.mark.parametrize("island", ["capitalist", "capitalist_tax", "socialist"])
@pytest.mark.parametrize("seed", range(3))
def test_island_runs_and_keeps_invariants(island, seed):
    isl = run_island(IslandConfig(island=island, n=30, days=8, seed=seed, workers=1), RandomJSON(seed))
    m = island_metrics(isl)
    assert 0 <= m["survivors"] <= 30
    assert m["survivors"] + m["deaths_starved"] + m["deaths_mobs"] + m["deaths_cave_in"] == 30
    assert all(v >= 0 for p in isl.people for v in p.inv.values()) and all(v >= 0 for v in isl.store.values())
    assert not [e for e in isl.log if e["kind"] == "death" and e["cause"] == "mobs" and e["day"] <= 2]
    if island == "socialist":
        assert m["trades"] == 0 and m["leader"] is not None and m["wealth_gini"] is None
    else:
        assert m["leader"] is None and 0 <= m["wealth_gini"] <= 1


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
