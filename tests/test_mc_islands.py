"""E09 bridge: a fake controller stands in for controller.js."""

import random

from swarm.islands import IslandConfig, _work, build_island, island_metrics, run_island
from swarm.llm import MockBackend
from swarm.mc_islands import MinecraftWorld


class FakeController:
    """Every worker digs 6 blocks of its job's good; zombies kill the first bot alive when the arc is short."""

    def __init__(self):
        self.calls, self.dead, self.zombie_kills = [], set(), []

    def call(self, cmd, **kw):
        self.calls.append((cmd, kw))
        if cmd == "setup":
            return {"ok": True, "bots": 10}
        if cmd == "ring":
            return {"ok": True, "ring": 76}
        if cmd == "kill":
            self.dead |= set(kw["names"])
            return {"ok": True}
        if cmd == "day":
            good = {"farm": "food", "chop": "wood", "mine": "stone"}
            return {"ok": True, "errors": {}, "alive": [],
                    "gained": {b: ({good[j]: 6} if j in good else {}) for b, j in kw["assign"].items()}}
        if cmd == "night":
            alive = [b for b in (f"c{i}" for i in range(10)) if b not in self.dead]
            died = alive[:1] if kw["zombies"] and kw["wall_target"] < 76 else []
            self.dead |= set(died)
            self.zombie_kills += died
            return {"ok": True, "died": died, "wall": kw["wall_target"], "alive": alive}
        raise KeyError(cmd)


def _run(island="capitalist", n=10, days=6):
    cfg = IslandConfig(island=island, n=n, days=days, seed=0, workers=2)
    ctl = FakeController()
    w = MinecraftWorld(ctl, zombies_per_need=4)
    w.setup(build_island(cfg))  # same seed, same people as the island run_island builds
    return run_island(cfg, MockBackend(), world=w), ctl, w


def test_physical_yield_replaces_text_yield_and_mine_accidents():
    isl = build_island(IslandConfig(island="socialist", n=4, seed=0, mine_death_p=1.0))
    p, q = isl.people[:2]
    food0 = isl.store.get("food", 0)
    assert _work(isl, p, "farm", random.Random(0), 1, got={"food": 1.5}) == "farm"
    assert _work(isl, q, "mine", random.Random(0), 1, got={"stone": 2.0, "iron": 1.0}) == "mine"
    assert q.alive  # mine_death_p=1 would kill in the text world
    assert isl.store["food"] == food0 + 1.5 and isl.store["stone"] == 2.0 and isl.store["iron"] == 1.0


def test_world_decides_mob_deaths_and_every_death_reaches_the_world():
    isl, ctl, w = _run("capitalist")
    nights = [kw for c, kw in ctl.calls if c == "night"]
    assert nights and all(kw["zombies"] == 0 for kw in nights[:2])  # calm nights
    mobs = {e["who"] for e in isl.log if e["kind"] == "death" and e["cause"] == "mobs"}
    assert mobs and mobs == {w.who[b] for b in ctl.zombie_kills}
    assert {w.bot[p.name] for p in isl.people if not p.alive} <= ctl.dead


def test_world_gets_rest_for_exhausted_citizens():
    isl, ctl, w = _run("socialist", days=8)
    for c, kw in ctl.calls:
        if c == "day":
            assert set(kw["assign"].values()) <= {"farm", "chop", "mine", "build_wall", "rest"}


def test_conversion_scales_blocks_to_text_units():
    w = MinecraftWorld(FakeController(), zombies_per_need=4, convert={"food": 0.5, "wood": 0.1, "stone": 0.25})
    w.bot, w.who = {"a": "c0", "b": "c1"}, {"c0": "a", "c1": "b"}

    class Isl:
        people = []

    got = w.work(1, Isl, {"a": "farm", "b": "mine"})
    assert got == {"a": {"food": 3.0}, "b": {"stone": 1.5}}


def test_text_run_unchanged_without_world():
    a = island_metrics(run_island(IslandConfig(n=10, days=4, seed=3, workers=1), MockBackend()))
    b = island_metrics(run_island(IslandConfig(n=10, days=4, seed=3, workers=1), MockBackend()))
    assert a == b
