"""E13: F1-F5 from results/E13/e13.jsonl (text) and the Minecraft cells from results/E09/e13_mc.jsonl."""

import json
from math import comb
from pathlib import Path

CELL = {("capitalist", True): "PS", ("directed", False): "PC", ("directed", True): "PC",
        ("commons", False): "CS", ("commons", True): "CS", ("socialist", True): "CC"}


def load(path):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()] if Path(path).exists() else []
    return [r for r in rows if (r["island"], r.get("neutral", False)) in CELL]


def sign_p(k, n):
    """One-sided sign test: P(X >= k) under Binomial(n, 1/2)."""
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n


def contrasts(rows, key):
    by = {}
    for r in rows:
        by.setdefault(r["seed"], {})[CELL[(r["island"], r.get("neutral", False))]] = r[key]
    full = {s: c for s, c in sorted(by.items()) if len(c) == 4}
    f = {"F1 ownership (CS+CC)-(PS+PC)": lambda c: c["CS"] + c["CC"] - c["PS"] - c["PC"],
         "F2 coordination (PC+CC)-(PS+CS)": lambda c: c["PC"] + c["CC"] - c["PS"] - c["CS"],
         "F3 interaction (CC-CS)-(PC-PS)": lambda c: (c["CC"] - c["CS"]) - (c["PC"] - c["PS"]),
         "F4 labels CC-PS": lambda c: c["CC"] - c["PS"]}
    out = {}
    for name, fn in f.items():
        d = [fn(c) for c in full.values()]
        out[name] = {"per_seed": d, "positive": sum(x > 0 for x in d), "n": len(d),
                     "p_one_sided": round(sign_p(sum(x > 0 for x in d), len(d)), 4) if d else None}
    return full, out


if __name__ == "__main__":
    text = load("results/E08/e13.jsonl")
    for key in ("survivors", "walls_built"):
        cells, res = contrasts(text, key)
        print(f"\n== text, {key}, seeds {list(cells)}")
        for s, c in cells.items():
            print(" seed", s, c)
        for k, v in res.items():
            print(f" {k}: {v}")
    mc = load("results/E09/e13_mc.jsonl")
    print("\n== minecraft seed 0")
    for r in mc:
        print(" ", CELL[(r["island"], r.get("neutral", False))], {k: r[k] for k in
              ("survivors", "deaths_starved", "deaths_mobs", "walls_built", "rest_rate", "compliance")})
