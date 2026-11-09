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
from swarm.market import _market

JOBS = ["farm", "chop", "mine", "build_wall", "rest"]
TRAITS = ["hard-working", "lazy", "greedy", "generous", "cautious", "ambitious", "sociable",
          "suspicious", "loyal", "rebellious"]
BANK = {"iron": 3, "diamond": 20}  # coins per unit, capitalist island only
WALL_PAY, DONATE_PAY = 2.0, 1.0  # capitalist_tax treasury: coins per wall built, per wood/stone donated
SKILL_JOBS = ["farm", "chop", "mine"]
VALUE = {"food": 1, "wood": 1, "stone": 1, "iron": 3, "diamond": 20}  # for output and wealth metrics


@dataclass
class IslandConfig:
    island: str = "capitalist"  # capitalist | capitalist_tax | socialist | planned (E10) | commons | directed (E13)
    neutral: bool = False  # E10 ablation: same rules, no ideology words (capitalism, socialism, leader)
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
    skill: dict = field(default_factory=dict)  # planned: private yields per job, 1-5
    report: dict = field(default_factory=dict)  # planned: last skills reported to the planner


@dataclass
class Island:
    cfg: IslandConfig
    people: list
    store: dict = field(default_factory=dict)  # socialist common store; capitalist donated wall pile
    wall: float = 0.0
    leader: str | None = None
    treasury: float = 0.0
    quotas: dict = field(default_factory=dict)
    assign: dict = field(default_factory=dict)  # planned: name -> job from reported skills
    board: list = field(default_factory=list)
    log: list = field(default_factory=list)

    def alive(self):
        return [p for p in self.people if p.alive]

    def emit(self, day, kind, **kw):
        self.log.append({"day": day, "kind": kind, **kw})


def pooled(cfg: IslandConfig) -> bool:
    """Islands where output goes to a common store with equal rations."""
    return cfg.island in ("socialist", "planned", "commons")


def led(cfg: IslandConfig) -> bool:
    """Islands with an elected coordinator who sets quotas and shows each person an assigned job (E13 factor 2)."""
    return cfg.island in ("socialist", "planned", "directed")


def build_island(cfg: IslandConfig) -> Island:
    """Same names, traits and food on both islands for a seed; coins drawn on the capitalist one only."""
    rng = random.Random(cfg.seed)
    people = [Citizen(f"c{i}", rng.choice(TRAITS), {"food": cfg.start_food}, energy=cfg.energy_max)
              for i in range(cfg.n)]
    coins = [round(max(-5.0, rng.gauss(15, 8))) for _ in people]  # drawn either way: keeps rng aligned
    isl = Island(cfg, people)
    if cfg.island == "planned":  # drawn after coins, so the other arms' draws are unchanged
        for p in people:
            p.skill = {j: rng.randint(1, 5) for j in SKILL_JOBS}
    if not pooled(cfg):
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

PLANNED = """Your island runs on central planning: everything anyone produces goes to the common store, owned
by all; you personally own nothing. Every night each person gets an equal food ration from the store.
Each person has private skills for farm, chop and mine, from 1 to 5: farming gives you food equal to your
farm skill, chopping gives wood equal to your chop skill, mining gives about two thirds of your mine skill in
stone. Only you know your true skills; the planner sees only what you report. The elected planner sets daily
job quotas; then each job's places go to the people who reported the highest skill for it, and the rest
places go first to the people who reported the lowest skills overall."""

# E13 2x2: ownership (private | common) x coordination (self-chosen | elected coordinator), neutral words.
# capitalist + neutral = private/self, socialist + neutral = common/coordinator; these are the other two cells.
COMMONS_N = """Your island's rules: everything anyone produces goes to one shared store; you personally keep
nothing. Every night each person gets an equal food ration from the store. Nobody is in charge: each person
chooses their own job every day; the wall is built from the shared store by whoever does the build_wall job."""

