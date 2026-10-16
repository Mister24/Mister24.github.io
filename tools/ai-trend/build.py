#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯静态站点生成器（不依赖 Hexo）

读取 tools/ai-trend/data/trends.json，生成：
  - index.html            首页（AI 趋势日报）
  - archive/<date>.html   单期归档
  - posts/index.html      博客归档（来自 _legacy/hexo/source/_posts）
  - posts/<slug>.html     单篇文章
用法：python3 tools/ai-trend/build.py
"""

import html
import json
import os
import re
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tools", "ai-trend", "data")
LEGACY_POSTS = os.path.join(ROOT, "_legacy", "hexo", "source", "_posts")

TRACK_STYLE = {
    "AI Coding": ("#1d4ed8", "rgba(29,78,216,.09)"),
    "具身智能": ("#047857", "rgba(4,120,87,.09)"),
    "模型": ("#6d28d9", "rgba(109,40,217,.09)"),
    "Agent": ("#b45309", "rgba(180,83,9,.09)"),
}
DEFAULT_STYLE = ("#4b5563", "rgba(75,85,99,.09)")


def esc(s):
    return html.escape(s or "", quote=True)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def chip(track):
    fg, bg = TRACK_STYLE.get(track, DEFAULT_STYLE)
    return f'<span class="chip" style="color:{fg};background:{bg}">{esc(track)}</span>'


def tags_html(tags):
    return "".join(f'<span class="tag">{esc(t)}</span>' for t in tags or [])
def shell(title, body, active="trend"):
    nav = [("trend", "AI 日报", "/"), ("posts", "博客", "/posts/")]
    links = "".join(
        f'<a href="{u}" class="{"on" if k == active else ""}">{t}</a>'
        for k, t, u in nav)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)}</title>
<meta name="description" content="AI 趋势日报 · 聚焦 AI Coding 与具身智能，每日 09:00 更新"/>
<meta name="color-scheme" content="dark light"/>
<link rel="stylesheet" href="/assets/style.css"/>
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="/">Mister24<span>AI 趋势日报</span></a>
  <nav class="nav">{links}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">
  数据源：AITNT 全球 AI 新闻日报 · 多路交叉验证 ｜ 每日 09:00 自动渲染并推送 ｜ © 2026 Mister24
</footer>
<script src="/assets/app.js"></script>
</body>
</html>
"""


def cats_html(tr):
    tracks, out = [], []
    for it in tr["items"]:
        if it["track"] not in tracks:
            tracks.append(it["track"])
    out.append(f'<button class="cat on" data-f="all">全部<em>{len(tr["items"])}</em></button>')
    for t in tracks:
        n = sum(1 for x in tr["items"] if x["track"] == t)
        out.append(f'<button class="cat" data-f="{esc(t)}">{esc(t)}<em>{n}</em></button>')
    return '<div class="cats">' + "".join(out) + "</div>"
def lead_html(tr):
    it = tr["items"][0]
    return (
        f'<section class="lead" data-t="{esc(it["track"])}">'
        f'<div><span class="badge">头条</span>{chip(it["track"])}</div>'
        f'<h3>{esc(it["title"])}</h3>'
        f'<p>{esc(it.get("event", ""))}</p>'
        f'<div class="why"><b>为什么值得关注 · </b>{esc(it.get("why", ""))}</div>'
        f'<div class="tags">{tags_html(it.get("tags"))}</div>'
        f'<div class="meta"><span>{esc(it.get("source_name", "来源"))}</span>'
        f'<a href="{esc(it.get("source", "#"))}" target="_blank" rel="noopener">详情 →</a>'
        f'</div></section>')


def digest_html(tr):
    rows = "".join(
        f'<li data-t="{esc(it["track"])}"><i>{i:02d}</i>'
        f'<span>{esc(it["title"])}</span>'
        f'<small>{esc(it.get("source_name", ""))}</small></li>'
        for i, it in enumerate(tr["items"], 1))
    return f'<ul class="digest">{rows}</ul>'


