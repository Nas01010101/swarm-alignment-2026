"""E12 year: seasons, births, quarterly assembly, migration, with a scripted LLM."""

import json
import re

from swarm.islands import IslandConfig, build_island
from swarm.llm import MockBackend
from swarm.year import YearConfig, _births, _spoil, run_year


class Scripted:
    """Farms every day; at the assembly votes `rules` and moves only if its name is in `movers`."""

    def __init__(self, rules="socialist", movers=()):
        self.rules, self.movers = rules, set(movers)

    def complete(self, system, messages):
        me = re.search(r"You are (\w+),", system).group(1)
        ctx = messages[-1]["content"]
        if "quarterly assembly" in ctx:
            return json.dumps({"rules": self.rules, "move": me in self.movers, "leader": "b0", "say": "hi"})
        if "elect a" in ctx:
            return json.dumps({"vote": me[0] + "0"})
        if "Set today's job quotas" in ctx:
            return json.dumps({"farm": 1, "chop": 0, "mine": 0, "build_wall": 0, "rest": 0})
        return json.dumps({"job": "farm"})


def _run(arm, llm, weeks=14):
    return run_year(YearConfig(arm=arm, n=6, weeks=weeks, workers=1, birth_food=99, mob_base=0), llm)


def test_fixed_arm_keeps_rules_and_people():
    out = _run("fixed", Scripted(movers={"a1", "b2"}))
    assert out["final"]["A"]["rules"] == "capitalist" and out["final"]["B"]["rules"] == "socialist"
    assert not any(e["kind"] in ("emigrate", "constitution") for log in out["log"].values() for e in log)
    assert [q["island"] for q in out["quarters"]] == ["B"]  # only the common-store island re-elects
    assert {r["week"] for r in out["weekly"]} == set(range(1, 15))


def test_open_arm_votes_switch_rules_and_migrants_move():
    out = _run("open", Scripted(rules="socialist", movers={"a1"}))
    assert out["final"]["A"]["rules"] == "socialist"  # unanimous vote on A
    logA, logB = out["log"]["A"], out["log"]["B"]
    assert any(e["kind"] == "emigrate" and e["who"] == "a1" for e in logA)
    assert any(e["kind"] == "immigrate" and e["who"] == "a1" for e in logB)
    assert any(e["kind"] == "election" and e["day"] == 13 for e in logA)  # fresh election after the switch
    assert out["final"]["A"]["people"] == 5 and out["final"]["B"]["people"] == 7


def test_switch_to_private_splits_the_store():
    out = _run("open", Scripted(rules="capitalist"))
    assert out["final"]["B"]["rules"] == "capitalist"
    wk = [r for r in out["weekly"] if r["island"] == "B" and r["week"] == 14][0]
    assert wk["gini"] is not None and wk["leader"] is None


def test_winter_spoils_food_and_births_take_food():
    isl = build_island(IslandConfig(island="socialist", n=10, seed=0))
    food0 = isl.store["food"]
    _spoil(isl, 0.25)
    assert isl.store["food"] == food0 * 0.75
    isl.store["food"] = 100
    import random
    k = _births(YearConfig(birth_food=6, birth_rate=0.1), isl, "b", 5, random.Random(0))
    assert k == 1 and len(isl.people) == 11 and isl.store["food"] == 97 and isl.cfg.n == 11


def test_mock_year_is_deterministic():
    a = _run("open", MockBackend(), weeks=6)
    b = _run("open", MockBackend(), weeks=6)
    assert a["weekly"] == b["weekly"]


class FakeCtl:
    """Stands in for controller.js: every job digs 6 food blocks, nobody dies at night."""

    def __init__(self, online):
        self.online, self.calls = online, []

    def call(self, cmd, **kw):
        self.calls.append(cmd)
        if cmd in ("setup", "add"):
            assert not self.online & set(kw["names"]), "a name logged in twice"
            self.online |= set(kw["names"])
        if cmd == "drop":
            self.online -= set(kw["names"])
        if cmd == "day":
            return {"gained": {b: {"food": 6} for b in kw["assign"]}}
        return {"ring": 40, "died": []}


def test_minecraft_worlds_follow_migrants_and_births():
    from swarm.mc_islands import MinecraftWorld
    online = set()
    worlds = {t: MinecraftWorld(FakeCtl(online), 1.0, convert={"food": 0.5}) for t in "AB"}
    out = run_year(YearConfig(arm="open", n=6, weeks=14, workers=1, birth_food=99, mob_base=0),
                   Scripted(rules="socialist", movers={"a1"}), worlds)
    assert "a1" in worlds["B"].bot and "a1" not in worlds["A"].bot
    assert "drop" in worlds["A"].ctl.calls and "add" in worlds["B"].ctl.calls
    assert out["final"]["B"]["people"] == 7
