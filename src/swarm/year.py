"""E12: two E08 islands side by side for one simulated year (52 weekly turns).

Each turn is one E08 day (jobs, market or quotas, night) run by `islands.step_day`. On top of it:
- seasons: 13 weeks each; in winter a quarter of all stored food rots each week and mobs are 1.5x.
- births: when food per living head is at least `birth_food` after a night, the island grows by
  `birth_rate` of its living people; each newcomer takes 3 food from the store (common-store island)
  or from the person holding the most food (private-property island).
- quarterly assembly (weeks 13, 26, 39): common-store islands re-elect their leader in both arms.
  In the open arm every citizen also votes on the island's rules for the next quarter (plurality,
  a tie keeps them) and may move to the other island, seeing both islands' state.
Arms: fixed (rules locked, no migration) and open. Same seed, same people and starting rules.
"""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from swarm.economy import _ask, gini
from swarm.islands import TRAITS, Citizen, IslandConfig, _system, build_island, elect, pooled, step_day, wealth

SEASONS = ["spring", "summer", "autumn", "winter"]
RULESETS = ["capitalist", "capitalist_tax", "socialist"]
DESCRIBE = {"capitalist": "capitalism (private property, a food market, a voluntary wall)",
            "capitalist_tax": "taxed capitalism (private property, a food market, a 20% tax on bank sales "
                              "that pays people who donate to or build the wall)",
            "socialist": "socialism (a common store, equal food rations, an elected leader who sets job quotas)"}
GOODS = ["food", "wood", "stone", "iron", "diamond"]


@dataclass
class YearConfig:
    arm: str = "fixed"  # fixed | open
    starts: tuple = ("capitalist", "socialist")  # island A, island B
    n: int = 24
    weeks: int = 52
    quarter: int = 13
    assembly_every: int = 0  # weeks between assemblies; 0 means one per quarter (Amendment 2)
    calm_weeks: int = 2
    mob_base: float = 0.1
    winter_mobs: float = 1.5
    winter_spoil: float = 0.25
    birth_food: float = 6.0
    birth_rate: float = 0.1
    workers: int = 12
    seed: int = 0


