"""Concordia adapters: the Adaption endpoint as a Concordia LanguageModel, and an offline embedder."""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Collection, Sequence

import numpy as np
from concordia.language_model import language_model

from swarm.llm import AdaptionBackend


class AdaptionLM(language_model.LanguageModel):
    """Concordia model over Adaption /responses. Ignores Concordia's max_tokens: reasoning models
    spend their budget thinking first, so the cap is set once here (see E05 notebook entry)."""

    fallbacks = 0  # choices the model never answered; reported so a run can be judged on them

    def __init__(self, model: str, max_tokens: int = 2000):
        self._b = AdaptionBackend(model=model, max_tokens=max_tokens)

    def sample_text(self, prompt: str, *, max_tokens: int = 0, terminators: Collection[str] = (),
                    temperature: float = 1.0, top_p: float = 1.0, top_k: int = 0,
                    timeout: float = 120, seed: int | None = None) -> str:
        text = self._b.complete("", [{"role": "user", "content": prompt}])
        for t in terminators:
            text = text.split(t)[0]
        return text

    def sample_choice(self, prompt: str, responses: Sequence[str], *, seed: int | None = None):
        menu = "\n".join(f"({i}) {r}" for i, r in enumerate(responses))
        ask = f"{prompt}\n\nOptions:\n{menu}\nAnswer with the option number only."
        for _ in range(3):
            m = re.search(r"\d+", self.sample_text(ask))
            if m and int(m.group()) < len(responses):
                i = int(m.group())
                return i, responses[i], {}
        # Uniform, not a fixed default: menus end on different options (e.g. "sabotage it"),
        # so a fixed fallback would bias outcomes. Seeded for reproducibility when a seed is given.
        AdaptionLM.fallbacks += 1
        i = random.Random(seed).randrange(len(responses))
        return i, responses[i], {"fallback": True}


def hash_embedder(text: str, dim: int = 256) -> np.ndarray:
    """Bag-of-words hashing embedder: offline and deterministic, so memory retrieval costs no
    API call. Coarser than a neural embedder; agents here act on recent observations anyway."""
    v = np.zeros(dim)
    for w in re.findall(r"\w+", text.lower()):
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % dim] += 1
    n = np.linalg.norm(v)
    return v / n if n else v
