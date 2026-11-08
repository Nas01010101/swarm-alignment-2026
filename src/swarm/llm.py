"""Model backends behind one method: complete(system, messages) -> str.

Real backends import their SDK lazily so tests run with no keys and no extras.
Pick one with SWARM_BACKEND=mock|anthropic|openai|adaption (OpenAI-compatible covers
OpenRouter, vLLM, Ollama via OPENAI_BASE_URL)."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import defaultdict
from typing import Protocol

USAGE: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "errors": 0})
_LOCK = threading.Lock()


class TokenCapExceeded(RuntimeError):
    """Raised before a call once total tokens pass SWARM_TOKEN_CAP (spend guard)."""


def record_usage(model: str, tin: int, tout: int, error: bool = False, cost: float = 0.0) -> None:
    with _LOCK:
        u = USAGE[model]
        u["usd"] = round(u.get("usd", 0.0) + cost, 6)
        u["calls"] += int(not error)
        u["in"] += tin
        u["out"] += tout
        u["errors"] += int(error)


def check_cap() -> None:
    cap = int(os.environ.get("SWARM_TOKEN_CAP", "0") or 0)
    if cap and sum(u["in"] + u["out"] for u in USAGE.values()) >= cap:
        raise TokenCapExceeded(f"token cap {cap} reached; raise SWARM_TOKEN_CAP to continue")


class Backend(Protocol):
    def complete(self, system: str, messages: list[dict]) -> str: ...


class MockBackend:
    """Deterministic stand-in: same input, same output. For tests and dry runs."""

    def __init__(self, model: str | None = None, max_tokens: int = 300):
        self.model = model or "mock"

    def complete(self, system: str, messages: list[dict]) -> str:
        h = hashlib.sha256((system + repr(messages)).encode()).hexdigest()
        return f"TO: ?\nack {h[:8]}"


class AnthropicBackend:
    def __init__(self, model: str | None = None, max_tokens: int = 300):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("SWARM_MODEL", "claude-haiku-5-5")
        self.max_tokens = max_tokens

    def complete(self, system: str, messages: list[dict]) -> str:
        r = self.client.messages.create(
            model=self.model, system=system, messages=messages, max_tokens=self.max_tokens
        )
        return "".join(b.text for b in r.content if b.type == "text")


class OpenAICompatBackend:
    def __init__(self, model: str | None = None, max_tokens: int = 300):
        import openai

        self.client = openai.OpenAI(base_url=os.environ.get("OPENAI_BASE_URL"))
        self.model = model or os.environ["SWARM_MODEL"]
        self.max_tokens = max_tokens

    def complete(self, system: str, messages: list[dict]) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            max_tokens=self.max_tokens,
        )
        return r.choices[0].message.content or ""


class AdaptionBackend:
    """Adaption Labs /api/v1/responses (Responses-API shape), billed to the team's
    Adaption credits. Stdlib HTTP so it needs no extra dependency.
    Models: GET /api/v1/models (e.g. gemma-4-26b-a4b-it, qwen3.8-27b, deepseek-v4-flash)."""

    url = "https://api.prod.adaptionlabs.ai/api/v1/responses"
    spent = 0.0  # USD across all instances, from the API's usage.cost
    calls = 0

    def __init__(self, model: str | None = None, max_tokens: int = 300, reasoning: str | None = None):
        self.key = os.environ["ADAPTION_API_KEY"]
        self.model = model or os.environ.get("SWARM_MODEL", "gemma-4-26b-a4b-it")
        self.max_tokens = max_tokens
        # Reasoning models (qwen3.8, deepseek-v4, glm-5) spend the whole budget thinking
        # unless effort is capped; "low" + a few thousand tokens returns an answer.
        self.reasoning = reasoning

    retries = 5  # 6 attempts in all

    def _post(self, body: dict) -> dict:
        import json
        import time
        import urllib.request

        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            out = json.load(r)
        cost = (out.get("usage") or {}).get("cost") or 0.0
        with _LOCK:
            AdaptionBackend.spent += cost
            AdaptionBackend.calls += 1
        return out

    def _post_retry(self, body: dict) -> dict:
        """One retry layer for every caller: 408/409/429/5xx, network errors, timeouts and
        truncated JSON back off exponentially (or as long as Retry-After says)."""
        import urllib.error

        for attempt in range(self.retries + 1):
            wait = None
            try:
                return self._post(body)
            except urllib.error.HTTPError as e:
                if e.code not in (408, 409, 429) and e.code < 500 or attempt == self.retries:
                    raise
                wait = e.headers.get("Retry-After") if e.headers else None
            except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError):
                if attempt == self.retries:
                    raise
            record_usage(self.model, 0, 0, error=True)
            time.sleep(float(wait) if wait and str(wait).isdigit() else 2 ** (attempt + 1))
        raise AssertionError("unreachable")

    def complete(self, system: str, messages: list[dict]) -> str:
        check_cap()
        r = self._post_retry(
            {
                "model": self.model,
                "instructions": system,
                "input": messages,
                "max_output_tokens": self.max_tokens,
                **({"reasoning": {"effort": self.reasoning}} if self.reasoning else {}),
            }
        )
        u = r.get("usage") or {}
        record_usage(self.model, u.get("input_tokens", 0) or 0, u.get("output_tokens", 0) or 0,
                     cost=u.get("cost") or 0.0)
        return "".join(
            c.get("text", "")
            for item in r.get("output", [])
            if item.get("type") == "message"
            for c in item.get("content", [])
            if c.get("type") == "output_text"
        )


def get_backend(name: str | None = None, model: str | None = None,
                max_tokens: int = 300, reasoning: str | None = None) -> Backend:
    name = name or os.environ.get("SWARM_BACKEND", "mock")
    if name == "adaption":
        return AdaptionBackend(model=model, max_tokens=max_tokens, reasoning=reasoning)
    return {
        "mock": MockBackend,
        "anthropic": AnthropicBackend,
        "openai": OpenAICompatBackend,
        "adaption": AdaptionBackend,
    }[name](model=model, max_tokens=max_tokens)