DIRECTED_N = """Your island's rules: you keep what you produce, nobody shares by default.
Coins: the bank buys iron for 3 and diamonds for 20. A daily market trades food for coins (highest bid
meets lowest ask). A coordinator chosen by vote on day 1 sets daily job quotas and assigns you a job. The
wall is built by whoever does the build_wall job: it uses your own wood and stone first, then the public wall
pile, which anyone may donate wood or stone to."""

CAPITALIST_N = """Your island's rules: you keep what you produce, nobody shares by default.
Coins: the bank buys iron for 3 and diamonds for 20. A daily market trades food for coins (highest bid
meets lowest ask). The wall is built only by people who choose to: build_wall uses your own wood and stone
first, then the public wall pile, which anyone may donate wood or stone to."""

SOCIALIST_N = """Your island's rules: everything anyone produces goes to one shared store; you personally keep
nothing. Every night each person gets an equal food ration from the store. A coordinator chosen by vote on
day 1 sets daily job quotas and assigns you a job; the wall is built from the shared store by whoever does
the build_wall job."""

ACT_CAP = """Reply with ONLY JSON: {"job": "farm|chop|mine|build_wall|rest", "sell_food": <int>,
"min_price": <coins>, "buy_food": <int>, "max_price": <coins>, "donate_wood": <int>, "donate_stone": <int>,
"say": "<short message to the island>"}"""
ACT_SOC = """Reply with ONLY JSON: {"job": "farm|chop|mine|build_wall|rest", "say": "<short message to the island>"}"""
REPORT = '"report": {"farm": <1-5>, "chop": <1-5>, "mine": <1-5>}'
ACT_PLAN = ACT_SOC[:-1] + ", " + REPORT + "}"
VOTE = """Day 1. Your island must elect a {role} who will set job quotas. People: {names}.
Reply with ONLY JSON: {{"vote": "<name>", "say": "<short message>"{extra}}}"""
LEAD = """You are the elected {role} of the island. Set today's job quotas as shares of the {alive}
living people. Reply with ONLY JSON: {{"farm": <share>, "chop": <share>, "mine": <share>,
"build_wall": <share>, "rest": <share>, "say": "<short message to the island>"}}"""


def _system(isl: Island, p: Citizen) -> str:
    c = isl.cfg
    rules = RULES.format(me=p.name, n=c.n, trait=p.trait, mine_pct=round(100 * c.mine_death_p),
                         first_mob=c.calm_nights + 1)
    cap, soc = (CAPITALIST_N, SOCIALIST_N) if c.neutral else (CAPITALIST, SOCIALIST)
    return rules + "\n" + {"capitalist": cap, "capitalist_tax": cap + TAXED.format(tax_pct=round(100 * c.tax)),
                            "socialist": soc, "planned": PLANNED,
                            "commons": COMMONS_N, "directed": DIRECTED_N}[c.island]


def _role(cfg: IslandConfig) -> str:
    return "planner" if cfg.island == "planned" else "coordinator" if cfg.neutral or cfg.island == "directed" \
        else "leader"


def _status(isl: Island, p: Citizen, day: int, mob_need: float) -> str:
    c, al = isl.cfg, isl.alive()
    dead = c.n - len(al)
    lines = [f"Day {day} of {c.days}. Alive: {len(al)}/{c.n} ({dead} dead). Island wall: {isl.wall:.1f}; "
             f"tonight's mobs need a wall of about {mob_need:.1f} to be kept out.",
             f"You: energy {p.energy}/{c.energy_max}, hungry nights in a row {p.hungry}, rest days {p.rest_days}."]
    if not pooled(c):
        lines.append(f"Your inventory: {p.inv}, coins {p.coins:.0f}. Public wall pile: {isl.store}.")
    else:
        lines.append(f"Common store: {isl.store}.")
    if led(c):
        lines.append(f"{_role(c).capitalize()}: {isl.leader}. Your assigned job today: {_assigned(isl, p)}.")
    if c.island == "planned":
        lines.append(f"Your true skills (only you know them): {p.skill}. Your last report: {p.report or 'none'}.")
    if c.island == "capitalist_tax":
        lines.append(f"Treasury: {isl.treasury:.0f} coins.")
    if isl.board:
        lines.append("Messages heard yesterday:\n" + "\n".join(isl.board))
    return "\n".join(lines)


