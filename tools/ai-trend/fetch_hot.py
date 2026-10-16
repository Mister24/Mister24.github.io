#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取热榜（知乎热榜 / 虎扑步行街），输出 tools/ai-trend/data/hot.json

用法：python3 tools/ai-trend/fetch_hot.py
单个来源抓取失败时沿用上一次的数据，不影响站点构建。
"""

import datetime
import html as htmlmod
import json
import os
import re
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tools", "ai-trend", "data")
DAYS = os.path.join(DATA, "hot-days")
OUT = os.path.join(DATA, "hot.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
ZH_URL = "https://60s.viki.moe/v2/zhihu"
HUPU_URL = "https://bbs.hupu.com/bxj"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def num(s):
    try:
        return int(re.sub(r"[^\d]", "", s or ""))
    except ValueError:
        return 0


def txt(s):
    return htmlmod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or ""))).strip()


def fetch_zhihu(limit=25):
    """知乎热榜：走 60s 聚合接口（zhihu 官方接口需登录态，直连会 401）"""
    data = []
    for i in range(3):                             # 接口偶发返回空，重试几次
        data = json.loads(get(ZH_URL)).get("data") or []
        if data:
            break
        time.sleep(2)
    out = []
    for d in data[:limit]:
        if not d.get("title") or not d.get("link"):
            continue
        out.append({
            "title": txt(d["title"]),
            "url": d["link"],
            "hot": txt(d.get("hot_value_desc", "")),
            "answers": num(str(d.get("answer_cnt", 0))),
        })
    return out


def parse_hupu(page, limit=25):
    """虎扑步行街：解析版面帖子列表（标题 / 回复 / 浏览 / 作者 / 时间）"""
    out = []
    for blk in re.findall(r'<li class="bbs-sl-web-post-body">(.*?)</li>', page, re.S):
        m = re.search(r'<a href="/(\d+)\.html"[^>]*class="p-title"[^>]*>(.*?)</a>',
                      blk, re.S)
        if not m:
            continue
        title = txt(m.group(2))
        if not title:
            continue
        tail = re.sub(r"<svg[\s\S]*?</svg>", "", blk[m.end():])
        segs = [s.strip() for s in re.sub(r"<[^>]+>", "\x01", tail).split("\x01") if s.strip()]
        stat = next((s for s in segs if re.fullmatch(r"[\d,]+\s*/\s*[\d,]+", s)), "")
        rep, view = (stat.split("/") + ["", ""])[:2] if stat else ("", "")
        out.append({
            "title": title,
            "url": f"https://bbs.hupu.com/{m.group(1)}.html",
            "replies": num(rep),
            "views": num(view),
            "author": segs[-2] if len(segs) >= 4 else "",
            "time": segs[-1] if segs else "",
        })
        if len(out) >= limit:
            break
    return out


def fetch_hupu(limit=25):
    out = []
    for i in range(3):                             # 版面偶发返回空，重试几次
        out = parse_hupu(get(HUPU_URL), limit)
        if out:
            break
        time.sleep(2)
    return out


def main():
    os.makedirs(DAYS, exist_ok=True)
    today = datetime.date.today().isoformat()
    result = {"date": today, "zhihu": [], "hupu": []}
    for key, fn in (("zhihu", fetch_zhihu), ("hupu", fetch_hupu)):
        try:
            result[key] = fn()
        except Exception as exc:                   # 单个来源失败：沿用上一次结果
            print(f"warn: {key} fetch failed ({exc})")
            if os.path.exists(OUT):
                prev = json.load(open(OUT, encoding="utf-8"))
                result[key] = prev.get(key, [])
    if not result["zhihu"] and not result["hupu"]:
        print("skip: 无数据，保留既有 hot.json")
        return
    if not result["zhihu"] or not result["hupu"]:   # 只有一个来源成功时补旧值
        if os.path.exists(OUT):
            prev = json.load(open(OUT, encoding="utf-8"))
            for key in ("zhihu", "hupu"):
                if not result[key] and prev.get(key):
                    result[key] = prev[key]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(DAYS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"hot: {len(result['zhihu'])} zhihu / {len(result['hupu'])} hupu @ {today}")


if __name__ == "__main__":
    main()
