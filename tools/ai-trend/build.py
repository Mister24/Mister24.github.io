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
import shutil
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

# 栏目路径：AI 日报 /ai-trend/ ，博客 /posts/
NAV = [("home", "首页", "/"), ("trend", "AI 日报", "/ai-trend/"),
       ("aiblog", "AI 技术博客", "/aiblog/"), ("gh", "GitHub 热点", "/github/"),
       ("hot", "博文热点", "/hot/")]
# 注：/posts/ 博客归档暂不对外展示，页面仍生成但无入口
TREND = "ai-trend"
AIBLOG = "aiblog"
GH = "github"
HOT = "hot"


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


SUBS = {"home": "首页", "trend": "AI 趋势日报", "aiblog": "AI 技术博客",
        "gh": "GitHub 热点", "hot": "博文热点", "posts": "技术博客"}


def shell(title, body, active="trend", noindex=False):
    links = "".join(
        f'<a href="{u}" class="{"on" if k == active else ""}">{t}</a>'
        for k, t, u in NAV)
    sub = SUBS.get(active, "AI 趋势日报")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)}</title>
<meta name="description" content="AI 趋势日报 · 聚焦 AI Coding 与具身智能，每日 09:00 更新"/>
<meta name="color-scheme" content="dark light"/>
<link rel="stylesheet" href="/assets/style.css"/>
{'<meta name="robots" content="noindex,nofollow"/>' if noindex else ''}
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="/">Mister24<span>{sub}</span></a>
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
    p = (f'<a class="nv" href="/{TREND}/{prev_d}.html">←</a>'
         if prev_d else '<span class="nv off">←</span>')
    n = (f'<a class="nv" href="/{TREND}/{next_d}.html">→</a>'
         if next_d else '<span class="nv off">→</span>')
    return f'<div class="datenav">{p}<b>{tr["date"]}</b>{n}</div>'


