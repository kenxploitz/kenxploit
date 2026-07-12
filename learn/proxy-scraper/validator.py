"""
KenXploit Proxy Scraper — Async Validator v2
Multi-endpoint validation, speed measurement, continuous mode
"""
import asyncio
import aiohttp
import time
import random
import logging
from typing import List, Tuple, Dict, Optional, Callable

logger = logging.getLogger("validator")

# Multiple test URLs for redundancy
TEST_URLS = [
    "http://api.ipify.org?format=json",
    "http://ifconfig.me/ip",
    "http://icanhazip.com",
    "http://ip-api.com/json",
    "http://httpbin.org/ip",
]

TIMEOUT_CONFIGS = [
    {"connect": 3, "total": 8, "label": "fast"},
    {"connect": 5, "total": 12, "label": "normal"},
]

async def validate_proxy(session: aiohttp.ClientSession, ip: str, port: str, 
                          protocol: str = "http", timeout_config: int = 0) -> Optional[Dict]:
    """Validate a single proxy against multiple test URLs."""
    proxy_url = f"{protocol}://{ip}:{port}"
    timeout_settings = TIMEOUT_CONFIGS[timeout_config]
    
    # Try each test URL
    for test_url in TEST_URLS[:2]:  # Try first 2 URLs
        try:
            start = time.time()
            async with session.get(
                test_url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(
                    total=timeout_settings["total"], 
                    connect=timeout_settings["connect"]
                ),
                ssl=False,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            ) as resp:
                if resp.status == 200:
                    latency = round((time.time() - start) * 1000)
                    body = await resp.text(errors='ignore')
                    
                    # Extract external IP
                    external_ip = ip
                    try:
                        import json
                        data = json.loads(body)
                        external_ip = data.get("origin", data.get("ip", data.get("query", ip)))
                    except:
                        # Plain text response (icanhazip.com)
                        body_clean = body.strip()
                        if body_clean and not body_clean.startswith("{"):
                            external_ip = body_clean
                    
                    return {
                        "ip": ip,
                        "port": port,
                        "protocol": protocol,
                        "latency_ms": latency,
                        "external_ip": external_ip,
                        "alive": True,
                        "last_checked": int(time.time()),
                        "speed_mbps": None,
                    }
        except (asyncio.TimeoutError, aiohttp.ClientError, OSError):
            continue
        except Exception as e:
            logger.debug(f"[VAL] {ip}:{port} error: {str(e)[:60]}")
            continue
    
    return None

async def validate_batch(proxies: List[Tuple[str, str, str]], 
                          max_concurrent: int = 300,
                          timeout: int = 8,
                          progress_callback: Optional[Callable] = None) -> List[Dict]:
    """Validate a batch of proxies concurrently with progress reporting."""
    results = []
    total = len(proxies)
    done = 0
    
    connector = aiohttp.TCPConnector(
        limit=max_concurrent, ttl_dns_cache=30,
        enable_cleanup_closed=True, force_close=True,
        verify_ssl=False
    )
    
    timeout_config = 0 if timeout <= 8 else 1
    
    async with aiohttp.ClientSession(connector=connector) as session:
        sem = asyncio.Semaphore(max_concurrent)
        
        async def sem_validate(ip, port, proto):
            async with sem:
                return await validate_proxy(session, ip, port, proto, timeout_config)
        
        # Create tasks in chunks for progress reporting
        chunk_size = max_concurrent * 2
        for i in range(0, total, chunk_size):
            chunk = proxies[i:i + chunk_size]
            tasks = [sem_validate(ip, port, proto) for ip, port, proto in chunk]
            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in gathered:
                if isinstance(result, dict) and result.get("alive"):
                    results.append(result)
            
            done += len(chunk)
            if progress_callback:
                progress_callback(done, total, len(results))
        
        logger.info(f"[VALIDATOR] {len(results)}/{total} alive")
    
    return results

async def continuous_validator_worker(stop_event: asyncio.Event, 
                                       log_callback: Optional[Callable] = None):
    """Continuous validation worker — runs in background forever.
    
    Validates all alive proxies in DB. Uses 2-pass validation:
    - Pass 1: test semua proxy
    - Pass 2: test ulang yang gagal (biar gak false positive)
    - Baru di-mark dead kalo gagal 2x berturut-turut
    """
    import database as db
    
    logger.info("[VALIDATOR] Continuous validator started")
    
    while not stop_event.is_set():
        try:
            # Get all alive proxies, oldest first
            result = await db.get_proxies(alive_only=True, limit=5000, sort_by="last_checked", sort_order="ASC")
            proxies = result["proxies"]
            
            if not proxies:
                if log_callback:
                    log_callback("INFO", "No proxies to validate", "validator")
                await asyncio.sleep(5)
                continue
            
            total = len(proxies)
            if log_callback:
                log_callback("INFO", f"Validating {total} proxies...", "validator")
            
            proxy_list = [(p["ip"], p["port"], p["protocol"]) for p in proxies]
            batch_size = 500
            
            # ─── Pass 1: test semua ───
            pass1_alive = []
            for i in range(0, total, batch_size):
                batch = proxy_list[i:i + batch_size]
                alive = await validate_batch(batch, max_concurrent=250, timeout=8)
                pass1_alive.extend(alive)
                if log_callback:
                    log_callback("INFO", f"  Pass 1: {min(i+batch_size, total)}/{total} tested", "validator")
                await asyncio.sleep(0.3)
            
            pass1_alive_set = {(p["ip"], p["port"], p["protocol"]) for p in pass1_alive}
            
            # ─── Pass 2: test ulang yang gagal ───
            retry_list = [(ip, port, proto) for ip, port, proto in proxy_list 
                         if (ip, port, proto) not in pass1_alive_set]
            
            if retry_list:
                if log_callback:
                    log_callback("INFO", f"  Pass 2: retesting {len(retry_list)} failed proxies...", "validator")
                
                pass2_alive = []
                for i in range(0, len(retry_list), batch_size):
                    batch = retry_list[i:i + batch_size]
                    alive = await validate_batch(batch, max_concurrent=250, timeout=10)
                    pass2_alive.extend(alive)
                    await asyncio.sleep(0.3)
                
                pass2_alive_set = {(p["ip"], p["port"], p["protocol"]) for p in pass2_alive}
                
                # Hanya mark dead kalo gagal di 2 pass
                dead_list = [(ip, port, proto) for ip, port, proto in retry_list 
                            if (ip, port, proto) not in pass2_alive_set]
                
                all_alive = pass1_alive + pass2_alive
                alive_count = len(all_alive)
                
                if dead_list:
                    await db.mark_dead(dead_list)
                    if log_callback:
                        log_callback("WARNING", f"Marked {len(dead_list)} proxies as dead (failed 2x)", "validator")
                
                if log_callback:
                    log_callback("INFO", f"Done: {alive_count}/{total} alive ({len(dead_list)} dead, {len(pass2_alive)} recovered)", "validator")
            else:
                alive_count = len(pass1_alive)
                if log_callback:
                    log_callback("INFO", f"Done: {alive_count}/{total} alive (0 dead)", "validator")
            
            # Cleanup old dead
            deleted = await db.cleanup_old(max_age_hours=6)
            if deleted > 0 and log_callback:
                log_callback("INFO", f"Cleaned {deleted} old dead proxies", "validator")
            
            # Wait before next cycle
            await asyncio.sleep(30)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[VALIDATOR] Error: {e}")
            if log_callback:
                log_callback("ERROR", f"Validator error: {str(e)[:100]}", "validator")
            await asyncio.sleep(10)
            await asyncio.sleep(10)
