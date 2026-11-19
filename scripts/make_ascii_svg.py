#!/usr/bin/env python3
import html
import itertools
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

from theme import (ACCENT, ACCENT_DEEP, BRIGHT, FRAME, MUTED, PAD, RADIUS, TEXT,
                   TITLEBAR_H, WIDTH, window_open)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "ahnaf-ascii.svg")
DATA_PATH = os.environ.get("GH_DATA", os.path.join(HERE, "..", "data", "github_data.json"))


def env_flag(name):
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


COLS = int(os.environ.get("COLS", 120))
STATIC_ONLY = env_flag("STATIC")
RAMP = " .`:-=+*cs#%@"

MAIN_H = 324
PORTRAIT_GAP = 10
TEXT_X = PAD + 16
BAR_W = WIDTH - 2 * TEXT_X
BAR_H = 10
BAR_GAP = 2
LEGEND_SIZE = 11
LEGEND_ROW_H = 21
CHAR_W = LEGEND_SIZE * 0.6
MAX_LANGS = 8

HEAD_RATIO = 1.18
EDGE_BOOST = 3.0
EDGE_RADIUS = 4
GAMMA = 1.2
MIN_DENSITY = 0.12
EQUALIZE = 0.6
FACE_MARGIN = 14

INTRO_DELAY = 0.2
TYPE_ROLE = 0.020
TYPE_NAME = 0.030
TYPE_DESC = 0.012
TYPE_PAUSE = 0.08
CARET_LINGER = 0.30
PHASE_GAP = 0.20
PORTRAIT_TIME = 2.6
BAR_LEAD = 0.30
BAR_TIME = 1.8
BAR_SPLINE = (0.4, 0.0, 0.2, 1.0)

LANG_COLORS = {
    "Dart": "#00B4AB", "Python": "#3572A5", "PHP": "#8892bf", "Java": "#e8883a",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#8957e5",
    "Jupyter Notebook": "#DA5B0B", "Blade": "#f7523f", "Kotlin": "#A97BFF", "C++": "#f34b7d",
    "C": "#8a8a8a", "Vue": "#41b883", "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
    "SQLite": "#0b7fcc", "SQL": "#e38c00", "Ruby": "#701516", "C#": "#178600", "CMake": "#6a8fb5",
    "Packet Tracer": "#1BA0D7", "Other": "#6e7681",
}
FALLBACK_COLORS = [ACCENT, "#a371f7", "#3fb950", "#d29922", "#f778ba", "#00B4AB", "#e34c26"]
SHORT_NAMES = {"Jupyter Notebook": "Jupyter"}

DESCRIPTION = ["A versatile builder bridging scalable web",
               "architectures, cross-platform mobile apps,",
               "and intelligent data solutions."]

CSS = """
@keyframes type { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.t { opacity: 0; animation: type .6s cubic-bezier(.2,.8,.2,1) both; }
@keyframes grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }
.g { transform-box: fill-box; transform-origin: top; animation: grow .9s cubic-bezier(.2,.8,.2,1) both; }
@media (prefers-reduced-motion: reduce) { .g { animation: none !important; transform: none !important; } }
"""

ids = itertools.count()
defs = []
body = []
STATIC = False


def load_languages():
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            block = json.load(f).get("languages")
    except (OSError, ValueError):
        return None
    if not block or not block.get("items"):
        return None
    return block


def shrink(items, keep):
    named = sorted((i for i in items if i["name"] != "Other"), key=lambda i: -i["percent"])
    other = sum(i["percent"] for i in items if i["name"] == "Other")
    if len(named) > keep:
        other += sum(i["percent"] for i in named[keep:])
        named = named[:keep]
    other = round(other, 1)
    return named + ([{"name": "Other", "percent": other}] if other else [])


def short(name):
    return SHORT_NAMES.get(name, name)


