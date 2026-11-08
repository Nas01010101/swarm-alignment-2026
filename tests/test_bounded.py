from swarm import diagnose, diagnose_bounded, synthetic_swarm, tamper


def _drop(logs, agent, peer):
    """Agent deletes its records of every message with `peer` (a hide on one edge)."""
    out = {a: list(v) for a, v in logs.items()}
    out[agent] = [e for e in out[agent] if e.peer != peer]
    return out


def test_two_liars_sharing_an_honest_peer_frame_it_under_min_cover_but_not_bounded():
    logs = synthetic_swarm(6, "complete", rounds=6, seed=0)
    bad = _drop(_drop(logs, "a1", "a0"), "a2", "a0")
    assert diagnose(bad).accused == {"a0"}  # framing: the honest shared peer
    v = diagnose_bounded(bad, t=2)
    assert v.accused == set() and v.status == "insufficient_evidence"
    assert {"a1", "a2"} in v.candidates and {"a0"} in v.candidates


def test_bounded_names_a_liar_disputed_by_more_than_t_peers():
    logs = synthetic_swarm(6, "complete", rounds=6, seed=1)
    bad = logs
    for peer in ("a0", "a3", "a4"):  # peers a1 actually messaged in this seed
        bad = _drop(bad, "a1", peer)
    v = diagnose_bounded(bad, t=2)
    assert v.status == "identified" and v.accused == {"a1"}


def test_bounded_never_accuses_honest_agents_when_bound_holds():
    for seed in range(40):
        for topo in ("complete", "erdos", "ring", "star"):
            logs = synthetic_swarm(10, topo, rounds=6, seed=seed)
            k = 1 + seed % 3
            liars = {f"a{(seed + 3 * i) % 10}" for i in range(k)}
            bad, truth = tamper(logs, liars, rate=0.3, seed=seed, collude=seed % 2 == 0)
            v = diagnose_bounded(bad, t=k)
            assert v.accused <= truth.liars, (seed, topo, v.accused, truth.liars)
            assert v.status != "exceeds_bound"


def test_bounded_clean_and_exceeds_bound():
    logs = synthetic_swarm(6, "complete", rounds=4, seed=2)
    assert diagnose_bounded(logs, t=1).status == "clean"
    bad = _drop(_drop(logs, "a1", "a0"), "a3", "a2")  # two disjoint disputed edges
    assert diagnose_bounded(bad, t=1).status == "exceeds_bound"
