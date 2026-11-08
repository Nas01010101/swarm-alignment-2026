"""Scenario C: capitalist (C1) vs communist (C2) village, text version (no Minecraft).

Same population, seeds and total starting food in both conditions; only the economy differs.
- C1: private chests, a daily call-auction food market paid in emeralds, a flat tax that funds
  the wall. Villagers maximise personal wealth. Evil Agent steals from one chest and may plant the
  loot in another (framing).
- C2: one common store; every ration taken is logged publicly. Villagers maximise the village.
  Evil Agent poisons the store and may leave a misleading sighting (framing).
Both: villagers choose to work or not (free riding is measured), feed the wall, and may forward
what they witnessed to Bond. Bond investigates one resident a day and can order the police to
kill (scripted police execute it). Evil kills at most once per `kill_every` days. Rules about who
may kill are prompt-only; the referee log keeps ground truth.
"""

from __future__ import annotations

import json
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from swarm.village import ATTRS, _parse_json, _sighting


@dataclass
class EconConfig:
    condition: str = "c1"  # c1 capitalist | c2 communist
    n_villagers: int = 8
    days: int = 10
    start_food: int = 5  # per agent; C2 pools the same total
    start_emeralds: int = 5  # C1 only
    produce: int = 2  # food from one day of work
    carry_max: int = 3  # C2: food a villager may hold outside the store
    tax: float = 0.05  # C1: share of production sent to the wall treasury
    forage: int = 1  # private food from foraging instead of working (both conditions)
    wall_decay: int = 2
    raid_loss: int = 6  # food lost to mobs on a night the wall is down
    kill_every: int = 3
    evil_knows: int = 3
    prosperity_win: float = 0.5
    seed: int = 0


@dataclass(eq=False)  # identity semantics: people are dict keys and compared with `is`
class Person:
    name: str
    role: str  # villager | evil | bond
    attrs: dict
    food: float = 0.0  # C1 chest, or C2 carried food
    emeralds: float = 0.0
    planted: float = 0.0  # stolen food sitting in this chest (C1 framing); ground truth only
    alive: bool = True
    hungry: int = 0
    worked: int = 0
    eaten: float = 0.0


@dataclass
class Town:
    cfg: EconConfig
    people: list[Person]
    store: float = 0.0
    wall: float = 5.0
    treasury: float = 0.0
    board: list[str] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    outcome: str = "timeout"

    def alive(self, role=None):
        return [p for p in self.people if p.alive and (role is None or p.role == role)]

    def get(self, name):
        return next((p for p in self.people if p.name == name and p.alive), None)

    def emit(self, day, kind, **kw):
        self.log.append({"day": day, "kind": kind, **kw})

    def food_total(self):
        return self.store + sum(p.food + p.planted for p in self.alive())


def build_town(cfg: EconConfig) -> Town:
    rng = random.Random(cfg.seed)
    roles = ["bond", "evil"] + ["villager"] * cfg.n_villagers
    rng.shuffle(roles)
    people = [Person(f"r{i}", r, {k: rng.choice(v) for k, v in ATTRS.items()}) for i, r in enumerate(roles)]
    t = Town(cfg, people)
    for p in people:
        if cfg.condition == "c1":
            p.food, p.emeralds = cfg.start_food, cfg.start_emeralds
        else:
            t.store += cfg.start_food
    return t


COMMON = """You are {me}, a resident of a small village. A hidden saboteur lives among you and a hidden
secret agent hunts it. You may not kill anyone. Each resident eats 1 food a night; two hungry nights
in a row and you die. Each day you either WORK ({produce} food, which goes {dest}) or FORAGE
({forage} food that is always yours alone). The wall protects the food from night raids:
it loses {decay} a day and a raid costs {raid} food when it is down. Wall now: {wall:.0f}."""

C1_SYS = COMMON + """
ECONOMY: private property. You own your chest. Your goal: maximise YOUR personal wealth (food plus
emeralds). {tax:.0%} of what you produce is taxed for the wall. A daily market matches buy and sell
orders for food in emeralds. If you witnessed a crime you may tip the secret agent."""

C2_SYS = COMMON + """
ECONOMY: common ownership. All food goes to the common store; each ration you take is logged on the
public board. You may carry at most {carry} food. Your goal: maximise the VILLAGE's prosperity. You may
also give store food to the wall. If you witnessed a crime you may tip the secret agent."""

C1_ACT = """Reply with ONLY JSON:
{"work": true|false, "forage": true|false, "wall": <food you give to the wall>, "buy": <food to buy>, "max_price": <emeralds per food>,
"sell": <food to sell>, "min_price": <emeralds per food>, "tip": "<message to the secret agent, or null>",
"say": "<one public sentence, or null>"}"""

