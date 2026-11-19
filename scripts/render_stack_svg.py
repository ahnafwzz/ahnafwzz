import os
import json
from itertools import product
import urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))

from theme import window_open, BG, ACCENT, TEXT, MUTED, FRAME, TITLEBAR_H, WIDTH, PAD

OUT_PATH = os.path.join(HERE, "..", "ahnaf-stack.svg")

BACKGROUND = BG
BORDER = FRAME

# ==========================================
# 0. PENGATURAN IKON
# ==========================================
SI_VERSION = "16.38.0"   # versi Simple Icons yang dipakai (dikunci biar hasilnya selalu sama)
CDN_URL = "https://cdn.jsdelivr.net/npm/simple-icons@{ver}/icons/{slug}.svg"
ICON_FILE = os.path.join(HERE, "icon.json")  # satu file: cache Simple Icons + ikon berwarna asli
COLOR_ICON_MIN_CONTRAST = 1.6   # kontras minimal ikon berwarna (lebih longgar biar warna aslinya terjaga)
AUTO_CONTRAST = True     # ikon yang terlalu gelap untuk latar otomatis dicerahkan
MIN_CONTRAST = 4.5       # batas minimal kontras ikon terhadap latar

# ==========================================
# 1. DATABASE IKON
# ==========================================
# Urutan prioritas pengambilan ikon:
#   1. "color_icon" : ikon berwarna asli (banyak layer) dari icon.json (bagian "color")
#   2. "path"       : path SVG manual (viewBox 24x24), satu warna
#   3. "slug"       : ikon Simple Icons, dibaca dari icon.json (bagian "cache", offline).
#                     Kalau belum ada di cache, otomatis di-download lalu disimpan.
#   4. Kalau semuanya gagal, dipakai ikon huruf supaya layout tidak geser
#   (kalau "color_icon" tidak ketemu, otomatis lanjut ke "path" atau "slug" sebagai cadangan)
#
# Opsional:
#   "ver"   : kunci ke versi Simple Icons lama, buat logo yang sudah dihapus dari versi terbaru
#   "color" : kalau dikosongkan, dipakai warna resmi dari Simple Icons
#   "min_contrast" : kontras minimal khusus ikon ini (buat ikon bergaris tipis yang kelihatan pucat)
ICONS = {
    # -- IKON DENGAN HARDCODE PATH --
    "CSS": {"color": "#1572B6", "path": "M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L3 17h3.428l.348 3.976 5.212 1.449 5.179-1.449.678-7.76H3.428v-3.8h15.05l.329-3.8H6.187l-.328-3.8H22.5z"},
    "Windows": {"color": "#0078D4", "path": "M0 0h11.4v11.4H0zm12.6 0H24v11.4H12.6zM0 12.6h11.4V24H0zm12.6 0H24V24H12.6z"},
    "VS Code": {"color": "#007ACC", "path": "M23.15 2.587L18.21.21a1.494 1.494 0 0 0-1.705.29l-9.46 8.63-4.12-3.128a.999.999 0 0 0-1.276.057L.327 7.261A1 1 0 0 0 .326 8.74L3.899 12 .326 15.26a1 1 0 0 0 .001 1.479L1.65 17.94a.999.999 0 0 0 1.276.057l4.12-3.128 9.46 8.63a1.492 1.492 0 0 0 1.704.29l4.942-2.377A1.5 1.5 0 0 0 24 20.06V3.939a1.5 1.5 0 0 0-.85-1.352zm-5.146 14.861L10.826 12l7.178-5.448v10.896z"},

    # -- IKON GAMBAR SENDIRI (belum ada di Simple Icons) --
    # Antigravity bukan logo resmi, hanya gambar sederhana. Orange memakai ikon berwarna
    # (icon.json), path di bawah cuma cadangan kalau file itu tidak ada.
    "Orange": {"color_icon": "orange", "color": "#F1A42B", "path": "M12 5.2a8.4 8.4 0 1 0 0 16.8 8.4 8.4 0 0 0 0-16.8zM12 5.6c3.4.8 5.4-1 5.4-4C14 1.6 12 3.2 12 5.6zM5.7 12.5A6.4 6.4 0 0 1 8.8 8.06l.9 1.56a4.6 4.6 0 0 0-2.23 3.18z"},
    "Antigravity": {"color": "#4285F4", "path": "M2.6 21l7.6-16.6Q12 1 13.8 4.4L21.4 21h-4.2L12 9.6 6.8 21z"},

    # -- IKON SIMPLE ICONS (dari icon.json) --
    # Canva sudah dihapus dari Simple Icons versi terbaru, jadi dikunci ke versi lama
    "Canva": {"slug": "canva", "ver": "14.15.0", "color": "#00C4CC"},

    "HTML": {"slug": "html5", "color": "#E34F26"},
    "JavaScript": {"slug": "javascript", "color": "#F7DF1E"},
    "PHP": {"slug": "php", "color": "#777BB4", "min_contrast": 7},
    "CodeIgniter": {"slug": "codeigniter", "color": "#EF4223"},
    "Laravel": {"slug": "laravel", "color": "#FF2D20"},
    "Tailwind": {"slug": "tailwindcss", "color": "#06B6D4"},
    "Bootstrap": {"slug": "bootstrap", "color": "#7952B3"},
    "Node.js": {"slug": "nodedotjs", "color": "#339933"},
    "Vite": {"slug": "vite", "color": "#646CFF"},

    "Python": {"slug": "python", "color": "#3776AB"},
    "Jupyter": {"slug": "jupyter", "color": "#F37626"},
    "Java": {"slug": "java", "ver": "6.23.0", "color": "#437291", "min_contrast": 7},  # logo cangkir, ganti slug ke "openjdk" kalau mau logo OpenJDK
    "Scikit-Learn": {"slug": "scikitlearn", "color": "#F7931E"},

    "Linux": {"slug": "linux", "color": "#FCC624"},
    "Ubuntu": {"slug": "ubuntu", "color": "#E95420"},
    "Bash": {"slug": "gnubash", "color": "#4EAA25"},
    "Nginx": {"slug": "nginx", "color": "#009639"},
    "Docker": {"slug": "docker", "color": "#2496ED"},
    "Cisco": {"slug": "cisco", "color": "#1BA0D7", "min_contrast": 7},
    "VirtualBox": {"slug": "virtualbox", "color": "#183A61", "min_contrast": 7},

    "Android Studio": {"slug": "androidstudio", "color": "#3DDC84"},
    "Apache NetBeans": {"color_icon": "netbeans", "slug": "apachenetbeanside", "color": "#1B6AC6"},
    "Notepad++": {"slug": "notepadplusplus", "color": "#90E59A"},
    "Postman": {"slug": "postman", "color": "#FF6C37"},
    "Git": {"slug": "git", "color": "#F05032"},
    "GitHub": {"slug": "github", "color": "#181717"},

    "Flutter": {"slug": "flutter", "color": "#02569B"},
    "Dart": {"color_icon": "dart", "slug": "dart", "color": "#0175C2"},
    "Firebase": {"slug": "firebase", "color": "#FFCA28"},

    "MySQL": {"slug": "mysql", "color": "#4479A1", "min_contrast": 7},
    "SQLite": {"color_icon": "sqlite", "slug": "sqlite", "color": "#003B57"},
    "Supabase": {"slug": "supabase", "color": "#3ECF8E"},
    "PostgreSQL": {"slug": "postgresql", "color": "#4169E1"}
}

