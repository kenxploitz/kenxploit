"""
KenXploit Proxy Scraper — SQLite Database v2
Users, API keys, proxy storage, stats, logging
"""
import aiosqlite
import time
import secrets
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("database")

DB_PATH = "/home/kenxploit/proxy-scraper/proxies.db"

# ═══════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════
async def init_db():
    """Initialize database with all tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # ─── Proxies table ───
        await db.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                port TEXT NOT NULL,
                protocol TEXT NOT NULL DEFAULT 'http',
                latency_ms INTEGER DEFAULT 0,
                speed_mbps REAL DEFAULT 0,
                country TEXT DEFAULT 'XX',
                external_ip TEXT DEFAULT '',
                alive INTEGER DEFAULT 1,
                uptime_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                first_seen INTEGER DEFAULT 0,
                last_checked INTEGER DEFAULT 0,
                last_alive INTEGER DEFAULT 0,
                source TEXT DEFAULT '',
                UNIQUE(ip, port, protocol)
            )
        """)
        
        # ─── Users table ───
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                api_key TEXT UNIQUE DEFAULT '',
                created_at INTEGER DEFAULT 0,
                last_login INTEGER DEFAULT 0
            )
        """)
        
        # ─── Scrape logs ───
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                total_scraped INTEGER DEFAULT 0,
                total_alive INTEGER DEFAULT 0,
                http_count INTEGER DEFAULT 0,
                socks4_count INTEGER DEFAULT 0,
                socks5_count INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                source_count INTEGER DEFAULT 0
            )
        """)
        
        # ─── Activity logs (real-time) ───
        await db.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                level TEXT DEFAULT 'INFO',
                message TEXT NOT NULL,
                category TEXT DEFAULT 'system'
            )
        """)
        
        # ─── Indexes ───
        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_alive ON proxies(alive)",
            "CREATE INDEX IF NOT EXISTS idx_protocol ON proxies(protocol)",
            "CREATE INDEX IF NOT EXISTS idx_latency ON proxies(latency_ms)",
            "CREATE INDEX IF NOT EXISTS idx_speed ON proxies(speed_mbps)",
            "CREATE INDEX IF NOT EXISTS idx_country ON proxies(country)",
            "CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_logs(timestamp)",
        ]:
            await db.execute(idx)
        
        await db.commit()
        
        # ─── Seed default admin if not exists ───
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]
        if count == 0:
            from auth import hash_password
            api_key = "kenx-" + secrets.token_hex(24)
            now = int(time.time())
            await db.execute(
                "INSERT INTO users (username, password_hash, role, api_key, created_at) VALUES (?, ?, ?, ?, ?)",
                ("admin", hash_password("KenXploit123!"), "admin", api_key, now)
            )
            await db.commit()
            logger.info(f"[DB] Created default user: admin / KenXploit123! / API: {api_key}")
        
        logger.info("[DB] Initialized")

# ═══════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════
async def get_user(username: str) -> Optional[Dict]:
    """Get user by username."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def update_last_login(username: str):
    """Update last login timestamp."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_login = ? WHERE username = ?", (int(time.time()), username))
        await db.commit()

async def change_password(username: str, new_hash: str):
    """Change user password."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
        await db.commit()

async def regenerate_api_key(username: str) -> str:
    """Regenerate API key for user."""
    api_key = "kenx-" + secrets.token_hex(24)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET api_key = ? WHERE username = ?", (api_key, username))
        await db.commit()
    return api_key

