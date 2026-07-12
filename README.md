# KenXploit

## 🔥 Ultimate AI-Powered Penetration Testing Framework

KenXploit adalah framework penetration testing berbasis AI yang menggunakan LLM lokal/remote untuk melakukan otomatisasi pentest dari fase reconnaissance sampai reporting. Dibangun di atas OpenCode engine dengan custom agent prompt untuk red-team ops.

---

## ✨ Fitur

| Fitur | Deskripsi |
|-------|-----------|
| **AI Agent Pentest** | 5 fase pentest: Recon → Scanning → Exploit → Post-Exploit → Report |
| **OSINT + CSINT** | OSINT deep + Cyber Social Intelligence (social media, email, domain, dorking) |
| **Multi Model** | Support DeepSeek, MiMo V2.5 Pro, dan LLM lokal/remote apapun via OpenAI-compatible API |
| **9 Exploit Scripts** | SQLi, SSRF, SSTI, XXE, JWT, GraphQL, Race Condition, Prototype Pollution, HTTP Smuggling |
| **Auto Reporting** | Generate report PDF/Markdown otomatis untuk CTF, Pentest, OSINT, Vuln Scan, Exploit |
| **Proxy Scraper** | Web dashboard untuk scraping & validasi proxy (FastAPI) |
| **Cloudflare Bypass** | Tools untuk bypass Cloudflare protection |
| **Vulnerable Lab** | Lab lokal Flask untuk latihan (SQLi, SSTI, SSRF, dll) |
| **Knowledge Base** | 13+ modul learning: old-web, modern-web, cloud, mobile, crypto, deser, WAF bypass, dll |

---

## 📋 Requirements

- **OS:** Linux (Ubuntu/Debian/Kali/Arch/Manjaro)
- **Python 3.10+**
- **Node.js 18+** (jika menggunakan OpenCode source)
- **Bun** (opsional, untuk OpenCode source)
- **API Key** untuk LLM (local atau remote)

---

## 🔧 Instalasi

### Cara 1: Auto Install (Recommended)

```bash
# Clone dulu repository ini
git clone https://github.com/kenxfear/kenxploit.git
cd kenxploit

# Jalankan auto installer
chmod +x install.sh
./install.sh
```

Installer akan melakukan:
1. Install Python dependencies (`pip install -r requirements.txt`)
2. Membuat symlink `/usr/local/bin/kenxploit` → binary KenXploit
3. Membuat wrapper script agar bisa dijalankan dari mana saja
4. Verifikasi instalasi

### Cara 2: Manual Install

```bash
# 1. Clone repository
git clone https://github.com/kenxfear/kenxploit.git
cd kenxploit

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Buat symlink biar bisa dipanggil dari terminal manapun
sudo ln -sf "$(pwd)/kenxploit" /usr/local/bin/kenxploit

# 4. Test
kenxploit --help
```

---

## ⚙️ Konfigurasi API Key

KenXploit mendukung **dua mode koneksi LLM**:

### Mode 1: Local LLM (DeepSeek / Model Lokal)

Edit file `config.json`:

```json
{
  "llm": {
    "api_key": "sk-your-local-api-key",
    "base_url": "http://localhost:20128/v1",
    "model": "combo/combo/deepseek-v4-flash",
    "max_tokens": 8192,
    "temperature": 0.3
  },
  "agent": {
    "max_steps": 50,
    "dry_run": false,
    "confirm_destructive": true,
    "output_dir": "reports"
  }
}
```

| Parameter | Description |
|-----------|-------------|
| `api_key` | API key LLM (bisa dummy/local) |
| `base_url` | Base URL OpenAI-compatible API |
| `model` | Model ID (contoh: `combo/combo/deepseek-v4-flash`) |
| `max_tokens` | Maksimum token per response |
| `temperature` | Kreativitas model (0.0 - 2.0) |
| `max_steps` | Maksimum langkah agent |
| `dry_run` | Mode simulasi (tidak eksekusi perintah) |
| `confirm_destructive` | Konfirmasi sebelum perintah destruktif |

### Mode 2: Remote API (Nusa API / OpenAI / Custom)

Edit file `opencode.json`:

```json
{
  "username": "kenxploit",
  "model": "nusa/mimo-v2.5-pro",
  "provider": {
    "nusa": {
      "api": "openai",
      "name": "Nusa API",
      "options": {
        "apiKey": "YOUR_NUSA_API_KEY",
        "baseURL": "https://ai.servernusa.com/v1"
      },
      "models": {
        "mimo-pro": { "id": "nusa/mimo-v2.5-pro" },
        "mimo": { "id": "nusa/mimo-v2.5" }
      }
    }
  }
}
```

### Daftar Model yang Didukung

