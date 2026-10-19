#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 AI 技术博客 / 落地实践分享，输出 tools/ai-trend/data/aiblog.json

用法：python3 tools/ai-trend/fetch_aiblog.py
来源：官方工程博客 RSS + 中文技术团队 RSS + Hacker News（Algolia API）
单个来源失败时沿用上一次的数据，不影响站点构建。
"""

import datetime
import email.utils
import html as htmlmod
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tools", "ai-trend", "data")
DAYS = os.path.join(DATA, "aiblog-days")
OUT = os.path.join(DATA, "aiblog.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HN_URL = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=50"

# key, 名称, 地址, 分组(official=官方工程博客 / cn=中文技术团队 / community=社区)
FEEDS = [
    ("openai", "OpenAI", "https://openai.com/news/rss.xml", "official"),
    ("deepmind", "Google DeepMind", "https://deepmind.google/blog/rss.xml", "official"),
    ("pytorch", "PyTorch", "https://pytorch.org/blog/feed/", "official"),
    ("aws", "AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/", "official"),
    ("google", "Google Blog", "https://blog.google/innovation-and-ai/technology/ai/rss/", "official"),
    ("meituan", "美团技术团队", "https://tech.meituan.com/rss.xml", "cn"),
    ("infoq", "InfoQ 中国", "https://www.infoq.cn/feed", "cn"),
    ("simon", "Simon Willison", "https://simonwillison.net/atom/everything/", "community"),
]
# 这些源内容不限于 AI，需要按关键词过滤
FILTER = {"meituan", "infoq", "simon", "hn"}
CN_KEYS = ("大模型", "模型", "智能", "智能体", "机器学习", "深度学习", "推理", "训练",
           "向量", "算力", "多模态", "具身", "预训练", "微调")
EN_KEYS = ("ai", "llm", "gpt", "agent", "rag", "nlp", "transformer", "diffusion",
           "claude", "gemini", "qwen", "deepseek", "neural", "prompt", "inference",
           "embedding", "machine learning", "chatbot", "copilot", "mcp")
JUNK = ("点击查看原文", "阅读全文", "read more", "continue reading")
PER_FEED = 6


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2)


def tag(block, name):
    m = re.search(rf"<{name}[^>]*>([\s\S]*?)</{name}>", block)
    if not m:
        return ""
    v = re.sub(r"<!\[CDATA\[([\s\S]*?)\]\]>", r"\1", m.group(1))
    return htmlmod.unescape(re.sub(r"<[^>]+>", " ", v)).strip()


def clean(s, n=110):
    s = htmlmod.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")


def to_date(s):
    s = (s or "").strip()
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    try:
        d = email.utils.parsedate_to_datetime(s)
        return d.date().isoformat()
    except Exception:
        return ""


def parse_feed(xml, key, name, kind, limit=PER_FEED):
    blocks = re.findall(r"<item[\s>][\s\S]*?</item>", xml)
    blocks = blocks or re.findall(r"<entry[\s>][\s\S]*?</entry>", xml)
    out = []
    for b in blocks:
        title = tag(b, "title")
        link = tag(b, "link")
        if not link:                                  # Atom: <link href="..."/>
            m = re.search(r'<link[^>]+href="([^"]+)"', b)
            link = m.group(1) if m else ""
        if not title or not link:
            continue
        summary = desc(tag(b, "description") or tag(b, "summary")
                       or tag(b, "content") or tag(b, "content:encoded"))
        row = {"title": title, "url": htmlmod.unescape(link), "source": key,
               "source_name": name, "kind": kind,
               "date": to_date(tag(b, "pubDate") or tag(b, "published")
                               or tag(b, "updated") or tag(b, "dc:date")),
               "summary": summary, "points": 0}
        if key in FILTER and not hit(title + " " + summary):
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out


def hit(text):
    """英文按单词边界匹配（避免 maintainer/email 里的 ai 子串误命中）"""
    t = (text or "").lower()
    if any(k in t for k in CN_KEYS):
        return True
    return bool(re.search(r"\b(" + "|".join(EN_KEYS) + r")\b", t))


def desc(text):
    s = clean(text)
    return "" if any(s.strip().lower().startswith(j) for j in JUNK) else s


def fetch_hn(limit=PER_FEED):
    data = json.loads(get(HN_URL)).get("hits") or []
    out = []
    for h in data:
        title = (h.get("title") or "").strip()
        if not title or not hit(title):
            continue
        out.append({"title": title,
                    "url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "source": "hn", "source_name": "Hacker News", "kind": "community",
                    "date": to_date(h.get("created_at", "")),
                    "summary": desc(h.get("story_text") or title)[:90],
                    "points": h.get("points") or 0})
        if len(out) >= limit:
            break
    return out


def main():
    os.makedirs(DAYS, exist_ok=True)
    today = datetime.date.today().isoformat()
    items, ok = [], 0
    for key, name, url, kind in FEEDS:
        try:
            rows = parse_feed(get(url), key, name, kind)
            if rows:
                ok += 1
                items += rows
        except Exception as exc:
            print(f"warn: {key} failed ({exc})")
    try:
        hn = fetch_hn()
        if hn:
            ok += 1
            items += hn
    except Exception as exc:
        print(f"warn: hn failed ({exc})")
    if not items:                                    # 全部失败：保留既有数据
        print("skip: 无新数据，保留既有 aiblog.json")
        return
    items.sort(key=lambda x: (x["date"], x["points"]), reverse=True)
    result = {"date": today, "items": items}
    if ok < len(FEEDS) + 1 and os.path.exists(OUT):   # 部分失败时补回旧条目
        prev = json.load(open(OUT, encoding="utf-8"))
        have = {(x["source"], x["title"]) for x in items}
        items += [x for x in prev.get("items", []) if (x["source"], x["title"]) not in have]
        items.sort(key=lambda x: (x["date"], x["points"]), reverse=True)
        result["items"] = items
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(DAYS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"aiblog: {len(items)} items from {ok} sources @ {today}")


if __name__ == "__main__":
    main()