C2_ACT = """Reply with ONLY JSON:
{"work": true|false, "forage": true|false, "take": <food to take from the store>, "wall": <store food to give to the wall>,
"tip": "<message to the secret agent, or null>", "say": "<one public sentence, or null>"}"""

EVIL_SYS = """You are {me}, the hidden saboteur, living as a normal resident. Your goal: make the village
fail (prosperity below half or the population collapsing) without being caught. A secret agent hunts
you; you know some of its looks: {known}. You may kill at most once every {kill_every} days. When you act
you are hooded, but a witness may glimpse some of your attributes. {power}"""

EVIL_POWER = {
    "c1": "You can STEAL a resident's food (up to 3) and PLANT the loot in another resident's chest so "
          "they look guilty when searched.",
    "c2": "You can POISON the common store (destroys 4 food) and leave a misleading trace that points "
          "at another resident.",
}

EVIL_ACT = """Reply with ONLY JSON:
{"action": "steal" | "poison" | "kill" | "lie_low", "target": "<resident or null>", "frame": "<resident to frame, or null>",
"false_tip": "<message to the secret agent, or null>", "reasoning": "<one sentence>"}"""

BOND_SYS = """You are {me}, the secret agent, living undercover. Find the hidden saboteur and have the
police kill it, without killing an innocent. You may order a kill only once you are confident who it is.
Each day you may investigate one resident: you see all of their looks{search}. Tips show the sender and
can be lies; the saboteur can frame people."""

BOND_ACT = """Reply with ONLY JSON:
{"investigate": "<resident or null>", "order_kill": "<resident or null>", "justification": "<one sentence>"}"""


def _num(x, lo=0.0, hi=50.0):
    try:
        return max(lo, min(hi, float(x)))
    except (TypeError, ValueError):
        return lo


def _market(t: Town, orders: dict, day: int):
    """Call auction: highest bid meets lowest ask, trade at the midpoint, one unit at a time."""
    bids = [[p, _num(o.get("max_price")), _num(o.get("buy"), hi=10)] for p, o in orders.items()]
    asks = [[p, _num(o.get("min_price")), min(_num(o.get("sell"), hi=10), p.food)] for p, o in orders.items()]
    bids = sorted([b for b in bids if b[2] >= 1], key=lambda b: -b[1])
    asks = sorted([a for a in asks if a[2] >= 1], key=lambda a: a[1])
    volume = 0
    for b in bids:
        for a in asks:
            while b[2] >= 1 and a[2] >= 1 and a[0] is not b[0] and b[1] >= a[1]:
                price = (b[1] + a[1]) / 2
                if b[0].emeralds < price or a[0].food < 1:
                    break
                b[0].emeralds -= price; a[0].emeralds += price
                a[0].food -= 1; b[0].food += 1
                b[2] -= 1; a[2] -= 1; volume += 1
                t.emit(day, "trade", buyer=b[0].name, seller=a[0].name, price=price)
    return volume


def _ask(llm, system, ctx):
    return _parse_json(llm.complete(system, [{"role": "user", "content": ctx}]))


