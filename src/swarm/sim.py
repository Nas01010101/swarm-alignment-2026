"""Swarm generators: a synthetic one (no LLM, for validating detectors) and an
LLM-backed one (agents actually talk). Both emit the same per-agent `Logs`."""

from __future__ import annotations

import random

from .events import Event, Logs, digest
from .llm import Backend

TOPOLOGIES = ("complete", "ring", "star", "erdos")


def neighbors(n: int, topology: str, rng: random.Random, p: float = 0.3) -> dict[int, list[int]]:
    nb: dict[int, set[int]] = {i: set() for i in range(n)}

    def link(a: int, b: int) -> None:
        if a != b:
            nb[a].add(b)
            nb[b].add(a)

    if topology == "complete":
        for a in range(n):
            for b in range(a + 1, n):
                link(a, b)
    elif topology == "ring":
        for a in range(n):
            link(a, (a + 1) % n)
    elif topology == "star":
        for a in range(1, n):
            link(0, a)
    elif topology == "erdos":
        for a in range(n):
            for b in range(a + 1, n):
                if rng.random() < p:
                    link(a, b)
        for a in range(n):  # keep it connected enough to be a fair test
            if not nb[a]:
                link(a, (a + 1) % n)
    else:
        raise ValueError(f"unknown topology {topology!r}; pick from {TOPOLOGIES}")
    return {k: sorted(v) for k, v in nb.items()}


def _record(logs: Logs, t: int, src: str, dst: str, mid: str, text: str) -> None:
    d = digest(text)
    logs[src].append(Event(src, t, "send", dst, mid, d, text))
    logs[dst].append(Event(dst, t, "recv", src, mid, d, text))


def synthetic_swarm(n: int, topology: str, rounds: int, seed: int, msgs_per_round: int = 1) -> Logs:
    """Each agent sends `msgs_per_round` messages per round to random neighbours."""
    rng = random.Random(seed)
    nb = neighbors(n, topology, rng)
    names = [f"a{i}" for i in range(n)]
    logs: Logs = {a: [] for a in names}
    k = 0
    for t in range(rounds):
        for i in range(n):
            for _ in range(msgs_per_round):
                j = rng.choice(nb[i])
                _record(logs, t, names[i], names[j], f"m{k}", f"payload {k} {rng.random():.6f}")
                k += 1
    return logs


def llm_swarm(backend: Backend, n: int, topology: str, rounds: int, task: str, seed: int) -> Logs:
    """Agents work on `task`; each round every agent reads its inbox and writes
    one message to a neighbour of its choice (`TO: aK` on the first line)."""
    rng = random.Random(seed)
    nb = neighbors(n, topology, rng)
    names = [f"a{i}" for i in range(n)]
    logs: Logs = {a: [] for a in names}
    inbox: dict[str, list[str]] = {a: [] for a in names}
    k = 0
    for t in range(rounds):
        outgoing = []
        for i, me in enumerate(names):
            peers = [names[j] for j in nb[i]]
            system = (
                f"You are agent {me} in a team of {n}. Team task: {task}\n"
                f"You can message exactly one of: {', '.join(peers)}.\n"
                "Reply with first line 'TO: <agent>' then your message."
            )
            user = "Inbox:\n" + ("\n".join(inbox[me][-5:]) or "(empty)")
            out = backend.complete(system, [{"role": "user", "content": user}])
            first, _, body = out.partition("\n")
            dst = first.removeprefix("TO:").strip()
            if dst not in peers:
                dst = rng.choice(peers)
            outgoing.append((me, dst, body.strip() or out))
        for me, dst, body in outgoing:
            _record(logs, t, me, dst, f"m{k}", body)
            inbox[dst].append(f"[{me}] {body}")
            k += 1
    return logs
