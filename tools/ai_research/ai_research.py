#!/usr/bin/env python3
"""
Multi-Source AI Research Tool
Fetches GitHub Trending + arXiv papers and generates daily briefings.

Usage:
    python3 ai_research.py [--keywords "LLM agent,agentic"] [--output /path/to/report.md]
"""

import argparse
import urllib.request
import urllib.parse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import html


def fetch_url(url, accept=None):
    headers = {"User-Agent": "Mozilla/5.0 (AI Research Tool)"}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode(errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


def parse_github_trending(since="daily"):
    """Scrape GitHub Trending page."""
    url = f"https://github.com/trending?since={since}"
    raw = fetch_url(url)
    repos = []
    # Extract repo names and descriptions
    for m in re.finditer(r'href="/([^/]+/[^/"]+)"[^>]*>\s*\n.*?(<h2|<p)', raw, re.S):
        full = m.group(1)
        if full.count("/") == 1 and not full.startswith("trending"):
            repos.append(full)
    # Extract star counts
    stars = re.findall(r'([\d,]+)\s*stars? today', raw)
    results = []
    seen = set()
    for i, repo in enumerate(repos[:20]):
        if repo in seen:
            continue
        seen.add(repo)
        star = stars[len(results)] if len(results) < len(stars) else "?"
        results.append({"repo": repo, "stars_today": star, "url": f"https://github.com/{repo}"})
        if len(results) >= 10:
            break
    return results


def parse_arxiv(keywords, max_results=10):
    """Fetch arXiv papers by keyword."""
    query = urllib.parse.quote(keywords)
    url = f"https://export.arxiv.org/api/query?search_query=all:{query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    raw = fetch_url(url)
    papers = []
    entries = re.findall(r'<entry>(.*?)</entry>', raw, re.S)
    for entry in entries:
        title = re.search(r'<title>(.*?)</title>', entry, re.S)
        summary = re.search(r'<summary>(.*?)</summary>', entry, re.S)
        link = re.search(r'<id>(.*?)</id>', entry)
        published = re.search(r'<published>(.*?)</published>', entry)
        if title and link:
            papers.append({
                "title": html.unescape(title.group(1).strip().replace("\n", " ")),
                "summary": html.unescape(summary.group(1).strip()[:300].replace("\n", " ")) if summary else "",
                "url": link.group(1).strip(),
                "published": published.group(1)[:10] if published else "?",
            })
    return papers


def generate_report(github_repos, arxiv_papers, keywords, output_path):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# 每日 AI 调研简报 — {date}",
        "",
        f"**生成时间：** {now}  ",
        f"**关键词：** {keywords}  ",
        f"**数据来源：** GitHub Trending + arXiv",
        "",
        "---",
        "",
        "## 🔥 GitHub 今日热门",
        "",
        "| 项目 | 今日 Stars |",
        "|------|-----------|",
    ]
    for r in github_repos[:10]:
        lines.append(f"| [{r['repo']}]({r['url']}) | ⭐ {r['stars_today']} |")

    lines += [
        "",
        "## 📚 arXiv 最新论文",
        "",
    ]
    for p in arxiv_papers[:10]:
        lines.append(f"### [{p['title']}]({p['url']})")
        lines.append(f"*发布：{p['published']}*")
        lines.append(f"{p['summary']}...")
        lines.append("")

    lines += [
        "---",
        f"*由 AI Research Tool 自动生成 | {now}*",
    ]

    report = "\n".join(lines)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(report)
        print(f"✅ 报告已保存: {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Multi-Source AI Research Tool")
    parser.add_argument("--keywords", default="LLM agent agentic self-reflection", help="arXiv 搜索关键词")
    parser.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"], help="GitHub Trending 时间范围")
    parser.add_argument("--output", default=None, help="输出报告路径")
    args = parser.parse_args()

    print("抓取 GitHub Trending...")
    repos = parse_github_trending(args.since)
    print(f"  找到 {len(repos)} 个项目")

    print("抓取 arXiv 论文...")
    papers = parse_arxiv(args.keywords)
    print(f"  找到 {len(papers)} 篇论文")

    report = generate_report(repos, papers, args.keywords, args.output)
    if not args.output:
        print(report)


if __name__ == "__main__":
    main()
