# Mister24.github.io

![Static Site](https://img.shields.io/badge/site-Static%20HTML-blue.svg)
![GitHub Pages](https://img.shields.io/badge/host-GitHub%20Pages-222.svg)

> 个人主页与技术博客（GitHub Pages 静态站点）。

## 项目简介
这是一个部署在 GitHub Pages 上的**静态个人站点**，用于沉淀技术文章、AI 趋势观察与个人随笔。站点为手写静态 HTML，无需构建步骤，推送到 `master` 即生效。

## 技术栈
- 纯静态 HTML / CSS / JavaScript
- 托管：GitHub Pages
- 无后端、无构建工具

## 目录结构
```
├── index.html          # 站点首页
├── posts/              # 技术文章（如 SQL 高级语句、Java 值传递与引用传递…）
├── tools/              # 小工具 / 专题
│   └── ai-trend/       #   AI 趋势日报（按日期）
├── ai-trend/           # AI 趋势专题页
├── photos/             # 图片资源
├── github/             # GitHub 相关页面
├── hot/                # 热点专题
└── assets/             # 公共样式与脚本（app.js / style.css）
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
