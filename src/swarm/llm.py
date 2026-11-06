"""Model backends behind one method: complete(system, messages) -> str.

Real backends import their SDK lazily so tests run with no keys and no extras.
Pick one with SWARM_BACKEND=mock|anthropic|openai (OpenAI-compatible covers
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


def get_backend(name: str | None = None) -> Backend:
    name = name or os.environ.get("SWARM_BACKEND", "mock")
    return {"mock": MockBackend, "anthropic": AnthropicBackend, "openai": OpenAICompatBackend}[name]()
