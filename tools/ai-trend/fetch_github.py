#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 GitHub Trending（日榜 / 周榜），输出 tools/ai-trend/data/github.json

用法：python3 tools/ai-trend/fetch_github.py
抓取失败时保留上一次的数据，不影响站点构建。
"""

import datetime
import html as htmlmod
import json
import os
import re
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tools", "ai-trend", "data")
DAYS = os.path.join(DATA, "gh-days")
OUT = os.path.join(DATA, "github.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def num(s):
    try:
        return int(re.sub(r"[^\d]", "", s or ""))
    except ValueError:
        return 0


def parse_trending(html, limit=15):
    items = []
    for blk in re.findall(r'<article class="Box-row">(.*?)</article>', html, re.S)[:limit]:
        m = re.search(r'<h2\b[^>]*>\s*<a\b[^>]*href="/([^"]+)"', blk)
        if not m:
            continue
        full = m.group(1).strip("/")
        desc = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', blk, re.S)
        lang = re.search(r'<span itemprop="programmingLanguage">(.*?)</span>', blk)
        stars = re.search(r'/stargazers"[\s\S]*?</svg>\s*([\d,\.km]+)\s*</a>', blk)
        forks = re.search(r'/forks"[\s\S]*?</svg>\s*([\d,\.km]+)\s*</a>', blk)
        period = re.search(
            r'float-sm-right">\s*<svg[\s\S]*?</svg>\s*([\d,]+)\s*stars\s+(today|this week|this month)',
            blk)
        desc_txt = re.sub(r"<[^>]+>", "", desc.group(1)) if desc else ""
        items.append({
            "name": full,
            "url": f"https://github.com/{full}",
            "desc": htmlmod.unescape(re.sub(r"\s+", " ", desc_txt)).strip(),
            "lang": (lang.group(1).strip() if lang else ""),
            "stars": num(stars.group(1)) if stars else 0,
            "forks": num(forks.group(1)) if forks else 0,
            "delta": num(period.group(1)) if period else 0,
            "since": (period.group(2) if period else ""),
        })
    return items


def main():
    os.makedirs(DAYS, exist_ok=True)
    today = datetime.date.today().isoformat()
    result = {"date": today, "daily": [], "weekly": []}
    try:
        result["daily"] = parse_trending(get("https://github.com/trending?since=daily"))
        result["weekly"] = parse_trending(get("https://github.com/trending?since=weekly"))
    except Exception as exc:                      # 抓取失败：沿用上一次结果
        print(f"warn: fetch failed ({exc})")
        if os.path.exists(OUT):
            prev = json.load(open(OUT, encoding="utf-8"))
            if not result["daily"]:
                result = prev
        else:
            result = None
    if not result or not result.get("daily"):
        print("skip: 无数据，保留既有 github.json")
        return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(DAYS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"github trending: {len(result['daily'])} daily / "
          f"{len(result['weekly'])} weekly @ {today}")


if __name__ == "__main__":
    main()