| Model ID | Provider | Type |
|----------|----------|------|
| `combo/combo/deepseek-v4-flash` | Local/Combo | Chat |
| `combo/mimo/mimo-v2.5` | Local/Combo | Chat |
| `combo/mimo/mimo-v2.5-pro` | Local/Combo | Chat Pro |
| `combo/mimo/mimo-auto` | Local/Combo | Auto |
| `tumpuk/mimo-v2.5` | Tumpuk | Chat |
| `tumpuk/mimo-v2.5-pro` | Tumpuk | Chat Pro |
| `tumpuk/mimo-v2.5-asr` | Tumpuk | ASR/Speech |
| `tumpuk/mimo-v2.5-tts` | Tumpuk | TTS |
| `oc/deepseek-v4-flash-free` | OC | Chat Free |
| `oc/mimo-v2.5-free` | OC | Chat Free |
| `oc/mimo-v2.5-pro` | OC | Chat Pro |

---

## 🚀 Penggunaan

### Basic Commands

```bash
# Lihat help
kenxploit --help

# Jalankan dengan target
kenxploit --target example.com

# Dry run (simulasi, tidak eksekusi)
kenxploit --target example.com --dry-run

# Specify config
kenxploit --config config.json --target example.com
```

### Fase Pentest

KenXploit menjalankan 5 fase pentest secara otomatis:

```
Phase 1: Reconnaissance
  → DNS enumeration, subdomain, WHOIS, port scan, technology detection

Phase 2: Scanning & Enumeration
  → Vulnerability scanning, service enumeration, directory brute force

Phase 3: Exploitation
  → SQLi, XSS, SSRF, LFI, RCE, auth bypass sesuai target

Phase 4: Post-Exploitation
  → Privilege escalation, lateral movement, data exfiltration, persistence

Phase 5: Reporting
  → Generate detailed report (Markdown/PDF)
```

### Contoh Penggunaan

```bash
# Pentest full 5 fase
kenxploit -t https://target.com

# OSINT + CSINT deep
kenxploit -t target.com --mode osint

# Vulnerability scan only
kenxploit -t target.com --mode vuln-scan

# Exploit only
kenxploit -t target.com --mode exploit
```

---

## 📁 Struktur Direktori

```
kenxploit/
├── kenxploit              # Binary utama
├── config.json            # Konfigurasi LLM
├── opencode.json          # Konfigurasi OpenCode + provider
├── requirements.txt       # Python dependencies
├── install.sh             # Auto installer
├── README.md              # Dokumentasi
├── agent/
│   └── pentest.md         # Prompt agent pentest
├── exploits/              # Exploit scripts
│   ├── advanced_sqli.py
│   ├── graphql_exploit.py
│   ├── jwt_exploit.py
│   ├── prototype_pollution.py
│   ├── race_exploit.py
│   ├── smuggler.py
│   ├── ssrf_exploit.py
│   ├── ssti_exploit.py
│   └── xxe_exploit.py
├── labs/
│   └── vuln_lab.py        # Vulnerable lab Flask lokal
├── tools/
│   ├── cf-bypass/         # Cloudflare bypass tools
│   ├── mc-bot-spammer/    # Minecraft bot tools
│   └── proxy-hunt/        # Proxy hunting tools
├── proxy-scraper/         # FastAPI proxy scraper dashboard
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── scraper.py
│   └── validator.py
├── learn/                 # Knowledge base
│   ├── old-web/
│   ├── modern-web/
│   ├── cloud/
│   ├── mobile/
│   ├── crypto/
│   ├── deser/
│   ├── waf-bypass/
│   └── micro-vuln-hunting.md
├── docs/
│   └── osint-capabilities.md
├── reports/               # Generated reports
├── wordlists/             # Wordlists (optional)
└── tmp/                   # Temp files
```

---

## 🔌 Proxy Scraper Dashboard

KenXploit includes a web-based proxy scraper dashboard:

```bash
cd proxy-scraper
pip install -r requirements.txt  # FastAPI, uvicorn, etc
python main.py
# → Dashboard: http://localhost:8080
```

Features:
- Scrape proxies from multiple sources
- Validate & test proxies
- Export to TXT/JSON
- Real-time logs via WebSocket
- Auth-protected dashboard

---

## 🔬 Vulnerable Lab

Latihan pentest lokal tanpa risiko:

```bash
cd labs
python vuln_lab.py
# → http://localhost:5000
```

Includes: SQLi, SSTI, SSRF, Command Injection, File Upload, XSS, Path Traversal

---

## ⚠️ Disclaimer

**KenXploit is for authorized security testing and educational purposes only.**

- Hanya gunakan pada target yang Anda miliki atau memiliki izin tertulis
- Penggunaan ilegal adalah tanggung jawab pengguna sepenuhnya
- Penulis tidak bertanggung jawab atas penyalahgunaan
- Compliance dengan UU ITE dan hukum yang berlaku

---

## 📝 License

MIT License — Pendidikan dan research hanya.

---

## 👤 Author

**Ken Xfear** — Red Team / Pentester

---

## 🌟 Support

- ⭐ Star repository ini jika bermanfaat
- 🐛 Report issues di GitHub Issues
- 🔄 Pull requests welcome
