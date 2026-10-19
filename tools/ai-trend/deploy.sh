#!/usr/bin/env bash
# 纯静态站点：构建 → 提交 → 推送到 GitHub Pages（仓库根目录即站点）
# 已移除 Hexo，不再需要 hexo generate / hexo deploy
set -euo pipefail
cd "$(dirname "$0")/../.."

BRANCH=$(git rev-parse --abbrev-ref HEAD)
DATE=$(date +%F)

echo "🐙 1/6 抓取 GitHub Trending..."
python3 tools/ai-trend/fetch_github.py || echo "⚠️  抓取失败，沿用上次数据"

echo "📝 2/6 抓取 AI 技术博客..."
python3 tools/ai-trend/fetch_aiblog.py || echo "⚠️  抓取失败，沿用上次数据"

echo "🔥 3/6 抓取博文热点（知乎 / 虎扑）..."
python3 tools/ai-trend/fetch_hot.py || echo "⚠️  抓取失败，沿用上次数据"

echo "🏗  4/6 构建静态站点..."
python3 tools/ai-trend/build.py

echo "📦 5/6 提交变更..."
git add -A
if git diff --cached --quiet; then
  echo "ℹ️  无内容变更，跳过提交"
  exit 0
fi
git commit -q -m "chore(site): ${DATE} AI 趋势日报 + GitHub 热点更新"

echo "🚀 6/6 推送到 GitHub Pages..."
export GIT_HTTP_LOW_SPEED_LIMIT=0
push() {
  git -c http.postBuffer=524288000 -c http.proxy="${GIT_PROXY:-}" push "$@"
}
if ! push origin "$BRANCH"; then
  echo "⚠️  普通推送失败，关闭代理后重试..."
  GIT_PROXY="" push origin "$BRANCH" || {
    echo "⚠️  仍失败，改为强制推送以替换站点"
    GIT_PROXY="" push -f origin "$BRANCH"
  }
fi
echo "✅ 已发布：https://mister24.github.io/"
