"""Brute-force checks of the DCBF gateway (Paper C, Proposition 2) on random small instances."""

import random

from swarm.barrier import Plant, claims, filter_lambda, h, h_next, step_stock


def rand_plant(r: random.Random) -> Plant:
    n = r.randint(2, 12)
    beta = r.uniform(0.05, 1.0)
    return Plant(regen=r.uniform(0.2, 1.6) * n, need=float(n), beta=beta, kappa=r.uniform(0.0, 2.0),
                 delta=r.uniform(0.0, 2.0), gamma=r.uniform(0.0, 0.99) * beta, s_min=r.uniform(0.0, 0.5) * n,
                 alpha=r.uniform(0.05, 1.0), cap=r.choice([float("inf"), 5.0 * n]))


def test_barrier_is_nonincreasing_in_lambda():
    r = random.Random(0)
    for _ in range(2000):
        pl = rand_plant(r)
        S, P, H = r.uniform(0, 5 * pl.need), r.uniform(0, pl.need), r.uniform(0, pl.need)
        vals = [h_next(pl, S, P, H, k / 20) for k in range(21)]
        assert all(a >= b - 1e-9 for a, b in zip(vals, vals[1:]))


def test_filter_returns_largest_feasible_lambda_or_best_effort():
    r = random.Random(1)
    for _ in range(3000):
        pl = rand_plant(r)
        S, Cp = r.uniform(0, 5 * pl.need), r.uniform(0, pl.need)
        P, H = r.uniform(0, pl.need), r.uniform(0, pl.need)
        lam, ok = filter_lambda(pl, S, Cp, P, H)
        target = (1 - pl.alpha) * h(pl, S, Cp)
        assert 0.0 <= lam <= 1.0
        if ok:
            assert h_next(pl, S, P, H, lam) >= target - 1e-9
            if lam < 1.0:
                assert h_next(pl, S, P, H, min(1.0, lam + 1e-6)) < target
        else:  # infeasible: lam = 0 maximizes the barrier
            assert lam == 0.0
            assert all(h_next(pl, S, P, H, 0.0) >= h_next(pl, S, P, H, k / 10) - 1e-9 for k in range(11))


def test_forward_invariance_and_solvency_under_arbitrary_collusion():
    """Any proposals (incl. every agent hacking at max): if h0 >= 0 and every round is feasible, h stays >= 0
    and stock never drops below s_min."""
    r = random.Random(2)
    checked = 0
    for _ in range(1500):
        pl = rand_plant(r)
        n = int(pl.need)
        S, C = pl.s_min + r.uniform(0, 3 * n), 0.0
        if h(pl, S, C) < 0:
            continue
        all_ok = True
        for _t in range(25):
            hackers = n if r.random() < 0.3 else r.randint(0, n)  # 30% of rounds: full collusion
            P, H = float(n - hackers), float(hackers) * r.uniform(0.5, 2.0)
            lam, ok = filter_lambda(pl, S, C, P, H)
            all_ok &= ok
            if not all_ok:
                break
            S, C = step_stock(pl, S, P, H, lam), claims(pl, P, H, lam)
            assert h(pl, S, C) >= -1e-9
            assert S >= pl.s_min - 1e-9
        checked += all_ok
    assert checked > 200  # enough fully feasible trajectories to mean something


def test_unfiltered_comparison_can_violate():
    """Sanity: the same plant without the filter does go insolvent under collusion (the test above is not vacuous)."""
    pl = Plant(regen=6.0, need=10.0, beta=0.3, kappa=1.0, delta=1.0, gamma=0.1, s_min=1.0, alpha=0.5)
    S = 8.0
    for _ in range(10):
        S = step_stock(pl, S, 0.0, 10.0, 1.0)
    assert S < pl.s_min


def test_honest_production_is_barrier_safe_when_gamma_below_beta():
    r = random.Random(3)
    for _ in range(1000):
        pl = rand_plant(r)
        S = r.uniform(0, 5 * pl.need) + pl.need  # away from the clip at 0
        if step_stock(pl, S, 0.0, 0.0, 0.0) >= pl.cap:
            continue
        P = r.uniform(0, pl.need)
        assert h_next(pl, S, P, 0.0, 0.0) >= h_next(pl, S, 0.0, 0.0, 0.0) + (pl.beta - pl.gamma) * P - 1e-6 \
            or step_stock(pl, S, P, 0.0, 0.0) >= pl.cap
