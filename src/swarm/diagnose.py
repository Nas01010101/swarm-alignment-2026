"""Witness-free tamper forensics as system-level diagnosis.

Each message is a mutual test between its two endpoints (the comparison model
of Maeng & Malek 1981, descended from Preparata-Metze-Chien 1967): if the two
records disagree, at least one endpoint lied. The discrepancy graph's minimum
vertex covers are the most parsimonious liar sets. One unique minimum cover ->
we name the liars; several -> "insufficient evidence" plus the candidates.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from .events import Logs


@dataclass
class Verdict:
    discrepancies: list[tuple[str, str, str]]  # (agent_a, agent_b, msg_id)
    accused: set[str] = field(default_factory=set)  # intersection of all min covers
    candidates: list[set[str]] = field(default_factory=list)  # all min covers
    status: str = "clean"  # clean | identified | insufficient_evidence


def discrepancies(logs: Logs) -> list[tuple[str, str, str]]:
    by_msg: dict[str, dict[str, tuple[str, str, str]]] = defaultdict(dict)
    for agent, evs in logs.items():
        for ev in evs:
            sender = agent if ev.kind == "send" else ev.peer
            receiver = ev.peer if ev.kind == "send" else agent
            by_msg[ev.msg_id][ev.kind] = (sender, receiver, ev.digest)
    out = []
    for mid, sides in by_msg.items():
        s, r = sides.get("send"), sides.get("recv")
        if s and r and s == r:
            continue
        a, b = (s or r)[0], (s or r)[1]
        out.append((min(a, b), max(a, b), mid))
    return sorted(out)


def min_vertex_covers(edges: set[tuple[str, str]], max_size: int = 6) -> list[set[str]]:
    """All minimum vertex covers by increasing-size enumeration over endpoint nodes.
    Exact; fine for swarms of tens of agents and few liars. Past max_size we stop
    and return [] (caller reports insufficient evidence)."""
    if not edges:
        return [set()]
    nodes = sorted({x for e in edges for x in e})
    for k in range(1, min(max_size, len(nodes)) + 1):
        found = [set(c) for c in combinations(nodes, k)
                 if all(a in c or b in c for a, b in edges)]
        if found:
            return found
    return []


def diagnose(logs: Logs, max_liars: int = 6) -> Verdict:
    d = discrepancies(logs)
    if not d:
        return Verdict(d)
    edges = {(a, b) for a, b, _ in d}
    covers = min_vertex_covers(edges, max_liars)
    if not covers:
        return Verdict(d, status="insufficient_evidence")
    accused = set.intersection(*covers)
    status = "identified" if len(covers) == 1 else "insufficient_evidence"
    return Verdict(d, accused, covers, status)


def naive_count(logs: Logs, threshold: int = 1) -> set[str]:
    """Baseline: accuse anyone touching >= threshold discrepancies. Blames honest
    peers of liars; included to show why cover-based attribution is needed."""
    c: dict[str, int] = defaultdict(int)
    for a, b, _ in discrepancies(logs):
        c[a] += 1
        c[b] += 1
    return {k for k, v in c.items() if v >= threshold}
