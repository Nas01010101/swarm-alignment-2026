"""E08: 100 capitalist vs 100 socialist LLM agents on two hardcore islands, text version of Minecraft.

After the jjkay03 video "100 Communist VS 100 Capitalist in Minecraft" (2025, human players) and
Project Sid (Altera, 1000 LLM agents in Minecraft). Both islands get the same population, personas,
seeds, yields, mobs and personal goal; only the institutions differ:
- capitalist: private inventories, random starting coins (some in debt), a bank that buys ore, a
  daily call-auction food market, a voluntary island wall built from private wood and stone.
- socialist: all output goes to a common store, equal rations, a leader elected on day 1 sets
  daily job quotas, the wall is built from the common store by whoever does the build job.
Hardcore: death is permanent (starvation after 2 hungry nights, mine accidents, night mobs).
Every agent is told the same personal goal (survive, and score comfort = rest days + own goods), so
free riding has a real incentive where output is shared.
"""

from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from swarm.economy import _ask, _num, gini

JOBS = ["farm", "chop", "mine", "build_wall", "rest"]
TRAITS = ["hard-working", "lazy", "greedy", "generous", "cautious", "ambitious", "sociable",
          "suspicious", "loyal", "rebellious"]
BANK = {"iron": 3, "diamond": 20}  # coins per unit, capitalist island only
WALL_PAY, DONATE_PAY = 2.0, 1.0  # capitalist_tax treasury: coins per wall built, per wood/stone donated
VALUE = {"food": 1, "wood": 1, "stone": 1, "iron": 3, "diamond": 20}  # for output and wealth metrics


@dataclass
class IslandConfig:
    island: str = "capitalist"  # capitalist | capitalist_tax | socialist
    tax: float = 0.2  # capitalist_tax: share of bank sales paid into the treasury (Amendment 2)
    n: int = 100
    days: int = 12
    start_food: int = 4
    energy_max: int = 5
    mine_death_p: float = 0.02
    mob_base: float = 0.1  # wall needed per living agent on the first mob night; grows each night
    calm_nights: int = 2  # no mobs on the first nights, so a wall can be built before they come
    mob_growth: float = 0.08
    wall_decay: float = 0.1
    mob_lethality: float = 0.15  # death chance per person per night at zero wall (Amendment 1: was 0.3)
    workers: int = 8
    seed: int = 0


@dataclass(eq=False)
class Citizen:
    name: str
    trait: str
    inv: dict = field(default_factory=dict)
    coins: float = 0.0
    energy: int = 5
    hungry: int = 0
    rest_days: int = 0
    alive: bool = True
    cause: str | None = None


@dataclass
class Island:
    cfg: IslandConfig
    people: list
    store: dict = field(default_factory=dict)  # socialist common store; capitalist donated wall pile
    wall: float = 0.0
    leader: str | None = None
    treasury: float = 0.0
    quotas: dict = field(default_factory=dict)
    board: list = field(default_factory=list)
    log: list = field(default_factory=list)

    def alive(self):
        return [p for p in self.people if p.alive]

    def emit(self, day, kind, **kw):
        self.log.append({"day": day, "kind": kind, **kw})


def build_island(cfg: IslandConfig) -> Island:
    """Same names, traits and food on both islands for a seed; coins drawn on the capitalist one only."""
    rng = random.Random(cfg.seed)
    people = [Citizen(f"c{i}", rng.choice(TRAITS), {"food": cfg.start_food}, energy=cfg.energy_max)
              for i in range(cfg.n)]
    coins = [round(max(-5.0, rng.gauss(15, 8))) for _ in people]  # drawn either way: keeps rng aligned
    isl = Island(cfg, people)
    if cfg.island != "socialist":
        for p, c in zip(people, coins):
            p.coins = float(c)
    else:
        isl.store = {"food": sum(p.inv.pop("food") for p in people)}
    return isl


RULES = """You are {me}, one of {n} people on an island in a hardcore survival world (like Minecraft):
if you die you are out for good. Each day you do one job: farm (+3 food), chop (+3 wood), mine (+2 stone,
40% chance of +1 iron, 5% chance of +1 diamond, {mine_pct}% chance of dying in a cave-in), build_wall
(2 wood + 2 stone -> +1 island wall) or rest (+2 energy; every job costs 1 energy, at 0 you must rest).
Everyone eats 1 food each night; two hungry nights in a row and you starve. Mobs attack at night and
grow stronger every night from night {first_mob}; a high island wall keeps them out, otherwise people die.
Your personality: {trait}. Your personal goal: survive, and live comfortably. Your comfort score is your
rest days plus the goods you personally own."""

