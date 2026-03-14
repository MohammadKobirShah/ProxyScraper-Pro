#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║       ProxyScraper Pro — Standalone Proxy Validator       ║
║    Use this to re-validate existing proxy lists           ║
╚══════════════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import json
import time
import sys
import os
from pathlib import Path

import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    TimeRemainingColumn, MofNCompleteColumn, TaskProgressColumn,
)
from rich import box
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Proxy

console = Console()


class ProxyValidator:
    """Standalone validator that checks proxy lists from files."""

    def __init__(self, timeout: int = 10, workers: int = 300):
        self.timeout = timeout
        self.workers = workers
        self.judge_url = "http://httpbin.org/ip"

    def load_proxies(self, filepath: str, protocol: str = "http") -> list[Proxy]:
        """Load proxies from a plain text file (ip:port per line)."""
        proxies = []
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        try:
                            proxies.append(Proxy(
                                ip=parts[0],
                                port=int(parts[1]),
                                protocol=protocol,
                            ))
                        except ValueError:
                            continue
        return proxies

    async def check_one(
        self, proxy: Proxy, session: aiohttp.ClientSession
    ) -> Proxy:
        """Check a single proxy."""
        start = time.monotonic()
        try:
            proxy_url = f"http://{proxy.ip}:{proxy.port}"
            async with session.get(
                self.judge_url,
                proxy=proxy_url,
                timeout=ClientTimeout(total=self.timeout),
            ) as resp:
                if resp.status == 200:
                    proxy.is_alive = True
                    proxy.speed_ms = (time.monotonic() - start) * 1000
                    if proxy.speed_ms < 1000:
                        proxy.speed_tier = "fast"
                    elif proxy.speed_ms < 3000:
                        proxy.speed_tier = "medium"
                    else:
                        proxy.speed_tier = "slow"
        except Exception:
            proxy.is_alive = False
        return proxy

    async def validate(self, proxies: list[Proxy]) -> list[Proxy]:
        """Validate a list of proxies."""
        alive = []
        dead = 0

        connector = TCPConnector(limit=self.workers, ssl=False)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, complete_style="green"),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TextColumn("[green]✓ {task.fields[alive]}[/green]"),
            TextColumn("[red]✗ {task.fields[dead]}[/red]"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Validating...", total=len(proxies), alive=0, dead=0
            )

            async with aiohttp.ClientSession(connector=connector) as session:
                batch_size = self.workers
                for i in range(0, len(proxies), batch_size):
                    batch = proxies[i : i + batch_size]
                    tasks = [self.check_one(p, session) for p in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, Proxy) and result.is_alive:
                            alive.append(result)
                            progress.update(task, advance=1, alive=len(alive), dead=dead)
                        else:
                            dead += 1
                            progress.update(task, advance=1, alive=len(alive), dead=dead)

        return sorted(alive, key=lambda p: p.speed_ms)


async def main():
    parser = argparse.ArgumentParser(description="Standalone Proxy Validator")
    parser.add_argument("file", help="Path to proxy list (ip:port per line)")
    parser.add_argument("--protocol", default="http", choices=["http", "https", "socks4", "socks5"])
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--workers", type=int, default=300)
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args()

    validator = ProxyValidator(timeout=args.timeout, workers=args.workers)

    console.print(f"\n[bold cyan]📂 Loading proxies from: {args.file}[/bold cyan]")
    proxies = validator.load_proxies(args.file, args.protocol)
    console.print(f"[bold]   Loaded: {len(proxies):,} proxies[/bold]\n")

    alive = await validator.validate(proxies)

    console.print(f"\n[bold green]✅ Alive: {len(alive):,}[/bold green]")
    console.print(f"[bold red]❌ Dead: {len(proxies) - len(alive):,}[/bold red]\n")

    output_file = args.output or args.file.replace(".txt", "_alive.txt")
    with open(output_file, "w") as f:
        for p in alive:
            f.write(f"{p.address}\n")
    console.print(f"[bold]💾 Saved to: {output_file}[/bold]\n")


if __name__ == "__main__":
    asyncio.run(main())
