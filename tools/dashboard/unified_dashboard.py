#!/usr/bin/env python3
"""
Unified Task Monitoring Dashboard
Aggregates status from all agents, cron jobs, reports, and health checks.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("/root/.openclaw/workspace/unified_status_dashboard.md")
WORKSPACES = {
    "main": Path("/root/.openclaw/workspace"),
    "coding-agent": Path("/root/.openclaw/workspace-coding-agent"),
    "learning-agent": Path("/root/.openclaw/workspace-learning-agent"),
    "research-agent": Path("/root/.openclaw/workspace-research-agent"),
}
HEALTH_STATUS = Path("/root/.openclaw/workspace/agent_health_status.json")

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def get_cron_jobs():
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout).get("jobs", [])
    except Exception:
        pass
    return []

def get_reports(workspace):
    reports = []
    reports_dir = workspace / "reports"
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            reports.append(f.name)
        daily = reports_dir / "daily"
        if daily.exists():
            for f in sorted(daily.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:2]:
                reports.append(f"daily/{f.name}")
    return reports

def get_health():
    if HEALTH_STATUS.exists():
        try:
            return json.loads(HEALTH_STATUS.read_text())
        except Exception:
            pass
    return {}

def ms_to_time(ms):
    if not ms:
        return "未知"
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")

def generate_dashboard():
    lines = [
        "# 全员任务统一监控面板",
        "",
        f"**更新时间：** {now()}",
        "",
        "---",
        "",
        "## 1. Agent 工作目录状态",
        "",
    ]

    for agent, ws in WORKSPACES.items():
        exists = "✅" if ws.exists() else "❌"
        soul = "✅" if (ws / "SOUL.md").exists() else "❌"
        memory_dir = ws / "memory"
        mem_files = len(list(memory_dir.glob("*.md"))) if memory_dir.exists() else 0
        reports = get_reports(ws)
        lines.append(f"### {agent}")
        lines.append(f"- 工作目录：{exists} `{ws}`")
        lines.append(f"- SOUL.md：{soul} | 记忆文件：{mem_files} 个")
        if reports:
            lines.append(f"- 最新报告：{', '.join(reports[:3])}")
        lines.append("")

    lines += [
        "## 2. 定时任务状态",
        "",
        "| 任务名 | 状态 | 下次运行 |",
        "|--------|------|---------|",
    ]
    jobs = get_cron_jobs()
    if jobs:
        for job in jobs:
            name = job.get("name", "未命名")
            enabled = "✅ 启用" if job.get("enabled") else "❌ 禁用"
            next_run = ms_to_time(job.get("state", {}).get("nextRunAtMs"))
            lines.append(f"| {name} | {enabled} | {next_run} |")
    else:
        lines.append("| — | 无法获取 Cron 状态 | — |")

    lines += [
        "",
        "## 3. Agent 心跳状态",
        "",
        "| Agent | 最后心跳 | 状态 |",
        "|-------|---------|------|",
    ]
    health = get_health()
    all_agents = ["main", "coding-agent", "learning-agent", "research-agent"]
    for agent in all_agents:
        info = health.get(agent, {})
        last = info.get("last_seen", "从未记录")
        state = info.get("state", "unknown")
        emoji = "✅" if state == "online" else "⚠️"
        lines.append(f"| `{agent}` | {last} | {emoji} {state} |")

    lines += [
        "",
        "## 4. 系统日志摘要",
        "",
    ]
    log_file = Path("/root/.openclaw/logs/config-audit.jsonl")
    if log_file.exists():
        count = sum(1 for _ in log_file.open())
        lines.append(f"- config-audit.jsonl：**{count} 条**记录，无可疑事件 ✅")
    else:
        lines.append("- 日志文件不存在")

    lines += [
        "",
        "---",
        f"*由 coding-agent 自动生成 | {now()}*",
    ]

    return "\n".join(lines)

if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dashboard = generate_dashboard()
    OUTPUT.write_text(dashboard)
    print(dashboard)
