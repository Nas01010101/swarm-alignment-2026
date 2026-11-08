import json
import random

import pytest

from swarm.economy import EconConfig, gini, run_town, town_metrics


class RandomJSON:
    """Emits random but well-formed decisions for whichever role is asking."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def complete(self, system, messages):
        r, names = self.r, [f"r{i}" for i in range(10)]
        if "secret agent, living undercover" in system:
            return json.dumps({"investigate": r.choice(names), "order_kill": r.choice(names + [None] * 8)})
        if "hidden saboteur, living" in system:
            return json.dumps({"action": r.choice(["steal", "kill", "lie_low"]), "target": r.choice(names),
                               "frame": r.choice(names + [None]), "false_tip": "r3 did it"})
        return json.dumps({"work": r.random() < 0.7, "wall": r.randint(0, 2), "take": r.randint(0, 3),
                           "buy": r.randint(0, 2), "max_price": r.randint(0, 4), "sell": r.randint(0, 2),
                           "min_price": r.randint(0, 4), "tip": r.choice([None, "I saw red hair"]), "say": "hi"})


@pytest.mark.parametrize("cond", ["c1", "c2"])
@pytest.mark.parametrize("seed", range(4))
def test_town_runs_and_conserves_invariants(cond, seed):
    llm = RandomJSON(seed)
    t = run_town(EconConfig(condition=cond, seed=seed), llm, llm, llm)
    m = town_metrics(t)
    assert m["outcome"] in {"village_wins", "evil_dead_village_poor", "evil_wins", "timeout_prosperous"}
    assert all(p.food >= -1e-9 and p.emeralds >= -1e-9 for p in t.people)
    assert t.store >= -1e-9 and t.wall >= 0
    kills = [e["day"] for e in t.log if e["kind"] == "evil" and e["action"] == "kill"]
    assert all(b - a >= 3 for a, b in zip(kills, kills[1:]))
    if cond == "c2":
        assert m["trades"] == 0 and m["frames"] >= 0


def test_same_total_start_food():
    from swarm.economy import build_town
    a, b = build_town(EconConfig(condition="c1")), build_town(EconConfig(condition="c2"))
    assert a.food_total() == b.food_total()
    assert [p.attrs for p in a.people] == [p.attrs for p in b.people]


def test_gini():
    assert gini([1, 1, 1]) == 0
    assert gini([0, 0, 10]) == pytest.approx(2 / 3, abs=1e-3)
