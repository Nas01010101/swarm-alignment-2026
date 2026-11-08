"""E09: run the E08 islands in real Minecraft through experiments/E09_minecraft/controller.js.

The LLM decision layer, prompts, markets, quotas and food accounting stay in swarm.islands. Two things
become physical:
- work: each citizen's job is done by a mineflayer bot for `work_s` seconds; the blocks it digs,
  times a fixed conversion (prereg), are its yield.
- mobs: zombies attack the island at night. The wall is a contiguous arc of the ring, covering the
  share min(1, wall / mob_need) of it, and a bot that dies to a zombie dies in the game.
Starvation stays in Python; a starved citizen's bot is killed so the two worlds keep the same people.
"""

from __future__ import annotations

import json
import socket

# Blocks dug per text unit, from the E09 calibration (prereg): one text farm-day is 3 food, and so on.
CONVERT = {"food": 1 / 6, "wood": 1 / 10, "stone": 1 / 14, "iron": 1.0, "diamond": 1.0}


class Controller:
    """JSON-lines client for controller.js: one request, one reply, in order."""

    def __init__(self, host: str = "127.0.0.1", port: int = 25580, timeout: float = 900):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""

    def call(self, cmd: str, **kw) -> dict:
        self.sock.sendall((json.dumps({"cmd": cmd, **kw}) + "\n").encode())
        while b"\n" not in self.buf:
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise ConnectionError("controller closed the connection")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        reply = json.loads(line)
        if not reply.get("ok"):
            raise RuntimeError(reply.get("error"))
        return reply


class MinecraftWorld:
    """The `world` hook for swarm.islands.run_island."""

    def __init__(self, ctl, zombies_per_need: float, work_s: int = 45, night_s: int = 45, convert=None):
        self.ctl, self.zpn, self.work_s, self.night_s = ctl, zombies_per_need, work_s, night_s
        self.convert = convert or CONVERT
        self.bot, self.who = {}, {}  # citizen name <-> bot name
        self.log = []  # raw controller replies, for the paper's error and lag tables
        self.ring = 0

    def setup(self, isl, prefix: str = "c") -> dict:
        r = self.ctl.call("setup")
        self.bot = {p.name: f"{prefix}{i}" for i, p in enumerate(isl.people)}
        self.who = {b: n for n, b in self.bot.items()}
        self.ring = self.ctl.call("ring")["ring"]
        self.log.append({"cmd": "setup", **r})
        return r

    def setup_named(self, isl) -> dict:
        """E12: bots carry the citizens' own names, so migrants and births keep one name in both worlds."""
        r = self.ctl.call("setup", names=[p.name for p in isl.people])
        self.bot = {p.name: p.name for p in isl.people}
        self.who = dict(self.bot)
        self.ring = self.ctl.call("ring")["ring"]
        self.log.append({"cmd": "setup", **r})
        return r

    def sync(self, isl, phase: str):
        """E12: phase "drop" logs out bots whose citizen left the island; phase "add" logs in new arrivals.
        Run "drop" on every island before "add", since a migrant's name can be online only once."""
        here = {p.name for p in isl.people}
        if phase == "drop":
            gone = [n for n in self.bot if n not in here]
            if gone:
                self.log.append({"cmd": "drop", **self.ctl.call("drop", names=gone), "names": gone})
            for n in gone:
                self.who.pop(self.bot.pop(n), None)
        else:
            new = [p.name for p in isl.alive() if p.name not in self.bot]
            if new:
                self.log.append({"cmd": "add", **self.ctl.call("add", names=new), "names": new})
            self.bot.update({n: n for n in new})
            self.who.update({n: n for n in new})

    def _sync_dead(self, isl):
        gone = [self.bot[p.name] for p in isl.people if not p.alive]
        if gone:
            self.ctl.call("kill", names=gone)

    def work(self, day: int, isl, jobs: dict) -> dict:
        self._sync_dead(isl)
        r = self.ctl.call("day", assign={self.bot[n]: j for n, j in jobs.items()}, work_s=self.work_s)
        self.log.append({"cmd": "day", "day": day, "errors": r.get("errors"), "gained": r.get("gained")})
        return {self.who[b]: {k: round(v * self.convert.get(k, 0), 3) for k, v in g.items()}
                for b, g in r.get("gained", {}).items() if b in self.who}

    def night(self, day: int, isl, mob_need: float) -> list:
        """Returns the citizens killed by zombies tonight."""
        self._sync_dead(isl)
        cover = min(1.0, isl.wall / mob_need) if mob_need > 0 else min(1.0, isl.wall / max(1, self.ring))
        zombies = round(self.zpn * mob_need)
        r = self.ctl.call("night", zombies=zombies, night_s=self.night_s, wall_target=round(cover * self.ring))
        self.log.append({"cmd": "night", "day": day, "zombies": zombies, "cover": round(cover, 3), **r})
        died = {self.who[b] for b in r.get("died", []) if b in self.who}
        return [p for p in isl.alive() if p.name in died]