def cards_html(tr):
    out = []
    for it in tr["items"][1:]:
        out.append(
            f'<article class="card" data-t="{esc(it["track"])}">{chip(it["track"])}'
            f'<h4>{esc(it["title"])}</h4>'
            f'<p>{esc(it.get("event", ""))}</p>'
            f'<div class="why"><b>值得关注 · </b>{esc(it.get("why", ""))}</div>'
            f'<div class="tags">{tags_html(it.get("tags"))}</div>'
            f'<div class="meta"><span>{esc(it.get("source_name", ""))}</span>'
            f'<a href="{esc(it.get("source", "#"))}" target="_blank" rel="noopener">详情 →</a>'
            f'</div></article>')
    return f'<div class="grid">{"".join(out)}</div>'
def nav_html(tr, dates):
    i = dates.index(tr["date"])
    prev_d = dates[i - 1] if i > 0 else None
    next_d = dates[i + 1] if i < len(dates) - 1 else None
    p = (f'<a class="nv" href="/archive/{prev_d}.html">←</a>'
         if prev_d else '<span class="nv off">←</span>')
    n = (f'<a class="nv" href="/archive/{next_d}.html">→</a>'
         if next_d else '<span class="nv off">→</span>')
    return f'<div class="datenav">{p}<b>{tr["date"]}</b>{n}</div>'


def archive_list_html(archive, cur):
    rows = "".join(
        f'<li><time>{a["date"]}</time>'
        f'<a href="/archive/{a["date"]}.html">{esc(a["headline"])}'
        f'{" 🔥" if a["date"] == cur else ""}</a></li>'
        for a in sorted(archive, key=lambda x: x["date"], reverse=True)[:20])
    return f'<ul class="arch">{rows}</ul>'


def insights_html(tr):
    return '<div class="ins">' + "".join(
        f'<div><h4>{esc(x["title"])}</h4><p>{esc(x["desc"])}</p></div>'
        for x in tr.get("insights", [])) + "</div>"


def term_html(tr, dates):
    """终端窗口 Hero"""
    tracks = len({it["track"] for it in tr["items"]})
    return f"""<div class="term">
  <div class="term-bar"><span class="dot r"></span><span class="dot y"></span>
    <span class="dot g"></span><b>~/ai-trend — zsh — 80×24</b></div>
  <div class="term-body">
    <div><span class="p">$</span>ai-trend --date {tr["date"]} --focus coding,embodied</div>
    <div class="d">&gt; scanning feeds ... ok</div>
    <div><span class="p">$</span>ai-trend --digest --top {len(tr["items"])}
      <span class="cursor"></span></div>
  </div>
</div>
<div class="kv">
  <div><b>{len(tr["items"])}</b>signals</div>
  <div><b>{tracks}</b>tracks</div>
  <div><b>{len(dates)}</b>editions</div>
  <div><b>09:00</b>daily</div>
</div>"""


def index_html(tr, archive, dates):
    date = tr["date"]
    body = f"""{term_html(tr, dates)}
<div class="top">
  <div><h1>A.I. 趋势日报</h1>
    <p>每天 09:00 更新 · 聚焦 AI Coding 与具身智能 · 每天 3–5 条值得关注的信号</p></div>
  {nav_html(tr, dates)}
</div>
{cats_html(tr)}
<div class="sec"><h2>头条</h2><span class="n">{date}</span></div>
{lead_html(tr)}
<div class="sec"><h2>本期要点速览</h2><span class="n">{len(tr["items"])} 条</span></div>
{digest_html(tr)}
<div class="sec"><h2>全部报道</h2><span class="n">{date}</span></div>
{cards_html(tr)}
<div class="empty">该赛道本期暂无内容。</div>
<div class="sec"><h2>趋势判断</h2><span class="n">持续跟踪</span></div>
{insights_html(tr)}
<div class="sec"><h2>往期话题</h2><span class="n">{len(archive)} 期</span></div>
{archive_list_html(archive, date)}"""
    return shell(f"AI 趋势日报 · {date}", body, "trend")