def pct(value):
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def lang_color(name, index):
    return LANG_COLORS.get(name) or FALLBACK_COLORS[index % len(FALLBACK_COLORS)]


def column_widths(items, cols):
    out = []
    for c in range(cols):
        group = items[c::cols]
        out.append((max(len(short(i["name"])) for i in group) * CHAR_W,
                    max(len(pct(i["percent"])) for i in group) * CHAR_W))
    return out


def fits(items, cols):
    widest = max(14 + n + 8 + p for n, p in column_widths(items, cols))
    return widest + 24 <= BAR_W / cols


def legend_grid(items):
    cols = len(items)
    while cols > 1 and not fits(items, cols):
        cols -= 1
    rows = math.ceil(len(items) / cols)
    balanced = math.ceil(len(items) / rows)
    if fits(items, balanced):
        cols = balanced
    return cols, rows


def render_portrait(art_h):
    img = Image.open(SRC).convert("RGBA")
    alpha_full = np.array(img.split()[-1])
    bbox = img.split()[-1].getbbox()
    if bbox is None:
        sys.exit(f"Gambar sumber kosong (semua pikselnya transparan): {SRC}")
    left, top, right, bottom = bbox

    band = alpha_full[top: top + int((bottom - top) * 0.3)]
    head_cols = np.where((band > 128).any(axis=0))[0]
    head_l, head_r = int(head_cols.min()), int(head_cols.max())
    head_w = head_r - head_l

    img = img.crop((max(0, head_l - FACE_MARGIN), max(0, top - FACE_MARGIN),
                    min(img.width, head_r + FACE_MARGIN), int(top + head_w * HEAD_RATIO)))
    w, h = img.size

    art_w = art_h * w / h
    cell_w = art_w / COLS
    cell_h = cell_w * 15 / 8
    rows = round(art_h / cell_h)

    big = (COLS * 3, rows * 3)
    alpha_big = np.array(img.split()[-1].resize(big, Image.LANCZOS)) / 255.0
    gray_big = np.array(img.convert("L").resize(big, Image.LANCZOS)) / 255.0
    alpha = np.array(img.split()[-1].resize((COLS, rows), Image.LANCZOS)) / 255.0

    body_mask = alpha_big > 0.5
    gray_big = np.where(body_mask, gray_big, gray_big[body_mask].mean())

    soft = Image.fromarray((gray_big * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(EDGE_RADIUS * 3))
    soft = np.array(soft) / 255.0
    mixed = np.clip(gray_big * 0.35 + 0.5 + (gray_big - soft) * EDGE_BOOST, 0, 1)

    lum = np.array(Image.fromarray((mixed * 255).astype("uint8")).resize((COLS, rows), Image.LANCZOS)) / 255.0
    inside = lum[alpha > 0.5]
    lo, hi = np.percentile(inside, 1), np.percentile(inside, 99)
    hi = max(hi, lo + 1e-6)
    norm = np.clip((lum - lo) / (hi - lo), 0, 1)
    rank = np.searchsorted(np.sort(inside), lum) / len(inside)
    norm = (1 - EQUALIZE) * norm + EQUALIZE * np.clip(rank, 0, 1)
    density = MIN_DENSITY + (1 - MIN_DENSITY) * norm ** GAMMA

    lines = []
    for y in range(rows):
        chars = []
        for x in range(COLS):
            if alpha[y, x] < 0.35:
                chars.append(" ")
                continue
            idx = int(density[y, x] * (len(RAMP) - 1) + 0.5)
            chars.append(RAMP[max(1, min(len(RAMP) - 1, idx))])
        lines.append("".join(chars))

    return lines, art_w, cell_w, cell_h, rows


def fade(delay):
    if STATIC:
        return ""
    return f'class="t" style="animation-delay:{delay:.2f}s"'


def wipe(markup, x, y, w, h, begin, dur, spline=None):
    if STATIC:
        return markup
    cid = f"w{next(ids)}"
    mode = f' calcMode="spline" keyTimes="0;1" keySplines="{" ".join(str(v) for v in spline)}"' if spline else ""
    defs.append(
        f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="0" height="{h:.1f}">'
        f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{begin:.3f}s" dur="{dur:.3f}s"{mode} fill="freeze"/>'
        f'</rect></clipPath>'
    )
    return f'<g clip-path="url(#{cid})">{markup}</g>'


def bezier(t, p1, p2):
    return 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3


def time_at_progress(p):
    x1, y1, x2, y2 = BAR_SPLINE
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if bezier(mid, y1, y2) < p:
            lo = mid
        else:
            hi = mid
    return bezier(lo, x1, x2)


def type_lines(lines, start):
    t = start
    events = []
    for ln in lines:
        text = ln["text"]
        n = len(text)
        size = ln["size"]
        markup = (f'<text x="{ln["x"]:.1f}" y="{ln["y"]:.1f}" font-size="{size}" '
                  f'textLength="{n * ln["adv"]:.1f}" lengthAdjust="spacing" '
                  f'{ln["attrs"]}>{html.escape(text)}</text>')
        if STATIC:
            body.append(markup)
            continue

        dt, adv = ln["dt"], ln["adv"]
        widths = [i * adv + 2 for i in range(n)] + [n * adv + 10]
        times = [i / n for i in range(n + 1)]
        cid = f"w{next(ids)}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="{ln["x"] - 2:.1f}" y="{ln["y"] - size * 0.95:.1f}" width="0" height="{size * 1.35:.1f}">'
            f'<animate attributeName="width" calcMode="discrete" values="{";".join(f"{v:.1f}" for v in widths)}" '
            f'keyTimes="{";".join(f"{v:.4f}" for v in times)}" begin="{t:.3f}s" dur="{n * dt:.3f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        body.append(f'<g clip-path="url(#{cid})">{markup}</g>')

        top, cw, ch = ln["y"] - size * 0.88, size * 0.5, size * 1.05
        for i in range(n + 1):
            events.append((t + i * dt, ln["x"] + i * adv, top, cw, ch))
        t += n * dt + TYPE_PAUSE

    if STATIC or not events:
        return start

    t0, tn = events[0][0], events[-1][0]
    span = tn - t0
    key_times = ";".join(f"{(e[0] - t0) / span:.4f}" for e in events)

    def track(attr, k):
        values = ";".join(f"{e[k]:.1f}" for e in events)
        return (f'<animate attributeName="{attr}" calcMode="discrete" values="{values}" keyTimes="{key_times}" '
                f'begin="{t0:.3f}s" dur="{span:.3f}s" fill="freeze"/>')

    _, x0, y0, w0, h0 = events[0]
    body.append(
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w0:.1f}" height="{h0:.1f}" fill="{ACCENT}" opacity="0">'
        f'<set attributeName="opacity" to="0.8" begin="{t0:.3f}s"/>'
        f'{track("x", 1)}{track("y", 2)}{track("width", 3)}{track("height", 4)}'
        f'<animate attributeName="opacity" from="0.8" to="0" begin="{tn + CARET_LINGER:.3f}s" dur="0.3s" fill="freeze"/>'
        f'</rect>'
    )
    return tn + CARET_LINGER


