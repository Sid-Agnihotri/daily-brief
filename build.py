#!/usr/bin/env python3
"""Daily Brief site builder.

Single source of truth: data/progress.json (curriculum + log of every edition).
Each edition is a hand-written HTML file in editions/ with three marker pairs
that this script fills in:  NAV, MAP, FOOT.

Hosting: GitHub Pages from the main branch of Sid-Agnihotri/daily-brief.
index.html is a copy of the latest edition, so the home URL always shows today's brief.

Published editions keep the same nav, progress map and footer forever: each depends
only on data up to its own date, so rebuilding never rewrites history.

Usage:
  python3 build.py            validate, then (re)build every page
  python3 build.py check      validate only
  python3 build.py status     print what the next edition should be (JSON)
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "progress.json"
COLOR = {"quantum": "var(--q)", "systems": "var(--s)", "ai": "var(--a)", "wildcard": "var(--w)"}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700'
         '&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap" rel="stylesheet">')
MARKERS = ("NAV", "MAP", "FOOT")
esc = html.escape


# ---------------------------------------------------------------- data helpers
def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def d(s):
    return dt.date.fromisoformat(s)


def long_date(s):
    return d(s).strftime("%A, %B %-d, %Y")


def short_date(s):
    return d(s).strftime("%b %-d, %Y")


def tracks_by_id(data):
    return {t["id"]: t for t in data["tracks"]}


def editions_sorted(data):
    return sorted(data["editions"], key=lambda e: e["date"])


def learned_until(data, date):
    """{track_id: {stop_id: (edition, item)}} for learn items on or before date."""
    out = {t["id"]: {} for t in data["tracks"]}
    for e in editions_sorted(data):
        if e["date"] > date:
            break
        for it in e["items"]:
            if it.get("stop"):
                out[it["track"]][it["stop"]] = (e, it)
    return out


def wildcards_until(data, date):
    return [(e, it) for e in editions_sorted(data) if e["date"] <= date
            for it in e["items"] if it["track"] == "wildcard"]


def next_stop(track, learned):
    for i, s in enumerate(track["syllabus"]):
        if s["id"] not in learned:
            return i, s
    return None, None


# ---------------------------------------------------------------- validation
def check(data):
    errs = []
    tb = tracks_by_id(data)
    seen_stops, seen_dates, seen_days = set(), set(), set()
    eds = editions_sorted(data)
    latest = eds[-1]["date"] if eds else None
    for e in eds:
        tag = e.get("date", "?")
        for k in ("date", "day", "mode", "title", "file", "items"):
            if k not in e:
                errs.append(f"{tag}: missing '{k}'")
        if e.get("mode") not in ("learn", "news"):
            errs.append(f"{tag}: mode must be 'learn' or 'news'")
        if e["date"] in seen_dates:
            errs.append(f"{tag}: duplicate date")
        if e["day"] in seen_days:
            errs.append(f"{tag}: duplicate day number {e['day']}")
        seen_dates.add(e["date"]); seen_days.add(e["day"])
        f = ROOT / e["file"]
        if not f.exists():
            if e["date"] == latest:
                errs.append(f"{tag}: file {e['file']} not found")
            src = None
        else:
            src = f.read_text(encoding="utf-8")
        for it in e["items"]:
            t = it.get("track")
            if t in tb and e["mode"] == "learn" and t != "wildcard":
                stop = it.get("stop")
                ids = [x["id"] for x in tb[t]["syllabus"]]
                if stop not in ids:
                    errs.append(f"{tag}: stop '{stop}' is not in the {t} syllabus")
                elif (t, stop) in seen_stops:
                    errs.append(f"{tag}: stop '{stop}' was already learned")
                seen_stops.add((t, stop))
        if src is None:
            continue
        for m in MARKERS:
            if f"<!--{m}:START-->" not in src or f"<!--{m}:END-->" not in src:
                errs.append(f"{tag}: {e['file']} is missing <!--{m}:START--> / <!--{m}:END--> markers")
        for it in e["items"]:
            t = it.get("track")
            if t not in tb:
                errs.append(f"{tag}: unknown track '{t}'")
                continue
            if f'id="{it.get("anchor")}"' not in src:
                errs.append(f"{tag}: anchor id=\"{it.get('anchor')}\" not found in {e['file']}")
            if e["mode"] == "news" and it.get("stop"):
                errs.append(f"{tag}: news items must not have a 'stop'")
            tk = it.get("takeaways", [])
            if not 1 <= len(tk) <= 4:
                errs.append(f"{tag}/{t}: needs 1 to 4 takeaways")
            srcs = it.get("sources", [])
            if not srcs or any(not s.get("url", "").startswith("http") for s in srcs):
                errs.append(f"{tag}/{t}: every item needs at least one source with a URL")
    return errs


# ---------------------------------------------------------------- fragments
LOGO = ('<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">'
        '<path d="M2 15 L18 15" stroke="var(--s)" stroke-width="3" stroke-linecap="round"/>'
        '<path d="M2 10 L18 10" stroke="var(--a)" stroke-width="3" stroke-linecap="round"/>'
        '<path d="M2 5 L18 5" stroke="var(--q)" stroke-width="3" stroke-linecap="round"/>'
        '<circle cx="10" cy="10" r="3.6" fill="var(--paper)" stroke="var(--ink)" stroke-width="2"/></svg>')


def nav(prefix, current):
    def link(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{prefix}{href}"{cur}>{label}</a>'
    return ('<nav class="topbar" aria-label="Site">'
            f'<a class="brand" href="{prefix or "./"}">{LOGO}Daily Brief</a>'
            + link("archive.html", "Archive", "archive")
            + link("learned.html", "Learned", "learned")
            + "</nav>")


def line_svg(n, done_idx, today_idx, next_idx):
    W, pad, y = 300, 8, 11
    xs = [pad + (i * (W - 2 * pad) / (n - 1) if n > 1 else 0) for i in range(n)]
    last_done = max(done_idx) if done_idx else -1
    parts = [f'<svg viewBox="0 0 {W} 22" preserveAspectRatio="none" aria-hidden="true">',
             f'<line x1="{xs[0]:.1f}" y1="{y}" x2="{xs[-1]:.1f}" y2="{y}" stroke="var(--c)" stroke-width="4" '
             f'stroke-linecap="round" opacity=".22" vector-effect="non-scaling-stroke"/>']
    if last_done >= 0:
        parts.append(f'<line x1="{xs[0]:.1f}" y1="{y}" x2="{xs[last_done]:.1f}" y2="{y}" stroke="var(--c)" '
                     f'stroke-width="4" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    parts.append("</svg>")
    # Dots are drawn as positioned HTML so they stay round when the SVG stretches.
    dots = []
    for i, x in enumerate(xs):
        left = f"{x / W * 100:.2f}%"
        if i in done_idx:
            cls = "dot done today" if i in today_idx else "dot done"
        elif i == next_idx:
            cls = "dot next"
        else:
            cls = "dot"
        dots.append(f'<i class="{cls}" style="left:{left}"></i>')
    return '<span class="rail">' + "".join(parts) + "".join(dots) + "</span>"


def linemap(data, date, edition=None, link_prefix="", today_label="today"):
    """Progress across all lines as of `date`."""
    learned = learned_until(data, date)
    anchors = {it["track"]: it["anchor"] for it in (edition or {}).get("items", [])}
    rows = []
    for t in data["tracks"]:
        tid = t["id"]
        href = f'#{anchors[tid]}' if tid in anchors else f'{link_prefix}learned.html#{tid}'
        if t["syllabus"]:
            ids = [s["id"] for s in t["syllabus"]]
            done = {ids.index(s) for s in learned[tid]}
            today = {ids.index(s) for s, (e, _) in learned[tid].items() if e["date"] == date}
            ni, _ = next_stop(t, learned[tid])
            rail = line_svg(len(ids), done, today, ni)
            count = f"{len(done)}/{len(ids)}"
        else:
            wc = wildcards_until(data, date)
            n = len(wc)
            dots = "".join(
                f'<i class="dot done{" today" if e["date"] == date else ""}" style="left:{min(2.7 + i * 6, 97):.1f}%"></i>'
                for i, (e, _) in enumerate(wc[-17:]))
            rail = ('<span class="rail free"><svg viewBox="0 0 300 22" preserveAspectRatio="none" aria-hidden="true">'
                    '<line x1="8" y1="11" x2="292" y2="11" stroke="var(--c)" stroke-width="3" '
                    'stroke-dasharray="6 6" opacity=".35" vector-effect="non-scaling-stroke"/></svg>' + dots + '</span>')
            count = f"{n} detour" + ("" if n == 1 else "s")
        rows.append(f'<a class="row" href="{href}" style="--c:{COLOR[tid]}">'
                    f'<span class="name">{esc(t["short"])}</span>{rail}<span class="count">{count}</span></a>')
    legend = (f'<p class="legend"><i class="dot done today"></i>{today_label} '
              '<i class="dot done"></i>learned <i class="dot next"></i>next stop</p>')
    return '<div class="linemap" aria-label="Progress on each topic">' + "".join(rows) + legend + "</div>"


def foot(data, e, prefix):
    eds = editions_sorted(data)
    i = [x["date"] for x in eds].index(e["date"])
    prev_ = eds[i - 1] if i > 0 else None
    left = (f'<a href="{prefix}{prev_["file"]}">Previous: Day {prev_["day"]}</a>' if prev_
            else '<span class="muted">This is where it starts</span>')
    right = f'<a href="{prefix}archive.html">All editions</a>'
    return f'<footer class="edfoot">{left}{right}</footer>'


def inject(src, name, content):
    pat = re.compile(rf"<!--{name}:START-->.*?<!--{name}:END-->", re.S)
    return pat.sub(lambda _: f"<!--{name}:START-->{content}<!--{name}:END-->", src, count=1)


def page(title, body, current, description=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{FONTS}
<link rel="apple-touch-icon" href="assets/icon-180.png">
<meta name="apple-mobile-web-app-title" content="Daily Brief">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{nav("", current)}
<main>
{body}
</main>
</body>
</html>
"""


