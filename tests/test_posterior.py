import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "posterior", Path(__file__).parents[1] / "experiments/E04_police_overreach/posterior.py")
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)


def test_likelihood():
    card = {"hair": "red", "height": "unknown"}
    assert post.likelihood(card, {"hair": "red"}) == 1
    assert post.likelihood(card, {"hair": "black"}) == 0
    assert post.likelihood(card, {"height": "tall"}) == pytest.approx(1 / 3)


def test_posterior_sums_to_n_evil_and_singles_out_match():
    cards = {"a": {"hair": "red"}, "b": {"hair": "black"}, "c": {"hair": "black"}, "d": {"hair": "unknown"}}
    p = post.posterior(cards, [(1, {"hair": "red"})] * 3, {}, set())
    assert sum(p.values()) == pytest.approx(2)
    assert p["a"] > 0.9 and p["b"] == p["c"] < p["d"]


def test_dead_resident_cannot_explain_later_sighting():
    cards = {"a": {"hair": "red"}, "b": {"hair": "red"}, "c": {"hair": "black"}}
    p = post.posterior(cards, [(2, {"hair": "red"})], {"a": 1}, set())
    assert p["b"] == pytest.approx(1)


def test_rebuilt_world_matches_logged_roles():
    """Cards are not logged; the rebuild must reproduce the logged world exactly."""
    files = sorted(Path("results/raw/E04/main_gemma").glob("*.json"))
    if not files:
        pytest.skip("raw E04 logs are local only")
    for f in files:
        cond, seed = f.stem.rsplit("_s", 1)
        w = post.build_world(post.Config(seed=int(seed), **post.CONDITIONS[cond]))
        roles = {a.name: (a.role, a.lookalike) for a in w.agents}
        for e in json.loads(f.read_text()):
            if e["kind"] == "police_action" and e["target"]:
                assert roles[e["target"]] == (e["target_role"], e["target_lookalike"]), f
            if e["kind"] in ("sighting", "murder", "sabotage"):
                assert roles[e["actor"]][0] == "evil", f
