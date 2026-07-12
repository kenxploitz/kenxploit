"""
KenXploit Proxy Scraper — Async Scraper Engine v2
Beast mode: 346+ sources, concurrent scraping, auto-detect protocol, log callback
"""
import asyncio
import aiohttp
import re
import time
import logging
from typing import Set, List, Dict, Tuple, Optional, Callable
from bs4 import BeautifulSoup
from sources import ALL_SOURCES

logger = logging.getLogger("scraper")

def detect_protocol(url: str) -> str:
    """Detect proxy type from source URL."""
    url_lower = url.lower()
    if "socks5" in url_lower or "socks_5" in url_lower:
        return "socks5"
    elif "socks4" in url_lower or "socks_4" in url_lower:
        return "socks4"
    elif "https" in url_lower and "socks" not in url_lower:
        return "http"
    return "http"

def extract_proxies(text: str, default_proto: str = "http") -> Set[Tuple[str, str, str]]:
    """Extract ip:port proxies from text. Returns set of (ip, port, protocol)."""
    proxies = set()
    
    # Pattern 1: ip:port (most common)
    matches = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s]+(\d{2,5})', text)
    for ip, port in matches:
        octets = ip.split('.')
        if all(0 <= int(o) <= 255 for o in octets):
            port_int = int(port)
            if 1 <= port_int <= 65535:
                proxies.add((ip, port, default_proto))
    
    # Pattern 2: protocol://ip:port
    proto_matches = re.findall(r'(socks[45]?|http|https)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})', text)
    for proto, ip, port in proto_matches:
        octets = ip.split('.')
        if all(0 <= int(o) <= 255 for o in octets):
            port_int = int(port)
            if 1 <= port_int <= 65535:
                if proto.startswith("socks4"):
                    proxies.add((ip, port, "socks4"))
                elif proto.startswith("socks5"):
                    proxies.add((ip, port, "socks5"))
                else:
                    proxies.add((ip, port, "http"))
    
    # Pattern 3: JSON format {"ip": "...", "port": "..."}
    json_matches = re.findall(
        r'"ip"\s*:\s*"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})".*?"port"\s*:\s*"?(\d{2,5})"?',
        text, re.DOTALL
    )
    for ip, port in json_matches:
        octets = ip.split('.')
        if all(0 <= int(o) <= 255 for o in octets):
            port_int = int(port)
            if 1 <= port_int <= 65535:
                proxies.add((ip, port, default_proto))
    
    return proxies

async def fetch_source(session: aiohttp.ClientSession, url: str, timeout: int = 15) -> str:
    """Fetch a single proxy source URL."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=timeout),
            ssl=False, headers=headers
        ) as resp:
            if resp.status == 200:
                return await resp.text(errors='ignore')
            else:
                logger.debug(f"[{resp.status}] {url}")
                return ""
    except Exception as e:
        logger.debug(f"[ERR] {url}: {str(e)[:80]}")
        return ""

async def scrape_all(
    sources: List[str] = None,
    max_concurrent: int = 100,
    log_callback: Optional[Callable] = None
) -> Dict[str, Set[Tuple[str, str, str]]]:
    """Scrape all sources concurrently. Returns dict of protocol -> set of (ip, port, proto)."""
    if sources is None:
        sources = ALL_SOURCES
    
    results = {"http": set(), "socks4": set(), "socks5": set()}
    total_found = 0
    total_sources_with_data = 0
    start_time = time.time()
    
    connector = aiohttp.TCPConnector(
        limit=max_concurrent, ttl_dns_cache=300,
        enable_cleanup_closed=True, force_close=True
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        batch_size = 50
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            tasks = []
            for url in batch:
                proto = detect_protocol(url)
                tasks.append((url, proto, fetch_source(session, url)))
            
            gathered = await asyncio.gather(*[t[2] for t in tasks], return_exceptions=True)
            
            for j, result in enumerate(gathered):
                url, proto, _ = tasks[j]
                if isinstance(result, str) and result:
                    proxies = extract_proxies(result, proto)
                    if proxies:
                        for ip, port, p in proxies:
                            results[p].add((ip, port, p))
                        total_found += len(proxies)
                        total_sources_with_data += 1
            
            if log_callback and (i % 100 == 0 or i + batch_size >= len(sources)):
                log_callback("INFO", f"Scraped {min(i+batch_size, len(sources))}/{len(sources)} sources...", "scrape")
            
            await asyncio.sleep(0.3)
    
    elapsed = time.time() - start_time
    
    if log_callback:
        log_callback("INFO", 
            f"Scrape done: {total_found} raw proxies from {total_sources_with_data} sources in {elapsed:.1f}s", "scrape")
        for proto in ["http", "socks4", "socks5"]:
            count = len(results[proto])
            if count:
                log_callback("INFO", f"  {proto.upper()}: {count} proxies", "scrape")
    
    logger.info(
        f"[SCRAPER] Done in {elapsed:.1f}s | "
        f"HTTP: {len(results['http'])} | "
        f"SOCKS4: {len(results['socks4'])} | "
        f"SOCKS5: {len(results['socks5'])} | "
        f"Total: {total_found}"
    )
    
    return results
