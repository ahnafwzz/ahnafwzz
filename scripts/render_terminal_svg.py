#!/usr/bin/env python3
import datetime
import json
import os
import textwrap
from html import escape

from theme import (ACCENT, BG, BRIGHT, FRAME, MUTED, PAD, TEXT, TITLEBAR_H, WIDTH,
                   window_open)

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "..", "data", "github_data.json")
OUT_PATH = os.path.join(HERE, "..", "ahnaf-focus.svg")

GAP = 16
CARD_H = 124
HEADER_H = 54

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "PHP": "#8892bf", "Java": "#e8883a", "HTML": "#e34c26", "CSS": "#8957e5",
    "Dart": "#00B4AB", "Kotlin": "#A97BFF", "C++": "#f34b7d", "C": "#8a8a8a",
    "Jupyter Notebook": "#DA5B0B", "Blade": "#f7523f", "Vue": "#41b883",
    "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
}

CSS = """
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
.r { opacity: 0; animation: rise .8s cubic-bezier(.2,.7,.2,1) both; }
"""


def time_ago(iso):
    if not iso:
        return "recently"
    try:
        then = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return iso[:10]
    days = (datetime.datetime.now(datetime.timezone.utc) - then).days
    if days <= 0:
        return "today"
    if days < 7:
        return f"{days}d ago"
    if days < 30:
        return f"{days // 7}w ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def nice_name(raw, limit):
    name = raw.replace("-", " ").replace("_", " ").title()
    return name if len(name) <= limit else name[:limit - 1].rstrip() + "…"


def render_card(idx, repo, card_w):
    x = PAD + idx * (card_w + GAP)
    y = TITLEBAR_H + HEADER_H
    delay = 0.3 + idx * 0.18

    name = nice_name(repo["name"], int((card_w - 56) / 8.4))
    lang = repo.get("language") or "Unknown"
    color = LANG_COLORS.get(lang, MUTED)
    desc = repo.get("description") or "No description yet"
    lines = textwrap.wrap(desc, int((card_w - 32) / 7.2))[:2]
    if len(textwrap.wrap(desc, int((card_w - 32) / 7.2))) > 2:
        lines[1] = lines[1].rstrip(".,") + "…"
    full_date = (repo.get("updated_at") or "")[:10]

    out = [
        f'<g class="r" style="animation-delay:{delay:.2f}s">',
        f'<rect x="{x:.1f}" y="{y}" width="{card_w:.1f}" height="{CARD_H}" rx="10" fill="{BG}" stroke="{FRAME}"/>',
        f'<rect x="{x + 14:.1f}" y="{y}" width="{card_w - 28:.1f}" height="2" rx="1" fill="{color}" opacity="0.85"/>',
        f'<path transform="translate({x + 16:.1f},{y + 16})" fill="none" stroke="{ACCENT}" stroke-width="1.5" '
        f'stroke-linejoin="round" d="M1 3a1 1 0 0 1 1-1h3.2l1.6 1.8H14a1 1 0 0 1 1 1V12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1z"/>',
        f'<text x="{x + 40:.1f}" y="{y + 29}" font-size="14" font-weight="700" fill="{BRIGHT}">{escape(name)}</text>',
    ]
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + 16:.1f}" y="{y + 56 + i * 17}" font-size="12" fill="{MUTED}">{escape(line)}</text>')

    out.append(f'<line x1="{x + 16:.1f}" y1="{y + CARD_H - 30}" x2="{x + card_w - 16:.1f}" y2="{y + CARD_H - 30}" stroke="{FRAME}"/>')
    out.append(f'<circle cx="{x + 21:.1f}" cy="{y + CARD_H - 14}" r="4.5" fill="{color}"/>')
    out.append(f'<text x="{x + 33:.1f}" y="{y + CARD_H - 10}" font-size="11" fill="{TEXT}">{escape(lang)}</text>')
    out.append(f'<text x="{x + card_w - 16:.1f}" y="{y + CARD_H - 10}" font-size="11" fill="{MUTED}" '
               f'text-anchor="end">{time_ago(repo.get("updated_at"))}<title>{full_date}</title></text>')
    out.append('</g>')
    return "".join(out)


def render(repos):
    repos = repos[:3]
    card_w = (WIDTH - PAD * 2 - GAP * 2) / 3
    height = TITLEBAR_H + HEADER_H + CARD_H + PAD + 4

    parts = window_open(height, "ahnafwzz@github: ~/current_focus", CSS)
    parts.append(f'<text class="r" style="animation-delay:.1s" x="{PAD}" y="{TITLEBAR_H + 33}" '
                 f'font-size="15" font-weight="700" fill="{BRIGHT}"><tspan fill="{ACCENT}">$ </tspan>'
                 f'ls -l ~/current_focus</text>')
    parts.append(f'<text class="r" style="animation-delay:.1s" x="{WIDTH - PAD}" y="{TITLEBAR_H + 33}" '
                 f'font-size="11" fill="{MUTED}" text-anchor="end">{len(repos)} active repositories</text>')
    for i, repo in enumerate(repos):
        parts.append(render_card(i, repo, card_w))
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        raise SystemExit("Data belum ditarik, jalankan fetch_github_data.py dulu.")
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render(data.get("top_repos", [])))
    print(f"Selesai! {OUT_PATH} dibuat")
