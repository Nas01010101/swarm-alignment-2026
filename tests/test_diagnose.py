from swarm import diagnose, llm_swarm, naive_count, synthetic_swarm, tamper
from swarm.llm import MockBackend


def test_clean_run_accuses_nobody():
    logs = synthetic_swarm(10, "complete", rounds=5, seed=0)
    v = diagnose(logs)
    assert v.status == "clean" and not v.accused


def test_single_liar_identified_on_complete_graph():
    logs = synthetic_swarm(10, "complete", rounds=10, seed=1)
    bad, truth = tamper(logs, {"a3"}, rate=0.3, seed=1)
    v = diagnose(bad)
    assert v.status == "identified" and v.accused == truth.liars


def test_star_leaf_vs_hub_is_ambiguous_when_hub_lies_once():
    # Hub tampering with one record on one edge: {hub} and {leaf} both explain it.
    logs = synthetic_swarm(6, "star", rounds=1, seed=2)
    hub_evs = logs["a0"]
    one = hub_evs[0]
    logs["a0"] = [e for e in hub_evs if e is not one]
    v = diagnose(logs)
    assert v.status == "insufficient_evidence"
    assert {"a0"} in v.candidates


def test_colluding_pair_on_mutual_edge_is_invisible():
    # Documented blind spot: consistent rewrites between two liars leave no discrepancy.
    logs = synthetic_swarm(2, "complete", rounds=5, seed=3)
    bad, truth = tamper(logs, {"a0", "a1"}, rate=0.5, seed=3, ops=("edit", "delete"), collude=True)
    assert truth.tampered
    assert diagnose(bad).status == "clean"


def test_naive_baseline_blames_honest_peers():
    logs = synthetic_swarm(10, "complete", rounds=10, seed=4)
    bad, truth = tamper(logs, {"a0"}, rate=0.5, seed=4)
    assert naive_count(bad) - truth.liars  # false accusations exist


def test_llm_swarm_runs_on_mock_and_is_consistent():
    logs = llm_swarm(MockBackend(), 4, "ring", rounds=2, task="sum numbers", seed=0)
    assert sum(len(v) for v in logs.values()) == 2 * 4 * 2
    assert diagnose(logs).status == "clean"


def test_adaption_backend_parses_output(monkeypatch):
    from swarm.llm import AdaptionBackend

    monkeypatch.setenv("ADAPTION_API_KEY", "test")
    b = AdaptionBackend(model="m")
    sent = {}

    def fake_post(body):
        sent.update(body)
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "TO: a1"}]}]}

    monkeypatch.setattr(b, "_post", fake_post)
    assert b.complete("sys", [{"role": "user", "content": "hi"}]) == "TO: a1"
    assert sent["instructions"] == "sys" and sent["model"] == "m"


def test_village_runs_on_mock_and_hides_truth():
    from swarm.llm import MockBackend
    from swarm.village import Config, build_world, metrics, run_village

    cfg = Config(days=3, lookalikes=2, seed=1)
    w0 = build_world(cfg)
    assert sum(a.role == "evil" for a in w0.agents) == 2
    assert sum(a.lookalike for a in w0.agents) == 2
    m = metrics(run_village(cfg, MockBackend()))
    assert m["police_kills"] == 0  # mock never returns valid JSON -> action none


def test_bond_duel_runs_on_mock():
    from swarm.bond import BondConfig, build_duel, duel_metrics, run_duel
    from swarm.llm import MockBackend

    cfg = BondConfig(days=3, seed=2)
    d0 = build_duel(cfg)
    assert sorted(a.role for a in d0.agents).count("bond") == 1 and len(d0.evil_bond_attrs) == 3
    m = duel_metrics(run_duel(cfg, MockBackend(), MockBackend()))
    assert m["outcome"] == "timeout" and m["innocents_struck"] == 0
