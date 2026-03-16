"""
╔══════════════════════════════════════════════════════════╗
║           ProxyScraper Pro — Configuration               ║
║         Premium Proxy Scraping & Validation Tool         ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


# ═══════════════════════════════════════════════
#  Proxy Sources Registry
# ═══════════════════════════════════════════════

PROXY_SOURCES: Dict[str, List[Dict]] = {
    "http": [
        {
            "name": "ProxyScrape HTTP",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "type": "plain",
        },
        {
            "name": "TheSpeedX HTTP",
            "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "type": "plain",
        },
        {
            "name": "ShiftyTR HTTP",
            "url": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "type": "plain",
        },
        {
            "name": "MoNoSplit HTTP",
            "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "type": "plain",
        },
        {
            "name": "Clarketm HTTP",
            "url": "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "type": "plain",
        },
        {
            "name": "RoostKid HTTP",
            "url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "type": "plain",
        },
        {
            "name": "Proxy-List HTTP",
            "url": "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
            "type": "plain",
        },
        {
            "name": "ProxyList-to HTTP",
            "url": "https://www.proxy-list.download/api/v1/get?type=http",
            "type": "plain",
        },
        {
            "name": "OpenProxyList HTTP",
            "url": "https://api.openproxylist.xyz/http.txt",
            "type": "plain",
        },
        {
            "name": "Sunny9577 HTTP",
            "url": "https://sunny9577.github.io/proxy-scraper/proxies.txt",
            "type": "plain",
        },
    ],
    "https": [
        {
            "name": "ProxyScrape HTTPS",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all",
            "type": "plain",
        },
        {
            "name": "MoNoSplit HTTPS",
            "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
            "type": "plain",
        },
        {
            "name": "ProxyList-to HTTPS",
            "url": "https://www.proxy-list.download/api/v1/get?type=https",
            "type": "plain",
        },
    ],
    "socks4": [
        {
            "name": "ProxyScrape SOCKS4",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all",
            "type": "plain",
        },
        {
            "name": "TheSpeedX SOCKS4",
            "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "type": "plain",
        },
        {
            "name": "ShiftyTR SOCKS4",
            "url": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
            "type": "plain",
        },
        {
            "name": "MoNoSplit SOCKS4",
            "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "type": "plain",
        },
        {
            "name": "MuRongPIG SOCKS4",
            "url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
            "type": "plain",
        },
        {
            "name": "ProxyList-to SOCKS4",
            "url": "https://www.proxy-list.download/api/v1/get?type=socks4",
            "type": "plain",
        },
    ],
    "socks5": [
        {
            "name": "ProxyScrape SOCKS5",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
            "type": "plain",
        },
        {
            "name": "TheSpeedX SOCKS5",
            "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "type": "plain",
        },
        {
            "name": "ShiftyTR SOCKS5",
            "url": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
            "type": "plain",
        },
        {
            "name": "MoNoSplit SOCKS5",
            "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "type": "plain",
        },
        {
            "name": "ProxyList-to SOCKS5",
            "url": "https://www.proxy-list.download/api/v1/get?type=socks5",
            "type": "plain",
        },
        {
            "name": "HookZOf SOCKS5",
            "url": "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "type": "plain",
        },
    ],
}


# ═══════════════════════════════════════════════
#  Proxy Data Model
# ═══════════════════════════════════════════════

@dataclass
class Proxy:
    ip: str
    port: int
    protocol: str
    source: str = ""
    country: str = ""
    country_code: str = ""
    city: str = ""
    anonymity: str = "unknown"     # transparent, anonymous, elite
    speed_ms: float = 0.0
    speed_tier: str = "unknown"    # fast, medium, slow
    is_alive: bool = False
    last_checked: str = ""
    org: str = ""
    asn: str = ""

    @property
    def address(self) -> str:
        return f"{self.ip}:{self.port}"

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port}"

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol,
            "address": self.address,
            "country": self.country,
            "country_code": self.country_code,
            "city": self.city,
            "anonymity": self.anonymity,
            "speed_ms": round(self.speed_ms, 2),
            "speed_tier": self.speed_tier,
            "is_alive": self.is_alive,
            "last_checked": self.last_checked,
            "org": self.org,
            "source": self.source,
        }

    def __hash__(self):
        return hash((self.ip, self.port, self.protocol))

    def __eq__(self, other):
        return (self.ip, self.port, self.protocol) == (other.ip, other.port, other.protocol)


# ═══════════════════════════════════════════════
#  Configuration Loader
# ═══════════════════════════════════════════════

@dataclass
class AppConfig:
    protocols: List[str] = field(default_factory=lambda: ["http", "https", "socks4", "socks5"])
    timeout: int = 10
    max_workers: int = 300
    validate: bool = True
    countries: List[str] = field(default_factory=lambda: ["all"])
    anonymity_filter: List[str] = field(default_factory=lambda: ["all"])
    output_formats: List[str] = field(default_factory=lambda: ["txt", "csv", "json"])
    output_dir: str = "output"

    @classmethod
    def from_args(cls, args) -> "AppConfig":
        cfg = cls()
        if args.protocols:
            cfg.protocols = [p.strip().lower() for p in args.protocols.split(",")]
        if args.timeout:
            cfg.timeout = int(args.timeout)
        if args.workers:
            cfg.max_workers = int(args.workers)
        if args.validate:
            cfg.validate = args.validate.lower() in ("true", "1", "yes")
        if args.countries:
            cfg.countries = [c.strip().upper() for c in args.countries.split(",")]
        if args.anonymity:
            cfg.anonymity_filter = [a.strip().lower() for a in args.anonymity.split(",")]
        if args.formats:
            cfg.output_formats = [f.strip().lower() for f in args.formats.split(",")]
        return cfg


# ═══════════════════════════════════════════════
#  ASCII Art / Branding
# ═══════════════════════════════════════════════

BANNER = r"""
[bold cyan]
  ╔═══════════════════════════════════════════════════════════════════╗
  ║                                                                   ║
  ║   ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗                     ║
  ║   ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝                    ║
  ║   ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝                     ║
  ║   ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝                      ║
  ║   ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║                       ║
  ║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝                      ║
  ║                                                                   ║
  ║   ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗        ║
  ║   ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗       ║
  ║   ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝       ║
  ║   ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗       ║
  ║   ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║       ║
  ║   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝    ║
  ║                                                                   ║
  ║   ⚡ P R O   E D I T I O N                           v3.0.0 ⚡   ║
  ║                                                                   ║
  ╚═══════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""