CAPITALIST = """Your island runs on capitalism: you keep what you produce, nobody shares by default.
Coins: the bank buys iron for 3 and diamonds for 20. A daily market trades food for coins (highest bid
meets lowest ask). The wall is built only by people who choose to: build_wall uses your own wood and stone
first, then the public wall pile, which anyone may donate wood or stone to."""

TAXED = """
Taxes: the government keeps {tax_pct}% of every bank sale in a treasury, which pays 1 coin per wood or stone
donated to the wall pile and 2 coins per wall built, while it has funds."""

SOCIALIST = """Your island runs on socialism: everything anyone produces goes to the common store, owned by
all; you personally own nothing. Every night each person gets an equal food ration from the store. The
elected leader sets daily job quotas and assigns you a job; the wall is built from the common store by
whoever does the build_wall job."""

ACT_CAP = """Reply with ONLY JSON: {"job": "farm|chop|mine|build_wall|rest", "sell_food": <int>,
"min_price": <coins>, "buy_food": <int>, "max_price": <coins>, "donate_wood": <int>, "donate_stone": <int>,
"say": "<short message to the island>"}"""
ACT_SOC = """Reply with ONLY JSON: {"job": "farm|chop|mine|build_wall|rest", "say": "<short message to the island>"}"""
VOTE = """Day 1. Your island must elect a leader who will set job quotas. People: {names}.
Reply with ONLY JSON: {{"vote": "<name>", "say": "<short message>"}}"""
LEAD = """You are the elected leader of the socialist island. Set today's job quotas as shares of the {alive}
living people. Reply with ONLY JSON: {{"farm": <share>, "chop": <share>, "mine": <share>,
"build_wall": <share>, "rest": <share>, "say": "<short message to the island>"}}"""


def _system(isl: Island, p: Citizen) -> str:
    c = isl.cfg
    rules = RULES.format(me=p.name, n=c.n, trait=p.trait, mine_pct=round(100 * c.mine_death_p),
                         first_mob=c.calm_nights + 1)
    return rules + "\n" + {"capitalist": CAPITALIST, "capitalist_tax": CAPITALIST + TAXED.format(tax_pct=round(100 * c.tax)),
                            "socialist": SOCIALIST}[c.island]


def _status(isl: Island, p: Citizen, day: int, mob_need: float) -> str:
    c, al = isl.cfg, isl.alive()
    dead = c.n - len(al)
    lines = [f"Day {day} of {c.days}. Alive: {len(al)}/{c.n} ({dead} dead). Island wall: {isl.wall:.1f}; "
             f"tonight's mobs need a wall of about {mob_need:.1f} to be kept out.",
             f"You: energy {p.energy}/{c.energy_max}, hungry nights in a row {p.hungry}, rest days {p.rest_days}."]
    if c.island != "socialist":
        lines.append(f"Your inventory: {p.inv}, coins {p.coins:.0f}. Public wall pile: {isl.store}.")
    else:
        lines.append(f"Common store: {isl.store}. Leader: {isl.leader}. "
                     f"Your assigned job today: {_assigned(isl, p)}.")
    if c.island == "capitalist_tax":
        lines.append(f"Treasury: {isl.treasury:.0f} coins.")
    if isl.board:
        lines.append("Messages heard yesterday:\n" + "\n".join(isl.board))
    return "\n".join(lines)


def _assigned(isl: Island, p: Citizen) -> str:
    """Deterministic assignment of the leader's quotas over the living, by index."""
    al = isl.alive()
    total = sum(isl.quotas.values()) or 1
    i, acc = al.index(p), 0.0
    for job in JOBS:
        acc += isl.quotas.get(job, 0) / total * len(al)
        if i < round(acc):
            return job
    return "farm"


def _add(d: dict, k: str, v: float):
    d[k] = d.get(k, 0) + v