def archive_list_html(archive, cur):
    rows = "".join(
        f'<li><time>{a["date"]}</time>'
        f'<a href="/{TREND}/{a["date"]}.html">{esc(a["headline"])}'
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
<p><a class="back" href="/{TREND}/">← 回到 AI 趋势日报</a> ｜ <a class="back" href="/">首页</a></p>"""
    return shell(f"AI 趋势日报 {tr['date']}", body, "trend")


# ---------- Markdown 渲染（支持：标题锚点 / 围栏代码块 / 有序无序嵌套列表 /
#           引用 / 表格 / 分割线 / 图片 figure / 行内代码与强调） ----------
FENCE_RE = re.compile(r"^```\s*([\w+#.-]*)\s*$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
HR_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
IMG_ONLY_RE = re.compile(r"\s*<img[^>]+>\s*")
IMG_LINE_RE = re.compile(r"^!\[[^\]]*\]\([^)]*\)\s*$")


def slug(text):
    s = re.sub(r"[^\w\u4e00-\u9fa5]+", "-", text.strip().lower()).strip("-")
    return s or "sec"


def fix_url(u):
    """文章页在 /posts/ 下，相对资源统一提到站点根"""
    u = u.strip()
    if re.match(r"^(https?:|//|/|#|mailto:)", u):
        return u
    return "/" + u.lstrip("./")


def link_html(m):
    href = fix_url(m.group(2))
    ext = ' target="_blank" rel="noopener"' if m.group(2).startswith("http") else ""
    return f'<a href="{href}"{ext}>{m.group(1)}</a>'


def inline(s):
    """行内渲染：先还原 HTML 实体（&nbsp; 等），再转义，避免实体被当字面量显示"""
    s = html.unescape(s)
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
               lambda m: f'<img src="{fix_url(m.group(2))}" alt="{m.group(1)}" loading="lazy"/>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", link_html, s)
    # 正文中裸写的 <br/> 还原为换行（作者习惯用它分段）
    s = re.sub(r"&lt;br\s*/?\s*&gt;", "<br/>", s, flags=re.I)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*([^*\n]+)\*(?![\*\w])", r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))])}</code>", s)
    return s


def parse_list(lines, i, base):
    items, n = [], len(lines)
    while i < n:
        m = LIST_RE.match(lines[i])
        if not m:
            break
        ind = len(m.group(1).replace("\t", "    "))
        if ind < base:
            break
        if ind > base:
            sub, i = parse_list(lines, i, ind)
            if items:
                items[-1]["sub"] = sub
            continue
        items.append({"text": m.group(3),
                      "ordered": m.group(2) not in "-*+", "sub": None})
        i += 1
        # 列表项下的缩进续行并入该项
        while i < n and lines[i].strip() and not LIST_RE.match(lines[i]) \
                and len(lines[i]) - len(lines[i].lstrip()) > base:
            items[-1]["text"] += " " + lines[i].strip()
            i += 1
    return items, i


def render_items(items):
    if not items:
        return ""
    tag = "ol" if items[0]["ordered"] else "ul"
    lis = []
    for it in items:
        txt = inline(it["text"])
        if it["sub"]:
            txt += render_items(it["sub"])
        lis.append(f"<li>{txt}</li>")
    return f'<{tag}>{"".join(lis)}</{tag}>'


def render_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head = cells[0]
    body = [r for r in cells[1:] if not set("".join(r)) <= set("-: ")]
    th = "".join(f"<th>{inline(c)}</th>" for c in head)
    tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                 for r in body)
    return (f'<div class="tbl"><table><thead><tr>{th}</tr></thead>'
            f"<tbody>{tb}</tbody></table></div>")


def is_block_start(ln):
    return bool(FENCE_RE.match(ln.strip()) or HEAD_RE.match(ln) or HR_RE.match(ln)
                or ln.lstrip().startswith(">") or LIST_RE.match(ln)
                or IMG_LINE_RE.match(ln) or ln.lstrip().startswith("|"))


def render_md(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out, toc, i, n = [], [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = FENCE_RE.match(ln.strip())
        if m:
            lang = (m.group(1) or "text").lower()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(buf).rstrip())
            out.append(
                f'<figure class="code"><figcaption><span class="lang">{esc(lang)}</span>'
                f'<button class="copy" type="button">copy</button></figcaption>'
                f'<pre><code class="language-{esc(lang)}">{code}</code></pre></figure>')
            continue
        m = HEAD_RE.match(ln)
        if m:
            lv = max(2, len(m.group(1)))
            txt = inline(m.group(2))
            sid = slug(m.group(2))
            out.append(f'<h{lv} id="{sid}"><a class="anchor" href="#{sid}">#</a>{txt}</h{lv}>')
            if lv <= 3:
                toc.append((lv, sid, re.sub(r"<[^>]+>", "", txt)))
            i += 1
            continue
        if HR_RE.match(ln):
            out.append("<hr/>")
            i += 1
            continue
        if ln.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + inline("\n".join(buf)).replace("\n", "<br/>")
                       + "</blockquote>")
            continue
        if LIST_RE.match(ln):
            # 以首行缩进为基准，兼容整体缩进的嵌套列表
            base = len(LIST_RE.match(ln).group(1).replace("\t", "    "))
            items, i = parse_list(lines, i, base)
            out.append(render_items(items))
            continue
        if IMG_LINE_RE.match(ln):
            out.append(f'<figure class="img">{inline(ln.strip())}</figure>')
            i += 1
            continue
        if ln.lstrip().startswith("|"):
            buf = []
            while i < n and lines[i].lstrip().startswith("|"):
                buf.append(lines[i].strip())
                i += 1
            out.append(render_table(buf))
            continue
        buf = []
        while i < n and lines[i].strip() and not is_block_start(lines[i]):
            buf.append(lines[i])
            i += 1
        para = inline("\n".join(buf))
        if IMG_ONLY_RE.fullmatch(para):
            out.append(f'<figure class="img">{para.strip()}</figure>')
        else:
            out.append(f"<p>{para}</p>")
    return "\n".join(out), toc
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
    name = os.path.splitext(os.path.basename(path))[0].replace("/", "-").strip()
    rendered, toc = render_md(body.strip())
    plain = re.sub(r"[#>`*!\[\]()|-]", " ", body)
    plain = re.sub(r"\s+", " ", html.unescape(plain)).strip()
    chars = len(re.findall(r"[\u4e00-\u9fa5]", body)) + len(re.findall(r"[A-Za-z]+", body))
    return {
        "title": meta.get("title") or name,
        "date": meta.get("date", "")[:10],
        "cat": meta.get("categories", ""),
        "tags": [t for t in re.split(r"[,，\s]+", meta.get("tags", "")) if t],
        "slug": name,
        "url": urllib.parse.quote(name),
        "body": rendered,
        "toc": toc,
        "excerpt": plain[:96] + ("…" if len(plain) > 96 else ""),
        "minutes": max(1, round(chars / 400)),
        "words": chars,
    }


def toc_html(toc):
    if len(toc) < 2:
        return ""
    rows = "".join(f'<a class="t{lv}" href="#{sid}">{esc(txt)}</a>'
                   for lv, sid, txt in toc)
    return f'<aside class="toc"><div class="toc-t">目录</div>{rows}</aside>'


def postnav_html(prev_p, next_p):
    p = (f'<a class="pn" href="/posts/{prev_p["url"]}.html">'
         f'<span>上一篇</span>{esc(prev_p["title"])}</a>'
         if prev_p else '<span class="pn off"><span>上一篇</span>没有了</span>')
    n = (f'<a class="pn r" href="/posts/{next_p["url"]}.html">'
         f'<span>下一篇</span>{esc(next_p["title"])}</a>'
         if next_p else '<span class="pn r off"><span>下一篇</span>没有了</span>')
    return f'<nav class="postnav">{p}{n}</nav>'


def build_posts():
    if not os.path.isdir(LEGACY_POSTS):
        return []
    posts = [parse_post(os.path.join(LEGACY_POSTS, f))
             for f in sorted(os.listdir(LEGACY_POSTS)) if f.endswith(".md")]
    posts.sort(key=lambda p: p["date"], reverse=True)

    # 归档页：按年分组的卡片流
    groups, years = {}, []
    for p in posts:
        y = p["date"][:4] or "未分类"
        if y not in groups:
            groups[y] = []
            years.append(y)
        groups[y].append(p)
    blocks = []
    for y in years:
        cards = "".join(
            f'<a class="pCard" href="/posts/{p["url"]}.html">'
            f'<div class="pCard-h"><time>{p["date"]}</time>'
            f'<span class="pCard-c">{esc(p["cat"])}</span></div>'
            f'<h3>{esc(p["title"])}</h3>'
            f'<p>{esc(p["excerpt"])}</p>'
            f'<div class="pCard-f">{p["minutes"]} min · {p["words"]} 字'
            f'{"".join(f"<em>#{esc(t)}</em>" for t in p["tags"])}</div></a>'
            for p in groups[y])
        blocks.append(f'<div class="sec"><h2>{y}</h2>'
                      f'<span class="n">{len(groups[y])} 篇</span></div>'
                      f'<div class="pGrid">{cards}</div>')
    body = (f'<div class="top"><div><h1>博客归档</h1>'
            f'<p>{len(posts)} 篇技术笔记 · Java 并发 / Spring / 数据结构与算法</p></div></div>'
            + "".join(blocks)
            + f'<p style="margin-top:26px"><a class="back" href="/{TREND}/">← 回到 AI 趋势日报</a></p>')
    save(os.path.join(ROOT, "posts", "index.html"),
         shell("博客归档", body, "posts", True))

    # 文章页
    for idx, p in enumerate(posts):
        prev_p = posts[idx - 1] if idx > 0 else None
        next_p = posts[idx + 1] if idx < len(posts) - 1 else None
        head = (f'<a class="back" href="/posts/">← 博客归档</a>'
                f'<header class="phead"><h1>{esc(p["title"])}</h1>'
                f'<div class="pmeta"><time>{esc(p["date"])}</time>'
                f'<span class="cat">{esc(p["cat"])}</span>'
                f'<span>{p["minutes"]} min read</span>'
                f'<span>{p["words"]} 字</span></div>'
                f'<div class="tags">{tags_html(p["tags"])}</div></header>')
        pb = (f'<div class="doc"><article class="prose">{head}{p["body"]}'
              f'{postnav_html(prev_p, next_p)}</article>{toc_html(p["toc"])}</div>')
        save(os.path.join(ROOT, "posts", f'{p["slug"]}.html'),
             shell(p["title"], pb, "posts", True))
    return posts


def fmt_num(n):
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


GH_LABEL = {"daily": "今日", "weekly": "本周", "monthly": "本月"}


def gh_rows(items, period):
    """榜单行：排名 / 仓库 / 描述 / 语言·star·fork·增速"""
    label = GH_LABEL.get(period, "今日")
    out = []
    for i, r in enumerate(items, 1):
        lang = f'<span class="lg">{esc(r["lang"])}</span>' if r.get("lang") else ""
        out.append(
            f'<a class="gh" href="{esc(r["url"])}" target="_blank" rel="noopener"'
            f' data-t="{period}"><i>{i:02d}</i>'
            f'<div class="gh-b"><div class="gh-n">{esc(r["name"])}</div>'
            f'<p>{esc(r.get("desc", ""))}</p>'
            f'<div class="gh-m">{lang}<span>★ {fmt_num(r["stars"])}</span>'
            f'<span>⑂ {fmt_num(r["forks"])}</span>'
            f'<span class="up">↑ {fmt_num(r["delta"])} {label}</span>'
            f'</div></div></a>')
    return "".join(out)


def gh_side(gh):
    langs = {}
    for r in gh.get("daily", []):
        if r.get("lang"):
            langs[r["lang"]] = langs.get(r["lang"], 0) + 1
    top = sorted(langs.items(), key=lambda x: -x[1])[:6]
    mx = max([c for _, c in top], default=1)
    bars = "".join(
        f'<li><span>{esc(k)}</span><i style="width:{int(c / mx * 100)}%"></i>'
        f'<em>{c}</em></li>' for k, c in top)
    return (f'<aside class="side"><div class="side-t">今日概览</div>'
            f'<div class="side-kv"><b>{len(gh.get("daily", []))}</b>日榜项目</div>'
            f'<div class="side-kv"><b>{len(gh.get("weekly", []))}</b>周榜项目</div>'
            f'<div class="side-kv"><b>{len(gh.get("monthly", []))}</b>月榜项目</div>'
            f'<div class="side-t">日榜语言分布</div><ul class="bars">{bars}</ul>'
            f'<div class="side-t">数据来源</div>'
            f'<p class="side-p">github.com/trending<br/>每日 09:00 自动抓取 · 更新于 '
            f'{esc(gh.get("date", ""))}</p></aside>')


def github_html(gh):
    daily, weekly = gh.get("daily", []), gh.get("weekly", [])
    monthly = gh.get("monthly", [])
    tabs = (f'<div class="cats">'
            f'<button class="cat on" data-f="daily">日榜<em>{len(daily)}</em></button>'
            f'<button class="cat" data-f="weekly">周榜<em>{len(weekly)}</em></button>'
            f'<button class="cat" data-f="monthly">月榜<em>{len(monthly)}</em></button>'
            f'</div>')
    body = (f'<div class="top"><div><h1>GitHub 热点</h1>'
            f'<p>每日 / 每周 / 每月 Trending 仓库 · 更新于 {esc(gh.get("date", ""))} 09:00</p></div>'
            f'<div class="kv"><div><b>{len(daily)}</b>daily</div>'
            f'<div><b>{len(weekly)}</b>weekly</div>'
            f'<div><b>{len(monthly)}</b>monthly</div></div></div>'
            f'{tabs}'
            f'<div class="ghWrap"><div class="ghMain">'
            f'<div class="ghList">{gh_rows(daily, "daily")}{gh_rows(weekly, "weekly")}'
            f'{gh_rows(monthly, "monthly")}</div>'
            f'<div class="empty">该榜单暂无内容。</div>'
            f'</div>{gh_side(gh)}</div>')
    return shell("GitHub 热点 · Trending 仓库榜", body, "gh")


def hot_rows(items, plat):
    """博文热点行：排名 / 标题 / 平台 · 热度 · 互动量"""
    label = {"zhihu": "知乎", "hupu": "虎扑", "bilibili": "B站"}.get(plat, plat)
    out = []
    for i, r in enumerate(items, 1):
        if plat == "zhihu":
            meta = (f'<span class="lg">{label}</span>'
                    f'<span>{esc(r.get("hot", ""))}</span>'
                    f'<span>{r.get("answers", 0)} 回答</span>')
        elif plat == "bilibili":
            meta = (f'<span class="lg">{label}</span>'
                    f'<span>{fmt_num(r.get("views", 0))} 播放</span>'
                    f'<span>{fmt_num(r.get("danmaku", 0))} 弹幕</span>'
                    f'<span>{esc(r.get("author", ""))}</span>')
        else:
            meta = (f'<span class="lg">{label}</span>'
                    f'<span>{r.get("replies", 0)} 回复</span>'
                    f'<span>{fmt_num(r.get("views", 0))} 浏览</span>'
                    f'<span>{esc(r.get("author", ""))}</span>'
                    f'<span>{esc(r.get("time", ""))}</span>')
        out.append(
            f'<a class="gh" href="{esc(r.get("url", "#"))}" target="_blank"'
            f' rel="noopener" data-t="{plat}"><i>{i:02d}</i>'
            f'<div class="gh-b"><div class="gh-n">{esc(r.get("title", ""))}</div>'
            f'<div class="gh-m">{meta}</div></div></a>')
    return "".join(out)


def hot_side(hot):
    zh, hp, bi = (hot.get("zhihu", []), hot.get("hupu", []), hot.get("bilibili", []))
    hot5 = ""
    if hp:
        top = sorted(hp, key=lambda x: -x.get("replies", 0))[:5]
        mx = max([x.get("replies", 0) for x in top] + [1])
        li = "".join(
            f'<li><a href="{esc(t.get("url", "#"))}" target="_blank" rel="noopener"'
            f' title="{esc(t["title"])}">'
            f'<span>{esc(t["title"][:12])}</span>'
            f'<i style="width:{int(t.get("replies", 0) / mx * 100)}%"></i>'
            f'<em>{t.get("replies", 0)}</em></a></li>' for t in top)
        hot5 = f'<div class="side-t">虎扑热议 TOP5</div><ul class="bars">{li}</ul>'
    bili5 = ""
    if bi:
        top = sorted(bi, key=lambda x: -x.get("views", 0))[:5]
        mx = max([x.get("views", 0) for x in top] + [1])
        li = "".join(
            f'<li><a href="{esc(t.get("url", "#"))}" target="_blank" rel="noopener"'
            f' title="{esc(t["title"])}">'
            f'<span>{esc(t["title"][:12])}</span>'
            f'<i style="width:{int(t.get("views", 0) / mx * 100)}%"></i>'
            f'<em>{fmt_num(t.get("views", 0))}</em></a></li>' for t in top)
        bili5 = f'<div class="side-t">B站热门 TOP5</div><ul class="bars">{li}</ul>'
    return (f'<aside class="side"><div class="side-t">今日概览</div>'
            f'<div class="side-kv"><b>{len(zh)}</b>知乎热榜</div>'
            f'<div class="side-kv"><b>{len(hp)}</b>虎扑步行街</div>'
            f'<div class="side-kv"><b>{len(bi)}</b>B站热门</div>'
            f'{hot5}{bili5}'
            f'<div class="side-t">数据来源</div>'
            f'<p class="side-p">zhihu.com/hot · bbs.hupu.com/bxj<br/>'
            f'bilibili.com/v/popular · 每日 09:00 抓取<br/>'
            f'更新于 {esc(hot.get("date", ""))}</p></aside>')


def hot_html(hot):
    zh, hp, bi = (hot.get("zhihu", []), hot.get("hupu", []), hot.get("bilibili", []))
    tabs = (f'<div class="cats">'
            f'<button class="cat on" data-f="zhihu">知乎<em>{len(zh)}</em></button>'
            f'<button class="cat" data-f="hupu">虎扑<em>{len(hp)}</em></button>'
            f'<button class="cat" data-f="bilibili">B站<em>{len(bi)}</em></button>'
            f'</div>')
    body = (f'<div class="top"><div><h1>博文热点</h1>'
            f'<p>知乎热榜 + 虎扑步行街 + B站热门 · 更新于 {esc(hot.get("date", ""))} 09:00</p>'
            f'</div><div class="kv"><div><b>{len(zh)}</b>zhihu</div>'
            f'<div><b>{len(hp)}</b>hupu</div>'
            f'<div><b>{len(bi)}</b>bili</div>'
            f'<div><b>09:00</b>daily</div></div></div>'
            f'{tabs}'
            f'<div class="ghWrap"><div class="ghMain">'
            f'<div class="ghList">{hot_rows(zh, "zhihu")}{hot_rows(hp, "hupu")}</div>'
            f'<div class="empty">该平台暂无内容。</div>'
            f'</div>{hot_side(hot)}</div>')
    return shell("博文热点 · 知乎热榜与虎扑步行街", body, "hot")


def aiblog_rows(items):
    """博客条目：编号 / 标题 / 来源·日期 / 摘要"""
    out = []
    for i, r in enumerate(items, 1):
        meta = (f'<span class="lg">{esc(r.get("source_name", ""))}</span>'
                f'<span>{esc(r.get("date", ""))}</span>')
        if r.get("points"):
            meta += f'<span>{r["points"]} 分</span>'
        s = esc(r.get("summary", ""))
        sm = f'<div class="gh-s">{s}</div>' if s else ""
        out.append(
            f'<a class="gh" href="{esc(r.get("url", "#"))}" target="_blank"'
            f' rel="noopener" data-t="{esc(r.get("kind", "official"))}"><i>{i:02d}</i>'
            f'<div class="gh-b"><div class="gh-n">{esc(r.get("title", ""))}</div>'
            f'<div class="gh-m">{meta}</div>{sm}</div></a>')
    return "".join(out)


def aiblog_side(items, date):
    cnt = {}
    for r in items:
        cnt[r.get("source_name", "")] = cnt.get(r.get("source_name", ""), 0) + 1
    mx = max(cnt.values() or [1])
    bars = "".join(
        f'<li><span>{esc(k)}</span>'
        f'<i style="width:{int(v / mx * 100)}%"></i><em>{v}</em></li>'
        for k, v in sorted(cnt.items(), key=lambda x: -x[1]))
    return (f'<aside class="side"><div class="side-t">今日概览</div>'
            f'<div class="side-kv"><b>{len(items)}</b>篇文章</div>'
            f'<div class="side-kv"><b>{len(cnt)}</b>个来源</div>'
            f'<div class="side-t">来源分布</div><ul class="bars">{bars}</ul>'
            f'<div class="side-t">数据来源</div>'
            f'<p class="side-p">OpenAI / DeepMind / PyTorch / AWS / Google<br/>'
            f'美团技术团队 · InfoQ · Hacker News<br/>'
            f'量子位 · 掘金 · 自定义公众号 RSS<br/>'
            f'每日 09:00 抓取 · 更新于 {esc(date)}</p></aside>')


def aiblog_html(data):
    items = data.get("items", [])
    kinds = [("official", "官方工程博客"), ("cn", "中文技术团队"),
             ("wechat", "公众号精选"), ("community", "社区分享")]
    tabs = '<div class="cats"><button class="cat on" data-f="official">官方工程博客'
    tabs += f'<em>{sum(1 for x in items if x.get("kind") == "official")}</em></button>'
    for key, name in kinds[1:]:
        tabs += (f'<button class="cat" data-f="{key}">{name}'
                 f'<em>{sum(1 for x in items if x.get("kind") == key)}</em></button>')
    tabs += "</div>"
    body = (f'<div class="top"><div><h1>AI 技术博客</h1>'
            f'<p>官方工程博客与社区落地实践 · 更新于 {esc(data.get("date", ""))} 09:00</p>'
            f'</div><div class="kv"><div><b>{len(items)}</b>posts</div>'
            f'<div><b>09:00</b>daily</div></div></div>'
            f'{tabs}'
            f'<div class="ghWrap"><div class="ghMain">'
            f'<div class="ghList">{aiblog_rows(items)}</div>'
            f'<div class="empty">该分类暂无内容。</div>'
            f'</div>{aiblog_side(items, data.get("date", ""))}</div>')
    return shell("AI 技术博客 · 落地实践与技术分享", body, "aiblog")


def home_html(tr, archive, dates, posts, gh=None, hot_data=None, blog=None):
    """站点首页：各栏目入口 + 最近更新"""
    n_hot = (len(hot_data.get("zhihu", [])) + len(hot_data.get("hupu", []))
             + len(hot_data.get("bilibili", []))
             if hot_data else 0)
    n_blog = len(blog.get("items", [])) if blog else 0
    cards = (
        '<div class="homeGrid">'
        f'<a class="homeCard" href="/{TREND}/"><span class="kc">01</span>'
        '<h2>AI 趋势日报</h2>'
        f'<p>每天 09:00 自动更新 · 聚焦 AI Coding 与具身智能</p>'
        f'<div class="kc-f">最新 {tr["date"]} · {len(dates)} 期归档 →</div></a>'
        f'<a class="homeCard" href="/{AIBLOG}/"><span class="kc">02</span>'
        '<h2>AI 技术博客</h2>'
        '<p>官方工程博客与社区落地实践</p>'
        f'<div class="kc-f">{n_blog} 篇技术分享 →</div></a>'
        '<a class="homeCard" href="/github/"><span class="kc">03</span>'
        '<h2>GitHub 热点</h2>'
        '<p>每日 / 每周 Trending 仓库与增速排名</p>'
        f'<div class="kc-f">{len(gh.get("daily", [])) if gh else 0} 个日榜项目 →</div></a>'
        '<a class="homeCard" href="/hot/"><span class="kc">04</span>'
        '<h2>博文热点</h2>'
        '<p>知乎 / 虎扑 / B站 的每日热帖</p>'
        f'<div class="kc-f">{n_hot} 条热点 →</div></a>'
        '</div>')
    eds = sorted(archive, key=lambda x: x["date"], reverse=True)[:5]
    latest_trend = "".join(
        f'<li><time>{a["date"]}</time>'
        f'<a href="/{TREND}/{a["date"]}.html">{esc(a["headline"])}</a></li>' for a in eds)
    hot = ""
    if gh and gh.get("daily"):
        hot_li = "".join(
            f'<li><span class="gh-h">{esc(r["name"])}</span>'
            f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">'
            f'{esc(r.get("desc", "")[:34])}</a>'
            f'<small>★{fmt_num(r["stars"])} ↑{fmt_num(r["delta"])}</small></li>'
            for r in gh["daily"][:5])
        hot = (f'<div class="sec"><h2>GitHub 今日热点</h2>'
               f'<span class="n">更新于 {esc(gh.get("date", ""))}</span></div>'
               f'<ul class="digest">{hot_li}</ul>')
    body = (f'<div class="top"><div><h1>Mister24</h1>'
            f'<p>写点代码，看点趋势 ｜ AI 日报 + AI 技术博客 + GitHub 热点 + 博文热点</p></div></div>'
            f'{cards}'
            f'{hot}'
            f'<div class="sec"><h2>最近日报</h2><span class="n">最近 {len(eds)} 期</span></div>'
            f'<ul class="arch">{latest_trend}</ul>')
    return shell("Mister24 · AI 趋势日报与技术笔记", body, "home")


def main():
    tr = load(os.path.join(DATA, "trends.json"))
    arc_path = os.path.join(DATA, "archive.json")
    archive = load(arc_path) if os.path.exists(arc_path) else []
    if not any(a["date"] == tr["date"] for a in archive):
        archive.append({"date": tr["date"], "headline": tr["headline"]})
        save(arc_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    dates = sorted({a["date"] for a in archive})
    # 旧路径 /archive/ 已废弃，日报整体迁到 /ai-trend/
    old_arch = os.path.join(ROOT, "archive")
    if os.path.isdir(old_arch):
        shutil.rmtree(old_arch)
    # 按日快照：每天存一份，保证往期单期页永久可访问
    days_dir = os.path.join(DATA, "days")
    save(os.path.join(days_dir, f'{tr["date"]}.json'),
         json.dumps(tr, ensure_ascii=False, indent=2) + "\n")
    save(os.path.join(ROOT, TREND, "index.html"), index_html(tr, archive, dates))
    for name in sorted(f for f in os.listdir(days_dir) if f.endswith(".json")):
        one = load(os.path.join(days_dir, name))
        save(os.path.join(ROOT, TREND, f'{one["date"]}.html'),
             archive_html(one, dates))
    posts = build_posts()
    gh = load(os.path.join(DATA, "github.json")) if os.path.exists(
        os.path.join(DATA, "github.json")) else None
    hot = load(os.path.join(DATA, "hot.json")) if os.path.exists(
        os.path.join(DATA, "hot.json")) else None
    blog = load(os.path.join(DATA, "aiblog.json")) if os.path.exists(
        os.path.join(DATA, "aiblog.json")) else None
    if gh:
        save(os.path.join(ROOT, GH, "index.html"), github_html(gh))
    if hot:
        save(os.path.join(ROOT, HOT, "index.html"), hot_html(hot))
    if blog:
        save(os.path.join(ROOT, AIBLOG, "index.html"), aiblog_html(blog))
    save(os.path.join(ROOT, "index.html"),
         home_html(tr, archive, dates, posts, gh, hot, blog))
    print(f'built {tr["date"]}: {len(tr["items"])} items, '
          f'archive={len(archive)}, posts={len(posts)}')


if __name__ == "__main__":
    main()

