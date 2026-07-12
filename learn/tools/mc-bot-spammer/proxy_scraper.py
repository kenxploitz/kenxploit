#!/usr/bin/env python3
"""
Proxy Scraper & Validator
Scrape proxy dari berbagai sumber dan validasi apakah hidup
"""

import requests
import socks
import socket
import threading
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProxyScraper:
    """Scrape dan validasi proxy dari berbagai sumber publik"""
    
    SOURCES = {
        "http": [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/http.txt",
        ],
        "socks4": [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
            "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks4.txt",
        ],
        "socks5": [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
            "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        ]
    }
    
    def __init__(self, timeout=5, max_threads=50):
        self.timeout = timeout
        self.max_threads = max_threads
        self.proxies = {"http": [], "socks4": [], "socks5": []}
        self.valid_proxies = []
        self.lock = threading.Lock()
    
    def scrape_all(self, proxy_types=None):
        """Scrape proxy dari semua sumber"""
        if proxy_types is None:
            proxy_types = ["http", "socks4", "socks5"]
        
        print(f"[*] Scraping proxy dari {sum(len(self.SOURCES[t]) for t in proxy_types)} sumber...")
        
        for ptype in proxy_types:
            sources = self.SOURCES.get(ptype, [])
            for url in sources:
                try:
                    resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        proxies = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}', resp.text)
                        with self.lock:
                            for p in proxies:
                                if p not in self.proxies[ptype]:
                                    self.proxies[ptype].append(p)
                        print(f"  [+] {url.split('/')[-1]}: {len(proxies)} proxy")
                except Exception as e:
                    print(f"  [-] Error: {url.split('/')[-1]}: {e}")
        
        total = sum(len(self.proxies[t]) for t in proxy_types)
        print(f"[*] Total proxy ditemukan: {total}")
        return self.proxies
    
    def validate_proxy(self, proxy, proxy_type="http"):
        """Validasi satu proxy apakah hidup"""
        try:
            if proxy_type == "http":
                proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                resp = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=self.timeout)
                return resp.status_code == 200
            else:
                # SOCKS proxy
                sock_type = socks.SOCKS4 if proxy_type == "socks4" else socks.SOCKS5
                host, port = proxy.split(":")
                s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
                s.set_proxy(sock_type, host, int(port))
                s.settimeout(self.timeout)
                s.connect(("httpbin.org", 80))
                s.send(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
                data = s.recv(1024)
                s.close()
                return b"200 OK" in data
        except:
            return False
    
    def validate_all(self, proxy_types=None, test_url="mc.hypixel.net", test_port=25565):
        """Validasi semua proxy - test koneksi ke MC server"""
        if proxy_types is None:
            proxy_types = list(self.proxies.keys())
        
        all_proxies = []
        for ptype in proxy_types:
            for p in self.proxies[ptype]:
                all_proxies.append((p, ptype))
        
        print(f"[*] Validating {len(all_proxies)} proxy (timeout: {self.timeout}s)...")
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {}
            for proxy, ptype in all_proxies:
                future = executor.submit(self._validate_mc_proxy, proxy, ptype, test_url, test_port)
                futures[future] = (proxy, ptype)
            
            done = 0
            for future in as_completed(futures):
                done += 1
                proxy, ptype = futures[future]
                try:
                    if future.result():
                        with self.lock:
                            self.valid_proxies.append({"proxy": proxy, "type": ptype})
                        print(f"  [+] VALID ({done}/{len(all_proxies)}): {ptype}://{proxy}")
                except:
                    pass
                
                if done % 100 == 0:
                    print(f"  [*] Progress: {done}/{len(all_proxies)} ({len(self.valid_proxies)} valid)")
        
        print(f"[*] Valid proxy: {len(self.valid_proxies)}/{len(all_proxies)}")
        return self.valid_proxies
    
    def _validate_mc_proxy(self, proxy, proxy_type, host, port):
        """Validasi proxy dengan koneksi ke Minecraft server"""
        try:
            if proxy_type == "http":
                # HTTP CONNECT tunnel
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                p_host, p_port = proxy.split(":")
                s.connect((p_host, int(p_port)))
                
                connect_req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
                s.send(connect_req.encode())
                resp = s.recv(4096)
                s.close()
                return b"200" in resp
            else:
                # SOCKS proxy
                sock_type = socks.SOCKS4 if proxy_type == "socks4" else socks.SOCKS5
                p_host, p_port = proxy.split(":")
                s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
                s.set_proxy(sock_type, p_host, int(p_port))
                s.settimeout(self.timeout)
                s.connect((host, port))
                s.close()
                return True
        except:
            return False
    
    def save(self, filepath="proxies.txt", proxy_type=None):
        """Simpan proxy ke file"""
        with open(filepath, "w") as f:
            if proxy_type:
                for p in self.proxies.get(proxy_type, []):
                    f.write(f"{p}\n")
            else:
                for ptype, proxies in self.proxies.items():
                    for p in proxies:
                        f.write(f"{ptype}://{p}\n")
        print(f"[*] Proxy disimpan ke {filepath}")
    
    def save_valid(self, filepath="valid_proxies.txt"):
        """Simpan proxy valid ke file"""
        with open(filepath, "w") as f:
            for p in self.valid_proxies:
                f.write(f"{p['type']}://{p['proxy']}\n")
        print(f"[*] Valid proxy disimpan ke {filepath}")
    
    def load(self, filepath):
        """Load proxy dari file"""
        proxies = []
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if "://" in line:
                        ptype, proxy = line.split("://", 1)
                        proxies.append({"proxy": proxy, "type": ptype})
                    elif ":" in line:
                        proxies.append({"proxy": line, "type": "http"})
            print(f"[*] Loaded {len(proxies)} proxy dari {filepath}")
        except Exception as e:
            print(f"[-] Error load proxy: {e}")
        return proxies


if __name__ == "__main__":
    scraper = ProxyScraper(timeout=5, max_threads=100)
    
    # Scrape
    scraper.scrape_all()
    
    # Save raw
    scraper.save("/home/keandra/ai-pentest/tools/mc-bot-spammer/proxies_raw.txt")
    
    # Validate
    scraper.validate_all()
    
    # Save valid
    scraper.save_valid("/home/keandra/ai-pentest/tools/mc-bot-spammer/proxies_valid.txt")