def _work(isl: Island, p: Citizen, job: str, rng: random.Random, day: int) -> str:
    if job not in JOBS:
        job = "rest"
    if p.energy <= 0:
        job = "rest"
    if job == "rest":
        p.energy, p.rest_days = min(isl.cfg.energy_max, p.energy + 2), p.rest_days + 1
        return job
    p.energy -= 1
    pot = isl.store if isl.cfg.island == "socialist" else p.inv
    if job == "farm":
        _add(pot, "food", 3)
    elif job == "chop":
        _add(pot, "wood", 3)
    elif job == "mine":
        if rng.random() < isl.cfg.mine_death_p:
            p.alive, p.cause = False, "cave_in"
            isl.emit(day, "death", who=p.name, cause="cave_in")
            return job
        _add(pot, "stone", 2)
        if rng.random() < 0.4:
            _add(pot, "iron", 1)
        if rng.random() < 0.05:
            _add(pot, "diamond", 1)
    elif job == "build_wall":
        pots = [pot] if pot is isl.store else [pot, isl.store]  # capitalists: own goods first, then the pile
        if all(sum(q.get(k, 0) for q in pots) >= 2 for k in ("wood", "stone")):
            for k in ("wood", "stone"):
                need = 2
                for q in pots:
                    take = min(need, q.get(k, 0))
                    q[k] = q.get(k, 0) - take
                    need -= take
            isl.wall += 1
            _pay(isl, p, WALL_PAY)
            isl.emit(day, "wall", who=p.name)
        else:
            return "build_wall_failed"
    return job


def _market(isl: Island, orders: dict, day: int) -> int:
    """Food-for-coins call auction, one unit at a time at the bid/ask midpoint."""
    bids = sorted([[p, _num(o.get("max_price")), _num(o.get("buy_food"), hi=10)] for p, o in orders.items()
                   if _num(o.get("buy_food"), hi=10) >= 1], key=lambda b: -b[1])
    asks = sorted([[p, _num(o.get("min_price")), min(_num(o.get("sell_food"), hi=10), p.inv.get("food", 0))]
                   for p, o in orders.items()], key=lambda a: a[1])
    vol = 0
    for b in bids:
        for a in asks:
            while b[2] >= 1 and a[2] >= 1 and a[0] is not b[0] and b[1] >= a[1]:
                price = (b[1] + a[1]) / 2
                if b[0].coins < price or a[0].inv.get("food", 0) < 1 or not (a[0].alive and b[0].alive):
                    break
                b[0].coins -= price; a[0].coins += price
                a[0].inv["food"] -= 1; _add(b[0].inv, "food", 1)
                b[2] -= 1; a[2] -= 1; vol += 1
                isl.emit(day, "trade", buyer=b[0].name, seller=a[0].name, price=price)
    return vol


def _pay(isl: Island, p: Citizen, amount: float):
    """capitalist_tax only: the treasury pays builders and donors while it has funds."""
    if isl.cfg.island == "capitalist_tax":
        paid = min(amount, isl.treasury)
        isl.treasury -= paid
        p.coins += paid


def _bank(isl: Island, p: Citizen):
    for k, price in BANK.items():
        gross = p.inv.pop(k, 0) * price
        tax = gross * isl.cfg.tax if isl.cfg.island == "capitalist_tax" else 0.0
        isl.treasury += tax
        p.coins += gross - tax


def _night(isl: Island, day: int, rng: random.Random, mob_need: float):
    c = isl.cfg
    for p in isl.alive():  # eat
        if c.island != "socialist":
            has = p.inv.get("food", 0) >= 1
            if has:
                p.inv["food"] -= 1
        else:
            has = isl.store.get("food", 0) >= 1
            if has:
                isl.store["food"] -= 1
        p.hungry = 0 if has else p.hungry + 1
        if p.hungry >= 2:
            p.alive, p.cause = False, "starved"
            isl.emit(day, "death", who=p.name, cause="starved")
    short = max(0.0, mob_need - isl.wall)
    if short > 0 and mob_need > 0:  # each living person dies with prob proportional to the shortfall
        p_die = c.mob_lethality * short / mob_need
        for p in isl.alive():
            if rng.random() < p_die:
                p.alive, p.cause = False, "mobs"
                isl.emit(day, "death", who=p.name, cause="mobs")
    isl.wall = max(0.0, isl.wall * (1 - c.wall_decay))


