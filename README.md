# OpenClaw Agent Toolkit

A collection of automation tools for [OpenClaw](https://github.com/openclaw/openclaw) multi-agent systems.

## Tools

### 📊 Log Monitor (`tools/log_monitor/`)
Analyzes OpenClaw audit logs and generates structured reports.
```bash
python3 tools/log_monitor/log_monitor.py
```

### 💓 Heartbeat Monitor (`tools/heartbeat/`)
Tracks agent liveness across sessions. Alerts via Telegram if any agent is unresponsive for >2 hours.
```bash
python3 tools/heartbeat/heartbeat_monitor.py
```

### 🗂️ Unified Dashboard (`tools/dashboard/`)
Generates a unified Markdown status board aggregating all agents, cron jobs, reports, and health checks.
```bash
python3 tools/dashboard/unified_dashboard.py
```

### 🔄 GitHub AutoSync (`tools/github_sync/`)
Automatically syncs agent configs, reports, and memories to a private GitHub repo — with token redaction.
```bash
# Setup
bash tools/github_sync/setup_repo.sh <username> <repo> <pat>

# Sync
bash tools/github_sync/autosync.sh
```

### 🔍 PR Reviewer (`tools/github_sync/`)
Monitors GitHub PRs and posts AI-generated code reviews using OpenClaw's built-in model.
```bash
GITHUB_TOKEN=... GITHUB_OWNER=... GITHUB_REPO=... python3 tools/github_sync/pr_reviewer.py
```

## AI Research (`tools/ai_research/`)
Multi-source AI research tool — fetches GitHub Trending + arXiv papers and generates daily briefings.

## Requirements
- Python 3.8+
- OpenClaw (https://github.com/openclaw/openclaw)
- `rsync` (for autosync)

## Setup
```bash
cp tools/github_sync/.env.example tools/github_sync/.env
# Edit .env with your tokens
```

## License
MIT
