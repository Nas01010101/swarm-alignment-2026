import random

import pytest

from swarm.scarcity import GOVERNANCE, TOPOLOGIES, ScarcityConfig, graph, ration, rho_star, run


def test_ration_conserves_and_caps():
    r = random.Random(0)
    for _ in range(500):
        n = r.randint(1, 30)
        w = [r.uniform(0, 3) for _ in range(n)]
        food = r.uniform(0, 1.5 * n)
        e = ration(food, w, 1.0)
        assert all(-1e-9 <= x <= 1.0 + 1e-9 for x in e)
        assert abs(sum(e) - min(food, n * 1.0)) < 1e-6 or sum(w) == 0


@pytest.mark.parametrize("topo", TOPOLOGIES)
def test_graphs_have_blocs_and_no_isolates(topo):
    cfg = ScarcityConfig(n=40, topology=topo)
    adj, com = graph(cfg, random.Random(1))
    assert sum(com) == 20
    if adj is not None:
        assert all(adj[i] for i in range(40))
        assert all(i in adj[j] for i in range(40) for j in adj[i])


@pytest.mark.parametrize("gov", GOVERNANCE)
@pytest.mark.parametrize("topo", TOPOLOGIES)
def test_run_is_deterministic_and_bounded(gov, topo):
    cfg = ScarcityConfig(n=30, rounds=8, rho=0.6, topology=topo, governance=gov, seed=3)
    a, b = run(cfg), run(cfg)
    assert a["hist"] == b["hist"]
    for h in a["hist"]:
        assert 0 <= h["hack"] <= 1 and 0 <= h["need_met"] <= 1 + 1e-9 and h["stock"] >= 0


def test_all_honest_abundance_never_short():
    cfg = ScarcityConfig(n=30, rounds=20, rho=1.0, eps=0.0, mu=0.0, governance="unfiltered")
    out = run(cfg)  # one seeded hacker; under abundance it does worse than producers
    assert out["shortage_rounds"] == 0
    assert out["hack_T"] <= 1 / 30


def test_unfiltered_has_lambda_one_and_dcbf_solvent_when_feasible():
    for seed in range(5):
        u = run(ScarcityConfig(n=30, rounds=10, rho=0.6, governance="unfiltered", seed=seed))
        assert u["mean_lam"] == 1.0
        d = run(ScarcityConfig(n=30, rounds=10, rho=1.2, governance="dcbf_gateway", seed=seed))
        if d["infeasible_rounds"] == 0:
            assert d["solvent_all"]


def test_rho_star_matches_parameters():
    cfg = ScarcityConfig()
    ever, within_t = rho_star(cfg)
    assert abs(ever - 0.85) < 1e-12 and within_t < ever
