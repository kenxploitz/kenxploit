#!/usr/bin/env python3
"""
KENXPROXY - Async Ultra Fast Validator v4.0
500 concurrent, 4s timeout, SOCKS support
"""
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
import sys
from pathlib import Path

BASE = Path("/home/keandra/kenxploit/tools/proxy-hunt")
RAW = BASE / "raw"
VERIFIED = BASE / "verified"
VERIFIED.mkdir(exist_ok=True)

TIMEOUT = aiohttp.ClientTimeout(total=4, connect=3)
SEM_LIMIT = 500
TEST_URL = "http://httpbin.org/ip"

async def check_http(session, proxy, sem, results):
    async with sem:
        try:
            async with session.get(TEST_URL, proxy=f"http://{proxy}", timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    results.append(proxy)
        except:
            pass

async def check_socks(session_factory, proxy, ptype, sem, results):
    async with sem:
        try:
            ptype_enum = ProxyType.SOCKS4 if ptype == "socks4" else ProxyType.SOCKS5
            host, port = proxy.split(":")
            connector = ProxyConnector(
                proxy_type=ptype_enum,
                host=host, port=int(port),
                rdns=True
            )
            timeout = aiohttp.ClientTimeout(total=4, connect=3)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as s:
                async with s.get(TEST_URL) as resp:
                    if resp.status == 200:
                        results.append(proxy)
        except:
            pass

async def validate_http(proxies):
    results = []
    sem = asyncio.Semaphore(SEM_LIMIT)
    connector = aiohttp.TCPConnector(limit=SEM_LIMIT, ssl=False, force_close=True)
    async with aiohttp.ClientSession(connector=connector, timeout=TIMEOUT) as session:
        tasks = [check_http(session, p, sem, results) for p in proxies]
        done = 0
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % 2000 == 0:
                print(f"  [HTTP] {done}/{len(proxies)} checked, {len(results)} valid")
    return results

async def validate_socks(proxies, ptype):
    results = []
    sem = asyncio.Semaphore(200)  # Lower for SOCKS (more resource heavy)
    done_count = [0]
    
    async def worker(proxy):
        await check_socks(None, proxy, ptype, sem, results)
        done_count[0] += 1
        if done_count[0] % 1000 == 0:
            print(f"  [{ptype.upper()}] {done_count[0]}/{len(proxies)} checked, {len(results)} valid")
    
    tasks = [worker(p) for p in proxies]
    # Process in chunks to avoid too many tasks
    chunk_size = 5000
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        await asyncio.gather(*chunk)
    
    return results

async def main():
    print("=" * 50)
    print("  KENXPROXY Async Validator v4.0")
    print("  HTTP: 500 concurrent | SOCKS: 200 concurrent")
    print("  Timeout: 4s")
    print("=" * 50)
    
    # Load all proxy lists
    http_proxies = list(set(line.strip() for line in open(RAW / "raw_http_final.txt") if line.strip()))
    socks4_proxies = list(set(line.strip() for line in open(RAW / "raw_socks4_final.txt") if line.strip()))
    socks5_proxies = list(set(line.strip() for line in open(RAW / "raw_socks5_final.txt") if line.strip()))
    
    print(f"\n[*] Loaded: HTTP={len(http_proxies)}, SOCKS4={len(socks4_proxies)}, SOCKS5={len(socks5_proxies)}")
    print(f"[*] Total: {len(http_proxies) + len(socks4_proxies) + len(socks5_proxies)}\n")
    
    # Run HTTP first (fastest), then SOCKS4, then SOCKS5
    print("[*] Phase 1: HTTP validation...")
    http_results = await validate_http(http_proxies)
    
    print("\n[*] Phase 2: SOCKS4 validation...")
    socks4_results = await validate_socks(socks4_proxies, "socks4")
    
    print("\n[*] Phase 3: SOCKS5 validation...")
    socks5_results = await validate_socks(socks5_proxies, "socks5")
    
    # Save results
    for name, data in [("http", http_results), ("socks4", socks4_results), ("socks5", socks5_results)]:
        out = VERIFIED / f"{name}_verified_v2.txt"
        with open(out, 'w') as f:
            for p in sorted(set(data)):
                f.write(f"{p}\n")
    
    # Merge all
    all_proxies = set(http_results + socks4_results + socks5_results)
    with open(VERIFIED / "all_verified_v2.txt", 'w') as f:
        for p in sorted(all_proxies):
            f.write(f"{p}\n")
    
    v_http = len(set(http_results))
    v_s4 = len(set(socks4_results))
    v_s5 = len(set(socks5_results))
    total = len(all_proxies)
    
    print(f"\n{'=' * 50}")
    print(f"  VERIFICATION COMPLETE")
    print(f"{'=' * 50}")
    print(f"  HTTP:    {v_http}")
    print(f"  SOCKS4:  {v_s4}")
    print(f"  SOCKS5:  {v_s5}")
    print(f"  TOTAL:   {total} unique verified proxies")
    print(f"{'=' * 50}")
    
    # Also merge with first batch
    first_batch = VERIFIED / "all_verified.txt"
    if first_batch.exists():
        combined = set(all_proxies)
        for line in open(first_batch):
            parts = line.strip().split("|")
            if parts:
                combined.add(parts[0])  # ip:port
        
        with open(VERIFIED / "all_verified_FINAL.txt", 'w') as f:
            for p in sorted(combined):
                f.write(f"{p}\n")
        
        print(f"\n[+] COMBINED with first batch: {len(combined)} total verified proxies")
        print(f"[+] Saved to: {VERIFIED}/all_verified_FINAL.txt")

if __name__ == "__main__":
    asyncio.run(main())
