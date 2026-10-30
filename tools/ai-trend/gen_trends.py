#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动生成 AI 趋势日报 tools/ai-trend/data/trends.json

替代原先的人工编排：从「每日自动抓取的 AI 博客/新闻聚合」aiblog.json 中，
挑选当日头条、按关键词归类赛道，产出 trends.json 与 days/<date>.json，
供 build.py 生成 /ai-trend/ 首页与往期归档页。

仅当 aiblog.json 已更新到「今天」时才重写 trends.json；否则保留既有内容，
避免抓取出错时把日报覆盖成陈旧数据。

用法：python3 tools/ai-trend/gen_trends.py
"""

import datetime
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "tools", "ai-trend", "data")
AIBLOG = os.path.join(DATA, "aiblog.json")
TRENDS = os.path.join(DATA, "trends.json")
DAYS = os.path.join(DATA, "days")
TOPN = 5

# 赛道归类：顺序即优先级，命中其一即归类（越具体越靠前）
TRACK_RULES = [
    ("具身智能", ("具身", "机器人", "embodied", "robot", "机器人大脑", "具身智能")),
    ("AI Coding", ("coding", "代码", "编程", "copilot", "cursor", "长任务编程",
                   "开发工具", "ide", "代码助手", "软件工程")),
    ("Agent", ("智能体", "agent", "autonomous", "mcp", "工作流", "多智能体")),
    ("模型", ("模型", "model", "gpt", "gemini", "claude", "deepseek", "llm",
              "大模型", "推理", "训练", "多模态", "开源", "预训练", "微调")),
]
DEFAULT_TRACK = "模型"

# 用于生成 tags 的关键词池（命中即作为标签）
TAG_KEYS = ("大模型", "智能体", "Agent", "推理", "多模态", "具身", "机器人",
            "开源", "训练", "RAG", "检索", "代码", "编程", "Copilot", "MCP",
            "GPT", "Gemini", "Claude", "DeepSeek", "Qwen", "PyTorch", "扩散",
            "对齐", "算力", "向量", "Embedding")


def classify(title, summary):
    t = (title + " " + summary).lower()
    for track, keys in TRACK_RULES:
        if any(k.lower() in t for k in keys):
            return track
    return DEFAULT_TRACK


def tags_from(title, summary):
    t = title + " " + summary
    out = []
    for k in TAG_KEYS:
        if k in t and k not in out:
            out.append(k)
    return out[:4]


def main():
    today = datetime.date.today().isoformat()
    if not os.path.exists(AIBLOG):
        print("skip: aiblog.json 不存在，保留既有 trends.json")
        return
    with open(AIBLOG, encoding="utf-8") as f:
        data = json.load(f)
    # aiblog 未更新到今天 -> 抓取可能失败，保留旧日报，不下覆盖
    if data.get("date") != today:
        print(f"skip: aiblog 停留在 {data.get('date')}（非今日），保留既有 trends.json")
        return

    items = data.get("items", [])
    if not items:
        print("skip: aiblog 无条目，保留既有 trends.json")
        return

    items.sort(key=lambda x: (x.get("date", ""), x.get("points", 0)), reverse=True)
    top = items[:TOPN]

    out_items = []
    for x in top:
        title = x.get("title", "") or ""
        summary = (x.get("summary", "") or "").strip()
        track = classify(title, summary)
        event = summary if summary else title
        why = (f"该动态来自今日 AI 资讯聚合（{x.get('source_name', '')}），"
               f"是「{track}」方向的代表性进展，建议持续跟踪其后续落地与生态反应。")
        out_items.append({
            "track": track,
            "title": title,
            "event": event,
            "why": why,
            "source": x.get("url", ""),
            "source_name": x.get("source_name", ""),
            "tags": tags_from(title, summary),
        })

    headline = " ｜ ".join(x["title"][:20] for x in out_items)
    result = {"date": today, "headline": headline, "items": out_items, "insights": []}

    with open(TRENDS, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.makedirs(DAYS, exist_ok=True)
    with open(os.path.join(DAYS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"trends: {len(out_items)} items @ {today}  (headline: {headline[:60]}…)")


if __name__ == "__main__":
    main()