def archive_html(tr, dates):
    rows = []
    for i, it in enumerate(tr["items"], 1):
        rows.append(f'<article class="card"><h4>{i:02d} · {esc(it["title"])}</h4>'
                    f'<div class="meta">{chip(it["track"])}'
                    f'<span>{esc(it.get("source_name", ""))}</span></div>'
                    f'<p style="margin-top:10px">{esc(it.get("event", ""))}</p>'
                    f'<div class="why"><b>为什么值得关注 · </b>{esc(it.get("why", ""))}</div>'
                    f'<div class="tags">{tags_html(it.get("tags"))}</div></article>')
    ins = insights_html(tr)
    body = f"""<div class="top">
  <div><h1>{tr["date"]} · AI 趋势日报</h1><p>{esc(tr["headline"])}</p></div>
  {nav_html(tr, dates)}
</div>
<div class="sec"><h2>本期报道</h2><span class="n">{len(tr["items"])} 条</span></div>
<div class="grid">{"".join(rows)}</div>
<div class="sec"><h2>趋势判断</h2><span class="n">持续跟踪</span></div>
{ins}
<p><a class="back" href="/">← 回到 AI 趋势日报</a></p>"""
    return shell(f"AI 趋势日报 {tr['date']}", body, "trend")


def md_to_html(text):
    """极简 Markdown 渲染：标题 / 段落 / 列表 / 代码块 / 行内代码 / 链接 / 图片"""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            lv = len(m.group(1)) + 1
            out.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>")
        elif re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{b}</li>" for b in buf) + "</ul>")
            continue
        elif ln.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "\n".join(out)


def inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2"/>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s
def parse_post(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    meta, body = {}, raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            body = parts[2]
    raw = os.path.splitext(os.path.basename(path))[0].replace("/", "-").strip()
    title = meta.get("title") or raw
    return {"title": title, "date": meta.get("date", ""),
            "slug": raw, "url": urllib.parse.quote(raw),
            "body": md_to_html(body.strip())}


def build_posts():
    if not os.path.isdir(LEGACY_POSTS):
        return 0
    posts = [parse_post(os.path.join(LEGACY_POSTS, f))
             for f in sorted(os.listdir(LEGACY_POSTS)) if f.endswith(".md")]
    posts.sort(key=lambda p: p["date"], reverse=True)
    rows = "".join(f'<li><time>{p["date"][:10]}</time>'
                   f'<a href="/posts/{p["url"]}.html">{esc(p["title"])}</a></li>'
                   for p in posts)
    body = (f'<div class="top"><div><h1>博客归档</h1>'
            f'<p>{len(posts)} 篇历史文章</p></div></div>'
            f'<ul class="arch">{rows}</ul>'
            f'<p><a class="back" href="/">← 回到 AI 趋势日报</a></p>')
    save(os.path.join(ROOT, "posts", "index.html"), shell("博客归档", body, "posts"))
    for p in posts:
        pb = (f'<article class="post"><a class="back" href="/posts/">← 博客归档</a>'
              f'<h1>{esc(p["title"])}</h1>'
              f'<div class="date">{esc(p["date"][:10])}</div>{p["body"]}</article>')
        save(os.path.join(ROOT, "posts", f'{p["slug"]}.html'),
             shell(p["title"], pb, "posts"))
    return len(posts)


def main():
    tr = load(os.path.join(DATA, "trends.json"))
    arc_path = os.path.join(DATA, "archive.json")
    archive = load(arc_path) if os.path.exists(arc_path) else []
    if not any(a["date"] == tr["date"] for a in archive):
        archive.append({"date": tr["date"], "headline": tr["headline"]})
        save(arc_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    dates = sorted({a["date"] for a in archive})
    save(os.path.join(ROOT, "index.html"), index_html(tr, archive, dates))
    save(os.path.join(ROOT, "archive", f'{tr["date"]}.html'), archive_html(tr, dates))
    n = build_posts()
    print(f'built {tr["date"]}: {len(tr["items"])} items, archive={len(archive)}, posts={n}')


if __name__ == "__main__":
    main()