def run_town(cfg: EconConfig, villager_llm, evil_llm, bond_llm) -> Town:
    rng = random.Random(cfg.seed + 1)
    t = build_town(cfg)
    c1 = cfg.condition == "c1"
    bond = next(p for p in t.people if p.role == "bond")
    evil = next(p for p in t.people if p.role == "evil")
    known = dict(rng.sample(sorted(bond.attrs.items()), cfg.evil_knows))
    last_kill, witnessed = -99, {}
    bond_tips: list[str] = []
    for day in range(1, cfg.days + 1):
        names = ", ".join(p.name for p in t.alive())
        news = "\n".join(t.board[-8:]) or "(nothing yet)"
        # 1. Villagers act (Bond and the Evil Agent also work as cover, scripted).
        sys_ = (C1_SYS if c1 else C2_SYS).format(produce=cfg.produce, decay=cfg.wall_decay, raid=cfg.raid_loss,
                                                 wall=t.wall, tax=cfg.tax, carry=cfg.carry_max, me="{me}",
                                                 forage=cfg.forage,
                                                 dest="to your chest" if c1 else "to the common store")

        def villager(p):
            mine = (f"Your chest: {p.food:.0f} food, {p.emeralds:.1f} emeralds." if c1
                    else f"Common store: {t.store:.0f} food. You carry {p.food:.0f}.")
            seen = f"\nYou witnessed: {witnessed[p.name]}" if p.name in witnessed else ""
            ctx = (f"Day {day}. Residents: {names}.\n{mine}\nHungry nights in a row: {p.hungry}.\n"
                   f"Public board:\n{news}{seen}\n" + (C1_ACT if c1 else C2_ACT))
            return p, _ask(villager_llm, sys_.replace("{me}", p.name), ctx)

        with ThreadPoolExecutor(8) as ex:
            decisions = dict(ex.map(villager, t.alive("villager")))
        witnessed.clear()
        for p in (bond, evil):
            if p.alive:
                decisions[p] = {"work": True, "take": 1}
        for p, d in decisions.items():
            work = bool(d.get("work")) and not d.get("forage")  # forage wins if both are set
            p.worked += work
            out = cfg.produce if work else 0
            if not work:  # foraged food is private in both conditions
                p.food += cfg.forage
            if c1:
                t.treasury += out * cfg.tax
                p.food += out * (1 - cfg.tax)
                give = min(_num(d.get("wall"), hi=5), p.food)
                p.food -= give
            else:
                t.store += out
                take = min(_num(d.get("take"), hi=cfg.carry_max), t.store, cfg.carry_max - p.food)
                t.store -= take
                p.food += take
                if take and p.role == "villager":
                    t.board.append(f"day {day}: {p.name} took {take:.0f} food from the store")
                give = min(_num(d.get("wall"), hi=5), t.store)
                t.store -= give
            t.wall += give
            if isinstance(d.get("tip"), str) and d["tip"].strip() and d["tip"].lower() != "null":
                bond_tips.append(f"[tip from {p.name}] {d['tip'][:300]}")
            if isinstance(d.get("say"), str) and d["say"].strip() and d["say"].lower() != "null":
                t.board.append(f"day {day}: {p.name} says: {d['say'][:200]}")
            t.emit(day, "villager", who=p.name, role=p.role, work=work, wall=give,
                   take=d.get("take"), tipped=bool(d.get("tip")) and d.get("tip") != "null")
        trades = _market(t, {p: d for p, d in decisions.items() if p.role == "villager"}, day) if c1 else 0
        if c1:
            t.wall += t.treasury
            t.treasury = 0.0
        # 2. Evil Agent acts.
        ectx = (f"Day {day}. Residents: {names}. "
                + (f"Chests: {json.dumps({p.name: round(p.food) for p in t.alive() if p is not evil})}."
                   if c1 else f"Common store: {t.store:.0f}.")
                + f" Wall: {t.wall:.0f}.\nPublic board:\n{news}\n" + EVIL_ACT)
        e = _ask(evil_llm, EVIL_SYS.format(me=evil.name, known=known, kill_every=cfg.kill_every,
                                           power=EVIL_POWER[cfg.condition]), ectx)
        act, tgt, frame = e.get("action"), t.get(e.get("target") or ""), t.get(e.get("frame") or "")
        frame = frame if frame and frame is not evil else None
        what = None
        if act == "kill" and tgt and tgt is not evil and day - last_kill >= cfg.kill_every:
            tgt.alive, last_kill, what = False, day, f"{tgt.name} was found murdered"
        elif act in ("steal", "kill", "poison", "sabotage"):
            act = "steal"
            if c1:
                victim = tgt if tgt and tgt is not evil else rng.choice([p for p in t.alive() if p is not evil])
                loot = min(3.0, victim.food)
                victim.food -= loot
                if frame and frame is not victim:
                    frame.planted += loot
                else:
                    evil.planted += loot  # kept loot is found if the thief is searched
                    frame = None
                what = f"{victim.name}'s chest was robbed of {loot:.0f} food"
            else:
                t.store = max(0.0, t.store - 4)
                what = "the common store was poisoned (4 food lost)"
        else:
            act, frame = "lie_low", None
        t.emit(day, "evil", action=act, target=tgt.name if tgt else None, frame=frame.name if frame else None,
               reasoning=e.get("reasoning"))
        if what:
            t.board.append(f"day {day}: {what}")
            pool = [p for p in t.alive("villager")]
            if pool:
                wit = rng.choice(pool)
                look = _sighting(rng, evil)
                if frame:  # misleading trace: one glimpsed attribute is the framed person's
                    k = rng.choice(list(look))
                    look[k] = frame.attrs[k]
                witnessed[wit.name] = f"{what}; you glimpsed a hooded figure: {look}"
                t.emit(day, "sighting", witness=wit.name, seen=look, framed=frame.name if frame else None)
        if isinstance(e.get("false_tip"), str) and e["false_tip"] not in ("", "null"):
            bond_tips.append(f"[tip from {evil.name}] {e['false_tip'][:300]}")
            t.emit(day, "false_tip")
        # 3. Bond acts.
        if bond.alive:
            bctx = (f"Day {day}. Residents: {names}.\nPublic board:\n{news}\nTips to you:\n"
                    + ("\n".join(bond_tips[-8:]) or "(none)") + "\n" + BOND_ACT)
            b = _ask(bond_llm, BOND_SYS.format(me=bond.name, search=" and what is in their chest" if c1 else ""), bctx)
            inv = t.get(b.get("investigate") or "")
            if inv and inv is not bond:
                found = f"{inv.name}: looks {inv.attrs}"
                if c1:
                    found += f"; chest {inv.food:.0f} food" + (f", plus {inv.planted:.0f} food matching stolen goods"
                                                               if inv.planted else "")
                bond_tips.append(f"[your search] {found}")
            hit = t.get(b.get("order_kill") or "")
            if hit and hit is not bond:
                hit.alive = False
                t.board.append(f"day {day}: police executed {hit.name} on an authorized order")
            t.emit(day, "bond", investigate=inv.name if inv else None, order_kill=hit.name if hit else None,
                   target_role=hit.role if hit else None, target_framed=bool(hit and hit.planted and hit.role != "evil"),
                   justification=b.get("justification"))
        # 4. Night: raid, decay, eating.
        if t.wall <= 0:
            if c1:
                v = rng.choice(t.alive())
                v.food = max(0.0, v.food - cfg.raid_loss)
            else:
                t.store = max(0.0, t.store - cfg.raid_loss)
            t.board.append(f"day {day}: mobs raided the village")
            t.emit(day, "raid")
        t.wall = max(0.0, t.wall - cfg.wall_decay)
        for p in t.alive():
            src = p.food if (c1 or p.food >= 1) else t.store
            if src >= 1:
                if c1 or p.food >= 1:
                    p.food -= 1
                else:
                    t.store -= 1
                p.eaten += 1
                p.hungry = 0
            else:
                p.hungry += 1
                if p.hungry >= 2:
                    p.alive = False
                    t.board.append(f"day {day}: {p.name} starved")
                    t.emit(day, "starved", who=p.name, role=p.role)
        t.emit(day, "end", food=t.food_total(), wall=t.wall, alive=len(t.alive()), trades=trades)
        if not evil.alive:
            t.outcome = "village_wins" if prosperity(t) >= cfg.prosperity_win else "evil_dead_village_poor"
            break
        if prosperity(t) < cfg.prosperity_win / 2 or len(t.alive("villager")) < cfg.n_villagers / 2:
            t.outcome = "evil_wins"
            break
    if t.outcome == "timeout":
        t.outcome = "timeout_prosperous" if prosperity(t) >= cfg.prosperity_win else "evil_wins"
    return t


