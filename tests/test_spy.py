import pytest

pytest.importorskip("concordia")
from concordia.language_model.no_language_model import RandomChoiceLanguageModel  # noqa: E402

from swarm.spy import Film, SpyConfig, film_metrics  # noqa: E402

OUTCOMES = {"doomsday", "unfinished", "device_sabotaged", "vex_defeated", "device_unfinishable", "agent_killed"}


def test_film_runs_and_agent_never_uses_force():
    for s in range(5):
        f = Film(SpyConfig(seed=s), lambda r: RandomChoiceLanguageModel()).run()
        assert film_metrics(f)["outcome"] in OUTCOMES
        sterling = [e["act"] for e in f.log if e["kind"] == "act" and e["who"] == "Sterling"]
        assert not any(a.split()[0] in ("kill", "threaten", "bribe", "capture") for a in sterling)
        kills = [e["day"] for e in f.log if e["kind"] == "act" and e["act"].startswith("kill")]
        assert all(b - a >= 2 for a, b in zip(kills, kills[1:]))
        assert f.bugs >= 0 and f.bribes >= 0 and f.pens >= 0
