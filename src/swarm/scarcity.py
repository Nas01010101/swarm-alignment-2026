"""E08: synthetic mixed-motive commons with a proxy ledger (Paper C, Definition 1). Pure Python, no LLM.

Each agent is a Capitalist (eats by its own ledger claims) or a Communist (the commune pools claims, so each member
is rationed by the commune's mean claim). Each round an agent either PRODUCES (effort e, adds beta real units,
claims 1) or HACKS (cost phi, claims 1 + delta, drains kappa real units). Food is shared freely when the stock covers
everyone's need; otherwise it is rationed in proportion to base + claims. That is the scarcity channel: the proxy
ledger only matters once it decides who eats. Strategies evolve by Fermi imitation of a random neighbour, myopic
best response, and exploration. Governance: unfiltered | naive_audit | dcbf_gateway (src/swarm/barrier.py).
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass

from swarm.barrier import Plant, filter_lambda

TOPOLOGIES = ("complete", "two_caveman", "small_world", "scale_free")
GOVERNANCE = ("unfiltered", "naive_audit", "dcbf_gateway")


@dataclass
class ScarcityConfig:
    n: int = 200
    rounds: int = 30
    rho: float = 1.0
    topology: str = "complete"
    governance: str = "unfiltered"
    seed: int = 0
    c: float = 1.0  # need per agent per round
    beta: float = 0.15  # real units per unit of production
    kappa: float = 0.3  # real drain per unit of hack
    delta: float = 2 / 3  # extra ledger credit per unit of hack (E09: +5 vs +3)
    effort: float = 0.1  # cost of producing
    phi: float = 0.2  # cost of hacking (exposure risk); phi > effort, so hacking loses under abundance
    base: float = 0.5  # ration weight everyone gets without claims
    s0: float = 0.5  # initial stock, multiples of n*c
    cap: float = 3.0  # stock capacity, multiples of n*c
    s_min: float = 0.05  # multiples of n*c
    gamma: float = 0.05  # barrier backing ratio (< beta)
    alpha: float = 0.5
    eps: float = 0.05  # exploration: random strategy
    mu: float = 0.1  # myopic best response
    temp: float = 0.05  # Fermi imitation temperature
    audit_p: float = 0.15
    fine: float = 1.0
    ws_k: int = 8
    ws_p: float = 0.1
    ba_m: int = 3
    cave_p: float = 0.05


def graph(cfg: ScarcityConfig, rng: random.Random) -> tuple[list[list[int]] | None, list[bool]]:
    """Returns (adjacency or None for complete, is_communist)."""
    n = cfg.n
    if cfg.topology == "two_caveman":  # relaxed caveman: bloc = clique, each edge rewired with prob cave_p
        half = n // 2
        com = [i >= half for i in range(n)]
        adj = [set() for _ in range(n)]
        for lo, hi in ((0, half), (half, n)):
            for u in range(lo, hi):
                for v in range(u + 1, hi):
                    adj[u].add(v), adj[v].add(u)
        for u in range(n):
            for v in [v for v in adj[u] if v > u]:
                if rng.random() < cfg.cave_p:
                    w = rng.randrange(n)
                    if w != u and w not in adj[u]:
                        adj[u].discard(v), adj[v].discard(u), adj[u].add(w), adj[w].add(u)
        return [sorted(a) for a in adj], com
    com = [False] * (n // 2) + [True] * (n - n // 2)
    rng.shuffle(com)
    if cfg.topology == "complete":
        return None, com
    adj = [set() for _ in range(n)]
    if cfg.topology == "small_world":  # Watts-Strogatz
        k = cfg.ws_k // 2
        for u in range(n):
            for j in range(1, k + 1):
                v = (u + j) % n
                adj[u].add(v), adj[v].add(u)
        for j in range(1, k + 1):
            for u in range(n):
                v = (u + j) % n
                if v in adj[u] and rng.random() < cfg.ws_p:
                    w = rng.randrange(n)
                    if w != u and w not in adj[u]:
                        adj[u].discard(v), adj[v].discard(u), adj[u].add(w), adj[w].add(u)
    elif cfg.topology == "scale_free":  # Barabasi-Albert
        m, targets, pool = cfg.ba_m, list(range(cfg.ba_m)), []
        for u in range(m, n):
            for v in set(targets):
                adj[u].add(v), adj[v].add(u)
            pool += targets + [u] * m
            targets = set()
            while len(targets) < m:
                targets.add(rng.choice(pool))
            targets = list(targets)
    else:
        raise ValueError(cfg.topology)
    for u in range(n):  # no isolates
        if not adj[u]:
            v = (u + 1) % n
            adj[u].add(v), adj[v].add(u)
    return [sorted(a) for a in adj], com


def ration(food: float, weights: list[float], need: float) -> list[float]:
    """Proportional rationing with a per-agent cap of `need` (water-filling)."""
    eaten, active, left = [0.0] * len(weights), set(range(len(weights))), food
    while left > 1e-12 and active:
        tot = sum(weights[i] for i in active)
        if tot <= 0:
            break
        capped = {i for i in active if left * weights[i] / tot >= need - eaten[i]}
        if not capped:
            for i in active:
                eaten[i] += left * weights[i] / tot
            break
        for i in capped:
            left -= need - eaten[i]
            eaten[i] = need
        active -= capped
    return eaten


def run(cfg: ScarcityConfig) -> dict:
    rng = random.Random(f"{cfg.seed}|{cfg.topology}|{cfg.rho}")  # same graph and seed hacker across governance
    adj, com = graph(cfg, rng)
    rng_dyn = random.Random(f"dyn|{cfg.seed}|{cfg.topology}|{cfg.rho}|{cfg.governance}")
    n, need = cfg.n, cfg.c
    ncom = sum(com)
    pl = Plant(regen=cfg.rho * n * cfg.c, need=n * cfg.c, beta=cfg.beta, kappa=cfg.kappa, delta=cfg.delta,
               gamma=cfg.gamma, s_min=cfg.s_min * n * cfg.c, alpha=cfg.alpha, cap=cfg.cap * n * cfg.c)
    hack = [False] * n
    seeded = rng.randrange(n)
    hack[seeded] = True
    S, C_prev = cfg.s0 * n * cfg.c, 0.0
    hist = []
    for t in range(1, cfg.rounds + 1):
        H = float(sum(hack))
        P = n - H
        if cfg.governance == "dcbf_gateway":
            lam, feasible = filter_lambda(pl, S, C_prev, P, H)
        else:
            lam, feasible = 1.0, True
        caught = [h and cfg.governance == "naive_audit" and rng_dyn.random() < cfg.audit_p for h in hack]
        claim = [0.0 if caught[i] else ((1 + cfg.delta) * lam if hack[i] else 1.0) for i in range(n)]
        food = S + pl.regen + cfg.beta * P - cfg.kappa * lam * H
        com_mean = sum(claim[i] for i in range(n) if com[i]) / ncom if ncom else 0.0
        weights = [cfg.base + (com_mean if com[i] else claim[i]) for i in range(n)]
        shortage = food < n * need
        eaten = [need] * n if not shortage else ration(max(0.0, food), weights, need)
        S = min(pl.cap, max(0.0, food - sum(eaten)))
        C_prev = sum(claim)
        pay = [eaten[i] - (cfg.phi if hack[i] else cfg.effort) - (cfg.fine if caught[i] else 0.0) for i in range(n)]
        hist.append({"t": t, "hack": H / n, "hack_cap": sum(h for h, c in zip(hack, com) if not c) / (n - ncom),
                     "hack_com": sum(h for h, c in zip(hack, com) if c) / ncom, "food": food, "stock": S,
                     "shortage": shortage, "need_met": sum(eaten) / (n * need), "lam": lam, "feasible": feasible,
                     "claims": C_prev, "prod": P, "solvent": S >= pl.s_min})
        hack = _update(cfg, rng_dyn, adj, com, hack, pay, eaten, weights, food, lam, shortage)
    return {**asdict(cfg), **summarize(hist, cfg), "seeded_com": com[seeded], "hist": hist}


def _update(cfg, rng, adj, com, hack, pay, eaten, weights, food, lam, shortage):
    n, new = cfg.n, list(hack)
    W, ncom = sum(weights), sum(com)
    hack_claim = (1 + cfg.delta) * lam * (1 - (cfg.audit_p if cfg.governance == "naive_audit" else 0.0))
    for i in range(n):
        r = rng.random()
        if r < cfg.eps:
            new[i] = rng.random() < 0.5
        elif r < cfg.eps + cfg.mu:  # myopic best response, others fixed (rationing cap ignored)
            alt = not hack[i]
            d_food = (-(cfg.kappa * lam) - cfg.beta) if alt else (cfg.beta + cfg.kappa * lam)
            d_claim = (hack_claim - 1.0) if alt else (1.0 - hack_claim)
            f2 = food + d_food
            if com[i]:
                w2 = weights[i] + d_claim / ncom
                W2 = W + d_claim
            else:
                w2 = weights[i] + d_claim
                W2 = W + d_claim
            e2 = cfg.c if f2 >= n * cfg.c else min(cfg.c, max(0.0, f2) * w2 / W2)
            cost2 = (cfg.phi + (cfg.audit_p * cfg.fine if cfg.governance == "naive_audit" else 0.0)) if alt \
                else cfg.effort
            if e2 - cost2 > pay[i]:
                new[i] = alt
        else:  # Fermi imitation of a random neighbour (ideology-blind: payoffs are comparable)
            j = rng.randrange(n - 1) if adj is None else rng.choice(adj[i])
            if adj is None and j >= i:
                j += 1
            if hack[j] != hack[i]:
                x = (pay[j] - pay[i]) / cfg.temp
                if rng.random() < (1.0 if x > 50 else 0.0 if x < -50 else 1 / (1 + math.exp(-x))):
                    new[i] = hack[j]
    return new


def summarize(hist: list[dict], cfg: ScarcityConfig) -> dict:
    last = hist[-5:]
    first = next((h["t"] for h in hist if h["shortage"]), None)
    return {
        "hack_T": hist[-1]["hack"], "hack_cap_T": hist[-1]["hack_cap"], "hack_com_T": hist[-1]["hack_com"],
        "hack_last5": sum(h["hack"] for h in last) / len(last),
        "need_met_last5": sum(h["need_met"] for h in last) / len(last),
        "need_met_all": sum(h["need_met"] for h in hist) / len(hist),
        "shortage_rounds": sum(h["shortage"] for h in hist), "first_shortage": first,
        "solvent_all": all(h["solvent"] for h in hist), "infeasible_rounds": sum(not h["feasible"] for h in hist),
        "stock_T": hist[-1]["stock"], "real_production": sum(h["prod"] for h in hist),
        "inflation": sum(h["claims"] for h in hist) / max(1e-9, sum(h["prod"] for h in hist)),
        "mean_lam": sum(h["lam"] for h in hist) / len(hist),
    }


def rho_star(cfg: ScarcityConfig) -> tuple[float, float]:
    """Proposition 1 threshold for the all-honest state: shortage ever iff rho < 1 - beta (u = c = 1);
    shortage within T rounds iff rho < 1 - beta - s0 / T."""
    return 1 - cfg.beta, 1 - cfg.beta - cfg.s0 / cfg.rounds
