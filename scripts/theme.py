BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#c9d1d9"
BRIGHT = "#f0f6fc"
ACCENT = "#46a5f2"
ACCENT_DEEP = "#1f6feb"

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
WIDTH = 840
PAD = 24
TITLEBAR_H = 36
RADIUS = 12


def window_open(height, title, css=""):
    w = WIDTH
    r = RADIUS
    base_css = (
        "@media (prefers-reduced-motion: reduce) {"
        ".r,.c,.f,.t{animation:none !important;opacity:1 !important;transform:none !important}}"
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" '
        f'viewBox="0 0 {w} {height}" font-family="{FONT}" role="img" aria-label="{title}">',
        f'<style>{css}{base_css}</style>',
        '<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        f'<radialGradient id="glow" cx="0.92" cy="0" r="0.75">'
        f'<stop offset="0" stop-color="{ACCENT_DEEP}" stop-opacity="0.16"/>'
        f'<stop offset="1" stop-color="{ACCENT_DEEP}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="topline" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.9"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>'
        '</defs>',
        f'<rect width="{w}" height="{height}" rx="{r}" fill="url(#bg)"/>',
        f'<rect width="{w}" height="{height}" rx="{r}" fill="url(#glow)"/>',
        f'<path d="M0 {r} A{r} {r} 0 0 1 {r} 0 H{w - r} A{r} {r} 0 0 1 {w} {r} V{TITLEBAR_H} H0 Z" '
        f'fill="#ffffff" fill-opacity="0.025"/>',
        f'<rect x="60" y="0" width="{w - 120}" height="1.5" fill="url(#topline)"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{height - 1}" rx="{r}" '
        f'fill="none" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD - 4 + i * 18}" cy="{TITLEBAR_H / 2}" r="5.5" fill="{color}"/>')
    parts.append(
        f'<text x="{w / 2}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle" '
        f'font-size="12" fill="{MUTED}">{title}</text>'
    )
    return parts