#!/usr/bin/env python3
"""
Cross-Agent Heartbeat Monitor
Checks agent session status and alerts K if any agent is unresponsive.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_FILE = Path("/root/.openclaw/workspace/agent_health_status.json")
ALERT_THRESHOLD_HOURS = 2
AGENTS = ["main", "coding-agent", "learning-agent", "research-agent"]

def load_status():
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())
        except Exception:
            pass
    return {}

def save_status(status):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2))

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def now_ts():
    return datetime.now(timezone.utc).timestamp()

def check_agents():
    """Use openclaw sessions list to check agent activity."""
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "list", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None

def generate_report(status, alerts):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 跨代理心跳监测报告",
        "",
        f"**生成时间：** {now}",
        "",
        "## Agent 状态",
        "",
        "| Agent | 最后心跳 | 状态 |",
        "|-------|----------|------|",
    ]
    for agent, info in status.items():
        last = info.get("last_seen", "未知")
        state = info.get("state", "未知")
        emoji = "✅" if state == "online" else "⚠️"
        lines.append(f"| `{agent}` | {last} | {emoji} {state} |")

    if alerts:
        lines += ["", "## ⚠️ 告警", ""]
        for a in alerts:
            lines.append(f"- `{a['agent']}` 超过 {a['hours']:.1f} 小时未响应")
    else:
        lines += ["", "## ✅ 无告警", "", "所有 Agent 均在线。"]

    return "\n".join(lines)

if __name__ == "__main__":
    status = load_status()
    now_t = now_ts()
    now_s = now_iso()

    # Update current agent (coding-agent) as online
    status["coding-agent"] = {
        "last_seen": now_s,
        "last_ts": now_t,
        "state": "online"
    }

    # Check for stale agents
    alerts = []
    for agent in AGENTS:
        if agent == "coding-agent":
            continue
        info = status.get(agent, {})
        last_ts = info.get("last_ts")
        if last_ts:
            hours_ago = (now_t - last_ts) / 3600
            if hours_ago > ALERT_THRESHOLD_HOURS:
                alerts.append({"agent": agent, "hours": hours_ago})
                status[agent]["state"] = "offline"
        else:
            # Never seen — mark as unknown
            status[agent] = {
                "last_seen": "从未记录",
                "last_ts": None,
                "state": "unknown"
            }

    save_status(status)
    report = generate_report(status, alerts)
    print(report)

    if alerts:
        sys.exit(2)  # Signal alerts exist
    sys.exit(0)