STACK_GROUPS = [
    {"title": "Web Development", "items": ["HTML", "CSS", "JavaScript", "PHP", "CodeIgniter", "Laravel", "Tailwind", "Bootstrap", "Node.js", "Vite"]},
    {"title": "Data, ML &amp; AI", "items": ["Python", "Jupyter", "Java", "Scikit-Learn", "Orange"]},
    {"title": "OS, Network &amp; DevOps", "items": ["Windows", "Linux", "Ubuntu", "Bash", "Nginx", "Docker", "Cisco", "VirtualBox"]},
    {"title": "IDEs &amp; Tools", "items": ["VS Code", "Antigravity", "Android Studio", "Apache NetBeans", "Canva", "Notepad++", "Postman", "Git", "GitHub"]},
    {"title": "Mobile (learning)", "items": ["Flutter", "Dart", "Firebase"]},
    {"title": "Database", "items": ["MySQL", "SQLite", "Supabase", "PostgreSQL"]}
]

# ==========================================
# 2. FUNGSI IKON (CACHE, FETCH, KONTRAS)
# ==========================================
def load_icon_file():
    # satu file berisi dua bagian: "cache" (ikon Simple Icons) dan "color" (ikon berwarna asli)
    try:
        with open(ICON_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        print(f"[!] {os.path.basename(ICON_FILE)} tidak ditemukan, ikon berwarna pakai cadangan")
        data = {}
    data.setdefault("cache", {})
    data.setdefault("color", {})
    return data

ICON_DATA = load_icon_file()
CACHE = ICON_DATA["cache"]
COLOR_ICONS = ICON_DATA["color"]
CACHE_AWAL = json.dumps(CACHE, sort_keys=True)
IKON_GAGAL = []      # ikon yang gagal diambil, dilaporkan di akhir
GRADIENT_DEFS = {}   # definisi gradasi yang dipakai, dimasukkan ke <defs> saat build

def save_cache():
    # hanya ditulis ulang kalau ada ikon baru, bagian "color" ikut ditulis apa adanya
    if json.dumps(CACHE, sort_keys=True) == CACHE_AWAL:
        return
    with open(ICON_FILE, "w", encoding="utf-8") as f:
        json.dump(ICON_DATA, f, indent=1, sort_keys=True)
    print(f"[*] icon.json diperbarui ({len(CACHE)} ikon Simple Icons)")

def fetch_svg_path(slug, ver):
    url = CDN_URL.format(ver=ver, slug=slug)
    error = "SVG tidak punya path"
    for _ in range(2):  # coba 2 kali
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
            # baca atribut d lewat parser XML, bukan regex
            paths = [el.get("d") for el in root.iter() if el.tag.endswith("path") and el.get("d")]
            if paths:
                return " ".join(paths)
        except Exception as e:
            error = e
    print(f"[!] Gagal mengambil ikon '{slug}' (v{ver}): {error}")
    return ""

def get_svg_path(name):
    icon_data = ICONS.get(name, {})

    # 1. Prioritaskan custom path kalau ada
    if icon_data.get("path"):
        return icon_data["path"]

    # 2. Simple Icons: cache dulu, baru internet
    slug = icon_data.get("slug", "")
    if not slug:
        return ""
    key = f"{icon_data.get('ver', SI_VERSION)}/{slug}"
    if key not in CACHE:
        path = fetch_svg_path(slug, icon_data.get("ver", SI_VERSION))
        if not path:
            return ""
        CACHE[key] = {"path": path}
    return CACHE[key]["path"]

def get_color(name):
    icon_data = ICONS.get(name, {})
    if icon_data.get("color"):
        return icon_data["color"]
    # kalau warna nggak diisi, pakai warna resmi dari cache
    key = f"{icon_data.get('ver', SI_VERSION)}/{icon_data.get('slug', '')}"
    hex_resmi = CACHE.get(key, {}).get("hex")
    return f"#{hex_resmi}" if hex_resmi else MUTED

def _rgb(color):
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))

