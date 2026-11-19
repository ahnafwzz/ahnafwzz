#!/usr/bin/env python3
import json
import math
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USERNAME = os.environ.get("GH_PROFILE_USER", "ahnafwzz")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "github_data.json")

MAX_REPOS = 100
TOP_LANGS = int(os.environ.get("TOP_LANGS", 8))
MIN_SHARE = float(os.environ.get("MIN_SHARE", 0.5))
LANG_WEIGHT = os.environ.get("LANG_WEIGHT", "repo")
LANG_IGNORE = {name.strip() for name in os.environ.get("LANG_IGNORE", "").split(",") if name.strip()}

# repo yang isinya bukan kode (misal file .pkt Packet Tracer) tidak punya bahasa di GitHub
LANGUAGE_OVERRIDES = {"jaringan": "Packet Tracer"}
OVERRIDES = {repo.lower(): lang for repo, lang in LANGUAGE_OVERRIDES.items()}

API_HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    API_HEADERS["Authorization"] = f"Bearer {TOKEN}"


def make_session():
    session = requests.Session()
    session.headers["User-Agent"] = "ahnaf-terminal-bot/4.0"
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET",), respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
    return session


SESSION = make_session()


def load_previous():
    try:
        with open(OUT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def fetch_contributions():
    url = f"https://github.com/users/{USERNAME}/contributions"
    print(f"[*] Menarik data kontribusi dari {url}")
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        raise ValueError("kalender kontribusi tidak ditemukan, struktur halaman GitHub mungkin berubah")

    tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        text = tooltips.get(td.get("id"), "")
        match = re.match(r"(\d+)", text)
        count = int(match.group(1)) if match and not re.search(r"no contributions", text, re.I) else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})

    days.sort(key=lambda d: d["date"])
    return days


def fetch_repos():
    print(f"[*] Mengambil daftar repository {USERNAME}")
    repos = []
    page = 1
    while len(repos) < MAX_REPOS:
        try:
            resp = SESSION.get(
                f"https://api.github.com/users/{USERNAME}/repos",
                headers=API_HEADERS,
                params={"sort": "pushed", "per_page": 100, "page": page},
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException as err:
            print(f"[!] Gagal ambil repo: {err}")
            return None
        batch = resp.json()
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos[:MAX_REPOS]


def pick_top_repos(repos):
    top = []
    for r in repos:
        if r.get("fork") or r.get("archived") or r["name"].lower() == USERNAME.lower():
            continue
        top.append({
            "name": r["name"],
            "description": r.get("description") or "",
            "language": r.get("language") or "Unknown",
            "stars": r.get("stargazers_count", 0),
            "updated_at": r.get("pushed_at") or r.get("updated_at"),
        })
        if len(top) == 3:
            break
    return top


def fetch_repo_languages(repo):
    try:
        resp = SESSION.get(repo["languages_url"], headers=API_HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, KeyError, ValueError) as err:
        print(f"[!] Bahasa {repo.get('name')} dilewati: {err}")
        return None


def repo_weights(stats):
    stats = {name: n for name, n in stats.items() if name not in LANG_IGNORE and n > 0}
    total = sum(stats.values())
    if not total:
        return {}
    if LANG_WEIGHT == "repo":
        return {name: n / total for name, n in stats.items()}
    if LANG_WEIGHT == "sqrt":
        return {name: math.sqrt(n) for name, n in stats.items()}
    return stats


def round_to_hundred(shares):
    floors = [int(s) for s in shares]
    remainders = [s - f for s, f in zip(shares, floors)]
    for i in sorted(range(len(shares)), key=lambda i: remainders[i], reverse=True)[:100 - sum(floors)]:
        floors[i] += 1
    return floors


def summarize_languages(totals, repo_count):
    grand = sum(totals.values())
    if not grand:
        return None

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    named = [(name, value / grand * 100) for name, value in ranked[:TOP_LANGS]]
    named = [(name, share) for name, share in named if share >= MIN_SHARE]
    other = 100 - sum(share for _, share in named)

    entries = list(named)
    if other >= 0.5:
        entries.append(("Other", other))

    percents = round_to_hundred([share for _, share in entries])
    items = [{"name": name, "percent": p} for (name, _), p in zip(entries, percents) if p > 0]
    return {"repo_count": repo_count, "weighting": LANG_WEIGHT, "items": items}


def split_repos(repos):
    counted, skipped = [], []
    for r in repos:
        if r.get("fork"):
            skipped.append((r["name"], "fork"))
        elif r["name"].lower() == USERNAME.lower():
            skipped.append((r["name"], "repo profil"))
        else:
            counted.append(r)
    return counted, skipped


def fetch_languages(repos):
    counted, skipped = split_repos(repos)
    if not counted:
        return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_repo_languages, counted))

    totals = {}
    rows = []
    for repo, stats in zip(counted, results):
        weights = repo_weights(stats or {})
        if weights:
            note = ", ".join(sorted(weights, key=weights.get, reverse=True)[:3])
        elif repo["name"].lower() in OVERRIDES:
            extra = OVERRIDES[repo["name"].lower()]
            weights = {extra: 1.0}
            note = f"tanpa bahasa terdeteksi, pakai override: {extra}"
        else:
            note = "tanpa bahasa terdeteksi (tetap dihitung sebagai repo)"
        for name, value in weights.items():
            totals[name] = totals.get(name, 0) + value
        rows.append((repo["name"], note))

    print(f"[*] Komposisi bahasa: {len(counted)} repo dihitung, {len(skipped)} dilewati")
    for name, note in rows:
        print(f"    + {name:<30} {note}")
    for name, why in skipped:
        print(f"    - {name:<30} dilewati ({why})")

    return summarize_languages(totals, len(counted))


def build_data(days, repos, languages):
    return {
        "username": USERNAME,
        "total_contributions": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "days": days,
        "top_repos": repos,
        "languages": languages,
    }


def save(data):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp_path = OUT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, OUT_PATH)


if __name__ == "__main__":
    previous = load_previous()

    try:
        days = fetch_contributions()
    except (requests.RequestException, ValueError) as err:
        if not previous.get("days"):
            sys.exit(f"Gagal ambil kontribusi dan belum ada data lama: {err}")
        print(f"[!] {err}. Pakai kontribusi sebelumnya")
        days = previous["days"]

    repos = fetch_repos()
    if repos is None:
        top_repos = previous.get("top_repos", [])
        languages = previous.get("languages")
        print("[!] Pakai data repo dan bahasa sebelumnya")
    else:
        top_repos = pick_top_repos(repos)
        languages = fetch_languages(repos) or previous.get("languages")

    save(build_data(days, top_repos, languages))
    print("Selesai! Data disimpan di data/github_data.json")
