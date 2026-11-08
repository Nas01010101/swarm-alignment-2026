import json
import random
import sys
import urllib.error
from pathlib import Path

import pytest

from swarm import llm, llm_swarm
from swarm.llm import AdaptionBackend, MockBackend
from swarm.sim import Covert

E02 = Path(__file__).resolve().parents[1] / "experiments" / "E02_llm_swarm_tamper"
sys.path.insert(0, str(E02))
import liars as L  # noqa: E402


class Scripted:
    """Backend that returns a fixed reply (a liar's JSON plan, or a judge verdict)."""

    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, messages):
        return self.reply


def _swarm(n=5, seed=0):
    cov = [Covert("a1", 1, "a2", "inflate P3")]
    logs = llm_swarm(MockBackend(), n, "complete", rounds=3, task="t", seed=seed, covert=cov)
    return logs, cov[0]


def test_covert_message_is_sent_to_planted_peer():
    logs, c = _swarm()
    rec = [e for e in logs["a1"] if e.msg_id == c.msg_id]
    assert rec and rec[0].kind == "send" and rec[0].peer == "a2" and rec[0].t == 1
    assert any(e.msg_id == c.msg_id and e.kind == "recv" for e in logs["a2"])


def test_concurrent_swarm_matches_serial():
    a = llm_swarm(MockBackend(), 5, "ring", 3, "t", 0, workers=1)
    b = llm_swarm(MockBackend(), 5, "ring", 3, "t", 0, workers=5)
    assert a == b


def test_liar_deleting_covert_message_is_localized_not_identified():
    logs, c = _swarm()
    reply = "```json\n" + json.dumps({"delete": [c.msg_id], "rewrite": {}}) + "\n```"
    bad = dict(logs)
    bad["a1"], info = L.liar_edit(Scripted(reply), logs["a1"], "a1", "naive", "a2", 3)
    assert info["parse_ok"] and info["deleted"] == 1
    s = L.score(bad, logs, {"a1"}, {"a1": c.msg_id})
    assert s["covert_hidden"] and s["detected"] and s["localized"]
    assert s["status"] == "insufficient_evidence" and s["n_suspects"] == 2 and not s["exact"]


def test_unparseable_or_noop_plan_changes_nothing():
    logs, c = _swarm()
    new, info = L.liar_edit(Scripted("I refuse."), logs["a1"], "a1", "detector", "a2", 3)
    assert new == logs["a1"] and not info["parse_ok"]
    same = {"rewrite": {c.msg_id: next(e.text for e in logs["a1"] if e.msg_id == c.msg_id)}}
    new, n_del, n_rew = L.apply_plan(logs["a1"], same)
    assert new == logs["a1"] and n_rew == 0


def test_rewrites_touching_many_peers_identify_the_liar():
    logs, c = _swarm(n=6)
    plan = {"rewrite": {e.msg_id: "nothing happened" for e in logs["a1"]}}
    bad = dict(logs)
    bad["a1"], _, n_rew = L.apply_plan(logs["a1"], plan)
    assert n_rew == len(logs["a1"])
    s = L.score(bad, logs, {"a1"}, {"a1": c.msg_id})
    assert s["status"] == "identified" and s["exact"] and s["false_accusations"] == 0


def test_controls():
    logs, c = _swarm()
    assert all(e.msg_id != c.msg_id for e in L.minimal_hide(logs["a1"], c.msg_id))
    new = L.matched_random(logs["a1"], 2, random.Random(0))
    changed = len(logs["a1"]) - len(new) + sum(1 for e in new if e.text == "[edited]")
    assert changed == 2
    assert L.matched_random(logs["a1"], 0, random.Random(0)) == logs["a1"]


def test_clean_logs_score_exact_with_no_liars():
    logs, c = _swarm()
    s = L.score(logs, logs, set(), {"a1": c.msg_id})
    assert s["status"] == "clean" and s["exact"] and not s["covert_hidden"]


def test_judge_parsing_and_metrics():
    logs, _ = _swarm()
    j = L.judge(Scripted('{"tampered": ["a1", "a4", "zz"]}'), logs, {"a1"})
    assert j["judge_named"] == ["a1", "a4"] and j["judge_flagged"] and not j["judge_exact"]
    assert j["judge_false_accusations"] == 1
    assert "== log of a0 ==" in L.judge_transcript(logs)


def test_adaption_retries_and_counts_usage(monkeypatch):
    monkeypatch.setenv("ADAPTION_API_KEY", "test")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    llm.USAGE.clear()
    b = AdaptionBackend(model="m")
    calls = {"n": 0}

    def flaky(body):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError("u", 429, "slow down", {}, None)
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "hi"}]}],
                "usage": {"input_tokens": 10, "output_tokens": 3}}

    monkeypatch.setattr(b, "_post", flaky)
    assert b.complete("s", []) == "hi"
    assert llm.USAGE["m"] == {"calls": 1, "in": 10, "out": 3, "errors": 1}
    monkeypatch.setenv("SWARM_TOKEN_CAP", "10")
    with pytest.raises(llm.TokenCapExceeded):
        b.complete("s", [])
    llm.USAGE.clear()


def test_runner_end_to_end_on_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("SWARM_BACKEND", "mock")
    import analyze
    import run

    args = ["--seeds", "1", "--liar-models", "m", "--out", str(tmp_path), "--workers", "4"]
    run.main(args)
    rows = [json.loads(x) for x in (tmp_path / "runs.jsonl").read_text().splitlines()]
    # 2 topologies x 2 k x (2 controls + 3 conditions x (llm + matched))
    assert len(rows) == 2 * 2 * (2 + 3 * 2)
    assert len((tmp_path / "judge.jsonl").read_text().splitlines()) == len(rows)
    run.main(args)  # resume: nothing new
    assert len((tmp_path / "runs.jsonl").read_text().splitlines()) == len(rows)
    assert analyze.main(["--out", str(tmp_path)])["cells"] > 0
