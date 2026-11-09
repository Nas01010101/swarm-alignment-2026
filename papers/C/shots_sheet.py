"""Build a contact sheet of Minecraft screenshots matching a time prefix."""

import argparse
from math import ceil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SHOTS_DIR = Path("papers/C/shots")
OUT_DIR = Path("papers/C/figs")
COLS = 4
THUMB_W, THUMB_H = 360, 202
LABEL_H = 26
PAD = 8


def parse_label(stem: str) -> str:
    parts = stem.split("_")
    if len(parts) >= 4:
        ts, island, view, tod = parts[0], parts[1], parts[2], parts[3]
        coord = "x=0" if island == "A" else "x=300"
        return f"Island {island} ({coord}) | {view} | {tod} ({ts})"
    return stem


def make_sheet(prefix: str) -> Path | None:
    files = sorted(SHOTS_DIR.glob(f"{prefix}*.png"))
    if not files:
        return None
    rows = ceil(len(files) / COLS)
    cell_w = THUMB_W + PAD * 2
    cell_h = THUMB_H + LABEL_H + PAD * 2
    sheet = Image.new("RGB", (COLS * cell_w, rows * cell_h), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, path in enumerate(files):
        r, c = divmod(idx, COLS)
        x0, y0 = c * cell_w + PAD, r * cell_h + PAD
        with Image.open(path) as im:
            thumb = im.convert("RGB").resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x0, y0))
        draw.rectangle([x0, y0 + THUMB_H, x0 + THUMB_W, y0 + THUMB_H + LABEL_H], fill=(30, 30, 30))
        draw.text((x0 + 6, y0 + THUMB_H + 6), parse_label(path.stem), fill=(255, 255, 255), font=font)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"shots_{prefix}.png"
    sheet.save(out_path)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", nargs="?", default="01", help="Screenshot filename time prefix")
    args = ap.parse_args()
    make_sheet(args.prefix)


if __name__ == "__main__":
    main()
