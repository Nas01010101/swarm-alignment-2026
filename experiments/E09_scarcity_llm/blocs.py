"""Per-bloc action shares, seeded-villager compliance and starvation from raw village logs → <out>/blocs.json.

uv run python experiments/E09_scarcity_llm/blocs.py results/raw/E09/main results/E09
uv run python experiments/E09_scarcity_llm/blocs.py results/raw/E09c/main results/E09c
Groups by everything in the village key except the seed (model, economy, rho, seeded, loophole, governance).
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main(raw: Path, out: Path):
    agg = defaultdict(Counter)
    for f in sorted(raw.glob("*.json")):
        group = "|".join(f.stem.split("_")[:-1])  # drop the seed
        for e in json.loads(f.read_text())["log"]:
            if e["kind"] == "villager":
                c = agg[f"{group}|{e['econ']}"]
                c["villager_days"] += 1
                c[e["action"]] += 1
                if e.get("seeded"):
                    c["seed_days"] += 1
                    c["seed_hack_days"] += e["action"] == "ledger_sync"
            elif e["kind"] == "starved":
                agg[f"{group}|{e['econ']}"]["starved"] += 1
            elif e["kind"] == "raid":
                agg[f"{group}|all"]["raids"] += 1
    res = {}
    for k, c in sorted(agg.items()):
        d = c["villager_days"]
        res[k] = {**c, **({f"share_{a}": round(c[a] / d, 4) for a in ("work", "forage", "ledger_sync")} if d else {})}
    (out / "blocs.json").write_text(json.dumps({"source": str(raw), "groups": res}, indent=1) + "\n")
    print(f"wrote {out / 'blocs.json'} ({len(res)} groups)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