def _luminance(rgb):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

def readable_color(color, min_contrast=None):
    # Ikon gelap di latar gelap (misal GitHub hitam) bakal hilang.
    # Kalau kontrasnya kurang, warnanya digeser pelan-pelan ke putih (atau hitam di latar terang).
    if not AUTO_CONTRAST:
        return color
    min_contrast = min_contrast or MIN_CONTRAST
    try:
        fg, bg = _rgb(color), _rgb(BACKGROUND)
    except (ValueError, TypeError, AttributeError):
        return color
    if _contrast(fg, bg) >= min_contrast:
        return color
    target = (255, 255, 255) if _luminance(bg) < 0.5 else (0, 0, 0)
    for _ in range(20):
        fg = tuple(round(c + (t - c) * 0.12) for c, t in zip(fg, target))
        if _contrast(fg, bg) >= min_contrast:
            break
    return "#%02X%02X%02X" % fg

def color_icon_svg(key, x, y):
    # Ikon berwarna: tiap layer punya warna sendiri. Layer polos diberi garis tipis
    # sewarna supaya tidak ada celah halus antar bidang.
    icon = COLOR_ICONS.get(key)
    if not icon:
        return ""
    for gid, g in icon.get("gradients", {}).items():
        full = f"ci-{key}-{gid}"
        stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in g["stops"])
        GRADIENT_DEFS[full] = f'<linearGradient id="{full}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'
    layers = []
    for layer in icon["layers"]:
        fill = layer["fill"]
        if fill.startswith("grad:"):
            layers.append(f'<path d="{layer["d"]}" fill="url(#ci-{key}-{fill[5:]})"/>')
        else:
            fill = readable_color(fill, COLOR_ICON_MIN_CONTRAST)
            layers.append(f'<path d="{layer["d"]}" fill="{fill}" stroke="{fill}" stroke-width="0.1" stroke-linejoin="round"/>')
    return f'<g transform="translate({x + 10}, {y + 6}) scale(0.66)">{"".join(layers)}</g>'

