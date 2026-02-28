#!/usr/bin/env python3
"""
GitHub PR Reviewer
监听指定仓库的 PR，用 AI 进行代码评审，自动提交 Review 并 Telegram 通知 K
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

# 配置从环境变量读取
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = os.environ.get("GITHUB_OWNER", "")
REPO_NAME = os.environ.get("GITHUB_REPO", "")
STATE_FILE = Path("/root/.openclaw/workspace-coding-agent/tools/github/pr_state.json")

def github_api(path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"GitHub API 错误 {e.code}: {e.read().decode()}")
        return None

def get_pr_diff(pr_number):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode(errors="replace")
    except Exception as e:
        return f"无法获取 diff: {e}"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"reviewed": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def review_with_ai(pr_title, pr_body, diff):
    """调用 openclaw 内置模型进行代码评审（通过 sessions_spawn 或本地推理）"""
    prompt = f"""你是一名资深代码评审专家。请对以下 PR 进行简洁的评审，重点关注：
1. 逻辑正确性
2. 安全风险
3. 性能问题
4. 代码质量

PR 标题：{pr_title}
PR 描述：{pr_body or '无'}

代码变更（Diff）：
{diff[:4000]}

请用中文输出评审结果，格式：
- 总体评价（1句话）
- 主要问题（如有）
- 建议（简短）
"""
    # 通过 openclaw sessions_spawn 调用 AI
    try:
        result = subprocess.run(
            ["openclaw", "agent", "run", "--message", prompt],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "自动评审不可用，请人工评审此 PR。"

def post_review(pr_number, body):
    return github_api(
        f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/reviews",
        method="POST",
        data={"body": body, "event": "COMMENT"}
    )

def notify_k(pr_number, pr_title, review_summary):
    msg = f"🔍 **PR 评审完成 #{pr_number}**\n\n**标题：** {pr_title}\n\n**评审摘要：**\n{review_summary[:500]}\n\n[查看 PR](https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{pr_number})"
    subprocess.run([
        "openclaw", "message", "send",
        "--channel", "telegram",
        "--target", "7655210263",
        "--message", msg
    ], timeout=10)

def main():
    if not GITHUB_TOKEN or not REPO_OWNER or not REPO_NAME:
        print("缺少环境变量: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        sys.exit(1)

    state = load_state()
    prs = github_api(f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open&per_page=10")
    if not prs:
        print("没有开放的 PR 或无法连接 GitHub")
        return

    new_reviews = 0
    for pr in prs:
        pr_number = pr["number"]
        if pr_number in state["reviewed"]:
            continue

        print(f"评审 PR #{pr_number}: {pr['title']}")
        diff = get_pr_diff(pr_number)
        review = review_with_ai(pr["title"], pr.get("body", ""), diff)
        post_review(pr_number, f"**🤖 AI 自动评审**\n\n{review}")
        notify_k(pr_number, pr["title"], review)
        state["reviewed"].append(pr_number)
        new_reviews += 1

    save_state(state)
    print(f"完成评审 {new_reviews} 个新 PR")

if __name__ == "__main__":
    main()