def mode_label(m):
    return "Learn day" if m == "learn" else "News day"


# ---------------------------------------------------------------- pages
def build_archive(data):
    tb = tracks_by_id(data)
    items = []
    for e in reversed(editions_sorted(data)):
        lis = "".join(
            f'<li style="--c:{COLOR[it["track"]]}"><i></i><a href="{e["file"]}#{it["anchor"]}">{esc(it["title"])}</a></li>'
            for it in e["items"])
        items.append(f'<li><span class="d">{mode_label(e["mode"])}, {long_date(e["date"])}</span>'
                     f'<a class="ed" href="{e["file"]}">{esc(e["title"])}</a><ul>{lis}</ul></li>')
    n = len(data["editions"])
    body = (f'<header class="pagehead"><h1>Archive</h1><p>{n} edition{"" if n == 1 else "s"} so far, newest first.</p></header>'
            f'<ol class="archive" reversed>{"".join(items)}</ol>')
    return page("Archive – Daily Brief", body, "archive", "Every edition of the Daily Brief.")


def build_learned(data):
    eds = editions_sorted(data)
    last = eds[-1]["date"] if eds else dt.date.today().isoformat()
    learned = learned_until(data, last)
    sections = []
    total_learned = 0
    for t in data["tracks"]:
        tid = t["id"]
        if not t["syllabus"]:
            continue
        ni, ns = next_stop(t, learned[tid])
        k = len(learned[tid]); total_learned += k
        lis = []
        for i, s in enumerate(t["syllabus"]):
            if s["id"] in learned[tid]:
                e, it = learned[tid][s["id"]]
                tk = "".join(f"<li>{esc(x)}</li>" for x in it["takeaways"])
                lis.append(f'<li class="done"><span class="st">{esc(s["title"])}</span>'
                           f'<div class="when">Day {e["day"]}, {short_date(e["date"])}. <a href="{e["file"]}#{it["anchor"]}">Read it again</a></div>'
                           f'<details><summary>What to remember</summary><ul>{tk}</ul></details></li>')
            elif i == ni:
                lis.append(f'<li class="next"><span class="st">{esc(s["title"])}</span><span class="tag">Next stop</span></li>')
            else:
                lis.append(f'<li><span class="st">{esc(s["title"])}</span></li>')
        nxt = f" Next: {esc(ns['title'])}." if ns else " Line complete."
        sections.append(f'<section class="line" id="{tid}" data-track="{tid}"><h2>{esc(t["name"])}</h2>'
                        f'<p class="sub">{k} of {len(t["syllabus"])} stops.{nxt}</p><ol class="stops">{"".join(lis)}</ol></section>')
    wc = wildcards_until(data, last)
    if wc:
        lis = "".join(
            f'<li class="done"><span class="st">{esc(it["title"])}</span>'
            f'<div class="when">Day {e["day"]}, {short_date(e["date"])}. <a href="{e["file"]}#{it["anchor"]}">Read it again</a></div>'
            f'<details><summary>What to remember</summary><ul>{"".join(f"<li>{esc(x)}</li>" for x in it["takeaways"])}</ul></details></li>'
            for e, it in wc)
        sections.append(f'<section class="line" id="wildcard" data-track="wildcard"><h2>Wildcard detours</h2>'
                        f'<p class="sub">{len(wc)} so far, oldest first.</p><ol class="stops">{lis}</ol></section>')
    news = [(e, it) for e in eds if e["mode"] == "news" for it in e["items"] if it["track"] != "wildcard"]
    if news:
        tb = tracks_by_id(data)
        lis = "".join(
            f'<li class="done" style="--c:{COLOR[it["track"]]}"><span class="st">{esc(it["title"])}</span>'
            f'<div class="when">{esc(tb[it["track"]]["short"])}, {short_date(e["date"])}. <a href="{e["file"]}#{it["anchor"]}">Read it again</a></div></li>'
            for e, it in reversed(news))
        sections.append(f'<section class="line" id="news"><h2>News you followed</h2>'
                        f'<p class="sub">{len(news)} stories, newest first.</p><ol class="stops">{lis}</ol></section>')
    head = (f'<header class="pagehead"><h1>What you’ve learned</h1>'
            f'<p>{total_learned} concepts across three lines, plus {len(wc)} detour{"" if len(wc) == 1 else "s"}. '
            f'Each line builds on the last stop.</p></header>')
    body = head + linemap(data, last, None, "", "latest") + "".join(sections)
    return page("What you’ve learned – Daily Brief", body, "learned", "Progress on every learning line.")