def build(static, languages, portrait_data):
    global STATIC, ids
    STATIC = static
    ids = itertools.count()
    defs.clear()
    body.clear()

    portrait, ART_W, CELL_W, CELL_H, ROWS = portrait_data
    items = shrink(languages["items"], MAX_LANGS) if languages else []
    cols, legend_rows = legend_grid(items) if items else (0, 0)

    FOOTER_TOP = TITLEBAR_H + MAIN_H
    FOOTER_H = (76 + LEGEND_ROW_H * (legend_rows - 1) + 24) if items else 12
    CANVAS_H = FOOTER_TOP + FOOTER_H

    ART_H = ROWS * CELL_H
    ASCII_X = WIDTH - PAD - ART_W
    ASCII_TOP = TITLEBAR_H + (MAIN_H - ART_H) / 2
    ART_BOTTOM = ASCII_TOP + ART_H
    CENTER_X = ASCII_X + ART_W / 2
    CENTER_Y = ASCII_TOP + ART_H / 2

    defs.append(
        f'<linearGradient id="face" gradientUnits="userSpaceOnUse" x1="0" y1="{ASCII_TOP:.1f}" x2="0" y2="{ART_BOTTOM:.1f}">'
        f'<stop offset="0" stop-color="{BRIGHT}"/><stop offset="0.55" stop-color="{TEXT}"/>'
        f'<stop offset="1" stop-color="{ACCENT}"/></linearGradient>'
        f'<radialGradient id="halo" cx="0.5" cy="0.45" r="0.55">'
        f'<stop offset="0" stop-color="{ACCENT_DEEP}" stop-opacity="0.24"/>'
        f'<stop offset="1" stop-color="{ACCENT_DEEP}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="dotfade"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
        f'<mask id="dotmask" maskUnits="userSpaceOnUse" x="{CENTER_X - 230:.1f}" y="{CENTER_Y - 230:.1f}" width="460" height="460">'
        f'<rect x="{CENTER_X - 230:.1f}" y="{CENTER_Y - 230:.1f}" width="460" height="460" fill="url(#dotfade)"/></mask>'
        f'<pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="0.9" fill="#fff" fill-opacity="0.16"/></pattern>'
        f'<clipPath id="main-clip"><rect x="1" y="{TITLEBAR_H}" width="{WIDTH - 2}" height="{MAIN_H}"/></clipPath>'
        f'<linearGradient id="rule" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/><stop offset="0.5" stop-color="{ACCENT}"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0.22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )

    body.append(f'<g clip-path="url(#main-clip)"><g mask="url(#dotmask)">'
                f'<rect x="{CENTER_X - 230:.1f}" y="{CENTER_Y - 230:.1f}" width="460" height="460" fill="url(#dots)"/></g></g>')
    body.append(f'<ellipse cx="{CENTER_X:.1f}" cy="{CENTER_Y:.1f}" rx="{ART_W * 0.75:.1f}" ry="{ART_H * 0.62:.1f}" fill="url(#halo)"/>')

    GAP_ROLE_NAME, GAP_NAME, GAP_NAME_DESC, GAP_DESC = 64, 52, 44, 22
    block_h = GAP_ROLE_NAME + GAP_NAME + GAP_NAME_DESC + GAP_DESC * (len(DESCRIPTION) - 1)
    role_y = TITLEBAR_H + (MAIN_H - block_h) / 2 + 2
    name_y = role_y + GAP_ROLE_NAME
    surname_y = name_y + GAP_NAME
    desc_y = surname_y + GAP_NAME_DESC
    block_bottom = desc_y + GAP_DESC * (len(DESCRIPTION) - 1)

    rule_top = role_y - 20
    rule_h = block_bottom - rule_top + 14
    rule_class = "" if STATIC else f'class="g" style="animation-delay:{INTRO_DELAY:.2f}s" '
    body.append(f'<rect {rule_class}x="{TEXT_X - 16}" y="{rule_top:.1f}" width="2" height="{rule_h:.1f}" rx="1" fill="url(#rule)"/>')
    body.append(f'<rect {fade(INTRO_DELAY)} x="{TEXT_X}" y="{role_y - 9:.1f}" width="8" height="8" rx="2" fill="{ACCENT}"/>')

    left_lines = [
        {"text": "SOFTWARE ENGINEER", "x": TEXT_X + 18, "y": role_y, "size": 12.5, "adv": 12.5 * 0.6 + 2.2,
         "dt": TYPE_ROLE, "attrs": f'fill="{ACCENT}"'},
        {"text": "Ahnaf Fawwaz", "x": TEXT_X, "y": name_y, "size": 44, "adv": 44 * 0.6,
         "dt": TYPE_NAME, "attrs": f'font-weight="700" fill="{BRIGHT}"'},
        {"text": "Arjanta", "x": TEXT_X, "y": surname_y, "size": 44, "adv": 44 * 0.6,
         "dt": TYPE_NAME, "attrs": f'font-weight="700" fill="{BRIGHT}"'},
    ] + [
        {"text": line, "x": TEXT_X, "y": desc_y + n * GAP_DESC, "size": 13.5, "adv": 13.5 * 0.6,
         "dt": TYPE_DESC, "attrs": f'fill="{TEXT}"'}
        for n, line in enumerate(DESCRIPTION)
    ]
    left_end = type_lines(left_lines, INTRO_DELAY + 0.3)

    portrait_start = left_end + PHASE_GAP
    row_time = PORTRAIT_TIME / ROWS
    font_size = CELL_H * 0.86
    for ry, line in enumerate(portrait):
        stripped = line.strip(" ")
        if not stripped:
            continue
        start = len(line) - len(line.lstrip(" "))
        row_y = ASCII_TOP + ry * CELL_H
        safe = html.escape(stripped).replace(" ", "\u00a0")
        text = (f'<text xml:space="preserve" x="{ASCII_X + start * CELL_W:.1f}" y="{row_y + CELL_H * 0.76:.1f}" fill="url(#face)" '
                f'font-size="{font_size:.2f}" textLength="{len(stripped) * CELL_W:.1f}" lengthAdjust="spacing">{safe}</text>')
        body.append(wipe(text, ASCII_X, row_y, ART_W, CELL_H, portrait_start + ry * row_time, row_time))

    if not STATIC:
        body.append(
            f'<rect x="{ASCII_X - 8:.1f}" y="{ASCII_TOP + CELL_H:.1f}" width="{ART_W + 16:.1f}" height="1.6" fill="url(#scan)" opacity="0">'
            f'<animate attributeName="y" from="{ASCII_TOP + CELL_H:.1f}" to="{ART_BOTTOM:.1f}" begin="{portrait_start:.3f}s" '
            f'dur="{PORTRAIT_TIME:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.04;0.92;1" begin="{portrait_start:.3f}s" '
            f'dur="{PORTRAIT_TIME:.3f}s" fill="freeze"/></rect>')

    footer_start = portrait_start + PORTRAIT_TIME + PHASE_GAP
    if items:
        r = RADIUS
        body.append(f'<path d="M1 {FOOTER_TOP} H{WIDTH - 1} V{CANVAS_H - r} A{r - 1} {r - 1} 0 0 1 {WIDTH - r} {CANVAS_H - 1} '
                    f'H{r} A{r - 1} {r - 1} 0 0 1 1 {CANVAS_H - r} Z" fill="#ffffff" fill-opacity="0.02"/>')
        body.append(f'<line x1="0" y1="{FOOTER_TOP}" x2="{WIDTH}" y2="{FOOTER_TOP}" stroke="{FRAME}"/>')

        label_y = FOOTER_TOP + 30
        bar_y = FOOTER_TOP + 42
        count = languages.get("repo_count", 0)
        lang_total = len([i for i in languages["items"] if i["name"] != "Other"])
        noun = "REPOSITORY" if count == 1 else "REPOSITORIES"
        body.append(f'<text {fade(footer_start)} x="{TEXT_X}" y="{label_y}" font-size="10.5" letter-spacing="2" fill="{MUTED}">LANGUAGES</text>')
        if count:
            body.append(f'<text {fade(footer_start)} x="{WIDTH - TEXT_X}" y="{label_y}" font-size="10.5" letter-spacing="1.5" '
                        f'text-anchor="end" fill="{MUTED}">{count} {noun} &#183; {lang_total} LANGUAGES</text>')

        bar_begin = footer_start + BAR_LEAD
        body.append(f'<rect {fade(footer_start)} x="{TEXT_X}" y="{bar_y}" width="{BAR_W}" height="{BAR_H}" rx="{BAR_H / 2}" '
                    f'fill="#ffffff" fill-opacity="0.07"/>')

        segments = []
        total = sum(i["percent"] for i in items) or 1
        cursor = TEXT_X
        starts = []
        for index, item in enumerate(items):
            seg_w = item["percent"] / total * BAR_W
            draw_w = max(seg_w - (BAR_GAP if index < len(items) - 1 else 0), 1)
            segments.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{draw_w:.1f}" height="{BAR_H}" fill="{lang_color(item["name"], index)}"/>')
            starts.append((cursor - TEXT_X) / BAR_W)
            cursor += seg_w
        segments.append(f'<rect x="{TEXT_X}" y="{bar_y}" width="{BAR_W}" height="{BAR_H}" fill="url(#gloss)"/>')
        defs.append(f'<clipPath id="bar-round"><rect x="{TEXT_X}" y="{bar_y}" width="{BAR_W}" height="{BAR_H}" rx="{BAR_H / 2}"/></clipPath>')
        filled = wipe("".join(segments), TEXT_X, bar_y - 1, BAR_W, BAR_H + 2, bar_begin, BAR_TIME, spline=BAR_SPLINE)
        body.append(f'<g clip-path="url(#bar-round)">{filled}</g>')

        pitch = BAR_W / cols
        widths = column_widths(items, cols)
        for index, item in enumerate(items):
            row, col = divmod(index, cols)
            name_w, pct_w = widths[col]
            x = TEXT_X + col * pitch
            y = bar_y + BAR_H + 24 + row * LEGEND_ROW_H
            name = short(item["name"])
            label = pct(item["percent"])
            right = x + 14 + name_w + 8 + pct_w
            delay = bar_begin + time_at_progress(starts[index]) * BAR_TIME + 0.05
            body.append(
                f'<g {fade(delay)}>'
                f'<circle cx="{x + 4:.1f}" cy="{y - 4}" r="4" fill="{lang_color(item["name"], index)}"/>'
                f'<text x="{x + 14:.1f}" y="{y}" font-size="{LEGEND_SIZE}" textLength="{len(name) * CHAR_W:.1f}" lengthAdjust="spacing" fill="{MUTED}">{html.escape(name)}</text>'
                f'<text x="{right - len(label) * CHAR_W:.1f}" y="{y}" font-size="{LEGEND_SIZE}" font-weight="700" textLength="{len(label) * CHAR_W:.1f}" lengthAdjust="spacing" fill="{TEXT}">{label}</text>'
                f'</g>'
            )

    svg = window_open(CANVAS_H, "ahnafwzz@github: ~/profile", CSS)
    svg.append("<defs>" + "".join(defs) + "</defs>")
    svg += body
    svg.append("</svg>")
    return "".join(svg), CANVAS_H, len(items)


def main():
    if not os.path.exists(SRC):
        sys.exit(f"Gambar sumber tidak ditemukan: {SRC}")

    languages = load_languages()
    portrait_data = render_portrait(MAIN_H - 2 * PORTRAIT_GAP)

    root, ext = os.path.splitext(OUT)
    jobs = [(True, OUT)] if STATIC_ONLY else [(False, OUT), (True, f"{root}-static{ext}")]
    for static, path in jobs:
        svg, canvas_h, n_items = build(static, languages, portrait_data)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        mode = "statis" if static else "animasi"
        print(f"Selesai! {path} dibuat ({mode}, {WIDTH} x {canvas_h}, {COLS} kolom x {portrait_data[4]} baris, "
              f"{n_items} bahasa, {len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()