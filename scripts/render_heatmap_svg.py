#!/usr/bin/env python3
import datetime
import json
import os

from theme import (ACCENT, BRIGHT, FRAME, MUTED, PAD, TEXT, TITLEBAR_H, WIDTH,
                   window_open)

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "github_data.json")
OUT_PATH = os.path.join(HERE, "..", "ahnaf-heatmap.svg")

PALETTE = ["#161b22", "#0c2d5a", "#0b4a8f", "#1f6feb", "#4c9aff", "#9fd0ff"]
LEFT_LABEL_W = 32
HEADER_H = 46
MONTH_ROW_H = 20
LEGEND_H = 34
STATS_H = 74

CSS = """
@keyframes pop { from { opacity: 0; transform: scale(.4); } to { opacity: 1; transform: scale(1); } }
.c { opacity: 0; transform-box: fill-box; transform-origin: center;
     animation: pop .5s cubic-bezier(.2,.8,.2,1) both; }
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
.f { opacity: 0; animation: fade .8s ease-out 1s both; }
"""


def make_levels(days):
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    if not counts:
        return [1, 2, 3, 4]
    cuts = []
    for p in (0.25, 0.5, 0.75, 0.92):
        cuts.append(counts[min(len(counts) - 1, int(len(counts) * p))])
    return cuts


def level_for(count, cuts):
    if count == 0:
        return 0
    level = 1
    for cut in cuts:
        if count > cut:
            level += 1
    return min(level, 5)


def build_grid(days, cuts):
    first = datetime.date.fromisoformat(days[0]["date"])
    grid = []
    col = [None] * ((first.weekday() + 1) % 7)
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"], cuts)))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        col += [None] * (7 - len(col))
        grid.append(col)
    return grid


def pretty_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def render(data):
    days = data["days"]
    cuts = make_levels(days)
    grid = build_grid(days, cuts)

    grid_left = PAD + LEFT_LABEL_W
    step = (WIDTH - PAD - grid_left) / len(grid)
    cell = step * 0.8
    grid_h = 7 * step

    header_y = TITLEBAR_H
    month_y = header_y + HEADER_H
    grid_top = month_y + MONTH_ROW_H
    legend_y = grid_top + grid_h + 12
    sep_y = legend_y + LEGEND_H
    height = round(sep_y + STATS_H)

    parts = window_open(height, "ahnafwzz@github: ~/contributions", CSS)

    parts.append(f'<text x="{PAD}" y="{header_y + 30}" font-size="15" font-weight="700" fill="{BRIGHT}">'
                 f'<tspan fill="{ACCENT}">$ </tspan>git log --activity</text>')
    rng = data["range"]
    parts.append(f'<text x="{WIDTH - PAD}" y="{header_y + 30}" font-size="11" fill="{MUTED}" text-anchor="end">'
                 f'{pretty_date(rng["start"])}  &#8594;  {pretty_date(rng["end"])}</text>')

    last_label_col = -10
    for ci, column in enumerate(grid):
        first_cell = next((c for c in column if c), None)
        if not first_cell:
            continue
        date = datetime.date.fromisoformat(first_cell[0])
        if date.day <= 7 and ci - last_label_col >= 3:
            last_label_col = ci
            parts.append(f'<text x="{grid_left + ci * step:.1f}" y="{month_y + 12}" '
                         f'font-size="10" fill="{MUTED}">{date.strftime("%b")}</text>')

    for wi, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * step + cell * 0.8
        parts.append(f'<text x="{PAD}" y="{y:.1f}" font-size="9" fill="{MUTED}">{name}</text>')

    parts.append('<defs><filter id="neon" x="-60%" y="-60%" width="220%" height="220%">'
                 '<feGaussianBlur stdDeviation="2.4" result="b"/>'
                 '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
                 '</filter></defs>')

    base, bright = [], []
    for ci, column in enumerate(grid):
        for ri, item in enumerate(column):
            if item is None:
                continue
            date_s, count, lvl = item
            x = grid_left + ci * step
            y = grid_top + ri * step
            delay = ci * 0.011 + ri * 0.025
            plural = "" if count == 1 else "s"
            rect = (f'<rect class="c" x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                    f'rx="3" fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                    f'<title>{pretty_date(date_s)}: {count} contribution{plural}</title></rect>')
            (bright if lvl >= 4 else base).append(rect)
    parts += base
    parts.append('<g filter="url(#neon)">' + "".join(bright) + '</g>')

    leg_cell = 11
    leg_w = len(PALETTE) * (leg_cell + 3) - 3
    lx = WIDTH - PAD - 34 - leg_w - 8
    ly = legend_y + 8
    parts.append(f'<text class="f" x="{lx - 8}" y="{ly + 9}" font-size="10" fill="{MUTED}" text-anchor="end">Less</text>')
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect class="f" x="{lx + lvl * (leg_cell + 3)}" y="{ly}" width="{leg_cell}" '
                     f'height="{leg_cell}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text class="f" x="{lx + leg_w + 8}" y="{ly + 9}" font-size="10" fill="{MUTED}">More</text>')

    parts.append(f'<line x1="0" y1="{sep_y}" x2="{WIDTH}" y2="{sep_y}" stroke="{FRAME}"/>')

    best = max(days, key=lambda d: d["count"])
    active = [d for d in days if d["count"] > 0]
    avg = data["total_contributions"] / len(active) if active else 0
    stats = [
        (f'{data["total_contributions"]:,}', "CONTRIBUTIONS"),
        (f'{data["active_days"]}', "ACTIVE DAYS"),
        (f'{best["count"]}', f'BEST DAY  {datetime.date.fromisoformat(best["date"]).strftime("%d %b")}'),
        (f'{avg:.1f}', "AVG / ACTIVE DAY"),
    ]
    col_w = (WIDTH - PAD * 2) / len(stats)
    for i, (value, label) in enumerate(stats):
        x = PAD + i * col_w
        if i:
            parts.append(f'<line x1="{x - 12:.1f}" y1="{sep_y + 16}" x2="{x - 12:.1f}" y2="{sep_y + STATS_H - 16}" stroke="{FRAME}"/>')
        parts.append(f'<text class="f" x="{x:.1f}" y="{sep_y + 36}" font-size="22" font-weight="700" fill="{ACCENT}">{value}</text>')
        parts.append(f'<text class="f" x="{x:.1f}" y="{sep_y + 56}" font-size="10" letter-spacing="1" fill="{MUTED}">{label}</text>')

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    with open(IN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render(data))
    print(f"Selesai! {OUT_PATH} dibuat")