def icon_svg(name, x, y):
    data = ICONS.get(name, {})
    if data.get("color_icon"):
        svg = color_icon_svg(ICONS[name]["color_icon"], x, y)
        if svg:
            return svg

    color = readable_color(get_color(name), data.get("min_contrast"))
    path = get_svg_path(name)

    if path:
        return f'<g transform="translate({x + 10}, {y + 6}) scale(0.66)"><path d="{path}" fill="{color}"/></g>'

    # Fallback: kotak berwarna berisi huruf pertama, ukurannya sama dengan ikon biasa
    if name not in IKON_GAGAL:
        IKON_GAGAL.append(name)
    huruf = escape(name[:1].upper())
    return (f'<rect x="{x + 10}" y="{y + 6}" width="16" height="16" rx="4" fill="{color}"/>'
            f'<text x="{x + 18}" y="{y + 18}" font-size="11" font-weight="bold" '
            f'text-anchor="middle" fill="{BACKGROUND}">{huruf}</text>')

def check_icons():
    # Cek typo: nama di STACK_GROUPS harus ada di ICONS
    dipakai = {item for group in STACK_GROUPS for item in group["items"]}
    for name in sorted(dipakai - set(ICONS)):
        print(f"[!] '{name}' ada di STACK_GROUPS tapi belum ada di ICONS (dipakai ikon huruf)")
    for name, data in ICONS.items():
        if data.get("color_icon") and data["color_icon"] not in COLOR_ICONS:
            print(f"[!] ikon berwarna '{data['color_icon']}' untuk '{name}' tidak ada di icon.json")
    for name in sorted(set(ICONS) - dipakai):
        print(f"[i] '{name}' ada di ICONS tapi tidak dipakai di STACK_GROUPS")

# ==========================================
# 3. LOGIKA RENDER LAYOUT SVG & ANIMASI
# ==========================================
OUTER_X = PAD                                   # margin kiri-kanan, ikut theme.py
GAP = 16                                        # jarak antar kotak
COL_WIDTH = (WIDTH - 2 * OUTER_X - GAP) / 2     # lebar satu kolom
TOP_Y = TITLEBAR_H + 24                         # awal konten di bawah titlebar

BOX_PAD = 16                                    # jarak isi ke tepi kotak
TITLE_H = 40                                    # tinggi area judul di dalam kotak
BOX_RADIUS = 10
BOX_FILL = "#ffffff"
BOX_FILL_OPACITY = 0.025

PILL_HEIGHT = 28
PILL_GAP_X = 10
PILL_GAP_Y = 10

CSS_ANIMATION = """
@keyframes typeIn {
    0% { opacity: 0; transform: translateX(-5px); }
    100% { opacity: 1; transform: translateX(0); }
}
.anim {
    opacity: 0;
    animation: typeIn 0.3s ease-out forwards;
}
@media (prefers-reduced-motion: reduce) {
    .anim { animation: none !important; opacity: 1 !important; transform: none !important; }
}
"""

def pill_width(name):
    return 46 + len(name) * 7.5

def get_anim_delay(x, y):
    return (y - TOP_Y) * 0.003 + (x - OUTER_X) * 0.001

