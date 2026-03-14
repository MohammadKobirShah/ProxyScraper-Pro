#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║        ProxyScraper Pro — Main Scraping Engine            ║
║   Multi-source | Async | Validated | Geo-tagged           ║
╚══════════════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import re
import sys
import time
import json
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from collections import Counter, defaultdict

import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
)
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

# Local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROXY_SOURCES, Proxy, AppConfig, BANNER

console = Console()


# ═══════════════════════════════════════════════
#  Utility Functions
# ═══════════════════════════════════════════════

PROXY_REGEX = re.compile(
    r"(?:(?:https?|socks[45])://)?"
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"[:\s]+"
    r"(\d{2,5})"
)


def parse_proxies_from_text(text: str, protocol: str, source_name: str) -> List[Proxy]:
    """Extract proxy addresses from raw text."""
    proxies = []
    seen = set()

    for match in PROXY_REGEX.finditer(text):
        ip, port_str = match.group(1), match.group(2)
        port = int(port_str)

        # Validate IP octets
        octets = ip.split(".")
        if not all(0 <= int(o) <= 255 for o in octets):
            continue
        if not (1 <= port <= 65535):
            continue

        key = f"{ip}:{port}"
        if key not in seen:
            seen.add(key)
            proxies.append(
                Proxy(
                    ip=ip,
                    port=port,
                    protocol=protocol,
                    source=source_name,
                )
            )
    return proxies


def get_user_agent() -> str:
    """Return a randomized User-Agent string."""
    try:
        from fake_useragent import UserAgent
        return UserAgent().random
    except Exception:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )


# ═══════════════════════════════════════════════
#  Scraper Engine
# ═══════════════════════════════════════════════

