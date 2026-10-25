#!/usr/bin/env python3
"""Watch GuodongSubs releases on Nyaa and create a Hugo post for each new torrent.

Bounded-retry policy: max 3 attempts, per-wait <= 30 s, cumulative wait <= 120 s.
On exhaustion the script exits 0 with a warning so the scheduled run is not
killed by a transient rate limit or outage; the next scheduled run retries.
"""
import json
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RSS_URL = "https://nyaa.si/?page=rss&u=GuodongSubs"
STATE_FILE = Path("data/nyaa_seen.json")
POSTS_DIR = Path("content/posts")

TRACKERS = [
    ("http", "nyaa.tracker.wf", "7777"),
    ("udp", "open.stealth.si", "80"),
    ("udp", "tracker.opentrackr.org", "1337"),
    ("udp", "exodus.desync.com", "6969"),
    ("udp", "tracker.torrent.eu.org", "451"),
]

NY = "{https://nyaa.si/xmlns/namespace}"


def parse_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.iter("item"):
        get = lambda tag: (item.findtext(tag) or "").strip()
        items.append({
            "id": get(NY + "infoHash") or get("guid"),
            "title": get("title"),
            "link": get("link"),
            "torrent": get(NY + "torrentLink") or get("link"),
            "infohash": get(NY + "infoHash"),
            "size": get(NY + "size"),
            "date": get("pubDate"),
        })
    return items


def fetch_rss():
    waited = 0
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(RSS_URL, headers={
                "User-Agent": "guodongsubs-site-watcher/1.0",
                "Accept": "application/rss+xml",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                delay = min(int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt, 30)
            elif e.code < 500:
                print(f"nyaa returned HTTP {e.code}; not retrying")
                sys.exit(0)
            else:
                delay = min(2 ** attempt, 30)
        except Exception as e:
            print(f"fetch error: {e}")
            delay = min(2 ** attempt, 30)
        if attempt == 3 or waited + delay > 120:
            print("retries exhausted; skipping this run (next scheduled run will retry)")
            sys.exit(0)
        time.sleep(delay)
        waited += delay


def magnet_for(infohash, title):
    if not infohash:
        return ""
    from urllib.parse import quote
    tr = "".join(f"&tr={s}%3A%2F%2F{h}%3A{p}%2Fannounce" for s, h, p in TRACKERS)
    return f"magnet:?xt=urn:btih:{infohash}&dn={quote(title)}{tr}"


def is_japanese(title):
    return bool(re.search(r"\[(?:JP|日本語|Japanese)\]|日本語", title, re.I))


def write_post(item):
    slug = item["infohash"] or re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")
    try:
        dt = datetime.strptime(item["date"], "%a, %d %b %Y %H:%M:%S %z")
        date_iso = dt.isoformat()
    except ValueError:
        date_iso = datetime.now(timezone.utc).isoformat()
    cat = "日本語" if is_japanese(item["title"]) else "English"

    parts = [
        "---",
        f"title: {json.dumps(item['title'], ensure_ascii=False)}",
        f"date: {date_iso}",
        f"url: /archives/{slug}/",
        f"categories: [{json.dumps(cat, ensure_ascii=False)}]",
        "draft: false",
        "---",
        "",
        f"Download address：<{item['link']}>",
        "",
        f"<{item['torrent']}>",
        "",
    ]
    magnet = magnet_for(item["infohash"], item["title"])
    if magnet:
        parts += [magnet, ""]
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    out = POSTS_DIR / f"nyaa-{slug}.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main():
    seen = set()
    if STATE_FILE.exists():
        seen = set(json.loads(STATE_FILE.read_text()))
    items = parse_items(fetch_rss())
    new = [i for i in items if i["id"] and i["id"] not in seen]
    if not new:
        print("no new releases")
        return
    created = []
    for item in sorted(new, key=lambda x: x["date"]):
        created.append(write_post(item))
        seen.add(item["id"])
        print("new post:", item["title"])
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=1))
    print(f"{len(created)} post(s) created; commit and push to deploy")


if __name__ == "__main__":
    main()
