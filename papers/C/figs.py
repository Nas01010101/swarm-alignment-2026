"""Generate Paper C figures from results/E08 and results/E09 JSONL files."""

import json
from pathlib import Path
import matplotlib.pyplot as plt

CELL = {
    "capitalist": "PS",
    "directed": "PC",
    "capitalist_tax": "TX",
    "commons": "CS",
    "socialist": "CC",
    "planned": "PL",
}
E08_ISLANDS = ["capitalist", "capitalist_tax", "socialist"]
E14_CELLS = ["PS", "PC", "TX", "CS", "CC", "PL"]
FILES = [
    "results/E08/main_gemma.jsonl",
    "results/E08/e13.jsonl",
    "results/E08/e14.jsonl",
    "results/E09/e09_mc.jsonl",
    "results/E09/e13_mc.jsonl",
    "results/E09/e14_mc.jsonl",
]


def load_jsonl(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def is_cell(row: dict, code: str) -> bool:
    isl = row.get("island")
    return CELL.get(isl) == code and bool(row.get("neutral") or isl in ("directed", "commons", "planned"))


def plot_e08(text_rows: list[dict], mc_rows: list[dict], out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.6), dpi=200)
    xs = range(len(E08_ISLANDS))
    means, seen_t, seen_m = [], False, False
    for i, isl in enumerate(E08_ISLANDS):
        vals = [r["survivors"] for r in text_rows if r.get("island") == isl]
        means.append(sum(vals) / len(vals) if vals else 0.0)
        if vals:
            jitter = [i + (k - (len(vals) - 1) / 2) * 0.06 for k in range(len(vals))]
            ax.scatter(jitter, vals, color="#1f4e79", zorder=3, s=28,
                       label=None if seen_t else "Text seed (n=100)")
            seen_t = True
        mc = [r["survivors"] for r in mc_rows if r.get("island") == isl]
        if mc:
            ax.scatter([i] * len(mc), mc, marker="*", s=95, color="#c0392b", zorder=4,
                       label=None if seen_m else "Minecraft seed 0 (n=50)")
            seen_m = True
    ax.bar(xs, means, width=0.48, color="#9dc3e6", edgecolor="#1f4e79", zorder=2, label="Text mean")
    ax.set_xticks(list(xs), E08_ISLANDS)
    ax.set_ylabel("Day-12 survivors")
    ax.set_title("E08: Survivors by island rule set")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig1_e08.png")
    plt.close(fig)


def plot_e13(text_rows: list[dict], mc_rows: list[dict], out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.6), dpi=200)
    own_groups = [("Private", "PS", "PC"), ("Common", "CS", "CC")]
    colors = {"Self-chosen": "#7f8c8d", "Coordinator": "#2e8b57"}
    offsets = [("Self-chosen", -0.18, 1), ("Coordinator", 0.18, 2)]
    seen_t, seen_m = False, False
    for x_idx, (_, self_code, coord_code) in enumerate(own_groups):
        for coord_label, offset, code_idx in offsets:
            code = self_code if code_idx == 1 else coord_code
            vals = [r["survivors"] for r in text_rows if is_cell(r, code)]
            mean_val = sum(vals) / len(vals) if vals else 0.0
            pos = x_idx + offset
            ax.bar(pos, mean_val, width=0.32, color=colors[coord_label], alpha=0.65,
                   edgecolor="black", label=coord_label if x_idx == 0 else None, zorder=2)
            if vals:
                jitter = [pos + (k - (len(vals) - 1) / 2) * 0.04 for k in range(len(vals))]
                ax.scatter(jitter, vals, color="black", s=24, zorder=3,
                           label=None if seen_t else "Text seed")
                seen_t = True
            mc = [r["survivors"] for r in mc_rows if is_cell(r, code)]
            if mc:
                ax.scatter([pos] * len(mc), mc, marker="*", s=90, color="#c0392b", zorder=4,
                           label=None if seen_m else "Minecraft")
                seen_m = True
    ax.set_xticks([0, 1], ["Private (PS, PC)", "Common (CS, CC)"])
    ax.set_ylabel("Day-12 survivors")
    ax.set_title("E13: 2x2 ownership by coordination")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig2_e13.png")
    plt.close(fig)


def plot_e14(text_rows: list[dict], mc_rows: list[dict], out_dir: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.6), dpi=200)
    xs = range(len(E14_CELLS))
    seen_t, seen_m = False, False
    for i, code in enumerate(E14_CELLS):
        t_cell = [r for r in text_rows if is_cell(r, code)]
        m_cell = [r for r in mc_rows if is_cell(r, code)]
        jit = [i + (k - (len(t_cell) - 1) / 2) * 0.06 for k in range(len(t_cell))]
        if t_cell:
            lbl = None if seen_t else "Text seed"
            ax1.scatter(jit, [r.get("hack_rate", 0.0) or 0.0 for r in t_cell], color="#1f4e79", s=28, zorder=3, label=lbl)
            ax2.scatter(jit, [r["survivors"] for r in t_cell], color="#1f4e79", s=28, zorder=3, label=lbl)
            seen_t = True
        if m_cell:
            lbl = None if seen_m else "Minecraft"
            ax1.scatter([i] * len(m_cell), [r.get("hack_rate", 0.0) or 0.0 for r in m_cell], marker="*", s=95, color="#c0392b", zorder=4, label=lbl)
            ax2.scatter([i] * len(m_cell), [r["survivors"] for r in m_cell], marker="*", s=95, color="#c0392b", zorder=4, label=lbl)
            seen_m = True
    for ax, ylabel, title in [
        (ax1, "Hack rate (ledger_sync share)", "E14: Loophole hack rate"),
        (ax2, "Day-12 survivors", "E14: Survivors"),
    ]:
        ax.set_xticks(list(xs), E14_CELLS)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig3_e14.png")
    plt.close(fig)


def main() -> None:
    data = {path: load_jsonl(path) for path in FILES}
    out_dir = Path("papers/C/figs")
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_e08(data["results/E08/main_gemma.jsonl"], data["results/E09/e09_mc.jsonl"], out_dir)
    plot_e13(data["results/E08/e13.jsonl"], data["results/E09/e13_mc.jsonl"], out_dir)
    plot_e14(data["results/E08/e14.jsonl"], data["results/E09/e14_mc.jsonl"], out_dir)


if __name__ == "__main__":
    main()