async def verify_api_key(api_key: str) -> Optional[str]:
    """Verify API key and return username."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT username FROM users WHERE api_key = ?", (api_key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def create_user(username: str, password_hash: str, role: str = "admin") -> bool:
    """Create a new user."""
    try:
        api_key = "kenx-" + secrets.token_hex(24)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO users (username, password_hash, role, api_key, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, role, api_key, int(time.time()))
            )
            await db.commit()
        return True
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════
#  PROXIES
# ═══════════════════════════════════════════════════════════
async def upsert_proxies(proxies: List[Dict], source: str = "") -> int:
    """Insert or update proxies. Returns count."""
    now = int(time.time())
    new_count = 0
    
    async with aiosqlite.connect(DB_PATH) as db:
        for p in proxies:
            try:
                await db.execute("""
                    INSERT INTO proxies (ip, port, protocol, latency_ms, speed_mbps, 
                                        country, external_ip, alive, uptime_count, 
                                        first_seen, last_checked, last_alive, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)
                    ON CONFLICT(ip, port, protocol) DO UPDATE SET
                        latency_ms = excluded.latency_ms,
                        speed_mbps = COALESCE(excluded.speed_mbps, speed_mbps),
                        external_ip = COALESCE(excluded.external_ip, external_ip),
                        alive = 1,
                        uptime_count = uptime_count + 1,
                        last_alive = excluded.last_alive,
                        last_checked = excluded.last_checked
                """, (
                    p["ip"], p["port"], p["protocol"],
                    p.get("latency_ms", 0), p.get("speed_mbps", 0),
                    p.get("country", "XX"), p.get("external_ip", ""),
                    now, now, now, source
                ))
                new_count += 1
            except Exception as e:
                logger.debug(f"[DB] Upsert error: {e}")
        
        await db.commit()
    
    return new_count

async def mark_dead(dead_proxies: List[Tuple[str, str, str]]):
    """Mark proxies as dead."""
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        for ip, port, protocol in dead_proxies:
            await db.execute("""
                UPDATE proxies SET alive = 0, fail_count = fail_count + 1, 
                                   last_checked = ?
                WHERE ip = ? AND port = ? AND protocol = ?
            """, (now, ip, port, protocol))
        await db.commit()

async def delete_proxy(proxy_id: int) -> bool:
    """Delete a proxy by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()
        return cursor.rowcount > 0

async def delete_dead_proxies() -> int:
    """Delete all dead proxies."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM proxies WHERE alive = 0")
        await db.commit()
        return cursor.rowcount

async def get_proxies(protocol: str = None, alive_only: bool = True,
                       limit: int = 10000, offset: int = 0,
                       sort_by: str = "latency_ms", sort_order: str = "ASC",
                       search: str = "", country: str = "") -> List[Dict]:
    """Get proxies with filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = "SELECT * FROM proxies WHERE 1=1"
        params = []
        
        if alive_only:
            query += " AND alive = 1"
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        if search:
            query += " AND (ip LIKE ? OR port LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if country:
            query += " AND country = ?"
            params.append(country)
        
        valid_sorts = ["latency_ms", "speed_mbps", "last_checked", "last_alive", "uptime_count", "ip", "first_seen"]
        if sort_by not in valid_sorts:
            sort_by = "latency_ms"
        sort_dir = "DESC" if sort_order.upper() == "DESC" else "ASC"
        
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        query += f" ORDER BY {sort_by} {sort_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return {"proxies": [dict(row) for row in rows], "total": total}

async def get_proxy_count(alive_only: bool = True, protocol: str = None) -> int:
    """Get count of proxies."""
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT COUNT(*) FROM proxies WHERE 1=1"
        params = []
        if alive_only:
            query += " AND alive = 1"
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        cursor = await db.execute(query, params)
        return (await cursor.fetchone())[0]

