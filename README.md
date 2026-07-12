# KenXploit

## AI-Powered Penetration Testing Framework

KenXploit adalah framework penetration testing berbasis AI yang menggunakan LLM lokal/remote untuk melakukan otomatisasi pentest dari fase reconnaissance sampai reporting. Dibangun di atas OpenCode engine dengan custom agent prompt untuk operasi red-team.

---

## Fitur

| Fitur | Deskripsi |
|-------|-----------|
| **AI Agent Pentest** | 5 fase pentest: Recon, Scanning, Exploit, Post-Exploit, Report |
| **OSINT dan CSINT** | OSINT deep dan Cyber Social Intelligence (social media, email, domain, dorking) |
| **Multi Model** | Support DeepSeek, MiMo V2.5 Pro, dan LLM lokal/remote apapun via OpenAI-compatible API |
| **9 Exploit Scripts** | SQLi, SSRF, SSTI, XXE, JWT, GraphQL, Race Condition, Prototype Pollution, HTTP Smuggling |
| **Auto Reporting** | Generate report PDF/Markdown otomatis untuk CTF, Pentest, OSINT, Vuln Scan, Exploit |
| **Proxy Scraper** | Web dashboard untuk scraping dan validasi proxy (FastAPI) |
| **Cloudflare Bypass** | Tools untuk bypass Cloudflare protection |
| **Vulnerable Lab** | Lab lokal Flask untuk latihan (SQLi, SSTI, SSRF, dan lainnya) |
| **Knowledge Base** | 13+ modul learning: old-web, modern-web, cloud, mobile, crypto, deser, WAF bypass, dan lainnya |

---

## Requirements

- **OS:** Linux (Ubuntu/Debian/Kali/Arch/Manjaro)
- **Python 3.10+**
- **Node.js 18+** (jika menggunakan OpenCode source)
- **Bun** (opsional, untuk OpenCode source)
- **API Key** untuk LLM (local atau remote)

---

## Instalasi

### Cara 1: Auto Install (Recommended)

```bash
# Clone repository
git clone https://github.com/kenxfear/kenxploit.git
cd kenxploit

# Jalankan auto installer
chmod +x install.sh
./install.sh
```

Installer akan melakukan:
1. Install Python dependencies (`pip install -r requirements.txt`)
2. Membuat symlink `/usr/local/bin/kenxploit` menuju binary KenXploit
3. Membuat wrapper script agar bisa dijalankan dari mana saja
4. Verifikasi instalasi

### Cara 2: Manual Install

```bash
# 1. Clone repository
git clone https://github.com/kenxfear/kenxploit.git
cd kenxploit

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Buat symlink agar bisa dipanggil dari terminal manapun
sudo ln -sf "$(pwd)/kenxploit" /usr/local/bin/kenxploit

# 4. Verifikasi
kenxploit --help
```

---

## Konfigurasi API Key

KenXploit mendukung dua mode koneksi LLM:

### Mode 1: Local LLM (DeepSeek / Model Lokal)

Edit file `config.json`:

```json
{
  "llm": {
    "api_key": "YOUR_API_KEY_HERE",
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

| Parameter | Keterangan |
|-----------|------------|
| `api_key` | API key LLM (bisa dummy untuk local) |
| `base_url` | Base URL OpenAI-compatible API |
| `model` | Model ID (contoh: `combo/combo/deepseek-v4-flash`) |
| `max_tokens` | Maksimum token per response |
| `temperature` | Kreativitas model (0.0 - 2.0) |
| `max_steps` | Maksimum langkah agent |
| `dry_run` | Mode simulasi (tidak eksekusi perintah) |
| `confirm_destructive` | Konfirmasi sebelum perintah destruktif |

### Mode 2: Remote API (OpenAI-compatible)

Edit file `opencode.json`:

```json
{
  "username": "kenxploit",
  "model": "provider/model-name",
  "provider": {
    "custom": {
      "api": "openai",
      "name": "Custom API",
      "options": {
        "apiKey": "YOUR_API_KEY",
        "baseURL": "https://your-api-endpoint.com/v1"
      },
      "models": {
        "model-1": { "id": "provider/model-1" },
        "model-2": { "id": "provider/model-2" }
      }
    }
  }
}
```

### Rekomendasi Model

KenXploit bekerja optimal dengan model yang memiliki weak safety alignment. Berikut rekomendasi model:

| Model | Provider | Keterangan |
|-------|----------|------------|
| **MiMo V2.5 Pro** | Combo/Tumpuk/OC | Best for pentest, weak alignment |
| **MiMo V2.5** | Combo/Tumpuk/OC | Lightweight, fast |
| **DeepSeek V4 Flash** | Combo/OC | Fast inference, good for automation |
| **Big Pickle** | OC | Uncensored, strong for red-team |
| **North Mini Code** | OC | Code-focused, minimal filtering |

Model lain yang kompatibel (OpenAI-compatible API):
- Any model with weak safety alignment
- Local models via Ollama, LM Studio, text-generation-webui
- Self-hosted models tanpa content filter

---

## Penggunaan

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
  DNS enumeration, subdomain, WHOIS, port scan, technology detection

Phase 2: Scanning & Enumeration
  Vulnerability scanning, service enumeration, directory brute force

Phase 3: Exploitation
  SQLi, XSS, SSRF, LFI, RCE, auth bypass sesuai target

Phase 4: Post-Exploitation
  Privilege escalation, lateral movement, data exfiltration, persistence

Phase 5: Reporting
  Generate detailed report (Markdown/PDF)
```

