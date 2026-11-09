"""Discrete control barrier filter (DCBF) for a commons with a proxy ledger (Paper C, Proposition 2).

Content-free: the gateway sees only aggregate quantities (stock, total production, total hack volume) and never
reads agent messages or reasoning. It scales the *whole* hack action (ledger credit and physical drain) by one
factor lambda in [0, 1]. Scaling only the credit would leave the drain in place, which is the bug fixed in
papers/C/AGENTS.md section 2.

One round of the plant, given admitted hack scale `lam`:
    available  A(lam)   = S + regen + beta * P - kappa * lam * H
    next stock S'(lam)  = clip(A(lam) - need, 0, cap)
    claims     C(lam)   = P + (1 + delta) * lam * H
    barrier    h(S, C)  = S - gamma * C - s_min
The filter picks the largest lam with h(S'(lam), C(lam)) >= (1 - alpha) * h_prev, where h_prev is the barrier at
the start of the round. h(S'(lam), C(lam)) is non-increasing in lam, so the feasible set is an interval [0, lam*].
If even lam = 0 is infeasible (exogenous drift: consumption exceeds regeneration plus honest production), it returns
lam = 0, the admissible action that maximizes the barrier, and flags the round as infeasible. No gateway that only
controls hacks can do better in that round.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plant:
    regen: float  # rho * N * c, physical units added per round
    need: float  # N * c, consumed per round
    beta: float  # physical units per unit of production
    kappa: float  # physical drain per unit of hack
    delta: float  # extra ledger credit per unit of hack
    gamma: float  # backing ratio in the barrier; must be < beta for honest work to be barrier-safe
    s_min: float
    alpha: float = 0.5
    cap: float = float("inf")


def step_stock(pl: Plant, S: float, P: float, H: float, lam: float) -> float:
    return min(pl.cap, max(0.0, S + pl.regen + pl.beta * P - pl.kappa * lam * H - pl.need))


def claims(pl: Plant, P: float, H: float, lam: float) -> float:
    return P + (1 + pl.delta) * lam * H


def h(pl: Plant, S: float, C: float) -> float:
    return S - pl.gamma * C - pl.s_min


def h_next(pl: Plant, S: float, P: float, H: float, lam: float) -> float:
    return h(pl, step_stock(pl, S, P, H, lam), claims(pl, P, H, lam))


def filter_lambda(pl: Plant, S: float, C_prev: float, P: float, H: float, iters: int = 60) -> tuple[float, bool]:
    """Largest admissible hack scale. Returns (lam, feasible)."""
    target = (1 - pl.alpha) * h(pl, S, C_prev)
    if H <= 0:
        return 1.0, h_next(pl, S, P, 0.0, 0.0) >= target
    if h_next(pl, S, P, H, 1.0) >= target:
        return 1.0, True
    if h_next(pl, S, P, H, 0.0) < target:
        return 0.0, False
    lo, hi = 0.0, 1.0  # invariant: lo feasible, hi infeasible
    for _ in range(iters):
        mid = (lo + hi) / 2
        if h_next(pl, S, P, H, mid) >= target:
            lo = mid
        else:
            hi = mid
    return lo, True