class ProxyScraperPro:
    """Premium multi-source proxy scraper with async validation."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.all_proxies: List[Proxy] = []
        self.alive_proxies: List[Proxy] = []
        self.stats: Dict = {
            "sources_total": 0,
            "sources_success": 0,
            "sources_failed": 0,
            "scraped_total": 0,
            "scraped_unique": 0,
            "validated_total": 0,
            "alive_total": 0,
            "dead_total": 0,
            "start_time": None,
            "end_time": None,
            "by_protocol": Counter(),
            "by_country": Counter(),
            "by_anonymity": Counter(),
            "by_speed": Counter(),
            "by_source": Counter(),
            "fastest_proxy": None,
            "avg_speed_ms": 0,
        }
        self.judge_urls = [
            "http://httpbin.org/ip",
            "http://ip-api.com/json",
            "https://api.ipify.org?format=json",
        ]

    # ─── Source Scraping ───────────────────────────

    async def _fetch_source(
        self,
        session: aiohttp.ClientSession,
        source: Dict,
        protocol: str,
        progress: Progress,
        task_id,
    ) -> List[Proxy]:
        """Fetch proxies from a single source."""
        name = source["name"]
        url = source["url"]
        proxies = []

        for attempt in range(3):
            try:
                headers = {"User-Agent": get_user_agent()}
                async with session.get(
                    url, headers=headers, timeout=ClientTimeout(total=20)
                ) as resp:
                    if resp.status == 200:
                        text = await resp.text(errors="replace")
                        proxies = parse_proxies_from_text(text, protocol, name)
                        self.stats["sources_success"] += 1
                        progress.console.print(
                            f"  [green]✓[/green] {name}: [bold]{len(proxies):,}[/bold] proxies"
                        )
                        break
                    else:
                        if attempt == 2:
                            self.stats["sources_failed"] += 1
                            progress.console.print(
                                f"  [red]✗[/red] {name}: HTTP {resp.status}"
                            )
            except Exception as e:
                if attempt == 2:
                    self.stats["sources_failed"] += 1
                    progress.console.print(
                        f"  [red]✗[/red] {name}: {str(e)[:60]}"
                    )
                await asyncio.sleep(1)

        progress.advance(task_id)
        return proxies

    async def scrape_all(self) -> List[Proxy]:
        """Scrape proxies from all configured sources."""
        console.print(BANNER)
        console.print(
            Panel(
                f"[bold white]Protocols:[/bold white] {', '.join(self.config.protocols)}\n"
                f"[bold white]Validation:[/bold white] {'✅ Enabled' if self.config.validate else '❌ Disabled'}\n"
                f"[bold white]Workers:[/bold white] {self.config.max_workers}\n"
                f"[bold white]Timeout:[/bold white] {self.config.timeout}s\n"
                f"[bold white]Countries:[/bold white] {', '.join(self.config.countries)}\n"
                f"[bold white]Formats:[/bold white] {', '.join(self.config.output_formats)}",
                title="⚙️  Configuration",
                border_style="cyan",
                box=box.DOUBLE_EDGE,
            )
        )

        self.stats["start_time"] = time.time()

        # Build source list
        sources_list: List[Tuple[Dict, str]] = []
        for protocol in self.config.protocols:
            if protocol in PROXY_SOURCES:
                for source in PROXY_SOURCES[protocol]:
                    sources_list.append((source, protocol))

        self.stats["sources_total"] = len(sources_list)
        console.print(
            f"\n[bold cyan]📡 Fetching from {len(sources_list)} sources...[/bold cyan]\n"
        )

        all_scraped: List[Proxy] = []
        connector = TCPConnector(limit=50, ssl=False)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Scraping sources...", total=len(sources_list)
            )

            async with aiohttp.ClientSession(connector=connector) as session:
                # Process in batches of 10
                batch_size = 10
                for i in range(0, len(sources_list), batch_size):
                    batch = sources_list[i : i + batch_size]
                    tasks = [
                        self._fetch_source(session, src, proto, progress, task)
                        for src, proto in batch
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, list):
                            all_scraped.extend(result)
                    await asyncio.sleep(0.5)

        # Deduplicate
        seen = set()
        unique_proxies = []
        for p in all_scraped:
            key = (p.ip, p.port, p.protocol)
            if key not in seen:
                seen.add(key)
                unique_proxies.append(p)

        self.all_proxies = unique_proxies
        self.stats["scraped_total"] = len(all_scraped)
        self.stats["scraped_unique"] = len(unique_proxies)

        # Summary table
        scrape_table = Table(
            title="📊 Scraping Summary",
            box=box.ROUNDED,
            border_style="cyan",
            show_lines=True,
        )
        scrape_table.add_column("Metric", style="bold white", width=25)
        scrape_table.add_column("Value", style="bold green", justify="right", width=15)
        scrape_table.add_row("Sources Contacted", f"{self.stats['sources_total']:,}")
        scrape_table.add_row("Sources Successful", f"[green]{self.stats['sources_success']:,}[/green]")
        scrape_table.add_row("Sources Failed", f"[red]{self.stats['sources_failed']:,}[/red]")
        scrape_table.add_row("Total Scraped", f"{self.stats['scraped_total']:,}")
        scrape_table.add_row("Unique Proxies", f"[bold cyan]{self.stats['scraped_unique']:,}[/bold cyan]")

        for proto in self.config.protocols:
            count = sum(1 for p in unique_proxies if p.protocol == proto)
            scrape_table.add_row(f"  └─ {proto.upper()}", f"{count:,}")

        console.print()
        console.print(scrape_table)

        return unique_proxies

    # ─── Proxy Validation ─────────────────────────

    async def _check_proxy(
        self,
        proxy: Proxy,
        session: aiohttp.ClientSession,
        my_ip: str,
    ) -> Proxy:
        """Validate a single proxy for connectivity, speed, and anonymity."""
        start = time.monotonic()

        try:
            if proxy.protocol in ("http", "https"):
                proxy_url = f"http://{proxy.ip}:{proxy.port}"
                async with session.get(
                    self.judge_urls[0],
                    proxy=proxy_url,
                    timeout=ClientTimeout(total=self.config.timeout),
                    headers={"User-Agent": get_user_agent()},
                ) as resp:
                    if resp.status == 200:
                        elapsed = (time.monotonic() - start) * 1000
                        body = await resp.text()
                        proxy.is_alive = True
                        proxy.speed_ms = elapsed

                        # Speed tier
                        if elapsed < 1000:
                            proxy.speed_tier = "fast"
                        elif elapsed < 3000:
                            proxy.speed_tier = "medium"
                        else:
                            proxy.speed_tier = "slow"

                        # Anonymity detection
                        if my_ip in body:
                            proxy.anonymity = "transparent"
                        else:
                            # Check for proxy headers in the response
                            try:
                                data = json.loads(body)
                                origin = data.get("origin", "")
                                if my_ip in origin:
                                    proxy.anonymity = "transparent"
                                elif "," in origin:
                                    proxy.anonymity = "anonymous"
                                else:
                                    proxy.anonymity = "elite"
                            except (json.JSONDecodeError, KeyError):
                                proxy.anonymity = "anonymous"

            elif proxy.protocol in ("socks4", "socks5"):
                try:
                    from aiohttp_socks import ProxyConnector, ProxyType

                    ptype = (
                        ProxyType.SOCKS4
                        if proxy.protocol == "socks4"
                        else ProxyType.SOCKS5
                    )
                    connector = ProxyConnector(
                        proxy_type=ptype,
                        host=proxy.ip,
                        port=proxy.port,
                    )
                    async with aiohttp.ClientSession(connector=connector) as s:
                        async with s.get(
                            self.judge_urls[0],
                            timeout=ClientTimeout(total=self.config.timeout),
                            headers={"User-Agent": get_user_agent()},
                        ) as resp:
                            if resp.status == 200:
                                elapsed = (time.monotonic() - start) * 1000
                                proxy.is_alive = True
                                proxy.speed_ms = elapsed
                                proxy.anonymity = "elite"

                                if elapsed < 1000:
                                    proxy.speed_tier = "fast"
                                elif elapsed < 3000:
                                    proxy.speed_tier = "medium"
                                else:
                                    proxy.speed_tier = "slow"
                except ImportError:
                    pass

        except Exception:
            proxy.is_alive = False

        proxy.last_checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return proxy

    async def _get_my_ip(self) -> str:
        """Get the public IP of the runner."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.ipify.org?format=json",
                    timeout=ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json()
                    return data.get("ip", "0.0.0.0")
        except Exception:
            return "0.0.0.0"

    async def _geolocate_proxy(self, proxy: Proxy) -> Proxy:
        """Add geo-location data to proxy using ip-api (free)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://ip-api.com/json/{proxy.ip}?fields=country,countryCode,city,org,as",
                    timeout=ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        proxy.country = data.get("country", "")
                        proxy.country_code = data.get("countryCode", "")
                        proxy.city = data.get("city", "")
                        proxy.org = data.get("org", "")
                        proxy.asn = data.get("as", "")
        except Exception:
            pass
        return proxy

    async def validate_all(self) -> List[Proxy]:
        """Validate all scraped proxies concurrently."""
        if not self.config.validate:
            console.print(
                "\n[yellow]⏭  Validation skipped (disabled in config)[/yellow]\n"
            )
            self.alive_proxies = self.all_proxies
            return self.all_proxies

        console.print(
            f"\n[bold cyan]🔍 Validating {len(self.all_proxies):,} proxies "
            f"({self.config.max_workers} workers, {self.config.timeout}s timeout)...[/bold cyan]\n"
        )

        my_ip = await self._get_my_ip()
        console.print(f"  [dim]Runner IP: {my_ip}[/dim]\n")

        alive: List[Proxy] = []
        dead_count = 0

        connector = TCPConnector(limit=self.config.max_workers, ssl=False)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TextColumn("[green]✓ {task.fields[alive]}[/green]"),
            TextColumn("[red]✗ {task.fields[dead]}[/red]"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Validating...",
                total=len(self.all_proxies),
                alive=0,
                dead=0,
            )

            async with aiohttp.ClientSession(connector=connector) as session:
                # Process in batches
                batch_size = self.config.max_workers
                for i in range(0, len(self.all_proxies), batch_size):
                    batch = self.all_proxies[i : i + batch_size]
                    tasks = [
                        self._check_proxy(p, session, my_ip) for p in batch
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, Proxy):
                            if result.is_alive:
                                alive.append(result)
                                progress.update(
                                    task, advance=1, alive=len(alive), dead=dead_count
                                )
                            else:
                                dead_count += 1
                                progress.update(
                                    task, advance=1, alive=len(alive), dead=dead_count
                                )
                        else:
                            dead_count += 1
                            progress.update(
                                task, advance=1, alive=len(alive), dead=dead_count
                            )

        # Geo-locate alive proxies (batch of 40 with rate limiting for ip-api)
        if alive:
            console.print(
                f"\n[bold cyan]🌍 Geo-locating {len(alive):,} alive proxies...[/bold cyan]\n"
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                geo_task = progress.add_task(
                    "[cyan]Geo-locating...", total=len(alive)
                )

                # ip-api rate limit: 45 req/min for free
                batch_size = 40
                for i in range(0, len(alive), batch_size):
                    batch = alive[i : i + batch_size]
                    tasks = [self._geolocate_proxy(p) for p in batch]
                    await asyncio.gather(*tasks)
                    progress.advance(geo_task, advance=len(batch))
                    if i + batch_size < len(alive):
                        await asyncio.sleep(62)  # respect rate limit

        self.alive_proxies = alive

        # Update stats
        self.stats["validated_total"] = len(self.all_proxies)
        self.stats["alive_total"] = len(alive)
        self.stats["dead_total"] = dead_count
        self.stats["end_time"] = time.time()

        for p in alive:
            self.stats["by_protocol"][p.protocol] += 1
            if p.country_code:
                self.stats["by_country"][p.country_code] += 1
            self.stats["by_anonymity"][p.anonymity] += 1
            self.stats["by_speed"][p.speed_tier] += 1
            self.stats["by_source"][p.source] += 1

        if alive:
            speeds = [p.speed_ms for p in alive if p.speed_ms > 0]
            if speeds:
                self.stats["avg_speed_ms"] = sum(speeds) / len(speeds)
                fastest = min(alive, key=lambda p: p.speed_ms if p.speed_ms > 0 else float("inf"))
                self.stats["fastest_proxy"] = fastest

        return alive

    # ─── Filtering ─────────────────────────────────

    def apply_filters(self) -> List[Proxy]:
        """Apply country and anonymity filters."""
        filtered = self.alive_proxies

        # Country filter
        if "all" not in [c.lower() for c in self.config.countries]:
            filtered = [
                p for p in filtered if p.country_code in self.config.countries
            ]

        # Anonymity filter
        if "all" not in self.config.anonymity_filter:
            filtered = [
                p for p in filtered if p.anonymity in self.config.anonymity_filter
            ]

        self.alive_proxies = filtered
        return filtered

    # ─── Output ────────────────────────────────────

    def save_results(self):
        """Save proxies in all configured output formats."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        proxies = sorted(self.alive_proxies, key=lambda p: p.speed_ms)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

        console.print(
            f"\n[bold cyan]💾 Saving {len(proxies):,} proxies to '{output_dir}'...[/bold cyan]\n"
        )

        saved_files = []

        # ─── TXT Format ───
        if "txt" in self.config.output_formats:
            # Combined
            fpath = output_dir / "proxies_all.txt"
            with open(fpath, "w") as f:
                for p in proxies:
                    f.write(f"{p.address}\n")
            saved_files.append(fpath)

            # By protocol
            for proto in self.config.protocols:
                proto_proxies = [p for p in proxies if p.protocol == proto]
                if proto_proxies:
                    fpath = output_dir / f"proxies_{proto}.txt"
                    with open(fpath, "w") as f:
                        for p in proto_proxies:
                            f.write(f"{p.address}\n")
                    saved_files.append(fpath)

            # By anonymity
            for anon in ("elite", "anonymous", "transparent"):
                anon_proxies = [p for p in proxies if p.anonymity == anon]
                if anon_proxies:
                    fpath = output_dir / f"proxies_{anon}.txt"
                    with open(fpath, "w") as f:
                        for p in anon_proxies:
                            f.write(f"{p.address}\n")
                    saved_files.append(fpath)

            # By speed
            for tier in ("fast", "medium", "slow"):
                tier_proxies = [p for p in proxies if p.speed_tier == tier]
                if tier_proxies:
                    fpath = output_dir / f"proxies_{tier}.txt"
                    with open(fpath, "w") as f:
                        for p in tier_proxies:
                            f.write(f"{p.address}\n")
                    saved_files.append(fpath)

        # ─── CSV Format ───
        if "csv" in self.config.output_formats:
            fpath = output_dir / "proxies_all.csv"
            with open(fpath, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "ip", "port", "protocol", "address",
                        "country", "country_code", "city",
                        "anonymity", "speed_ms", "speed_tier",
                        "is_alive", "last_checked", "org", "source",
                    ],
                )
                writer.writeheader()
                for p in proxies:
                    writer.writerow(p.to_dict())
            saved_files.append(fpath)

        # ─── JSON Format ───
        if "json" in self.config.output_formats:
            fpath = output_dir / "proxies_all.json"
            data = {
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "total_proxies": len(proxies),
                    "protocols": self.config.protocols,
                    "validation_timeout": self.config.timeout,
                },
                "statistics": {
                    "by_protocol": dict(self.stats["by_protocol"]),
                    "by_country_top20": dict(self.stats["by_country"].most_common(20)),
                    "by_anonymity": dict(self.stats["by_anonymity"]),
                    "by_speed_tier": dict(self.stats["by_speed"]),
                    "average_speed_ms": round(self.stats["avg_speed_ms"], 2),
                },
                "proxies": [p.to_dict() for p in proxies],
            }
            with open(fpath, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            saved_files.append(fpath)

        # ─── Print saved files ───
        file_table = Table(
            title="📁 Output Files",
            box=box.ROUNDED,
            border_style="green",
        )
        file_table.add_column("File", style="bold white")
        file_table.add_column("Size", justify="right", style="cyan")
        file_table.add_column("Proxies", justify="right", style="green")

        for fpath in sorted(saved_files):
            size = fpath.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"

            # Count lines for txt
            count = ""
            if fpath.suffix == ".txt":
                with open(fpath) as f:
                    count = f"{sum(1 for _ in f):,}"
            elif fpath.suffix == ".csv":
                with open(fpath) as f:
                    count = f"{max(0, sum(1 for _ in f) - 1):,}"
            elif fpath.suffix == ".json":
                count = f"{len(proxies):,}"

            file_table.add_row(str(fpath), size_str, count)

        console.print(file_table)

        # ─── Save stats for reporter ───
        stats_path = output_dir / "stats.json"
        stats_export = {
            "sources_total": self.stats["sources_total"],
            "sources_success": self.stats["sources_success"],
            "sources_failed": self.stats["sources_failed"],
            "scraped_total": self.stats["scraped_total"],
            "scraped_unique": self.stats["scraped_unique"],
            "alive_total": self.stats["alive_total"],
            "dead_total": self.stats["dead_total"],
            "by_protocol": dict(self.stats["by_protocol"]),
            "by_country_top20": dict(self.stats["by_country"].most_common(20)),
            "by_anonymity": dict(self.stats["by_anonymity"]),
            "by_speed": dict(self.stats["by_speed"]),
            "avg_speed_ms": round(self.stats["avg_speed_ms"], 2),
            "fastest_proxy": self.stats["fastest_proxy"].to_dict() if self.stats["fastest_proxy"] else None,
            "duration_seconds": round(
                (self.stats["end_time"] or time.time()) - (self.stats["start_time"] or time.time()), 2
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(stats_path, "w") as f:
            json.dump(stats_export, f, indent=2)

    def print_final_summary(self):
        """Print a beautiful final summary."""
        duration = (self.stats["end_time"] or time.time()) - (
            self.stats["start_time"] or time.time()
        )

        console.print()
        summary = Table(
            title="🏆 Final Results",
            box=box.DOUBLE_EDGE,
            border_style="bold cyan",
            show_lines=True,
            width=65,
        )
        summary.add_column("Metric", style="bold white", width=30)
        summary.add_column("Value", style="bold", justify="right", width=30)

        summary.add_row("⏱  Duration", f"{duration:.1f}s")
        summary.add_row("📡 Sources", f"{self.stats['sources_success']}/{self.stats['sources_total']}")
        summary.add_row("🔎 Total Scraped", f"{self.stats['scraped_total']:,}")
        summary.add_row("🧹 Unique", f"{self.stats['scraped_unique']:,}")
        summary.add_row(
            "✅ Alive",
            f"[bold green]{self.stats['alive_total']:,}[/bold green]",
        )
        summary.add_row(
            "❌ Dead",
            f"[red]{self.stats['dead_total']:,}[/red]",
        )

        if self.stats["alive_total"] > 0 and self.stats["scraped_unique"] > 0:
            pct = (self.stats["alive_total"] / self.stats["scraped_unique"]) * 100
            summary.add_row("📈 Success Rate", f"{pct:.1f}%")
        summary.add_row("⚡ Avg Speed", f"{self.stats['avg_speed_ms']:.0f} ms")

        if self.stats["fastest_proxy"]:
            fp = self.stats["fastest_proxy"]
            summary.add_row(
                "🚀 Fastest",
                f"{fp.address} ({fp.speed_ms:.0f}ms)",
            )

        summary.add_row("", "")  # spacer

        # Protocol breakdown
        for proto, count in sorted(self.stats["by_protocol"].items()):
            emoji = {"http": "🌐", "https": "🔒", "socks4": "🧦", "socks5": "🧦"}.get(
                proto, "📌"
            )
            summary.add_row(f"  {emoji} {proto.upper()}", f"{count:,}")

        summary.add_row("", "")  # spacer

        # Anonymity breakdown
        for anon, count in sorted(self.stats["by_anonymity"].items()):
            emoji = {"elite": "🥇", "anonymous": "🥈", "transparent": "🥉"}.get(
                anon, "❔"
            )
            summary.add_row(f"  {emoji} {anon.title()}", f"{count:,}")

        summary.add_row("", "")  # spacer

        # Speed breakdown
        for tier, count in sorted(self.stats["by_speed"].items()):
            emoji = {"fast": "⚡", "medium": "🔶", "slow": "🐢"}.get(tier, "❔")
            summary.add_row(f"  {emoji} {tier.title()}", f"{count:,}")

        console.print(summary)

        # Top countries
        if self.stats["by_country"]:
            country_table = Table(
                title="🌍 Top 15 Countries",
                box=box.ROUNDED,
                border_style="cyan",
            )
            country_table.add_column("#", style="dim", width=4)
            country_table.add_column("Country", style="bold white", width=8)
            country_table.add_column("Count", justify="right", style="green", width=8)
            country_table.add_column("Bar", width=30)

            top = self.stats["by_country"].most_common(15)
            max_count = top[0][1] if top else 1
            for i, (cc, count) in enumerate(top, 1):
                bar_len = int((count / max_count) * 25)
                bar = "█" * bar_len + "░" * (25 - bar_len)
                country_table.add_row(str(i), cc, f"{count:,}", f"[cyan]{bar}[/cyan]")

            console.print(country_table)

        console.print(
            Panel(
                "[bold green]✨ ProxyScraper Pro completed successfully![/bold green]",
                border_style="green",
                box=box.DOUBLE_EDGE,
            )
        )


# ═══════════════════════════════════════════════
#  Main Entry Point
# ═══════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="ProxyScraper Pro")
    parser.add_argument("--protocols", default="http,https,socks4,socks5")
    parser.add_argument("--timeout", default="10")
    parser.add_argument("--workers", default="300")
    parser.add_argument("--validate", default="true")
    parser.add_argument("--countries", default="all")
    parser.add_argument("--anonymity", default="all")
    parser.add_argument("--formats", default="txt,csv,json")
    args = parser.parse_args()

    config = AppConfig.from_args(args)
    scraper = ProxyScraperPro(config)

    # Phase 1: Scrape
    await scraper.scrape_all()

    # Phase 2: Validate
    await scraper.validate_all()

    # Phase 3: Filter
    scraper.apply_filters()

    # Phase 4: Save
    scraper.save_results()

    # Phase 5: Summary
    scraper.print_final_summary()


if __name__ == "__main__":
    asyncio.run(main())