### Contoh Penggunaan

```bash
# Pentest full 5 fase
kenxploit -t https://target.com

# OSINT dan CSINT deep
kenxploit -t target.com --mode osint

# Vulnerability scan only
kenxploit -t target.com --mode vuln-scan

# Exploit only
kenxploit -t target.com --mode exploit
```

---

## Struktur Direktori

```
kenxploit/
├── kenxploit              # Binary utama
├── config.json            # Konfigurasi LLM
├── opencode.json          # Konfigurasi OpenCode dan provider
├── requirements.txt       # Python dependencies
├── install.sh             # Auto installer
├── uninstall.sh           # Uninstaller
├── README.md              # Dokumentasi
├── .gitignore             # Git ignore rules
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
│   └── proxy-hunt/        # Proxy hunting tools
├── proxy-scraper/         # FastAPI proxy scraper dashboard
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── scraper.py
│   └── validator.py
├── learn/                 # Knowledge base
│   ├── ad/                # Active Directory attacks
│   ├── cloud/             # Cloud exploitation
│   ├── crypto/            # Cryptography attacks
│   ├── deser/             # Deserialization attacks
│   ├── exploit/           # Exploit techniques (no domain)
│   ├── mobile/            # Mobile pentesting
│   ├── modern-web/        # Modern web stack exploits
│   ├── old-web/           # Legacy web exploits
│   └── waf-bypass/        # WAF bypass techniques
├── .config/
│   ├── learned.md         # Learning database
│   └── learn/             # Reference materials
└── Report/                # Generated reports (gitignored)
    ├── exploit/           # Exploit reports
    └── osint/             # OSINT reports
```

---

## Proxy Scraper Dashboard

KenXploit menyertakan web-based proxy scraper dashboard:

```bash
cd proxy-scraper
pip install -r requirements.txt
python main.py
# Dashboard tersedia di http://localhost:8080
```

Fitur:
- Scrape proxy dari multiple sources
- Validasi dan test proxy
- Export ke TXT/JSON
- Real-time logs via WebSocket
- Dashboard terproteksi autentikasi

---

## Vulnerable Lab

Latihan pentest lokal tanpa risiko:

```bash
cd labs
python vuln_lab.py
# Tersedia di http://localhost:5000
```

Mencakup: SQLi, SSTI, SSRF, Command Injection, File Upload, XSS, Path Traversal

---

## Struktur Penyimpanan Data

KenXploit menyimpan data di dalam folder instalasi:

| Lokasi | Fungsi |
|--------|--------|
| `Report/exploit/` | Laporan hasil exploit dan vulnerability |
| `Report/osint/` | Laporan hasil OSINT dan intelligence |
| `learn/exploit/` | Teknik exploit (tanpa domain/target) |
| `.config/learned.md` | Log umum teknik yang berhasil |
| `.config/learn/` | Reference materials dan CVE database |

**Penting:** Folder `learn/` hanya menyimpan teknik exploit, bukan identitas target. Domain dan informasi target spesifik tidak disimpan di folder learn.

---

## Disclaimer

**KenXploit hanya untuk security testing yang terotorisasi dan tujuan edukasi.**

- Hanya gunakan pada target yang Anda miliki atau memiliki izin tertulis
- Penggunaan ilegal adalah tanggung jawab pengguna sepenuhnya
- Penulis tidak bertanggung jawab atas penyalahgunaan
- Harus compliance dengan UU ITE dan hukum yang berlaku

---

## License

MIT License - Untuk pendidikan dan research saja.

---

## Author

**Ken Xfear** - Red Team / Pentester

---

## Support

- Star repository ini jika bermanfaat
- Report issues di GitHub Issues
- Pull requests welcome
