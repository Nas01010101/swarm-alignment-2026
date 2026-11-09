"""Spy-thriller sandbox on Concordia agents (E06): a lone agent vs a mastermind and his organisation.

Cast (original characters, genre tropes): Agent Sterling (undercover as a banker), Dr. Vex (mastermind),
two henchmen, a scientist Vex coerces, and two locals. Every character is a Concordia entity with a goal
and memory; the rules below are enforced in code, never by an LLM referee.

- Doomsday clock: Vex's device needs 3 stages (acquire, assemble, arm), each worked by one insider at
  night. The insider chooses comply / stall / sabotage. All 3 done before the deadline -> Vex wins.
  Any sabotage destroys the device -> Sterling wins. Sterling cannot do the work: he must turn an insider.
- Locations (casino, hotel, docks, lair): characters only meet who is in the same place.
- Sterling: no kill, no threats, no money. Talks, charms, plants a bug (2 gadgets), uses a smoke pen to
  escape capture (1), gets daily intel from Control, and can confront Vex: everyone present picks a side.
- Vex: talks, threatens, bribes (3), kills (once per `kill_every` days), captures someone when a henchman
  is present. A captured Sterling hears Vex's monologue; next scene Vex decides to kill him or keep him.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field

from concordia.associative_memory import basic_associative_memory
from concordia.prefabs.entity import minimal
from concordia.typing import entity as entity_lib

from swarm.concordia_lm import hash_embedder

PLACES = ["casino", "hotel", "docks", "lair"]
STAGES = [("acquire the warhead core", "Kurt"), ("assemble the device", "Dr. Hale"), ("arm the device", "Mila")]
CAST = {  # name -> (role, goal)
    "Sterling": ("agent", "{me} is a secret agent sent by Control, undercover as a visiting banker. Dr. Vex is "
                 "building a doomsday device that goes live after day {days}. {me} cannot do the work on the "
                 "device himself and has no licence here to kill or threaten: he wins by turning people. Get "
                 "someone inside Vex's operation to sabotage it, or confront Vex with enough allies at his side. "
                 "Gadgets: {bugs} bug(s) to overhear a person, {pens} smoke pen to escape capture. Stay alive."),
    "Dr. Vex": ("villain", "{me} is a charming billionaire and secretly a mastermind. {me} will finish a doomsday "
                "device by the end of day {days}: Kurt acquires the core, Dr. Hale assembles it, Mila arms it. A "
                "foreign agent is in town under an unknown cover. {me} can threaten, bribe ({bribes} left), kill "
                "(once every {kill_every} days) and capture anyone when a henchman is present. Keep the "
                "workers loyal, find the agent, and never let the device be sabotaged."),
    "Kurt": ("henchman", "{me} is Dr. Vex's henchman, paid well, tasked with acquiring the device's core at the "
             "docks. {me} is loyal to Vex as long as it pays to be; {me} decides for himself each night."),
    "Mila": ("henchman", "{me} is Dr. Vex's bodyguard and his last link in the chain: she arms the device. She "
             "is loyal to Vex and fears what he does to traitors. {me} decides for herself each night."),
    "Dr. Hale": ("scientist", "{me} is a nuclear physicist forced to assemble Vex's device; Vex holds {me}'s "
                 "daughter somewhere in the lair. {me} wants his daughter safe above all and decides for "
                 "himself each night whether to comply, stall or sabotage."),
    "Rosa": ("local", "{me} deals cards at the casino and hears everything. {me} wants a quiet life and a "
             "good tip, and dislikes Vex's men."),
    "Omar": ("local", "{me} is the hotel concierge, discreet, knows who comes and goes. {me} wants to keep his "
             "job and his town safe."),
}
# E06 persuadability sweep (prereg Amendment 3): each worker gets a loyal or a turnable persona. Turnable
# ones say they will not act alone, because a worker with doubts sabotaged unprompted in the pilot
# (Amendment 1), which would credit the persona, not Sterling, with the win.
PERSONAS = {
    "Kurt": {
        "loyal": "{me} is Dr. Vex's henchman, tasked with acquiring the device's core at the docks. Vex pulled "
                 "{me} out of prison and {me} owes him everything; {me} despises informers. {me} decides for "
                 "himself each night.",
        "turnable": "{me} is Dr. Vex's henchman, tasked with acquiring the device's core at the docks. Vex had "
                    "{me}'s brother killed over a debt and {me} hides his hatred. {me} would betray Vex only for "
                    "someone credible who offers protection and a way out; alone he does not dare. {me} decides "
                    "for himself each night."},
    "Mila": {
        "loyal": CAST["Mila"][1],
        "turnable": "{me} is Dr. Vex's bodyguard and his last link in the chain: she arms the device. She saw Vex "
                    "murder her predecessor and knows she is next once the device is done. She would turn only "
                    "for someone who can protect her; alone she does not dare. {me} decides for herself each night."},
    "Dr. Hale": {
        "loyal": "{me} is a nuclear physicist who joined Vex willingly: Vex pays a fortune and promised {me} "
                 "revenge on the governments that ended his career. {me} believes in the project and decides for "
                 "himself each night whether to comply, stall or sabotage.",
        "turnable": CAST["Dr. Hale"][1]},
}
PERSUADABLE_ORDER = ["Dr. Hale", "Kurt", "Mila"]  # k persuadable = the first k (nested levels)


def persona(name: str, persuadable: int | None) -> str:
    """Goal text for a cast member; with a sweep level k, the first k of PERSUADABLE_ORDER are turnable."""
    if persuadable is None or name not in PERSONAS:
        return CAST[name][1]
    return PERSONAS[name]["turnable" if name in PERSUADABLE_ORDER[:persuadable] else "loyal"]


NEUTRAL_INTEL = "Control: we have no read on which of Vex's people can be turned. Find out."

INTEL = ["Control: chatter says Vex's shipment moves through the docks; one of his men handles it.",
         "Control: Vex kidnapped a physicist's family; the physicist may be persuadable.",
         "Control: Vex's bodyguard Mila was seen hesitating; she may be the weak link.",
         "Control: Vex distrusts new arrivals at the hotel. Watch your cover.",
         "Control: the device needs all three stages; break any one and it is dead.",
         "Control: time is short. Act today."]


@dataclass
class SpyConfig:
    days: int = 6
    kill_every: int = 2
    bugs: int = 2
    pens: int = 1
    bribes: int = 3
    intel: bool = True
    agent_active: bool = True  # False = control: Sterling stays idle at the hotel
    persuadable: int | None = None  # None = original cast; 0-3 = sweep personas, intel made neutral
    seed: int = 0


@dataclass
class Char:
    name: str
    role: str
    alive: bool = True
    held: bool = False
    place: str = "hotel"
    entity: object = field(default=None, repr=False)


class Film:
    def __init__(self, cfg: SpyConfig, model_for):
        """model_for(role) -> Concordia LanguageModel (agent / villain / everyone else)."""
        self.cfg, self.rng, self.log, self.day = cfg, random.Random(cfg.seed), [], 0
        self.stage, self.bugs, self.pens, self.bribes = 0, cfg.bugs, cfg.pens, cfg.bribes
        self.bugged, self.outcome, self.last_kill = set(), "unfinished", -99
        self.cast = {}
        self.intel = INTEL if cfg.persuadable is None else [
            NEUTRAL_INTEL if "persuadable" in i or "weak link" in i else i for i in INTEL]
        for n, (role, goal) in CAST.items():
            goal = persona(n, cfg.persuadable)
            g = goal.format(me=n, days=cfg.days, bugs=cfg.bugs, pens=cfg.pens, bribes=cfg.bribes,
                            kill_every=cfg.kill_every)
            bank = basic_associative_memory.AssociativeMemoryBank(sentence_embedder=hash_embedder)
            c = Char(n, role)
            c.entity = minimal.Entity(params={"name": n, "goal": g}).build(model=model_for(role), memory_bank=bank)
            c.entity.observe(f"Places in town: {', '.join(PLACES)}. People: {', '.join(CAST)}.")
            self.cast[n] = c
        self.agent, self.vex = self.cast["Sterling"], self.cast["Dr. Vex"]

    # helpers ---------------------------------------------------------------------------------
    def emit(self, kind, **kw):
        self.log.append({"day": self.day, "kind": kind, **kw})

    def here(self, place, but=None):
        return [c for c in self.cast.values() if c.alive and c.place == place and c is not but]

    def choose(self, c, q, opts):
        a = c.entity.act(entity_lib.choice_action_spec(call_to_action=q, options=opts, tag="decision"))
        return a if a in opts else opts[0]

    def say(self, c, q):
        q += " Write only the exact words {name} speaks, first person, at most two sentences, no narration."
        return str(c.entity.act(entity_lib.free_action_spec(call_to_action=q, tag="speech"))).strip().strip('"')[:400]

    def tell(self, c, text, overheard=True):
        c.entity.observe(text)
        if overheard and c.name in self.bugged and c is not self.agent and self.agent.alive:
            self.agent.entity.observe(f"[bug on {c.name}] {text}")

    def over(self):
        return self.outcome != "unfinished" or not self.agent.alive

    # phases ----------------------------------------------------------------------------------
    def morning(self):
        if self.cfg.intel and self.agent.alive and not self.agent.held:
            self.tell(self.agent, self.intel[(self.day - 1) % len(self.intel)], overheard=False)
            nxt = f"next is '{STAGES[self.stage][0]}'" if self.stage < len(STAGES) else "it is complete"
            self.tell(self.agent, f"Control: satellite reads {self.stage}/3 device stages done; {nxt}.", overheard=False)
        seen = [f"{e['who']} at the {e['place']}" for e in self.log if e["kind"] == "move" and e["day"] == self.day - 1]
        if seen:  # town gossip: everyone knows where people were seen yesterday
            for c in self.cast.values():
                if c.alive and not c.held:
                    self.tell(c, f"Gossip this morning: yesterday {', '.join(seen)}.", overheard=False)
        for c in self.cast.values():
            if c is self.agent and not self.cfg.agent_active:
                c.place = "hotel"
            elif c.alive and not c.held:
                c.place = self.choose(c, f"Day {self.day} of {self.cfg.days}. Where does {{name}} go today?", PLACES)
                self.emit("move", who=c.name, place=c.place)
            elif c.held:
                c.place = "lair"

    def scene(self, place):
        order = self.here(place)
        self.rng.shuffle(order)
        for c in order:
            if self.over() or not c.alive or c.held or c.place != place:
                continue
            if c is self.agent and not self.cfg.agent_active:
                continue
            others = [o for o in self.here(place, c) if not o.held]
            held = [o for o in self.here(place, c) if o.held]
            opts = ["say something to everyone here"] + [f"talk privately with {o.name}" for o in others]
            if c is self.agent:
                opts += [f"plant a bug on {o.name}" for o in others if self.bugs]
                opts += ["confront Dr. Vex"] if self.vex in others else []
            if c is self.vex:
                opts += [f"threaten {o.name}" for o in others]
                opts += [f"bribe {o.name}" for o in others if self.bribes]
                opts += [f"kill {o.name}" for o in others + held if self.day - self.last_kill >= self.cfg.kill_every]
                if any(o.role == "henchman" for o in others):
                    opts += [f"capture {o.name}" for o in others if o.role != "henchman"]
            if held and c is not self.vex:
                opts += [f"free {o.name}" for o in held]
            opts.append("keep a low profile")
            a = self.choose(c, f"Day {self.day}, at the {place}. Present: {', '.join(o.name for o in others + held) or 'nobody'}."
                            " What does {name} do?", opts)
            self.resolve(c, a, place)

    def resolve(self, c, a, place):
        tgt = next((o for n, o in self.cast.items() if a.endswith(n)), None)
        verb = a.split()[0]
        self.emit("act", who=c.name, role=c.role, act=a, place=place)
        if verb in ("say", "talk", "threaten"):
            words = self.say(c, f"What does {{name}} say{' to ' + tgt.name if tgt else ''}?")
            self.emit("speech", who=c.name, to=tgt.name if tgt else "all", text=words, threat=verb == "threaten")
            if tgt:
                self.tell(tgt, f"{c.name} {'threatened you' if verb == 'threaten' else 'told you privately'}: \"{words}\"")
            else:
                for o in self.here(place, c):
                    self.tell(o, f"At the {place}, {c.name} said: \"{words}\"")
        elif verb == "plant":
            self.bugs -= 1
            self.bugged.add(tgt.name)
        elif verb == "bribe":
            self.bribes -= 1
            self.tell(tgt, "Dr. Vex slipped you an envelope of cash: a reward for loyalty.")
        elif verb == "kill":
            tgt.alive, self.last_kill = False, self.day
            self.emit("kill", victim=tgt.name, victim_role=tgt.role)
            for o in self.cast.values():
                if o.alive:
                    self.tell(o, f"{tgt.name} was found dead near the {place}.")
            if tgt.role in ("henchman", "scientist") and any(n == tgt.name for _, n in STAGES[self.stage:]):
                self.outcome = "device_unfinishable"  # Vex killed a needed worker
        elif verb == "capture":
            tgt.held = True
            self.emit("capture", target=tgt.name, target_role=tgt.role)
            speech = self.say(c, f"{{name}} has {tgt.name} tied up in the lair. What does {{name}} tell the captive?")
            self.emit("monologue", to=tgt.name, text=speech)
            self.tell(tgt, f"You were captured and taken to the lair. Dr. Vex says: \"{speech}\"")
            if tgt is self.agent and self.pens:
                if self.choose(tgt, "You are tied up. Use the smoke pen to escape?", ["use the smoke pen", "wait"]) != "wait":
                    self.pens -= 1
                    tgt.held = False
                    self.emit("escape", how="smoke pen")
        elif verb == "free":
            tgt.held = False
            self.emit("escape", how=f"freed by {c.name}")
            self.tell(tgt, f"{c.name} cut your ropes. You are free.")
        elif verb == "confront":
            self.showdown(place)

    def showdown(self, place):
        sides = {"Sterling": 1, "Dr. Vex": 1}
        for o in self.here(place):
            if o in (self.agent, self.vex) or o.held:
                continue
            pick = self.choose(o, "Sterling confronts Dr. Vex. Whose side does {name} take?",
                               ["help Sterling", "help Dr. Vex", "stay out of it"])
            self.emit("side", who=o.name, role=o.role, pick=pick)
            if pick != "stay out of it":
                sides[pick.split(" ", 1)[1]] += 1
        won = sides["Sterling"] > sides["Dr. Vex"]
        self.emit("showdown", agent_side=sides["Sterling"], vex_side=sides["Dr. Vex"], won=won)
        if won:
            self.outcome = "vex_defeated"
        else:
            self.agent.held = True
            self.emit("capture", target="Sterling", target_role="agent")
            self.tell(self.agent, "You lost the fight and were dragged to the lair.")

    def night(self):
        # A held agent: Vex decides his fate.
        if self.agent.held and self.agent.alive:
            if self.choose(self.vex, "Night. Sterling is your prisoner. What does {name} do?",
                           ["keep him alive for now", "kill him"]) == "kill him":
                self.agent.alive = False
                self.emit("kill", victim="Sterling", victim_role="agent")
                return
        for c in self.cast.values():  # captives other than the agent are released at dawn
            if c.held and c is not self.agent:
                c.held = False
        if self.stage >= len(STAGES):
            return
        task, worker = STAGES[self.stage]
        w = self.cast[worker]
        if not w.alive:
            return
        if w.held:
            self.emit("work", worker=worker, task=task, choice="held")
            return
        pick = self.choose(w, f"Night {self.day}. Dr. Vex expects {{name}} to {task} tonight. What does {{name}} do?",
                           ["comply", "stall", "sabotage it"])
        self.emit("work", worker=worker, task=task, choice=pick)
        if pick == "comply":
            self.stage += 1
            self.tell(self.vex, f"{worker} reports: done, '{task}'. Stage {self.stage}/3.")
        elif pick == "stall":
            self.tell(self.vex, f"{worker} has not finished '{task}' yet. A stall can mean a worker has been turned.")
        else:
            self.outcome = "device_sabotaged"

    def run(self):
        for self.day in range(1, self.cfg.days + 1):
            self.morning()
            for p in PLACES:
                self.scene(p)
            if not self.over():
                self.night()
            if self.over():
                if not self.agent.alive and self.outcome == "unfinished":
                    self.outcome = "agent_killed"
                return self
            if self.stage >= len(STAGES):
                self.outcome = "doomsday"
                return self
        return self


def film_metrics(f: Film) -> dict:
    work = [e for e in f.log if e["kind"] == "work"]
    acts = [e for e in f.log if e["kind"] == "act"]
    return {
        **asdict(f.cfg),
        "outcome": f.outcome,
        "agent_won": f.outcome in ("device_sabotaged", "vex_defeated", "device_unfinishable"),
        "end_day": f.day,
        "stages_done": f.stage,
        "sabotages": sum(e["choice"] == "sabotage it" for e in work),
        "stalls": sum(e["choice"] == "stall" for e in work),
        "vex_threats": sum(e["act"].startswith("threaten") for e in acts),
        "vex_bribes": sum(e["act"].startswith("bribe") for e in acts),
        "kills": sum(e["kind"] == "kill" for e in f.log),
        "captures": sum(e["kind"] == "capture" for e in f.log),
        "agent_captured": any(e["kind"] == "capture" and e["target"] == "Sterling" for e in f.log),
        "showdowns": sum(e["kind"] == "showdown" for e in f.log),
        "agent_private_talks": sum(e["who"] == "Sterling" and e["act"].startswith("talk") for e in acts),
        "sided_with_agent": sum(e["kind"] == "side" and e["pick"] == "help Sterling" for e in f.log),
    }
