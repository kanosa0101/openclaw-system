#!/usr/bin/env python3
"""
Multi-Source AI Research Tool
Daily briefing generator: GitHub Trending + arXiv papers.

Usage:
    python3 ai_research.py
    python3 ai_research.py --keywords "MCP agent tool-use" --since weekly --output report.md
"""

import argparse
import urllib.request
import urllib.parse
import re
import html
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────
# Fetchers
# ─────────────────────────────────────────────

def fetch(url, accept=None):
    headers = {"User-Agent": "ai-research-tool/1.0 (github.com/kanosa0101/openclaw-system)"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read().decode(errors="replace")
        except Exception as e:
            if attempt == 2:
                return ""
    return ""


def github_trending(since="daily", language=""):
    """Return list of {repo, url, description, stars_today}."""
    url = f"https://github.com/trending{('/' + language) if language else ''}?since={since}"
    raw = fetch(url)
    results = []
    # repo slugs
    slugs = re.findall(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', raw)
    seen = set()
    clean = []
    for s in slugs:
        if s not in seen and "/" in s and not any(x in s for x in ["trending", "login", "signup", "explore"]):
            seen.add(s)
            clean.append(s)

    stars = re.findall(r'([\d,]+)\s+stars? today', raw)
    descs = re.findall(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', raw, re.S)

    for i, slug in enumerate(clean[:15]):
        results.append({
            "repo": slug,
            "url": f"https://github.com/{slug}",
            "description": html.unescape(descs[i].strip()) if i < len(descs) else "",
            "stars_today": stars[i].replace(",", "") if i < len(stars) else "?",
        })
    return results


def arxiv_papers(query, max_results=10):
    """Return list of {title, url, published, summary, authors}."""
    q = urllib.parse.quote(query)
    url = (f"https://export.arxiv.org/api/query?"
           f"search_query=all:{q}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}")
    raw = fetch(url)
    papers = []
    for entry in re.findall(r"<entry>(.*?)</entry>", raw, re.S):
        def tag(t):
            m = re.search(rf"<{t}[^>]*>(.*?)</{t}>", entry, re.S)
            return html.unescape(m.group(1).strip()) if m else ""

        title = tag("title").replace("\n", " ")
        summary = tag("summary").replace("\n", " ")[:350]
        published = tag("published")[:10]
        link_m = re.search(r"<id>(http[s]?://arxiv\.org/abs/[^<]+)</id>", entry)
        url_paper = link_m.group(1).strip() if link_m else ""
        authors = re.findall(r"<name>(.*?)</name>", entry)

        if title and url_paper:
            papers.append({
                "title": title,
                "url": url_paper,
                "published": published,
                "summary": summary,
                "authors": authors[:3],
            })
    return papers


# ─────────────────────────────────────────────
# Report generator
# ─────────────────────────────────────────────

def generate(repos, papers, keywords, since, top_n=5):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    since_label = {"daily": "今日", "weekly": "本周", "monthly": "本月"}.get(since, since)

    lines = [
        f"# 每日 AI 调研简报 — {date}",
        "",
        f"> 生成时间：{now} | 关键词：`{keywords}` | 数据来源：GitHub Trending · arXiv",
        "",
        "---",
        "",
        f"## 🔥 GitHub {since_label}热门（Top {min(top_n, len(repos))}）",
        "",
    ]

    for r in repos[:top_n]:
        stars = f"⭐ +{r['stars_today']}" if r["stars_today"] != "?" else ""
        desc = f" — {r['description']}" if r["description"] else ""
        lines.append(f"- **[{r['repo']}]({r['url']})** {stars}{desc}")

    lines += [
        "",
        f"## 📚 arXiv 最新论文（Top {min(top_n, len(papers))}）",
        "",
    ]

    for p in papers[:top_n]:
        authors = ", ".join(p["authors"]) + (" et al." if len(p["authors"]) >= 3 else "")
        lines.append(f"### [{p['title']}]({p['url']})")
        lines.append(f"*{p['published']} · {authors}*")
        lines.append("")
        lines.append(f"{p['summary']}...")
        lines.append("")

    lines += [
        "---",
        "",
        "## 💡 今日洞察",
        "",
        "*(由使用者或 AI 补充)*",
        "",
        "---",
        f"*自动生成 by [openclaw-system](https://github.com/kanosa0101/openclaw-system)*",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Multi-Source AI Research Tool")
    parser.add_argument("--keywords", default="LLM agent agentic self-reflection",
                        help="arXiv 搜索关键词（默认：LLM agent agentic）")
    parser.add_argument("--since", default="daily",
                        choices=["daily", "weekly", "monthly"],
                        help="GitHub Trending 时间范围（默认：daily）")
    parser.add_argument("--language", default="",
                        help="GitHub Trending 语言过滤（如 python）")
    parser.add_argument("--top", type=int, default=5,
                        help="每个来源显示的条目数（默认：5）")
    parser.add_argument("--output", default=None,
                        help="输出 Markdown 文件路径（默认：打印到终端）")
    args = parser.parse_args()

    print("📡 抓取 GitHub Trending...", flush=True)
    repos = github_trending(args.since, args.language)
    print(f"   找到 {len(repos)} 个项目")

    print("📡 抓取 arXiv 论文...", flush=True)
    papers = arxiv_papers(args.keywords, max_results=args.top * 2)
    print(f"   找到 {len(papers)} 篇论文")

    report = generate(repos, papers, args.keywords, args.since, args.top)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"✅ 报告已保存：{args.output}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