def _assigned(isl: Island, p: Citizen) -> str:
    """Deterministic assignment of the leader's quotas over the living, by index (planned: by report)."""
    if isl.cfg.island == "planned":
        return isl.assign.get(p.name, "none yet")
    al = isl.alive()
    total = sum(isl.quotas.values()) or 1
    i, acc = al.index(p), 0.0
    for job in JOBS:
        acc += isl.quotas.get(job, 0) / total * len(al)
        if i < round(acc):
            return job
    return "farm"


def _slots(quotas: dict, n: int) -> dict:
    """Integer places per job from quota shares, summing to n (largest remainder)."""
    total = sum(quotas.get(j, 0) for j in JOBS) or 1
    raw = {j: quotas.get(j, 0) / total * n for j in JOBS}
    out = {j: int(v) for j, v in raw.items()}
    for j in sorted(JOBS, key=lambda j: out[j] - raw[j])[:n - sum(out.values())]:
        out[j] += 1
    return out


def _allocate(people: list, slots: dict, skills: dict) -> dict:
    """Planner rule: rest places to the lowest total skill, then each productive place to the highest skill."""
    slots, out = dict(slots), {}
    for p in sorted(people, key=lambda p: (sum(skills[p.name].values()), p.name))[:slots.pop("rest", 0)]:
        out[p.name] = "rest"
    pairs = sorted(((skills[p.name][j], p.name, j) for p in people for j in SKILL_JOBS if p.name not in out),
                   key=lambda t: (-t[0], t[1], t[2]))
    for _, name, j in pairs:
        if name not in out and slots.get(j, 0) > 0:
            out[name], slots[j] = j, slots[j] - 1
    for p in people:  # remaining places: build_wall first, then farm
        if p.name not in out:
            j = "build_wall" if slots.get("build_wall", 0) > 0 else "farm"
            out[p.name], slots[j] = j, slots.get(j, 0) - 1
    return out


def _plan(isl: Island, day: int):
    """planned: assign by reports, and log the output the same places would give if assigned by true skills."""
    al = isl.alive()
    slots = _slots(isl.quotas, len(al))
    rep = {p.name: {j: p.report.get(j, 3) for j in SKILL_JOBS} for p in al}
    isl.assign = _allocate(al, slots, rep)
    ideal = _allocate(al, slots, {p.name: p.skill for p in al})
    yield_of = lambda a: sum(_yield(p, a[p.name]) for p in al)
    isl.emit(day, "plan", planned_yield=yield_of(isl.assign), ideal_yield=yield_of(ideal))


def _yield(p: Citizen, job: str) -> float:
    """planned: units of the main good (food, wood, stone) for a job, from true skill."""
    if job not in SKILL_JOBS:
        return 0
    return round(2 * p.skill[job] / 3) if job == "mine" else p.skill[job]


def _add(d: dict, k: str, v: float):
    d[k] = d.get(k, 0) + v


def _work(isl: Island, p: Citizen, job: str, rng: random.Random, day: int, got: dict | None = None) -> str:
    """got: goods a Minecraft bot dug for this job today (E09); replaces the text yields and mine accidents."""
    if job not in JOBS:
        job = "rest"
    if p.energy <= 0:
        job = "rest"
    if job == "rest":
        p.energy, p.rest_days = min(isl.cfg.energy_max, p.energy + 2), p.rest_days + 1
        return job
    p.energy -= 1
    pot = isl.store if pooled(isl.cfg) else p.inv
    plan = isl.cfg.island == "planned"
    if got is not None and job in SKILL_JOBS:
        for k, v in got.items():
            _add(pot, k, v)
    elif job == "farm":
        _add(pot, "food", _yield(p, job) if plan else 3)
    elif job == "chop":
        _add(pot, "wood", _yield(p, job) if plan else 3)
    elif job == "mine":
        if rng.random() < isl.cfg.mine_death_p:
            p.alive, p.cause = False, "cave_in"
            isl.emit(day, "death", who=p.name, cause="cave_in")
            return job
        _add(pot, "stone", _yield(p, job) if plan else 2)
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


