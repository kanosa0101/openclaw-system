#!/bin/bash
set -e
source /root/.openclaw/workspace-coding-agent/tools/github/.env
REPO_DIR="/root/.openclaw/github-sync"
COMMIT_MSG="${1:-auto: sync $(date -u +%Y-%m-%d\ %H:%M\ UTC)}"

sync_files() {
    mkdir -p "$REPO_DIR/config" "$REPO_DIR/agents/coding-agent/reports" "$REPO_DIR/agents/coding-agent/memory" "$REPO_DIR/agents/research-agent/reports/daily"
    python3 /root/.openclaw/workspace-coding-agent/tools/github/sanitize_config.py \
        /root/.openclaw/openclaw.json "$REPO_DIR/config/openclaw.json"
    rsync -a /root/.openclaw/workspace-coding-agent/reports/ "$REPO_DIR/agents/coding-agent/reports/" 2>/dev/null || true
    rsync -a /root/.openclaw/workspace-coding-agent/memory/ "$REPO_DIR/agents/coding-agent/memory/" 2>/dev/null || true
    rsync -a /root/.openclaw/workspace-research-agent/reports/ "$REPO_DIR/agents/research-agent/reports/" 2>/dev/null || true
}

git_push() {
    cd "$REPO_DIR"
    # 更新远程 URL（含 token）
    git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git"
    git add -A
    if git diff --cached --quiet; then
        echo "没有变更，跳过推送"
        exit 0
    fi
    git commit -m "$COMMIT_MSG"
    # 重试逻辑
    for i in 1 2 3; do
        if git push origin main; then
            echo "✅ 推送成功"
            exit 0
        fi
        echo "推送失败，${i}/3，等待 10 秒重试..."
        sleep 10
    done
    echo "❌ 推送失败（3次）"
    exit 1
}

sync_files
git_push
