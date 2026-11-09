"""E14: H1-H4 from results/E08/e14.jsonl (text, seeds 0-2) and results/E09/e14_mc.jsonl (Minecraft, seed 0)."""

import json
from math import comb
from pathlib import Path

CELL = {"capitalist": "PS", "directed": "PC", "capitalist_tax": "TX",
        "commons": "CS", "socialist": "CC", "planned": "PL"}
PRIVATE, COMMON = ("PS", "PC", "TX"), ("CS", "CC", "PL")
KEYS = ("backend", "survivors", "deaths_starved", "deaths_mobs", "walls_built", "hack_rate", "hackers_share", "wall_drained")


def load(path):
    p = Path(path)
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    return [r for r in rows if r.get("loophole") is not False and r["island"] in CELL]


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact P(X >= a) for the 2x2 [[a, b], [c, d]] (rows private, common; cols hacked, not)."""
    r1, k, n = a + b, a + c, a + b + c + d
    return sum(comb(r1, i) * comb(n - r1, k - i) for i in range(a, min(r1, k) + 1)) / comb(n, k)


def rank(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):  # average ranks over ties
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else None


def by_seed(rows):
    out = {}
    for r in rows:
        out.setdefault(r["seed"], {})[CELL[r["island"]]] = r
    return dict(sorted(out.items()))


def report(rows, name):
    seeds = by_seed(rows)
    print(f"\n== {name}: {len(rows)} games, seeds {list(seeds)}")
    for s, cells in seeds.items():
        for c in PRIVATE + COMMON:
            if c in cells:
                print(f" s{s} {c}", {k: cells[c].get(k) for k in KEYS})
    h1 = [sum(c[x]["hack_rate"] for x in PRIVATE) / 3 - sum(c[x]["hack_rate"] for x in COMMON) / 3
          for c in seeds.values() if all(x in c for x in PRIVATE + COMMON)]
    print(" H1 private - common hack rate per complete seed:", [round(d, 3) for d in h1],
          f"positive {sum(d > 0 for d in h1)}/{len(h1)}")
    for hi, lo in (("PC", "PS"), ("CC", "CS")):
        d = [round(c[hi]["hack_rate"] - c[lo]["hack_rate"], 3) for c in seeds.values() if hi in c and lo in c]
        print(f" H2 {hi} - {lo} hack rate:", d, f"negative {sum(x < 0 for x in d)}/{len(d)}")
    return seeds


if __name__ == "__main__":
    text = load("results/E08/e14.jsonl")
    # Amendment 3: seeds 0-2 are confirmatory; seeds 3-9 (Modal) are an exploratory extension
    report([r for r in text if r["seed"] <= 2], "text, confirmatory seeds 0-2")
    report(text, "text, all seeds (exploratory)")
    # Amendment 2: rows with no backend field ran on Adaption
    report([r for r in text if r.get("backend", "adaption") == "adaption"], "text, Adaption seeds only")
    mc = load("results/E09/e14_mc.jsonl")
    seeds = report(mc, "minecraft")
    cells = seeds.get(0, {})
    if all(x in cells for x in PRIVATE + COMMON):
        hk = lambda xs: round(sum(cells[x]["hackers_share"] * cells[x]["n"] for x in xs))
        n = lambda xs: sum(cells[x]["n"] for x in xs)
        a, c = hk(PRIVATE), hk(COMMON)
        print(f" H1 agents ever hacked: private {a}/{n(PRIVATE)}, common {c}/{n(COMMON)},"
              f" Fisher one-sided p = {fisher_greater(a, n(PRIVATE) - a, c, n(COMMON) - c):.3g}"
              " (agents treated as independent: a lower bound on p)")
    done = [cells[x] for x in cells]
    if len(done) >= 3:
        print(f" H3 Spearman(wall_drained, survivors) over {len(done)} islands:",
              spearman([r["wall_drained"] for r in done], [r["survivors"] for r in done]))