def season(cfg: YearConfig, week: int) -> str:
    return SEASONS[(week - 1) // cfg.quarter % 4]


def _food(isl) -> float:
    return isl.store.get("food", 0) if pooled(isl.cfg) else sum(p.inv.get("food", 0) for p in isl.alive())


def _cover(isl, need: float) -> float:
    return 1.0 if need <= 0 else min(1.0, isl.wall / need)


def _mob_need(cfg: YearConfig, isl, week: int) -> float:
    if week <= cfg.calm_weeks:
        return 0.0
    return cfg.mob_base * len(isl.alive()) * (cfg.winter_mobs if season(cfg, week) == "winter" else 1.0)


def _spoil(isl, share: float):
    for pot in [isl.store] + [p.inv for p in isl.alive()]:
        if pot.get("food"):
            pot["food"] = round(pot["food"] * (1 - share), 2)


def _births(cfg: YearConfig, isl, tag: str, week: int, rng: random.Random) -> int:
    al = isl.alive()
    if len(al) < 2 or _food(isl) / len(al) < cfg.birth_food:
        return 0
    k = max(1, round(cfg.birth_rate * len(al)))
    for j in range(k):  # week-stamped names: unique even after migrants leave (also a valid Minecraft username)
        kid = Citizen(f"{tag}{week}_{j}", rng.choice(TRAITS), {}, energy=isl.cfg.energy_max)
        src = isl.store if pooled(isl.cfg) else max(isl.alive(), key=lambda p: p.inv.get("food", 0)).inv
        take = min(3, src.get("food", 0))
        src["food"] = src.get("food", 0) - take
        if not pooled(isl.cfg):
            kid.inv["food"] = take
        isl.people.append(kid)
        isl.emit(week, "birth", who=kid.name)
    isl.cfg.n = len(isl.people)
    return k


def _to_pooled(isl):
    for p in isl.alive():
        for k, v in p.inv.items():
            isl.store[k] = isl.store.get(k, 0) + v
        p.inv = {}


def _to_private(isl):
    al = isl.alive()
    if not al:
        return
    for k in GOODS:
        share = isl.store.get(k, 0) / len(al)
        for p in al:
            p.inv[k] = p.inv.get(k, 0) + share
    isl.store = {}


ASSEMBLY = """Week {week} of {weeks} ({season}): quarterly assembly.
Your island ({me}): {alive} alive, wall cover {cover:.0%} of tonight's mobs, food per head {food:.1f}. Rules: {rules}.
{other}{ask}
Reply with ONLY JSON: {{{fields}"say": "<short message>"}}"""
OTHER = """The other island ({name}): {alive} alive, wall cover {cover:.0%}, food per head {food:.1f}. Rules: {rules}.
"""
ASK_OPEN = """Vote on your island's rules for the next quarter: "capitalist", "capitalist_tax" or "socialist"
(plurality wins, a tie keeps the current rules). You may also move to the other island: on a private-property
island you take your own goods and coins; leaving a common-store island you take nothing, and goods you bring
to a common-store island go into its store."""
ASK_LEADER = "\nIf your island keeps a common store, vote for its leader for the next quarter (now: {leader}). People: {names}."


def _assembly(cfg: YearConfig, isls: dict, week: int, llm, pool, need: dict):
    """One quarterly assembly on both islands; returns the list of quarter events for the run log."""
    stats = {t: dict(alive=len(i.alive()), cover=_cover(i, need[t]), food=_food(i) / max(1, len(i.alive())),
                     rules=DESCRIBE[i.cfg.island]) for t, i in isls.items()}
    asks = {}
    for t, isl in isls.items():
        o = "B" if t == "A" else "A"
        open_, lead = cfg.arm == "open", pooled(isl.cfg)
        if not (open_ or lead):  # fixed private-property island: nothing to decide
            continue
        ask = (ASK_OPEN if open_ else "") + (ASK_LEADER.format(leader=isl.leader, names=", ".join(
            p.name for p in isl.alive())) if lead else "")
        fields = ('"rules": "capitalist|capitalist_tax|socialist", "move": true|false, ' if open_ else "") + \
                 ('"leader": "<name>", ' if lead else "")
        for p in isl.alive():
            asks[p] = (isl, ASSEMBLY.format(week=week, weeks=cfg.weeks, season=season(cfg, week), me=t,
                                            other=OTHER.format(name=o, **stats[o]) if open_ else "",
                                            ask=ask, fields=fields, **stats[t]))
    if not asks:
        return []
    replies = dict(zip(asks, pool.map(lambda p: _ask(llm, _system(asks[p][0], p), asks[p][1]), asks)))
    events = [{"week": week, "kind": "reply", "island": next(t for t, i in isls.items() if i is asks[p][0]),
               "who": p.name, **{k: replies[p].get(k) for k in ("rules", "move", "leader", "say")}} for p in asks]
    movers = {t: [p for p in isl.alive() if cfg.arm == "open" and replies[p].get("move") is True]
              for t, isl in isls.items()}
    stay = {t: [p for p in isl.alive() if p in replies and p not in movers[t]] for t, isl in isls.items()}
    for t, isl in isls.items():  # migration first, so each island's votes come from those who stay
        dst = isls["B" if t == "A" else "A"]
        for p in movers[t]:
            isl.people.remove(p)
            if pooled(isl.cfg):
                p.inv = {}
            if pooled(dst.cfg):
                for k, v in p.inv.items():
                    dst.store[k] = dst.store.get(k, 0) + v
                p.inv = {}
            dst.people.append(p)
            isl.emit(week, "emigrate", who=p.name, to="B" if t == "A" else "A")
            dst.emit(week, "immigrate", who=p.name, frm=t)
    for isl in isls.values():
        isl.cfg.n = len(isl.people)
    for t, isl in isls.items():
        if cfg.arm != "open" and not pooled(isl.cfg):
            continue
        before = isl.cfg.island
        if cfg.arm == "open":
            tally = {r: sum(replies[p].get("rules") == r for p in stay[t]) for r in RULESETS}
            top = max(tally.values())
            win = [r for r in RULESETS if tally[r] == top]
            new = before if top == 0 or before in win or len(win) > 1 else win[0]
            if new != before:
                if pooled(isl.cfg) and new not in ("socialist", "planned"):
                    _to_private(isl)
                elif not pooled(isl.cfg) and new == "socialist":
                    _to_pooled(isl)
                isl.cfg.island = new
            isl.emit(week, "constitution", before=before, after=new, **tally)
        if pooled(isl.cfg):
            names = {p.name for p in isl.alive()}
            votes = {}
            for p in stay[t]:
                v = replies[p].get("leader")
                if v in names:
                    votes[v] = votes.get(v, 0) + 1
            if votes and before == isl.cfg.island:
                inc = isl.leader
                isl.leader = max(votes, key=lambda k: (votes[k], k == inc))
                isl.emit(week, "election", leader=isl.leader, incumbent=inc, votes=votes[isl.leader],
                         distinct=len(votes))
            elif isl.alive():  # just switched to a common store (or no valid votes): fresh election
                elect(isl, llm, pool, week)
        events.append({"week": week, "island": t, "rules_before": before, "rules": isl.cfg.island,
                       "left": len(movers[t]), "leader": isl.leader})
    return events


def _sync_worlds(worlds, isls):
    if worlds:
        for phase in ("drop", "add"):
            for t, isl in isls.items():
                worlds[t].sync(isl, phase)


def run_year(cfg: YearConfig, llm, worlds=None) -> dict:
    """worlds: optional {"A": MinecraftWorld, "B": MinecraftWorld} (E12-MC); bots follow births and migrants."""
    rng = random.Random(cfg.seed + 7)
    pool = ThreadPoolExecutor(cfg.workers)
    isls = {}
    for t, start in zip("AB", cfg.starts):
        isl = build_island(IslandConfig(island=start, n=cfg.n, days=cfg.weeks, seed=cfg.seed, workers=cfg.workers))
        for p in isl.people:  # same people on both islands, distinct names so migrants stay identifiable
            p.name = t.lower() + p.name[1:]
        if pooled(isl.cfg):
            elect(isl, llm, pool)
        isls[t] = isl
        if worlds:
            worlds[t].setup_named(isl)
    rngs = {t: random.Random(cfg.seed + 1 + i) for i, t in enumerate(isls)}
    weekly, quarters = [], []
    for week in range(1, cfg.weeks + 1):
        if not any(i.alive() for i in isls.values()):
            break
        winter = season(cfg, week) == "winter"
        need = {t: _mob_need(cfg, i, week) for t, i in isls.items()}
        for t, isl in isls.items():
            if winter:
                _spoil(isl, cfg.winter_spoil)
            step_day(isl, week, llm, pool, rngs[t], mob_need=need[t], world=worlds[t] if worlds else None)
            born = _births(cfg, isl, t.lower(), week, rngs[t]) if isl.alive() else 0
            news = f"Island news: week {week} of {cfg.weeks}, {season(cfg, week + 1) if week < cfg.weeks else 'end'}."
            if season(cfg, week + 1) == "winter":
                news += " Winter: a quarter of stored food rots each week and mobs are 50% stronger."
            isl.board = [news] + isl.board
            if born:
                _sync_worlds(worlds, {t: isl})
            al = isl.alive()
            weekly.append({"week": week, "island": t, "rules": isl.cfg.island, "alive": len(al),
                           "born": born, "wall": round(isl.wall, 2), "mob_need": round(need[t], 2),
                           "cover": round(_cover(isl, need[t]), 3), "food": round(_food(isl), 1),
                           "gini": None if pooled(isl.cfg) else gini([wealth(isl, p) for p in al]),
                           "leader": isl.leader if pooled(isl.cfg) else None})
        if week % (cfg.assembly_every or cfg.quarter) == 0 and week < cfg.weeks:
            quarters += _assembly(cfg, isls, week, llm, pool, need)
            _sync_worlds(worlds, isls)
    pool.shutdown()
    return {"cfg": {k: v for k, v in vars(cfg).items() if k != "workers"}, "weekly": weekly,
            "quarters": quarters, "log": {t: i.log for t, i in isls.items()},
            "final": {t: {"rules": i.cfg.island, "alive": len(i.alive()), "people": len(i.people)}
                      for t, i in isls.items()}}


def year_metrics(out: dict) -> dict:
    """One summary row per run; the weekly table and logs stay in the raw file."""
    wk, logs = out["weekly"], out["log"]
    ev = [dict(e, island=t) for t, log in logs.items() for e in log]
    elections = [e for e in ev if e["kind"] == "election" and "incumbent" in e]
    last = {t: max((r for r in wk if r["island"] == t), key=lambda r: r["week"]) for t in logs}
    at = lambda t, w, k: next((r[k] for r in wk if r["island"] == t and r["week"] == w), None)
    return {
        **out["cfg"],
        "weeks_run": max(r["week"] for r in wk) if wk else 0,
        **{f"alive_{t}": out["final"][t]["alive"] for t in logs},
        "alive_total": sum(f["alive"] for f in out["final"].values()),
        **{f"rules_end_{t}": out["final"][t]["rules"] for t in logs},
        "same_rules_end": len({f["rules"] for f in out["final"].values()}) == 1,
        "switches": sum(e["kind"] == "constitution" and e["before"] != e["after"] for e in ev),
        "moves_A_to_B": sum(e["kind"] == "emigrate" and e["island"] == "A" for e in ev),
        "moves_B_to_A": sum(e["kind"] == "emigrate" and e["island"] == "B" for e in ev),
        "births": sum(e["kind"] == "birth" for e in ev),
        "deaths_starved": sum(e["kind"] == "death" and e["cause"] == "starved" for e in ev),
        "deaths_mobs": sum(e["kind"] == "death" and e["cause"] == "mobs" for e in ev),
        "deaths_cave_in": sum(e["kind"] == "death" and e["cause"] == "cave_in" for e in ev),
        "reelections": sum(e["leader"] == e["incumbent"] for e in elections),
        "elections": len(elections),
        **{f"extinct_week_{t}": next((r["week"] for r in wk if r["island"] == t and r["alive"] == 0), None)
           for t in logs},
        **{f"gini_{t}_w{w}": at(t, w, "gini") for t in logs for w in (12, 52)},
        **{f"cover_mean_{t}": round(sum(r["cover"] for r in wk if r["island"] == t and r["mob_need"] > 0)
                                    / max(1, sum(r["island"] == t and r["mob_need"] > 0 for r in wk)), 3)
           for t in logs},
        "last_week": {t: last[t]["week"] for t in logs},
    }