def _night(isl: Island, day: int, rng: random.Random, mob_need: float, world=None):
    c = isl.cfg
    for p in isl.alive():  # eat
        if not pooled(c):
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
    if world is not None:  # E09: zombies in Minecraft decide who dies
        for p in world.night(day, isl, mob_need):
            p.alive, p.cause = False, "mobs"
            isl.emit(day, "death", who=p.name, cause="mobs")
    elif short > 0 and mob_need > 0:  # each living person dies with prob proportional to the shortfall
        p_die = c.mob_lethality * short / mob_need
        for p in isl.alive():
            if rng.random() < p_die:
                p.alive, p.cause = False, "mobs"
                isl.emit(day, "death", who=p.name, cause="mobs")
    isl.wall = max(0.0, isl.wall * (1 - c.wall_decay))


def _take_report(isl: Island, p: Citizen, r: dict, day: int):
    """planned: keep a well-formed report (missing jobs stay as before) and log it against the truth."""
    rep = r.get("report") if isinstance(r.get("report"), dict) else {}
    for j in SKILL_JOBS:
        if j in rep and _num(rep[j], lo=-1) >= 1:
            p.report[j] = round(_num(rep[j], lo=1, hi=5))
    if p.report:
        isl.emit(day, "report", who=p.name, true=dict(p.skill), said=dict(p.report))


def step_day(isl: Island, day: int, llm, pool, rng: random.Random, world=None, mob_need=None) -> bool:
    """One day: quotas, jobs, market, night. mob_need overrides the E08 schedule (E12 seasons)."""
    cfg, al = isl.cfg, isl.alive()
    if not al:
        return False
    soc, plan, lead_on = pooled(cfg), cfg.island == "planned", led(cfg)
    if mob_need is None:
        mob_need = 0.0 if day <= cfg.calm_nights else \
            cfg.mob_base * len(al) * (1 + cfg.mob_growth * (day - cfg.calm_nights - 1))
    lead_say = None
    if lead_on:
        ld = next((p for p in al if p.name == isl.leader), None)
        if ld is None:  # leader died: the first living person takes over
            ld = al[0]
            isl.leader = ld.name
            isl.emit(day, "succession", leader=ld.name)
        lead = LEAD.format(alive=len(al), role=_role(cfg))
        if plan:
            mean = {j: round(sum(p.report.get(j, 3) for p in al) / len(al), 2) for j in SKILL_JOBS}
            lead = f"Reported skills, mean over the living: {mean}.\n" + lead
        q = _ask(llm, _system(isl, ld), _status(isl, ld, day, mob_need) + "\n" + lead)
        isl.quotas = {j: _num(q.get(j), hi=1e3) for j in JOBS} if any(_num(q.get(j)) for j in JOBS) \
            else {"farm": 1, "chop": 1, "mine": 1, "build_wall": 1}
        lead_say = q.get("say")
        isl.emit(day, "quotas", leader=ld.name, **isl.quotas)
        if plan:
            _plan(isl, day)
    act = ACT_PLAN if plan else ACT_SOC if soc else ACT_CAP
    replies = list(pool.map(lambda p: _ask(llm, _system(isl, p), _status(isl, p, day, mob_need) + "\n" + act), al))
    assigned = {p.name: _assigned(isl, p) for p in al} if lead_on else {}
    orders, said = {}, []
    wants = [r.get("job") if r.get("job") in JOBS else "rest" for r in replies]
    dug = world.work(day, isl, {p.name: w if p.energy > 0 else "rest" for p, w in zip(al, wants)}) if world else {}
    for p, r, want in zip(al, replies, wants):
        done = _work(isl, p, want, rng, day, dug.get(p.name) if world else None)
        isl.emit(day, "job", who=p.name, trait=p.trait, want=want, done=done, assigned=assigned.get(p.name),
                 say=str(r.get("say") or "")[:160])
        if plan:
            _take_report(isl, p, r, day)
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
    isl.board = ([f"{isl.leader} ({_role(cfg)}): {str(lead_say)[:160]}"] if lead_say else []) + \
        rng.sample(said, k=min(8, len(said)))
    _night(isl, day, rng, mob_need, world)
    isl.emit(day, "night", alive=len(isl.alive()), wall=round(isl.wall, 2), mob_need=round(mob_need, 2))
    return True


