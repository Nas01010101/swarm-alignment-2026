"""Fetch or inspect the AI Village transcripts (aidigestorg/ai-village on Hugging Face).

The schema is NOT verified yet; --inspect streams a few rows and prints configs,
columns and examples so E03's owner can write the Logs adapter.

    uv run --extra data python scripts/fetch_ai_village.py --inspect
    uv run --extra data python scripts/fetch_ai_village.py --download   # to data/ai-village/
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

REPO = "aidigestorg/ai-village"
DATA = Path(__file__).resolve().parents[1] / "data" / "ai-village"


def inspect(n: int) -> None:
    from datasets import get_dataset_config_names, load_dataset

    configs = get_dataset_config_names(REPO)
    print("configs:", configs)
    for cfg in configs[:5]:
        ds = load_dataset(REPO, cfg, split="train", streaming=True)
        rows = list(itertools.islice(ds, n))
        print(f"\n== {cfg}: columns {list(rows[0]) if rows else []}")
        for r in rows:
            print(json.dumps({k: str(v)[:160] for k, v in r.items()}, ensure_ascii=False))


def download() -> None:
    from huggingface_hub import snapshot_download

    DATA.mkdir(parents=True, exist_ok=True)
    print(snapshot_download(REPO, repo_type="dataset", local_dir=DATA))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("-n", type=int, default=3)
    a = ap.parse_args()
    if a.download:
        download()
    else:
        inspect(a.n)
