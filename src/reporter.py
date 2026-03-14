#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║        ProxyScraper Pro — Report Generator                ║
║   Generates GitHub Summary, Commit Messages, README       ║
╚══════════════════════════════════════════════════════════╝
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("output")


def load_stats() -> dict:
    """Load stats from the scraper output."""
    stats_file = OUTPUT_DIR / "stats.json"
    if stats_file.exists():
        with open(stats_file) as f:
            return json.load(f)
    return {}


def generate_github_summary(stats: dict):
    """Generate a rich GitHub Actions job summary."""
    md = []
    md.append("# 🔥 ProxyScraper Pro — Run Report\n")
    md.append(f"**Generated:** `{stats.get('timestamp', 'N/A')}`\n")

    # Overview
    md.append("## 📊 Overview\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| ⏱ Duration | `{stats.get('duration_seconds', 0):.1f}s` |")
    md.append(f"| 📡 Sources | `{stats.get('sources_success', 0)}/{stats.get('sources_total', 0)}` |")
    md.append(f"| 🔎 Scraped | `{stats.get('scraped_total', 0):,}` |")
    md.append(f"| 🧹 Unique | `{stats.get('scraped_unique', 0):,}` |")
    md.append(f"| ✅ **Alive** | **`{stats.get('alive_total', 0):,}`** |")
    md.append(f"| ❌ Dead | `{stats.get('dead_total', 0):,}` |")
    md.append(f"| ⚡ Avg Speed | `{stats.get('avg_speed_ms', 0):.0f}ms` |")

    alive = stats.get("alive_total", 0)
    unique = stats.get("scraped_unique", 1)
    if unique > 0:
        pct = (alive / unique) * 100
        md.append(f"| 📈 Success Rate | `{pct:.1f}%` |")

    md.append("")

    # Fastest proxy
    fp = stats.get("fastest_proxy")
    if fp:
        md.append(f"### 🚀 Fastest Proxy\n")
        md.append(f"```")
        md.append(f"{fp.get('address', 'N/A')} ({fp.get('protocol', '?').upper()})")
        md.append(f"Speed: {fp.get('speed_ms', 0):.0f}ms | {fp.get('country', 'Unknown')} ({fp.get('country_code', '??')})")
        md.append(f"Anonymity: {fp.get('anonymity', 'unknown').title()}")
        md.append(f"```\n")

    # Protocol breakdown
    by_proto = stats.get("by_protocol", {})
    if by_proto:
        md.append("## 🌐 By Protocol\n")
        md.append("| Protocol | Count | Bar |")
        md.append("|----------|-------|-----|")
        max_val = max(by_proto.values()) if by_proto.values() else 1
        for proto in ["http", "https", "socks4", "socks5"]:
            count = by_proto.get(proto, 0)
            bar_len = int((count / max_val) * 20) if max_val > 0 else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            emoji = {"http": "🌐", "https": "🔒", "socks4": "🧦", "socks5": "🧦"}.get(proto, "📌")
            md.append(f"| {emoji} {proto.upper()} | `{count:,}` | `{bar}` |")
        md.append("")

    # Anonymity breakdown
    by_anon = stats.get("by_anonymity", {})
    if by_anon:
        md.append("## 🎭 By Anonymity\n")
        md.append("| Level | Count |")
        md.append("|-------|-------|")
        for level in ["elite", "anonymous", "transparent"]:
            count = by_anon.get(level, 0)
            emoji = {"elite": "🥇", "anonymous": "🥈", "transparent": "🥉"}.get(level, "❔")
            md.append(f"| {emoji} {level.title()} | `{count:,}` |")
        md.append("")

    # Speed breakdown
    by_speed = stats.get("by_speed", {})
    if by_speed:
        md.append("## ⚡ By Speed Tier\n")
        md.append("| Tier | Count | Criteria |")
        md.append("|------|-------|----------|")
        tiers = {
            "fast": ("⚡", "< 1000ms"),
            "medium": ("🔶", "1000-3000ms"),
            "slow": ("🐢", "> 3000ms"),
        }
        for tier, (emoji, criteria) in tiers.items():
            count = by_speed.get(tier, 0)
            md.append(f"| {emoji} {tier.title()} | `{count:,}` | {criteria} |")
        md.append("")

    # Top countries
    by_country = stats.get("by_country_top20", {})
    if by_country:
        md.append("## 🌍 Top Countries\n")
        md.append("| # | Country | Count |")
        md.append("|---|---------|-------|")
        for i, (cc, count) in enumerate(
            sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:15], 1
        ):
            flag = chr(127397 + ord(cc[0])) + chr(127397 + ord(cc[1])) if len(cc) == 2 else "🏳️"
            md.append(f"| {i} | {flag} {cc} | `{count:,}` |")
        md.append("")

    # Output files
    md.append("## 📁 Output Files\n")
    md.append("| File | Size |")
    md.append("|------|------|")
    for fpath in sorted(OUTPUT_DIR.glob("*")):
        if fpath.name in ("stats.json", "commit_summary.txt", "github_summary.md"):
            continue
        size = fpath.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        md.append(f"| `{fpath.name}` | {size_str} |")
    md.append("")

    md.append("---")
    md.append("*Generated by [ProxyScraper Pro](https://github.com/)*")

    return "\n".join(md)


