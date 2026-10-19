# Mister24.github.io

![Static Site](https://img.shields.io/badge/site-Static%20HTML-blue.svg)
![GitHub Pages](https://img.shields.io/badge/host-GitHub%20Pages-222.svg)

> 个人主页与技术博客（GitHub Pages 静态站点）。

## 项目简介
这是一个部署在 GitHub Pages 上的**静态个人站点**，包含技术文章、AI 趋势日报、AI 技术博客聚合、GitHub 热点与博文热点等栏目。栏目页面由 `tools/ai-trend/build.py` 生成，每日 09:00 自动抓取数据并构建发布（也可手动运行），推送到 `master` 即生效。

## 技术栈
- 静态 HTML / CSS / JavaScript（Python 3 生成，无第三方依赖）
- 托管：GitHub Pages
- 无后端

## 目录结构
```
├── index.html          # 站点首页（生成）
├── posts/              # 技术文章（如 SQL 高级语句、Java 值传递与引用传递…）
├── ai-trend/           # AI 趋势日报（每日精选 + 按日期归档）
├── aiblog/             # AI 技术博客（官方工程博客 / 中文技术团队 / 社区分享）
├── github/             # GitHub 热点（日榜 / 周榜 / 月榜 Trending）
├── hot/                # 博文热点（知乎热榜 + 虎扑步行街）
├── photos/             # 图片资源
└── assets/             # 公共样式与脚本（app.js / style.css）
└── tools/ai-trend/     # 生成器与抓取脚本（build.py / fetch_*.py / deploy.sh）
```

## 本地预览
```bash
# 任意静态服务器均可，例如
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 说明
- 个人内容站点，文章与页面持续更新。
- 站点内容版权归作者所有，转载请注明出处。
- 仓库未声明开源协议（LICENSE）。
