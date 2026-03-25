# 🔥 ProxyScraper Pro

<div align="center">

```
  ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
  ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
  ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝
  ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝
  ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝
  S C R A P E R   P R O   v3.0
```

**A premium, automated proxy scraping & validation pipeline powered by GitHub Actions.**

[![Scrape Proxies](https://img.shields.io/badge/⚡_Run-Scraper-blue?style=for-the-badge)](../../actions/workflows/proxy-scraper.yml)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Multi-Protocol** | HTTP, HTTPS, SOCKS4, SOCKS5 |
| 📡 **40+ Sources** | Scrapes from 40+ public proxy providers |
| ⚡ **Async Validation** | 300 concurrent workers, sub-10s checks |
| 🎭 **Anonymity Detection** | Elite, Anonymous, Transparent classification |
| 🌍 **Geo-Location** | Country, city, ISP tagging for every proxy |
| 🏎️ **Speed Testing** | Fast / Medium / Slow tier classification |
| 📊 **Rich Reports** | GitHub Summary, CSV, JSON, TXT outputs |
| ⏰ **Auto-Schedule** | Runs every 6 hours automatically |
| 🎛️ **Full Control** | Manual trigger with custom parameters |
| 🆓 **100% Free** | Runs on GitHub Actions — no server needed |

---

## 🚀 Quick Start

### 1. Fork this repository

### 2. Enable GitHub Actions
Go to **Settings → Actions → General → Allow all actions**

### 3. Run manually
Go to **Actions → 🔥 ProxyScraper Pro → Run workflow**

### 4. Get your proxies
Download from **Actions → Latest Run → Artifacts**

Or find them auto-committed in the `/output` directory.

---

## 🎛️ Manual Trigger Options

| Parameter | Default | Options |
|-----------|---------|---------|
| `protocols` | `http,https,socks4,socks5` | Any combination |
| `max_timeout` | `10` | Seconds (1-30) |
| `max_workers` | `300` | Concurrent threads (50-500) |
| `validate` | `true` | `true` / `false` |
| `country_filter` | `all` | ISO codes: `US,GB,DE` |
| `anonymity_filter` | `all` | `elite,anonymous,transparent` |
| `output_formats` | `txt,csv,json` | Any combination |

---

## 📁 Output Files

```
output/
├── proxies_all.txt          # All alive proxies (ip:port)
├── proxies_all.csv          # Full data with geo & speed
├── proxies_all.json         # Structured JSON with metadata
├── proxies_http.txt         # HTTP only
├── proxies_https.txt        # HTTPS only
├── proxies_socks4.txt       # SOCKS4 only
├── proxies_socks5.txt       # SOCKS5 only
├── proxies_elite.txt        # Elite anonymity only
├── proxies_anonymous.txt    # Anonymous only
├── proxies_fast.txt         # Fast proxies (< 1s)
├── proxies_medium.txt       # Medium speed (1-3s)
├── stats.json               # Run statistics
└── github_summary.md        # Rich GitHub summary
```

---

## 📊 JSON Output Format

```json
{
  "metadata": {
    "generated_at": "2024-01-15T12:00:00+00:00",
    "total_proxies": 5000,
    "protocols": ["http", "https", "socks4", "socks5"]
  },
  "statistics": {
    "by_protocol": {"http": 2000, "socks5": 1500},
    "by_country_top20": {"US": 800, "DE": 400},
    "by_anonymity": {"elite": 3000, "anonymous": 1500},
    "average_speed_ms": 1250.5
  },
  "proxies": [
    {
      "ip": "1.2.3.4",
      "port": 8080,
      "protocol": "http",
      "country": "United States",
      "country_code": "US",
      "city": "New York",
      "anonymity": "elite",
      "speed_ms": 245.5,
      "speed_tier": "fast",
      "is_alive": true,
      "org": "DigitalOcean LLC"
    }
  ]
}
```

---

## 🛠️ Local Usage

```bash
# Clone
git clone https://github.com/YOU/proxy-scraper-pro.git
cd proxy-scraper-pro

# Install
pip install -r requirements.txt

# Run full scrape
python src/scraper.py

# Custom run
python src/scraper.py \
  --protocols "http,socks5" \
  --timeout 5 \
  --workers 500 \
  --countries "US,GB,DE"

# Validate existing list
python src/validator.py proxies.txt --protocol http --timeout 8
```

---

<!-- PROXY-STATS-START -->
## 📊 Latest Proxy Stats

| Metric | Value |
|--------|-------|
| ✅ Alive Proxies | **1,209** |
| 🌐 HTTP | 493 |
| 🔒 HTTPS | 0 |
| 🧦 SOCKS4 | 233 |
| 🧦 SOCKS5 | 483 |
| ⚡ Avg Speed | 3373ms |
| 🕐 Last Updated | 2026-03-25 03:16 UTC |

<!-- PROXY-STATS-END -->

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by ProxyScraper Pro

</div>