def draw_pill(x, y, name, delay):
    text_width = len(name) * 7.5

    # semua pill punya ikon (minimal ikon huruf), jadi lebarnya selalu sama
    inner_svg = f'<rect x="{x}" y="{y}" width="{pill_width(name)}" height="{PILL_HEIGHT}" rx="14" fill="{BACKGROUND}" stroke="{BORDER}" stroke-width="1"/>'
    inner_svg += icon_svg(name, x, y)
    inner_svg += f'<text x="{x + 32}" y="{y + 19}" font-size="12" fill="{TEXT}">{escape(name)}</text>'

    return f'<g class="anim" style="animation-delay: {delay:.2f}s;">{inner_svg}</g>'

def layout_group(group):
    # Hitung posisi tiap pill (relatif ke kotak) dan tinggi kotaknya
    inner_w = COL_WIDTH - 2 * BOX_PAD
    x, row = 0, 0
    items = []
    for name in group["items"]:
        w = pill_width(name)
        if x > 0 and x + w > inner_w:
            x, row = 0, row + 1
        items.append((name, x, row * (PILL_HEIGHT + PILL_GAP_Y)))
        x += w + PILL_GAP_X
    height = TITLE_H + (row + 1) * PILL_HEIGHT + row * PILL_GAP_Y + BOX_PAD
    return items, height

def draw_group(group, items, box_x, box_y, height):
    box = (f'<rect x="{box_x}" y="{box_y}" width="{COL_WIDTH}" height="{height}" rx="{BOX_RADIUS}" '
           f'fill="{BOX_FILL}" fill-opacity="{BOX_FILL_OPACITY}" stroke="{BORDER}"/>')
    title = (f'<text x="{box_x + BOX_PAD}" y="{box_y + BOX_PAD + 12}" font-weight="bold" '
             f'font-size="14" fill="{ACCENT}">{group["title"]}</text>')
    parts = [f'<g class="anim" style="animation-delay: {get_anim_delay(box_x, box_y):.2f}s;">{box}{title}</g>']

    for name, rel_x, rel_y in items:
        px, py = box_x + BOX_PAD + rel_x, box_y + TITLE_H + rel_y
        parts.append(draw_pill(px, py, name, get_anim_delay(px, py)))
    return parts

def assign_columns(heights):
    # Coba semua kemungkinan pembagian grup ke 2 kolom (cukup cepat untuk belasan grup),
    # ambil yang kolom terpanjangnya paling pendek supaya kedua kolom hampir sama tinggi.
    # Urutan grup di dalam kolom tetap mengikuti STACK_GROUPS.
    best = None
    for combo in product((0, 1), repeat=len(heights)):
        col = [0, 0]
        for c, h in zip(combo, heights):
            col[c] += h + GAP
        key = (max(col), abs(col[0] - col[1]), combo)
        if best is None or key < best[0]:
            best = (key, combo)
    return best[1]

def build_svg():
    print("[*] Memulai render Stack SVG dengan Animasi...")
    col_x = [OUTER_X, OUTER_X + COL_WIDTH + GAP]
    col_y = [TOP_Y, TOP_Y]
    parts = []

    layouts = [layout_group(group) for group in STACK_GROUPS]
    columns = assign_columns([height for _, height in layouts])

    for group, (items, height), c in zip(STACK_GROUPS, layouts, columns):
        parts += draw_group(group, items, col_x[c], col_y[c], height)
        col_y[c] += height + GAP

    total_height = max(col_y) - GAP + PAD

    header_parts = window_open(total_height, "ahnafwzz@github: ~/stack", css=CSS_ANIMATION)

    svg_content = "\n".join(header_parts)
    if GRADIENT_DEFS:
        svg_content += "\n<defs>" + "".join(GRADIENT_DEFS.values()) + "</defs>"
    svg_content += "\n" + "\n".join(parts)
    svg_content += "\n</svg>"

    return svg_content

if __name__ == "__main__":
    check_icons()
    svg_out = build_svg()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_out)
    save_cache()
    if IKON_GAGAL:
        print(f"[!] Ikon yang gagal diambil (dipakai ikon huruf): {', '.join(IKON_GAGAL)}")
    print(f"Selesai! ahnaf-stack.svg animasi berhasil dibuat di {OUT_PATH}")