def generate_commit_summary(stats: dict) -> str:
    """Generate a commit message body."""
    lines = []
    lines.append(f"📊 Proxies: {stats.get('alive_total', 0):,} alive / {stats.get('scraped_unique', 0):,} scraped")

    by_proto = stats.get("by_protocol", {})
    parts = []
    for p in ["http", "https", "socks4", "socks5"]:
        c = by_proto.get(p, 0)
        if c > 0:
            parts.append(f"{p.upper()}: {c:,}")
    if parts:
        lines.append(f"🌐 {' | '.join(parts)}")

    lines.append(f"⚡ Avg speed: {stats.get('avg_speed_ms', 0):.0f}ms")
    lines.append(f"⏱  Duration: {stats.get('duration_seconds', 0):.1f}s")

    return "\n".join(lines)


def update_readme(stats: dict):
    """Update the repo README with latest stats badge."""
    readme_path = Path("README.md")

    badge_section = f"""
<!-- PROXY-STATS-START -->
## 📊 Latest Proxy Stats

| Metric | Value |
|--------|-------|
| ✅ Alive Proxies | **{stats.get('alive_total', 0):,}** |
| 🌐 HTTP | {stats.get('by_protocol', {}).get('http', 0):,} |
| 🔒 HTTPS | {stats.get('by_protocol', {}).get('https', 0):,} |
| 🧦 SOCKS4 | {stats.get('by_protocol', {}).get('socks4', 0):,} |
| 🧦 SOCKS5 | {stats.get('by_protocol', {}).get('socks5', 0):,} |
| ⚡ Avg Speed | {stats.get('avg_speed_ms', 0):.0f}ms |
| 🕐 Last Updated | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} |

<!-- PROXY-STATS-END -->
"""

    if readme_path.exists():
        content = readme_path.read_text()
        import re
        pattern = r"<!-- PROXY-STATS-START -->.*?<!-- PROXY-STATS-END -->"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, badge_section.strip(), content, flags=re.DOTALL)
        else:
            content += "\n" + badge_section
        readme_path.write_text(content)
    else:
        readme_path.write_text(f"# 🔥 ProxyScraper Pro\n\n{badge_section}")


def main():
    stats = load_stats()
    if not stats:
        print("⚠️  No stats.json found — skipping report generation.")
        return

    # GitHub Summary
    summary_md = generate_github_summary(stats)
    summary_path = OUTPUT_DIR / "github_summary.md"
    summary_path.write_text(summary_md)
    print(f"✅ GitHub summary: {summary_path}")

    # Commit Summary
    commit_summary = generate_commit_summary(stats)
    commit_path = OUTPUT_DIR / "commit_summary.txt"
    commit_path.write_text(commit_summary)
    print(f"✅ Commit summary: {commit_path}")

    # Update README
    update_readme(stats)
    print("✅ README updated")


if __name__ == "__main__":
    main()
