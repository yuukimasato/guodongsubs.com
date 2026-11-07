# -*- coding: utf-8 -*-
"""Regenerate content/page/downloads.md from the subtitle release assets.

Usage: python3 tools/gen_downloads_page.py   (requires `gh` authenticated)
GitHub renames release assets on upload (spaces/brackets/& -> dots), so this
maps local files to real asset names by exact file size and links accordingly.
"""
import os, re, json, datetime, collections, subprocess
from urllib.parse import quote

ASS = os.path.join(os.path.dirname(__file__), "..", "..", "ass")
REPO = "yuukimasato/guodongsubs.com"
TAG = "v1.0-subtitles"
BASE = f"https://github.com/{REPO}/releases/download/{TAG}/"
OUT = os.path.join(os.path.dirname(__file__), "..", "content", "page", "downloads.md")

def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024

def fetch_assets():
    r = subprocess.run(["gh", "api", f"repos/{REPO}/releases/tags/{TAG}",
                        "--jq", "[.assets[] | {name, size}]"],
                       capture_output=True, text=True, timeout=120, check=True)
    return json.loads(r.stdout)

def main():
    assets = fetch_assets()
    by_size = collections.defaultdict(list)
    for a in assets:
        by_size[a["size"]].append(a["name"])
    groups = {}
    for f in sorted(os.listdir(ASS)):
        size = os.path.getsize(os.path.join(ASS, f))
        cands = by_size.get(size, [])
        asset = cands[0] if len(cands) == 1 else None
        if asset is None:
            print(f"SKIP (no unique size match): {f}")
            continue
        tokens = re.findall(r"\[([^\]]+)\]", f)
        series = tokens[1].lstrip("[").strip() if len(tokens) > 1 else "Others"
        groups.setdefault(series or "Others", []).append((f, asset, size))
    lines = [
        "---",
        'title: "Subtitle Downloads"',
        "url: /downloads/",
        "showReadingTime: false",
        "showDate: false",
        "draft: false",
        "---",
        "",
        "Complete subtitle packages (ASS scripts + fonts + sometimes hardsubbed MKV) released by GuodongSubs and FrozenFruitSubs between 2018 and 2021. Files are hosted on GitHub Releases and download directly. 字幕打包下载，点击文件名即可直接下载。",
        "",
        "> 字幕包共 %d 个，含内嵌字体。部分旧包为 MKV 视频压制版，体积较大。" % sum(len(v) for v in groups.values()),
        "",
    ]
    for series in sorted(groups):
        lines += [f"## {series}", "", "| File | Size | Date |", "|---|---|---|"]
        for f, asset, size in sorted(groups[series]):
            d = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(ASS, f))).strftime("%Y-%m-%d")
            disp = f.replace("[", "\\[").replace("]", "\\]")
            lines.append(f"| [{disp}]({BASE}{quote(asset)}) | {human(size)} | {d} |")
        lines.append("")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"written: {OUT} ({len(groups)} series, {sum(len(v) for v in groups.values())} files)")

if __name__ == "__main__":
    main()