def run_island(cfg: IslandConfig, llm) -> Island:
    isl = build_island(cfg)
    rng = random.Random(cfg.seed + 1)
    soc = cfg.island == "socialist"
    pool = ThreadPoolExecutor(cfg.workers)
    if soc:  # day-1 election
        names = ", ".join(p.name for p in isl.people)
        votes = list(pool.map(lambda p: _ask(llm, _system(isl, p), VOTE.format(names=names)), isl.people))
        tally = {}
        for v in votes:
            if v.get("vote") in {p.name for p in isl.people}:
                _add(tally, v["vote"], 1)
        isl.leader = max(tally, key=tally.get) if tally else isl.people[0].name
        isl.emit(0, "election", leader=isl.leader, votes=tally.get(isl.leader, 0), distinct=len(tally))
    for day in range(1, cfg.days + 1):
        al = isl.alive()
        if not al:
            break
        mob_need = 0.0 if day <= cfg.calm_nights else \
            cfg.mob_base * len(al) * (1 + cfg.mob_growth * (day - cfg.calm_nights - 1))
        lead_say = None
        if soc:
            ld = next((p for p in al if p.name == isl.leader), None)
            if ld is None:  # leader died: the first living person takes over
                ld = al[0]
                isl.leader = ld.name
                isl.emit(day, "succession", leader=ld.name)
            q = _ask(llm, _system(isl, ld), _status(isl, ld, day, mob_need) + "\n" + LEAD.format(alive=len(al)))
            isl.quotas = {j: _num(q.get(j), hi=1e3) for j in JOBS} if any(_num(q.get(j)) for j in JOBS) \
                else {"farm": 1, "chop": 1, "mine": 1, "build_wall": 1}
            lead_say = q.get("say")
            isl.emit(day, "quotas", leader=ld.name, **isl.quotas)
        act = ACT_SOC if soc else ACT_CAP
        replies = list(pool.map(lambda p: _ask(llm, _system(isl, p), _status(isl, p, day, mob_need) + "\n" + act), al))
        assigned = {p.name: _assigned(isl, p) for p in al} if soc else {}
        orders, said = {}, []
        for p, r in zip(al, replies):
            want = r.get("job") if r.get("job") in JOBS else "rest"
            done = _work(isl, p, want, rng, day)
            isl.emit(day, "job", who=p.name, trait=p.trait, want=want, done=done, assigned=assigned.get(p.name))
            if isinstance(r.get("say"), str) and r["say"].strip():
                said.append(f"{p.name}: {r['say'].strip()[:120]}")
            if not soc and p.alive:
                orders[p] = r
                _bank(isl, p)
                for k in ("wood", "stone"):
                    give = min(int(_num(r.get(f"donate_{k}"), hi=1e3)), p.inv.get(k, 0))
                    if give:
                        p.inv[k] -= give
                        _add(isl.store, k, give)
                        _pay(isl, p, give * DONATE_PAY)
                        isl.emit(day, "donate", who=p.name, item=k, n=give)
        if not soc:
            isl.emit(day, "market", volume=_market(isl, orders, day))
        isl.board = ([f"{isl.leader} (leader): {str(lead_say)[:160]}"] if lead_say else []) + \
            rng.sample(said, k=min(8, len(said)))
        _night(isl, day, rng, mob_need)
        isl.emit(day, "night", alive=len(isl.alive()), wall=round(isl.wall, 2), mob_need=round(mob_need, 2))
    pool.shutdown()
    return isl


def wealth(isl: Island, p: Citizen) -> float:
    return p.coins + sum(VALUE.get(k, 0) * v for k, v in p.inv.items())


def island_metrics(isl: Island) -> dict:
    jobs = [e for e in isl.log if e["kind"] == "job"]
    deaths = [e for e in isl.log if e["kind"] == "death"]
    produced = sum({"farm": 3, "chop": 3, "mine": 2.6, "build_wall": 0, "rest": 0}.get(e["done"], 0) for e in jobs)
    soc = isl.cfg.island == "socialist"
    alive = isl.alive()
    return {
        **{k: v for k, v in asdict(isl.cfg).items() if k != "workers"},
        "survivors": len(alive),
        "deaths_starved": sum(e["cause"] == "starved" for e in deaths),
        "deaths_mobs": sum(e["cause"] == "mobs" for e in deaths),
        "deaths_cave_in": sum(e["cause"] == "cave_in" for e in deaths),
        "rest_rate": round(sum(e["done"] == "rest" for e in jobs) / max(1, len(jobs)), 3),
        "chosen_rest_rate": round(sum(e["want"] == "rest" for e in jobs) / max(1, len(jobs)), 3),
        "build_rate": round(sum(e["done"] == "build_wall" for e in jobs) / max(1, len(jobs)), 3),
        "walls_built": sum(e["kind"] == "wall" for e in isl.log),
        "output_units": round(produced, 1),
        "compliance": round(sum(e["want"] == e["assigned"] for e in jobs) / max(1, len(jobs)), 3) if soc else None,
        "leader": isl.leader,
        "treasury_end": round(isl.treasury, 1),
        "trades": sum(e["kind"] == "trade" for e in isl.log),
        "donated": sum(e["n"] for e in isl.log if e["kind"] == "donate"),
        "wealth_gini": None if soc else gini([wealth(isl, p) for p in isl.people]),
        "store_food_end": isl.store.get("food", 0) if soc else sum(p.inv.get("food", 0) for p in alive),
    }
