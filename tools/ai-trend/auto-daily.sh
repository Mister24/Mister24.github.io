#!/usr/bin/env bash
# 每日自动抓取 → 生成日报 → 构建 → 用本机 git 提交并推送到 GitHub（commit 归属本机 git user，即 Mister24）
# 由 WorkBuddy 定时任务（每天 08:00）或手动调用。
set -uo pipefail

# 强制 HTTP/1.1：本机 git 直连 github.com 在坏代理下偶发 HTTP/2 framing layer 报错
export GODEBUG=http2client=0
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

REPO_DIR="/Users/mr.24/antFin/codeTrunk/Mister24.github.io"
LOG_DIR="$HOME/Library/Logs"
LOG="$LOG_DIR/mister24-auto-daily.log"
PY=python3

# 代理策略：首选直连（清空 git 全局坏代理 + 强制 HTTP/1.1），env 代理仅作兜底
GOPT=(-c http.version=1.1 -c http.proxy= -c https.proxy=)
PROXY="${HTTPS_PROXY:-${HTTP_PROXY:-}}"
if [ -n "$PROXY" ]; then
  GOPT_PROXY=(-c http.version=1.1 -c "http.proxy=$PROXY" -c "https.proxy=$PROXY")
else
  GOPT_PROXY=()
fi
GIT=(git "${GOPT[@]}")

ts() { date '+%F %T'; }
log() { echo "[$(ts)] $*" >>"$LOG"; }

mkdir -p "$LOG_DIR"
log "=== 开始每日自动抓取与提交（Mister24 账号）==="

cd "$REPO_DIR" || { log "无法进入仓库目录 $REPO_DIR"; exit 1; }

# 1/5 同步远程最新，避免 push 冲突
log "1/5 拉取远程最新..."
if ! "${GIT[@]}" pull --ff-only origin master >>"$LOG" 2>&1; then
  log "pull --ff-only 失败，回退到 fetch + reset --hard origin/master"
  "${GIT[@]}" fetch origin master >>"$LOG" 2>&1
  "${GIT[@]}" reset --hard origin/master >>"$LOG" 2>&1
fi

# 2/5 抓取三类数据源
log "2/5 抓取 GitHub Trending..."
"$PY" tools/ai-trend/fetch_github.py >>"$LOG" 2>&1 && log "  ✓ github" || log "  ✗ github 失败(不影响其他)"
log "2/5 抓取 AI 博客..."
"$PY" tools/ai-trend/fetch_aiblog.py >>"$LOG" 2>&1 && log "  ✓ aiblog" || log "  ✗ aiblog 失败(不影响其他)"
log "2/5 抓取热点..."
"$PY" tools/ai-trend/fetch_hot.py >>"$LOG" 2>&1 && log "  ✓ hot" || log "  ✗ hot 失败(不影响其他)"

# 3/5 由当日 aiblog 自动生成 AI 趋势日报
log "3/5 生成 AI 趋势日报..."
"$PY" tools/ai-trend/gen_trends.py >>"$LOG" 2>&1 && log "  ✓ gen_trends" || log "  ✗ gen_trends 失败"

# 4/5 构建静态站点
log "4/5 构建静态站点..."
"$PY" tools/ai-trend/build.py >>"$LOG" 2>&1 && log "  ✓ build" || log "  ✗ build 失败"

# 5/5 提交并推送（commit 归属本机 git user = Mister24）
log "5/5 提交并推送..."
"${GIT[@]}" add -A
if "${GIT[@]}" diff --cached --quiet; then
  log "无内容变更，跳过提交（今天无新数据）"
else
  MSG="chore(site): $(date +%F) AI 趋势日报自动更新"
  "${GIT[@]}" commit -m "$MSG" >>"$LOG" 2>&1 && log "  ✓ 已提交: $MSG"
  ok=0
  for i in 1 2 3 4 5; do
    if "${GIT[@]}" push origin master >>"$LOG" 2>&1; then
      log "  ✓ 推送成功（$(date +%F) 已记入 Mister24 的 contribution）"
      ok=1
      break
    fi
    # 直连失败：若有 env 代理，再试一次代理方式兜底
    if [ ${#GOPT_PROXY[@]} -gt 0 ] && git "${GOPT_PROXY[@]}" push origin master >>"$LOG" 2>&1; then
      log "  ✓ 推送成功（经 env 代理兜底）"
      ok=1
      break
    fi
    log "  推送失败，第 $i 次重试：先 rebase 再 push"
    "${GIT[@]}" pull --rebase origin master >>"$LOG" 2>&1
    sleep $((i*2))
  done
  [ "$ok" -ne 1 ] && log "  ✗ 推送最终失败，请检查网络/代理"
fi

log "=== 完成 ==="
