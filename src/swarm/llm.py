"""Model backends behind one method: complete(system, messages) -> str.

Real backends import their SDK lazily so tests run with no keys and no extras.
Pick one with SWARM_BACKEND=mock|anthropic|openai|adaption (OpenAI-compatible covers
OpenRouter, vLLM, Ollama via OPENAI_BASE_URL)."""

from __future__ import annotations

import hashlib
import os
from typing import Protocol


class Backend(Protocol):
    def complete(self, system: str, messages: list[dict]) -> str: ...


class MockBackend:
    """Deterministic stand-in: same input, same output. For tests and dry runs."""

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

    def __init__(self, model: str | None = None, max_tokens: int = 300):
        self.key = os.environ["ADAPTION_API_KEY"]
        self.model = model or os.environ.get("SWARM_MODEL", "gemma-4-26b-a4b-it")
        self.max_tokens = max_tokens

    def _post(self, body: dict) -> dict:
        import json
        import time
        import urllib.request

        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        tries = 6  # long games make ~200 calls; parallel runs hit HTTP 429, so back off exponentially
        for attempt in range(tries):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    out = json.load(r)
                break
            except (OSError, ValueError) as e:  # HTTPError (incl. 429) is an OSError
                if attempt == tries - 1:
                    raise
                wait = getattr(e, "headers", None) and e.headers.get("Retry-After")
                time.sleep(float(wait) if wait and str(wait).isdigit() else 2 ** (attempt + 1))
        AdaptionBackend.spent += (out.get("usage") or {}).get("cost") or 0.0
        AdaptionBackend.calls += 1
        return out

    def complete(self, system: str, messages: list[dict]) -> str:
        r = self._post(
            {
                "model": self.model,
                "instructions": system,
                "input": messages,
                "max_output_tokens": self.max_tokens,
            }
        )
        return "".join(
            c.get("text", "")
            for item in r.get("output", [])
            if item.get("type") == "message"
            for c in item.get("content", [])
            if c.get("type") == "output_text"
        )


def get_backend(name: str | None = None) -> Backend:
    name = name or os.environ.get("SWARM_BACKEND", "mock")
    return {
        "mock": MockBackend,
        "anthropic": AnthropicBackend,
        "openai": OpenAICompatBackend,
        "adaption": AdaptionBackend,
    }[name]()
