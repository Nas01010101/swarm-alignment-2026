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


if __name__ == "__main__":
    fig_e08_blocs()
    fig_e08_governance()