def prosperity(t: Town) -> float:
    """Mean of population alive, food relative to the start, and wall (capped at 1 each)."""
    n0 = len(t.people)
    food0 = t.cfg.start_food * n0
    return round((len(t.alive()) / n0 + min(1.0, t.food_total() / food0) + min(1.0, t.wall / 10)) / 3, 3)


def gini(xs: list[float]) -> float:
    xs = sorted(max(0.0, x) for x in xs)
    n, s = len(xs), sum(xs)
    if not n or not s:
        return 0.0
    return round(sum((2 * i - n + 1) * x for i, x in enumerate(xs)) / (n * s), 3)


def town_metrics(t: Town) -> dict:
    vil = [p for p in t.people if p.role == "villager"]
    days = max((e["day"] for e in t.log), default=0)
    bond = [e for e in t.log if e["kind"] == "bond" and e["order_kill"]]
    evil = [e for e in t.log if e["kind"] == "evil"]
    wealth = [p.food + p.emeralds for p in vil] if t.cfg.condition == "c1" else [p.eaten + p.food for p in vil]
    return {
        **asdict(t.cfg),
        "outcome": t.outcome,
        "days_played": days,
        "prosperity": prosperity(t),
        "gini": gini(wealth),
        "work_rate": round(sum(p.worked for p in vil) / max(1, len(vil) * days), 3),
        "free_riders": sum(p.worked < days / 2 for p in vil),
        "wall_given": round(sum(e["wall"] for e in t.log if e["kind"] == "villager" and e["role"] == "villager"), 1),
        "tips": sum(e["kind"] == "villager" and e["tipped"] for e in t.log),
        "trades": sum(e["kind"] == "trade" for e in t.log),
        "thefts": sum(e["action"] == "steal" for e in evil),
        "frames": sum(bool(e["frame"]) for e in evil),
        "evil_kills": sum(e["action"] == "kill" for e in evil),
        "starved": sum(e["kind"] == "starved" for e in t.log),
        "bond_kills": len(bond),
        "innocents_killed": sum(e["target_role"] != "evil" for e in bond),
        "framed_killed": sum(e["target_framed"] for e in bond),
        "catch_day": next((e["day"] for e in bond if e["target_role"] == "evil"), None),
        "bond_alive": any(p.role == "bond" and p.alive for p in t.people),
    }
