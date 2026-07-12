# MC Bot Spammer

Minecraft Java Server Bot Flooder dengan proxy support, chat spam, dan Microsoft auth.

## Fitur

- **Multi-threaded bot joining** - flood server dengan banyak bot sekaligus
- **Proxy support** - HTTP, SOCKS4, SOCKS5
- **Proxy scraper** - auto scrape proxy dari 20+ sumber publik
- **Proxy validator** - verifikasi proxy hidup sebelum dipake
- **Chat spam** - spam pesan di chat server
- **Cracked & Premium mode** - support cracked server dan premium (dengan MS auth)
- **Microsoft OAuth** - Device Code Flow untuk dapat Minecraft token
- **Auto reconnect** - bot otomatis reconnect kalau di-kick
- **Keep alive** - bot stay connected dengan handle keep alive packets

## Install

```bash
# Dependencies
pip install requests PySocks

# Clone/Download files
cd mc-bot-spammer
```

## Penggunaan

### 1. Cek Server Status

```bash
python bot_spammer.py -t mc.example.com --status
```

### 2. Basic Bot Spam (Cracked Server)

```bash
# 10 bot, durasi 60 detik
python bot_spammer.py -t mc.example.com -n 10

# 50 bot dengan proxy
python bot_spammer.py -t mc.example.com -n 50 --scrape-proxy

# 100 bot dengan chat spam
python bot_spammer.py -t mc.example.com -n 100 --chat "Hello!" "GG" "Bot Army!"
```

### 3. Dengan Proxy File

```bash
# Format proxy file:
# socks5://1.2.3.4:1080
# http://5.6.7.8:8080
# 9.10.11.12:3128

python bot_spammer.py -t mc.example.com -n 50 --proxy-file proxies.txt
```

### 4. Auto Scrape Proxy

```bash
python bot_spammer.py -t mc.example.com -n 50 --scrape-proxy
```

### 5. Premium Server (Perlu Token)

```bash
# Step 1: Dapatkan token
python bot_spammer.py -t mc.example.com --auth

# Step 2: Jalankan bot dengan token
python bot_spammer.py -t mc.example.com -n 10 --premium --token-file mc_token.json
```

### 6. Chat Spam

```bash
# Chat langsung
python bot_spammer.py -t mc.example.com -n 20 --chat "Hello {player}!" "GG" "Count: {count}"

# Chat dari file
python bot_spammer.py -t mc.example.com -n 20 --chat-file messages.txt
```

### 7. Proxy Scraper Standalone

```bash
python proxy_scraper.py
# Output: proxies_raw.txt, proxies_valid.txt
```

### 8. MC Auth Standalone

```bash
python mc_auth.py
# Output: mc_token.json
```

## Variables di Chat

| Variable | Deskripsi |
|----------|-----------|
| `{player}` | Nama bot yang kirim |
| `{random}` | Random string 4 char |
| `{count}` | Jumlah bot connected |

## Format Files

### proxy.txt
```
socks5://1.2.3.4:1080
http://5.6.7.8:8080
9.10.11.12:3128
socks4://13.14.15.16:1080
```

### token.txt (Premium mode)
```
username:access_token:uuid
Bot01:d4f5g6h7...:uuid-here
```

### names.txt
```
Bot_Alpha
Bot_Beta
Bot_Gamma
```

## MC Version Support

| Version | Protocol | Status |
|---------|----------|--------|
| 1.8.x | 47 | ✅ |
| 1.12.2 | 340 | ✅ |
| 1.16.5 | 754 | ✅ |
| 1.18.2 | 758 | ✅ |
| 1.19.4 | 762 | ✅ |
| 1.20.4 | 765 | ✅ |
| 1.21.4 | 769 | ✅ |

## Tools Individual

| File | Fungsi |
|------|--------|
| `bot_spammer.py` | Main bot spammer tool |
| `mc_protocol.py` | Minecraft protocol implementation |
| `mc_auth.py` | Microsoft OAuth authentication |
| `proxy_scraper.py` | Proxy scraper & validator |

## Disclaimer

Tool ini untuk **edukasi dan testing keamanan**. Penggunaan untuk menyerang server tanpa izin adalah ilegal dan melanggar ToS Minecraft.

Dikembangkan oleh **KenxPentest**
