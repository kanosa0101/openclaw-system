# openclaw-system

> OpenClaw 多代理体系自动化工具集

A set of automation tools for [OpenClaw](https://github.com/openclaw/openclaw) multi-agent systems — log monitoring, agent heartbeat, unified dashboard, AI research briefing, and GitHub autosync.

---

## 🛠️ Tools

### 📊 Log Monitor
Parses OpenClaw audit logs and outputs a structured event report.
```bash
python3 tools/log_monitor/log_monitor.py
```

### 💓 Heartbeat Monitor
Tracks agent liveness. Alerts via Telegram if any agent is silent for >2 hours.
```bash
python3 tools/heartbeat/heartbeat_monitor.py
# Status saved to: /root/.openclaw/workspace/agent_health_status.json
```

### 🗂️ Unified Dashboard
Aggregates all agents, cron jobs, reports, and health checks into a single Markdown board.
```bash
python3 tools/dashboard/unified_dashboard.py
# Output: /root/.openclaw/workspace/unified_status_dashboard.md
```

### 🔍 AI Research Briefing
Fetches GitHub Trending + arXiv papers and generates a daily Markdown briefing.
```bash
python3 tools/ai_research/ai_research.py
python3 tools/ai_research/ai_research.py --keywords "MCP agent tool-use" --since weekly --top 10 --output report.md
```
Options:
| Flag | Default | Description |
|------|---------|-------------|
| `--keywords` | `LLM agent agentic self-reflection` | arXiv search query |
| `--since` | `daily` | GitHub Trending window: `daily / weekly / monthly` |
| `--language` | *(any)* | Filter GitHub Trending by language (e.g. `python`) |
| `--top` | `5` | Number of results per source |
| `--output` | *(stdout)* | Save report to file |

### 🔄 GitHub AutoSync
Syncs agent configs, reports, and memories to a GitHub repo — with token redaction.
```bash
# First-time setup
bash tools/github_sync/setup_repo.sh <username> <repo> <pat>

# Sync
bash tools/github_sync/autosync.sh
```

### 🤖 PR Reviewer
Monitors open PRs and posts AI-generated code reviews.
```bash
export GITHUB_TOKEN=... GITHUB_OWNER=... GITHUB_REPO=...
python3 tools/github_sync/pr_reviewer.py
```

---

## ⚙️ Requirements

- Python 3.8+
- [OpenClaw](https://github.com/openclaw/openclaw)
- `rsync` (for autosync)
- No third-party Python packages required

## 🔐 Credentials

```bash
cp tools/github_sync/.env.example tools/github_sync/.env
# Edit .env — never commit this file
```

---

## 📄 License

MIT
