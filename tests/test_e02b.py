import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "experiments" / "E02b_framing"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"e02b_{name}", ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_plant_pairs_arrangements_and_targets_honest_agents():
    run = _load("run")
    for topo in ("complete", "erdos"):
        for seed in range(100, 110):
            same = run.plant(topo, 6, seed, 0.4, "same")
            dist = run.plant(topo, 6, seed, 0.4, "distinct")
            liars = [c.agent for c, _ in same]
            assert liars == [c.agent for c, _ in dist]  # paired: same liars, same graph
            assert same[0][0].dst == same[1][0].dst and dist[0][0].dst != dist[1][0].dst
            assert all(c.dst not in liars for c, _ in same + dist)


def test_e02b_end_to_end_on_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("SWARM_BACKEND", "mock")
    run, analyze = _load("run"), _load("analyze")
    run.main(["--seeds", "2", "--liar-models", "m", "--out", str(tmp_path), "--workers", "4"])
    rows = [json.loads(x) for x in (tmp_path / "runs.jsonl").read_text().splitlines()]
    assert len(rows) == 2 * 2 * 2 * (2 + 2)  # topo x seed x arrangement x (2 controls + 2 conditions)
    res = analyze.main(["--out", str(tmp_path)])
    assert res["minimal_framed_mincover_same"]["mean"] == 1.0
    assert res["minimal_framed_mincover_distinct"]["mean"] == 0.0
    assert res["bounded_false_accusations_total"] == 0
