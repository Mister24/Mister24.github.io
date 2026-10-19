# Mister24.github.io

> AI 趋势日报 · GitHub 热点 · 博文热点 · 技术笔记 —— 纯静态站点，每日 09:00 自动构建并发布

线上地址：https://mister24.github.io/

## 站点栏目

| 路径 | 内容 | 更新频率 |
|---|---|---|
| `/` | 首页落地页：栏目入口 + 最近日报 / 最近文章 | 每次构建 |
| `/ai-trend/` | AI 趋势日报主页（当期 3-5 条精选 + 趋势判断） | 每日 09:00 |
| `/ai-trend/<date>.html` | 单期归档，按日快照永久保留 | 每日追加 |
| `/github/` | GitHub Trending 热点：日榜 / 周榜 / 月榜 | 每日 09:00 |
| `/hot/` | 博文热点：知乎热榜 + 虎扑步行街 | 每日 09:00 |
| `/posts/` | 技术博客归档（Java 并发 / Spring / 数据结构与算法等） | 有新增时 |

当前数据：日报 4 期、文章 15 篇、GitHub 日/周/月榜 13/10/15、知乎 + 虎扑各 25 条（2026-10-18）。

## 目录结构

```
.
├── index.html            首页（生成）
├── ai-trend/             日报主页 + 单期归档
├── github/               GitHub 热点
├── hot/                  博文热点
├── posts/                文章页
├── assets/               style.css / app.js / photos
└── tools/ai-trend/       生成器与抓取脚本
    ├── build.py          静态站点生成器（Markdown 渲染 + 各栏目页面）
    ├── fetch_github.py   抓 GitHub Trending → data/github.json
    ├── fetch_hot.py      抓知乎热榜 / 虎扑步行街 → data/hot.json
    ├── deploy.sh         抓取 → 构建 → commit → push 一条龙
    └── data/             数据源与按日快照
        ├── trends.json   当日日报（每日覆盖）
        ├── archive.json  往期标题索引（自动追加）
        ├── github.json   GitHub 热点
        ├── hot.json      知乎 / 虎扑热点
        ├── days/         日报按日快照（保证往期永久可访问）
        ├── gh-days/      GitHub 热点快照
        └── hot-days/     博文热点快照
```

## 使用

```bash
# 只构建（不抓取、不提交）
python3 tools/ai-trend/build.py

# 完整发布：抓 GitHub + 抓博文热点 → 构建 → commit → push
bash tools/ai-trend/deploy.sh
```

仓库根目录即站点根目录，`master` 分支由 GitHub Pages 直接托管，无需额外的 CI。

抓取脚本对网络失败做了兜底：单个来源失败时沿用上一次的数据，不会中断构建；知乎接口偶发返回空，脚本内置 3 次重试。

## 数据来源

- AI 日报：AITNT 全球 AI 新闻日报 + 多路交叉验证，人工筛选 3-5 条，侧重 **AI Coding** 与 **具身智能**
- GitHub 热点：`github.com/trending`（daily / weekly / monthly）
- 博客热点：知乎热榜（60s 聚合接口；官方接口需登录态）、虎扑步行街版面
- 技术笔记：作者原创 Markdown（`_legacy/hexo/source/_posts`，构建时渲染）

## 说明

站点已从 Hexo 迁移为自研静态生成器：旧 Hexo 源码归档在 `_legacy/`（不发布），文章 Markdown 由 `build.py` 内置的 `render_md()` 渲染为静态页。
