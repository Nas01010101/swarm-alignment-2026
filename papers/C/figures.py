"""Figures for paper C, drawn only from committed result files.

    uv run --extra plot python papers/C/figures.py        -> papers/C/fig_*.pdf (+ .png previews)
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
# Validated categorical slots 1-4 (same palette as paper A), fixed order; identity also carried by marker + legend.
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
plt.rcParams.update({
    "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "lines.linewidth": 2, "lines.markersize": 5,
})
TOPO = [("complete", S1, "o"), ("two_caveman", S2, "s"), ("small_world", S3, "^"), ("scale_free", S4, "D")]
GOV = [("unfiltered", S1, "o", "unfiltered"), ("naive_audit", S2, "s", "naive audit (p=0.15)"),
       ("dcbf_gateway", S3, "^", "DCBF gateway")]


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def e08_rows():
    return [json.loads(line) for line in (ROOT / "results/E08/sweep.jsonl").open()]


def rho_line(ax):
    ax.axvline(0.85, color=MUTED, lw=1, ls="--")
    ax.text(0.87, 0.55, r"$\rho^*=0.85$", color=MUTED, transform=ax.get_xaxis_transform(), va="center", fontsize=7)


def fig_e08_blocs():
    """Unfiltered: hack share at t=30 vs rho, Capitalists vs Communists, one line per topology."""
    rows = [r for r in e08_rows() if r["governance"] == "unfiltered"]
    rhos = sorted({r["rho"] for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.3), sharey=True)
    for ax, key, title in ((axes[0], "hack_cap_T", "Capitalists"), (axes[1], "hack_com_T", "Communists")):
        for topo, col, mk in TOPO:
            ys = [statistics.fmean(r[key] for r in rows if r["rho"] == x and r["topology"] == topo) for x in rhos]
            ax.plot(rhos, ys, color=col, marker=mk, label=topo.replace("_", " "))
        rho_line(ax)
        ax.set_title(title, fontsize=8, color=INK, loc="left")
        ax.set_xlabel(r"scarcity $\rho$ (regeneration / need)")
        ax.set_ylim(-0.03, 1.03)
    axes[0].set_ylabel("share hacking at t=30\n(unfiltered, mean of 20 seeds)")
    axes[1].legend(loc="upper right", fontsize=7)
    save(fig, "fig_e08_blocs")


def fig_e08_governance():
    """Pooled over topologies: hack share at t=30 and share of need met, by governance."""
    rows = e08_rows()
    rhos = sorted({r["rho"] for r in rows})
    g = defaultdict(list)
    for r in rows:
        g[(r["governance"], r["rho"])].append(r)
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.3))
    for ax, key, ylabel in ((axes[0], "hack_T", "share hacking at t=30"),
                            (axes[1], "need_met_all", "share of food need met\n(mean over 30 rounds)")):
        for gov, col, mk, label in GOV:
            ys = [statistics.fmean(r[key] for r in g[(gov, x)]) for x in rhos]
            ax.plot(rhos, ys, color=col, marker=mk, label=label)
        rho_line(ax)
        ax.set_xlabel(r"scarcity $\rho$")
        ax.set_ylabel(ylabel)
        ax.set_ylim(-0.03, 1.03)
    axes[1].legend(loc="lower right", fontsize=7)
    save(fig, "fig_e08_governance")


def _rows(path):
    p = ROOT / path
    return [json.loads(x) for x in p.open()] if p.exists() else []


def fig_e09():
    """Gemma c3 villages: share of non-seeded villagers who ever used ledger_sync, by bloc, and survivors."""
    rows = [r for r in _rows("results/E09/main.jsonl") if r["model"] == "gemma-4-26b-a4b-it"]
    if not rows:
        return
    conds = [(2.0, False, "abundant\nunseeded"), (2.0, True, "abundant\nseeded"),
             (0.6, False, "scarce\nunseeded"), (0.6, True, "scarce\nseeded")]
    xs = range(len(conds))
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))
    for ec, col, mk, label, dx in (("c1", S1, "o", "private villagers", -0.08), ("c2", S2, "s", "commune villagers", 0.08)):
        ys = []
        for rho, sd, _ in conds:
            rs = [r for r in rows if r["rho"] == rho and r["seeded"] == sd]
            ys.append(statistics.fmean(r["by_econ"][ec]["adopters_nonseed"] / max(1, r["by_econ"][ec]["nonseed"])
                                       for r in rs) if rs else float("nan"))
        axes[0].plot([x + dx for x in xs], ys, color=col, marker=mk, ls="none", markersize=7, label=label)
    axes[0].set_ylabel("non-seeded villagers who\never used ledger_sync")
    axes[0].set_ylim(-0.03, 1.03)
    axes[0].legend(loc="upper left", fontsize=7)
    alive = [statistics.fmean(r["alive_end"] for r in rows if r["rho"] == rho and r["seeded"] == sd) for rho, sd, _ in conds]
    axes[1].plot(list(xs), alive, color=S1, marker="o", ls="none", markersize=7)
    axes[1].set_ylabel("villagers alive at day 10 (of 8)")
    axes[1].set_ylim(-0.2, 8.2)
    for ax in axes:
        ax.set_xticks(list(xs), [c[2] for c in conds])
    save(fig, "fig_e09")


def fig_e09b():
    s = ROOT / "results/E09b/summary.json"
    if not s.exists():
        return
    arms = json.loads(s.read_text())["arms"]
    order = [("unfiltered", "none"), ("constitutional_prompt", "prompt\nrule"), ("llm_judge", "LLM\nauditor"),
             ("hack_ban", "ban"), ("dcbf_gateway", "DCBF\ngateway")]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4))
    for ax, m, ylabel, top in ((axes[0], "attempt_rate", "ledger_sync attempts\n(share of villager-days)", 1.03),
                               (axes[1], "alive_end", "villagers alive at day 10 (of 8)", 8.2)):
        ax.plot(range(len(order)), [arms[g][m] for g, _ in order], color=S1, marker="o", ls="none", markersize=7)
        ax.set_xticks(range(len(order)), [lab for _, lab in order])
        ax.set_ylabel(ylabel)
        ax.set_ylim(-0.03 * top, top)
    save(fig, "fig_e09b")


if __name__ == "__main__":
    fig_e08_blocs()
    fig_e08_governance()
    fig_e09()
    fig_e09b()