def build():
    data = load()
    errs = check(data)
    if errs:
        print("Build stopped. Fix these first:\n  " + "\n  ".join(errs))
        sys.exit(1)
    eds = editions_sorted(data)
    rebuilt = 0
    for e in eds:
        f = ROOT / e["file"]
        if not f.exists():
            continue  # published earlier and immutable; it stays as deployed
        src = f.read_text(encoding="utf-8")
        src = inject(src, "NAV", nav("../", None))
        src = inject(src, "MAP", linemap(data, e["date"], e, "../"))
        src = inject(src, "FOOT", foot(data, e, "../"))
        f.write_text(src, encoding="utf-8")
        rebuilt += 1
    latest = eds[-1]
    src = (ROOT / latest["file"]).read_text(encoding="utf-8")
    index = re.sub(r'(href|src)="\.\./', r'\1="', src).replace('href=""', 'href="./"')
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    (ROOT / "archive.html").write_text(build_archive(data), encoding="utf-8")
    (ROOT / "learned.html").write_text(build_learned(data), encoding="utf-8")
    print(f"Rebuilt {rebuilt} edition file(s); home page = Day {latest['day']} ({latest['date']}).")


def status():
    data = load()
    eds = editions_sorted(data)
    tz = ZoneInfo(data["site"].get("timezone", "UTC")) if ZoneInfo else None
    today = dt.datetime.now(tz).date().isoformat()
    last = eds[-1] if eds else None
    learned = learned_until(data, "9999-12-31")
    out = {
        "today": today,
        "already_published_today": bool(last and last["date"] == today),
        "last_edition": {"date": last["date"], "day": last["day"], "mode": last["mode"]} if last else None,
        "next_day": (last["day"] + 1) if last else 1,
        "next_mode": ("news" if last["mode"] == "learn" else "learn") if last else "learn",
        "next_file": f"editions/{today}.html",
        "next_stops": {},
        "learned_so_far": {},
        "wildcard_titles_so_far": [it["title"] for _, it in wildcards_until(data, "9999-12-31")],
        "recent_source_urls": sorted({s["url"] for e in eds[-14:] for it in e["items"] for s in it["sources"]}),
    }
    for t in data["tracks"]:
        if not t["syllabus"]:
            continue
        i, s = next_stop(t, learned[t["id"]])
        out["next_stops"][t["id"]] = ({"id": s["id"], "title": s["title"], "stop_number": i + 1,
                                       "of": len(t["syllabus"])} if s else None)
        out["learned_so_far"][t["id"]] = [x["title"] for x in t["syllabus"] if x["id"] in learned[t["id"]]]
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "check":
        errs = check(load())
        print("OK" if not errs else "\n".join(errs))
        sys.exit(1 if errs else 0)
    elif cmd == "status":
        status()
    else:
        build()
