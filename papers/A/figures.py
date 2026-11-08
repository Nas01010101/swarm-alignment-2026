"""Figures for paper A, drawn only from committed result files.

    uv run --extra plot python papers/A/figures.py        -> papers/A/fig_*.pdf (+ .png previews)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
# Reference categorical slots 1-3 in fixed order; identity is also carried by marker shape + labels.
MIN, BND, JDG = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
plt.rcParams.update({
    "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "lines.linewidth": 2, "lines.markersize": 5,
})


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def fig_e01():
    s = json.loads((ROOT / "results/E01/bounded_summary.json").read_text())["cells"]
    topos = ["complete", "erdos", "ring", "star"]
    fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.3), sharex=True, sharey="row")
    for j, t in enumerate(topos):
        cs = [c for c in s if c["topology"] == t]
        ks = [c["liars"] for c in cs]
        for row, metric, ylabel in ((0, "liar_recall", "liars named\n(fraction)"),
                                    (1, "runs_with_false_accusation", "runs accusing\nan honest agent")):
            ax = axes[row, j]
            ax.plot(ks, [c["mincover"][metric] for c in cs], color=MIN, marker="o", label="min-cover")
            ax.plot(ks, [c["bounded_t=k"][metric] for c in cs], color=BND, marker="s", ls="--",
                    label="bounded (t = k)")
            ax.set_ylim(-0.05, 1.05)
            ax.set_xticks([1, 2, 3, 4])
            if j == 0:
                ax.set_ylabel(ylabel)
            if row == 0:
                ax.set_title(t, color=INK)
            else:
                ax.set_xlabel("liars k")
    axes[0, 0].legend(loc="lower left", fontsize=7)
    fig.tight_layout()
    save(fig, "fig_e01")


def fig_e02():
    h = json.loads((ROOT / "results/E02/summary.json").read_text())["hypotheses"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    vals = [(h["H4_llm_rows_localized"], "detector:\nliar localized", MIN),
            (h["H4_llm_rows_judge_flagged"], "LLM judge:\nliar flagged", JDG)]
    for i, (v, lab, col) in enumerate(vals):
        ax.barh(i, v["rate"], color=col, height=0.55)
        ax.errorbar(v["rate"], i, xerr=[[v["rate"] - v["ci"][0]], [v["ci"][1] - v["rate"]]],
                    color=INK, capsize=3, lw=1)
        ax.text(v["ci"][1] + 0.03, i, f"{v['rate']:.2f}", va="center", color=INK)
    ax.set_yticks([0, 1], [v[1] for v in vals])
    ax.set_xlim(0, 1.1)
    ax.invert_yaxis()
    ax.set_xlabel(f"fraction of LLM-liar runs (n={h['H4_llm_rows_localized']['n']}, 95% CI)")
    ax = axes[1]
    conds = ["naive", "crosscheck", "detector"]
    m = h["H3_minimal_edit_by_condition"]
    for i, c in enumerate(conds):
        v = m[c]
        ax.bar(i, v["rate"], color=MIN, width=0.55)
        ax.errorbar(i, v["rate"], yerr=[[v["rate"] - v["ci"][0]], [v["ci"][1] - v["rate"]]],
                    color=INK, capsize=3, lw=1)
        ax.text(i, 0.06, f"{v['rate']:.2f}", ha="center", color="white", fontsize=8)
    ax.axhline(0.8, color=MUTED, ls=":", lw=1)
    ax.set_xlim(-0.5, 2.5)
    ax.set_xticks(range(3), ["naive", "told logs\nare compared", "told the\ndetector rule"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("liars making the\nsmallest edit")
    fig.tight_layout()
    save(fig, "fig_e02")


def fig_e02b():
    p = ROOT / "results/E02b/summary.json"
    if not p.exists():
        return
    h = json.loads(p.read_text())
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    series = [("llm_framed_mincover", "min-cover", MIN, "o"), ("llm_framed_bounded", "bounded (t = 2)", BND, "s"),
              ("llm_judge_accused_receiver", "LLM judge*", JDG, "^")]
    xs = {"distinct": 0, "same": 1}
    for i, (key, lab, col, mk) in enumerate(series):
        off = (i - 1) * 0.18
        for ar, x in xs.items():
            v = h[f"{key}_{ar}"]
            ax.bar(x + off, v["mean"], width=0.17, color=col, label=lab if ar == "same" else None)
            ax.errorbar(x + off, v["mean"], yerr=[[v["mean"] - v["ci"][0]], [v["ci"][1] - v["mean"]]],
                        color=INK, capsize=2, lw=0.8)
            ax.text(x + off, v["ci"][1] + 0.03, f"{v['mean']:.2f}", ha="center", va="bottom", fontsize=6.5,
                    color=INK)
    ax.set_xticks([0, 1], ["distinct\nreceivers", "same\nreceiver"])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("runs accusing an honest\nreceiver (per-swarm mean)")
    ax.legend(fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, handlelength=1, columnspacing=1)
    fig.tight_layout()
    save(fig, "fig_e02b")


if __name__ == "__main__":
    fig_e01()
    fig_e02()
    fig_e02b()
    print("wrote", sorted(x.name for x in OUT.glob("fig_*.pdf")))