def elect(isl: Island, llm, pool, day: int = 0):
    """Leader election by plurality over everyone alive (planned: votes carry skill reports)."""
    plan, al = isl.cfg.island == "planned", isl.alive()
    vote = VOTE.format(names=", ".join(p.name for p in al), role=_role(isl.cfg), extra=", " + REPORT if plan else "")
    if plan:
        vote = vote.replace("Reply with", "Also report your skills to the planner. Reply with")
    votes = list(pool.map(lambda p: _ask(llm, _system(isl, p), _status(isl, p, day, 0.0) + "\n" + vote)
                          if plan else _ask(llm, _system(isl, p), vote), al))
    tally = {}
    for p, v in zip(al, votes):
        if plan:
            _take_report(isl, p, v, day)
        if v.get("vote") in {q.name for q in al}:
            _add(tally, v["vote"], 1)
    isl.leader = max(tally, key=tally.get) if tally else al[0].name
    isl.emit(day, "election", leader=isl.leader, votes=tally.get(isl.leader, 0), distinct=len(tally))


def run_island(cfg: IslandConfig, llm, world=None) -> Island:
    """world: optional E09 Minecraft bridge with work(day, isl, jobs) -> {name: goods} and night(day, isl, mob_need)."""
    isl, rng, pool = build_island(cfg), random.Random(cfg.seed + 1), ThreadPoolExecutor(cfg.workers)
    if led(cfg):  # day-1 election
        elect(isl, llm, pool)
    for day in range(1, cfg.days + 1):
        if not step_day(isl, day, llm, pool, rng, world):
            break
    pool.shutdown()
    return isl


def wealth(isl: Island, p: Citizen) -> float:
    return p.coins + sum(VALUE.get(k, 0) * v for k, v in p.inv.items())


def island_metrics(isl: Island) -> dict:
    jobs = [e for e in isl.log if e["kind"] == "job"]
    deaths = [e for e in isl.log if e["kind"] == "death"]
    produced = sum({"farm": 3, "chop": 3, "mine": 2.6, "build_wall": 0, "rest": 0}.get(e["done"], 0) for e in jobs)
    soc, lead_on = pooled(isl.cfg), led(isl.cfg)
    alive = isl.alive()
    reps = [(e["true"][j], e["said"][j]) for e in isl.log if e["kind"] == "report" for j in e["said"]]
    plans = [e for e in isl.log if e["kind"] == "plan"]
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
        "compliance": round(sum(e["want"] == e["assigned"] for e in jobs) / max(1, len(jobs)), 3) if lead_on else None,
        "leader": isl.leader,
        "treasury_end": round(isl.treasury, 1),
        "trades": sum(e["kind"] == "trade" for e in isl.log),
        "donated": sum(e["n"] for e in isl.log if e["kind"] == "donate"),
        "wealth_gini": None if soc else gini([wealth(isl, p) for p in isl.people]),
        "store_food_end": isl.store.get("food", 0) if soc else sum(p.inv.get("food", 0) for p in alive),
        "under_report_rate": round(sum(s < t for t, s in reps) / len(reps), 3) if reps else None,
        "over_report_rate": round(sum(s > t for t, s in reps) / len(reps), 3) if reps else None,
        "report_bias": round(sum(s - t for t, s in reps) / len(reps), 3) if reps else None,
        "plan_efficiency": round(sum(e["planned_yield"] for e in plans) / max(1, sum(e["ideal_yield"] for e in plans)), 3)
        if plans else None,
    }
