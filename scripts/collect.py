#!/usr/bin/env python3
"""
Daily source scan for the Quebec Capital Tracker.

Reads sources.yaml, fetches every rss/html source, keeps items whose title
matches a keyword and misses every exclude term, drops anything already seen,
and writes what is left to data/review-queue.json.

It does not touch data/deals.json. Nothing reaches the site until a human
moves an entry across. That boundary is the point: an extraction error that
publishes itself costs more than a day of delay.

    python scripts/collect.py
"""

import json
import re
import sys
import time
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
QUEUE = DATA / "review-queue.json"
SEEN = DATA / "seen.json"

UA = "QuebecCapitalTracker/1.0 (research project; contact via site)"
DELAY = 2.0  # seconds between requests, be a polite guest


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse_rss(body: str, base: str) -> list[dict]:
    items = []
    for block in re.findall(r"<item[^>]*>(.*?)</item>", body, re.S | re.I):
        title = re.search(r"<title[^>]*>(.*?)</title>", block, re.S | re.I)
        link = re.search(r"<link[^>]*>(.*?)</link>", block, re.S | re.I)
        if not title:
            continue
        items.append({
            "title": strip_tags(title.group(1)),
            "url": strip_tags(link.group(1)) if link else base,
        })
    return items


def parse_html(body: str, base: str) -> list[dict]:
    items = []
    for href, inner in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S | re.I):
        text = strip_tags(inner)
        if len(text) < 25 or len(text) > 400:
            continue
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        items.append({"title": text, "url": urljoin(base, href)})
    return items


def matches(title: str, keywords: list[str], excludes: list[str]) -> bool:
    low = title.lower()
    if any(x.lower() in low for x in excludes):
        return False
    return any(k.lower() in low for k in keywords)


def main() -> int:
    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    keywords = cfg.get("keywords", [])
    excludes = cfg.get("exclude", [])

    seen = set(json.loads(SEEN.read_text()) if SEEN.exists() else [])
    found, skipped = [], []

    for src in cfg["sources"]:
        name, method = src["name"], src["method"]

        if method == "manual":
            skipped.append({"source": name, "why": src.get("why", ""), "url": src["url"]})
            continue

        urls = [src["url"]]
        if method == "html" and src.get("pages", 1) > 1:
            urls += [f"{src['url']}?page={i}" for i in range(1, src["pages"])]

        for url in urls:
            try:
                body = fetch(url)
            except Exception as exc:  # a dead source should not kill the run
                print(f"  ! {name} <{url}>: {exc}", file=sys.stderr)
                continue

            base = src.get("base", url)
            items = parse_rss(body, base) if method == "rss" else parse_html(body, base)

            for it in items:
                if it["url"] in seen or not matches(it["title"], keywords, excludes):
                    continue
                seen.add(it["url"])
                found.append({
                    "source": name,
                    "title": it["title"],
                    "url": it["url"],
                    "first_seen": date.today().isoformat(),
                })
            time.sleep(DELAY)

        print(f"  · {name}: scanned")

    queue = json.loads(QUEUE.read_text()) if QUEUE.exists() else []
    queue = found + queue

    QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    SEEN.write_text(json.dumps(sorted(seen), indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{len(found)} new item(s) queued · {len(queue)} awaiting review")
    for it in found:
        print(f"  [{it['source']}] {it['title'][:90]}")
    if skipped:
        print(f"\n{len(skipped)} source(s) need a human:")
        for s in skipped:
            print(f"  [{s['source']}] {s['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