async def get_stats() -> Dict:
    """Get overall statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE alive = 1")
        stats["total_alive"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM proxies")
        stats["total_all"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE alive = 1 AND protocol = 'http'")
        stats["http_alive"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE alive = 1 AND protocol = 'socks4'")
        stats["socks4_alive"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE alive = 1 AND protocol = 'socks5'")
        stats["socks5_alive"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT AVG(latency_ms) FROM proxies WHERE alive = 1 AND latency_ms > 0")
        avg = (await cursor.fetchone())[0]
        stats["avg_latency_ms"] = round(avg, 1) if avg else 0
        
        cursor = await db.execute("SELECT MIN(latency_ms) FROM proxies WHERE alive = 1 AND latency_ms > 0")
        min_lat = (await cursor.fetchone())[0]
        stats["min_latency_ms"] = min_lat if min_lat else 0
        
        cursor = await db.execute("SELECT COUNT(DISTINCT country) FROM proxies WHERE alive = 1")
        stats["countries"] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats["users"] = (await cursor.fetchone())[0]
        
        # Last scrape
        cursor = await db.execute("""
            SELECT timestamp, total_scraped, total_alive, duration_seconds 
            FROM scrape_logs ORDER BY id DESC LIMIT 1
        """)
        row = await cursor.fetchone()
        if row:
            stats["last_scrape"] = {
                "timestamp": row[0],
                "total_scraped": row[1],
                "total_alive": row[2],
                "duration": row[3],
            }
        
        return stats

# ═══════════════════════════════════════════════════════════
#  LOGS
# ═══════════════════════════════════════════════════════════
async def log_scrape(total_scraped: int, total_alive: int, http_count: int,
                      socks4_count: int, socks5_count: int, duration: float,
                      source_count: int):
    """Log a scrape run."""
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO scrape_logs (timestamp, total_scraped, total_alive, 
                                    http_count, socks4_count, socks5_count, 
                                    duration_seconds, source_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, total_scraped, total_alive, 
              http_count, socks4_count, socks5_count, duration, source_count))
        await db.commit()

async def add_activity_log(level: str, message: str, category: str = "system"):
    """Add an activity log entry."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO activity_logs (timestamp, level, message, category) VALUES (?, ?, ?, ?)",
            (int(time.time()), level, message, category)
        )
        await db.commit()

async def get_activity_logs(limit: int = 100, offset: int = 0, 
                             level: str = None, category: str = None) -> Dict:
    """Get activity logs with filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = "SELECT * FROM activity_logs WHERE 1=1"
        params = []
        
        if level:
            query += " AND level = ?"
            params.append(level.upper())
        if category:
            query += " AND category = ?"
            params.append(category)
        
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return {"logs": [dict(row) for row in rows], "total": total}

async def get_latest_logs_since(since_id: int = 0, limit: int = 50) -> List[Dict]:
    """Get logs newer than since_id (for WebSocket streaming)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM activity_logs WHERE id > ? ORDER BY id ASC LIMIT ?",
            (since_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# ═══════════════════════════════════════════════════════════
#  EXPORT
# ═══════════════════════════════════════════════════════════
async def export_proxies(protocol: str = None, format: str = "txt") -> str:
    """Export proxies as text/json/csv."""
    result = await get_proxies(protocol=protocol, alive_only=True, limit=100000)
    proxies = result["proxies"]
    
    if format == "json":
        import json
        return json.dumps(proxies, indent=2)
    elif format == "csv":
        lines = ["ip,port,protocol,latency_ms,speed_mbps,country,external_ip"]
        for p in proxies:
            lines.append(f"{p['ip']},{p['port']},{p['protocol']},{p['latency_ms']},{p.get('speed_mbps', 0)},{p.get('country', 'XX')},{p.get('external_ip', '')}")
        return "\n".join(lines)
    else:  # txt
        lines = []
        for p in proxies:
            lines.append(f"{p['ip']}:{p['port']}")
        return "\n".join(lines)

async def cleanup_old(max_age_hours: int = 24) -> int:
    """Remove proxies not seen in X hours."""
    cutoff = int(time.time()) - (max_age_hours * 3600)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM proxies WHERE last_alive < ? AND alive = 0", (cutoff,))
        deleted = cursor.rowcount
        await db.execute("DELETE FROM scrape_logs WHERE timestamp < ?", (cutoff,))
        await db.execute("DELETE FROM activity_logs WHERE timestamp < ?", (cutoff - 3600,))
        await db.commit()
        return deleted
