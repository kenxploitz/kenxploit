"""
KenXploit Proxy Scraper — FastAPI v2
Authentication · Security · WebSocket Logs · Continuous Validation
"""
import os
import sys
import time
import json
import asyncio
import logging
import secrets
from typing import Optional, List
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime

from fastapi import (FastAPI, Query, Request, BackgroundTasks, 
                     WebSocket, WebSocketDisconnect, Depends, HTTPException, status)
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

import database as db
from scraper import scrape_all
from validator import validate_batch, continuous_validator_worker
from sources import ALL_SOURCES

# Auth module
sys.path.insert(0, os.path.dirname(__file__))
from auth import (hash_password, verify_password, create_token, verify_token,
                  get_current_user, optional_user)

logger = logging.getLogger("app")

# ═══════════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════════
scrape_state = {
    "running": False,
    "last_run": 0,
    "total_scraped": 0,
    "total_alive": 0,
    "cycle_count": 0,
}

# Rate limiter (in-memory, reset on restart — good enough)
rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60      # seconds
RATE_LIMIT_MAX = 60         # requests per window
LOGIN_LIMIT_WINDOW = 300    # 5 minutes
LOGIN_LIMIT_MAX = 5         # max 5 attempts per 5 min per IP

# WebSocket connections for live logs
ws_clients: List[WebSocket] = []

# Continuous validator control
validator_stop_event = asyncio.Event()
validator_running = False
auto_scrape_running = False

def get_client_ip(request: Request) -> str:
    """Get real client IP behind nginx reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"

def rate_limit_check(key: str):
    """Simple sliding window rate limiter."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    rate_limit_store[key] = [t for t in rate_limit_store[key] if t > window_start]
    if len(rate_limit_store[key]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[key].append(now)

# ═══════════════════════════════════════════════════════════
#  LOG CALLBACK (for WebSocket broadcast)
# ═══════════════════════════════════════════════════════════
async def broadcast_log(level: str, message: str, category: str = "system"):
    """Send log to all connected WebSocket clients + save to DB."""
    log_entry = {
        "timestamp": int(time.time()),
        "level": level,
        "message": message,
        "category": category,
    }
    
    # Save to DB
    try:
        await db.add_activity_log(level, message, category)
    except Exception:
        pass
    
    # Broadcast to WebSocket clients
    dead_clients = []
    for ws in ws_clients:
        try:
            await ws.send_json(log_entry)
        except Exception:
            dead_clients.append(ws)
    
    for ws in dead_clients:
        ws_clients.remove(ws)

def make_log_callback():
    """Create a sync-compatible log callback wrapper."""
    async def _log(level, message, category="system"):
        await broadcast_log(level, message, category)
    
    def _sync_log(level, message, category="system"):
        """Sync version for use in non-async contexts."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.ensure_future(_log(level, message, category))
        except RuntimeError:
            pass
    
    return _sync_log

log_cb = make_log_callback()

# ═══════════════════════════════════════════════════════════
#  LIFESPAN
# ═══════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    await db.init_db()
    await broadcast_log("INFO", f"App started with {len(ALL_SOURCES)} sources", "system")
    
    # Start continuous validator
    global validator_running, auto_scrape_running
    validator_running = True
    validator_stop_event.clear()
    asyncio.create_task(continuous_validator_worker(validator_stop_event, log_cb))
    await broadcast_log("INFO", "Continuous validator started", "system")
    
    # Start auto-scrape scheduler (every 5 minutes)
    auto_scrape_running = True
    asyncio.create_task(auto_scrape_scheduler())
    await broadcast_log("INFO", "Auto-scrape scheduler started (every 5 min)", "system")
    
    yield
    
    # Shutdown
    auto_scrape_running = False
    validator_stop_event.set()
    validator_running = False
    for ws in ws_clients:
        try:
            await ws.close()
        except Exception:
            pass
    ws_clients.clear()
    await broadcast_log("INFO", "App shutting down", "system")

app = FastAPI(
    title="KenXploit Proxy Scraper", 
    version="2.0", 
    lifespan=lifespan,
    docs_url=None,           # Disable Swagger in production
    redoc_url=None,
)

# ─── Templates ────────────────────────────────────────────
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ─── Security Middleware ───────────────────────────────────
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers — HSTS only on HTTPS
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    
    # CSP - strict but allows our own resources
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "font-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting by real IP (behind nginx)."""
    if request.url.path.startswith("/static"):
        return await call_next(request)
    
    client_ip = get_client_ip(request)
    try:
        rate_limit_check(client_ip)
    except HTTPException:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Slow down."}
        )
    return await call_next(request)

# ─── Auth-Exempt Routes ────────────────────────────────────
AUTH_EXEMPT = {"/login", "/api/login", "/api/health", "/favicon.ico"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Redirect to login if not authenticated (exempt certain paths)."""
    path = request.url.path
    
    # Static files and exempt routes
    if path.startswith("/static") or path in AUTH_EXEMPT:
        return await call_next(request)
    
    # API routes — check auth but don't redirect
    if path.startswith("/api/"):
        try:
            await get_current_user(request)
        except HTTPException:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        return await call_next(request)
    
    # Web routes — redirect to login if not authenticated
    try:
        await get_current_user(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    return await call_next(request)

# ═══════════════════════════════════════════════════════════
#  ROUTES — Authentication
# ═══════════════════════════════════════════════════════════
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    # If already logged in, redirect to dashboard
    try:
        await get_current_user(request)
        return RedirectResponse(url="/", status_code=302)
    except HTTPException:
        pass
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/login")
async def api_login(request: Request):
    """Login: verify credentials and return JWT token.
    Rate limited: 5 attempts per 5 minutes per IP.
    """
    # Login-specific rate limit (real IP behind nginx)
    client_ip = get_client_ip(request)
    login_key = f"login:{client_ip}"
    now = time.time()
    window_start = now - LOGIN_LIMIT_WINDOW
    rate_limit_store[login_key] = [t for t in rate_limit_store[login_key] if t > window_start]
    if len(rate_limit_store[login_key]) >= LOGIN_LIMIT_MAX:
        await broadcast_log("WARNING", f"Login rate limit hit for {client_ip}", "auth")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many login attempts. Try again in 5 minutes."}
        )
    rate_limit_store[login_key].append(now)
    
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()
        remember = body.get("remember", False)
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    
    if not username or not password:
        return JSONResponse(status_code=400, content={"detail": "Username and password required"})
    
    user = await db.get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        await broadcast_log("WARNING", f"Failed login attempt for '{username}' from {client_ip}", "auth")
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    
    # Create token
    token = create_token(username, remember=remember)
    await db.update_last_login(username)
    await broadcast_log("INFO", f"User '{username}' logged in", "auth")
    
    response = JSONResponse(content={"status": "ok", "token": token})
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=False,  # Dev mode (HTTP); set True in production with HTTPS
        samesite="lax",
        max_age=30*24*3600 if remember else 480*60,
    )
    return response

@app.post("/api/logout")
async def api_logout():
    """Logout: clear cookie."""
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("token")
    return response

# ═══════════════════════════════════════════════════════════
#  ROUTES — Dashboard
# ═══════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    """Main dashboard."""
    stats = await db.get_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "state": scrape_state,
        "sources_count": len(ALL_SOURCES),
        "user": user,
    })

@app.get("/proxies", response_class=HTMLResponse)
async def proxies_page(
    request: Request, 
    protocol: Optional[str] = None,
    page: int = Query(1, ge=1),
    user: str = Depends(get_current_user)
):
    """Proxies listing page."""
    stats = await db.get_stats()
    limit = 100
    offset = (page - 1) * limit
    result = await db.get_proxies(
        protocol=protocol, alive_only=True, 
        limit=limit, offset=offset,
        sort_by="latency_ms", sort_order="ASC"
    )
    return templates.TemplateResponse("proxies.html", {
        "request": request,
        "proxies": result["proxies"],
        "total": result["total"],
        "page": page,
        "limit": limit,
        "stats": stats,
        "selected_protocol": protocol or "all",
        "user": user,
    })

@app.get("/sources", response_class=HTMLResponse)
async def sources_page(
    request: Request,
    user: str = Depends(get_current_user)
):
    """Sources listing page."""
    return templates.TemplateResponse("sources.html", {
        "request": request,
        "sources": ALL_SOURCES,
        "total": len(ALL_SOURCES),
        "user": user,
    })

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    user: str = Depends(get_current_user)
):
    """Real-time logs page."""
    logs_data = await db.get_activity_logs(limit=50)
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs_data["logs"],
        "user": user,
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: str = Depends(get_current_user)
):
    """Settings page."""
    user_data = await db.get_user(user)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "user_data": user_data,
    })

# ═══════════════════════════════════════════════════════════
#  API — Stats & Proxies
# ═══════════════════════════════════════════════════════════
@app.get("/api/stats")
async def api_stats(user: str = Depends(get_current_user)):
    """API: Get stats."""
    stats = await db.get_stats()
    stats["state"] = scrape_state
    stats["sources_count"] = len(ALL_SOURCES)
    return JSONResponse(stats)

@app.get("/api/proxies")
async def api_proxies(
    protocol: Optional[str] = Query(None),
    alive: bool = Query(True),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    sort: str = Query("latency_ms"),
    order: str = Query("ASC"),
    search: str = Query(""),
    country: str = Query(""),
    user: str = Depends(get_current_user)
):
    """API: Get proxies with filters."""
    result = await db.get_proxies(
        protocol=protocol, alive_only=alive, 
        limit=limit, offset=offset, 
        sort_by=sort, sort_order=order,
        search=search, country=country
    )
    return JSONResponse(result)

@app.get("/api/export")
async def api_export(
    protocol: Optional[str] = Query(None),
    format: str = Query("txt"),
    user: str = Depends(get_current_user)
):
    """Export proxies as text/json/csv."""
    content = await db.export_proxies(protocol=protocol, format=format)
    
    if format == "json":
        return JSONResponse(json.loads(content))
    elif format == "csv":
        return PlainTextResponse(
            content, media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=proxies.csv"}
        )
    else:
        return PlainTextResponse(
            content, media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=proxies.txt"}
        )

@app.get("/api/export/{protocol}")
async def api_export_protocol(
    protocol: str, 
    format: str = Query("txt"),
    user: str = Depends(get_current_user)
):
    """Export proxies by protocol."""
    if protocol not in ["http", "socks4", "socks5"]:
        return JSONResponse({"error": "Invalid protocol"}, status_code=400)
    content = await db.export_proxies(protocol=protocol, format=format)
    return PlainTextResponse(
        content, media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={protocol}_proxies.txt"}
    )

@app.get("/api/count")
async def api_count(
    protocol: Optional[str] = None,
    user: str = Depends(get_current_user)
):
    """API: Get proxy counts."""
    total = await db.get_proxy_count(alive_only=False, protocol=protocol)
    alive = await db.get_proxy_count(alive_only=True, protocol=protocol)
    return JSONResponse({"total": total, "alive": alive, "dead": total - alive})

# ═══════════════════════════════════════════════════════════
#  API — Scrape & Validate Controls
# ═══════════════════════════════════════════════════════════
@app.post("/api/scrape")
async def api_trigger_scrape(
    background_tasks: BackgroundTasks,
    user: str = Depends(get_current_user)
):
    """API: Trigger manual scrape."""
    if scrape_state["running"]:
        return JSONResponse({"status": "already_running", "message": "Scrape already in progress"})
    
    background_tasks.add_task(run_scrape_cycle)
    await broadcast_log("INFO", "Manual scrape triggered by user", "action")
    return JSONResponse({"status": "started", "message": "Scrape started"})

@app.post("/api/validate")
async def api_trigger_validate(
    background_tasks: BackgroundTasks,
    user: str = Depends(get_current_user)
):
    """API: Trigger manual validation of all alive proxies."""
    background_tasks.add_task(run_validation_cycle)
    await broadcast_log("INFO", "Manual validation triggered by user", "action")
    return JSONResponse({"status": "started", "message": "Validation started"})

@app.post("/api/proxy/{proxy_id}/delete")
async def api_delete_proxy(
    proxy_id: int,
    user: str = Depends(get_current_user)
):
    """API: Delete a specific proxy."""
    deleted = await db.delete_proxy(proxy_id)
    if deleted:
        await broadcast_log("INFO", f"Deleted proxy #{proxy_id}", "action")
        return JSONResponse({"status": "deleted"})
    return JSONResponse({"status": "not_found"}, status_code=404)

@app.post("/api/proxies/cleanup")
async def api_cleanup_dead(
    user: str = Depends(get_current_user)
):
    """API: Delete all dead proxies."""
    deleted = await db.delete_dead_proxies()
    await broadcast_log("INFO", f"Cleaned up {deleted} dead proxies", "action")
    return JSONResponse({"status": "ok", "deleted": deleted})

# ═══════════════════════════════════════════════════════════
#  API — Logs
# ═══════════════════════════════════════════════════════════
@app.get("/api/logs")
async def api_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    level: Optional[str] = None,
    category: Optional[str] = None,
    user: str = Depends(get_current_user)
):
    """API: Get activity logs."""
    logs_data = await db.get_activity_logs(
        limit=limit, offset=offset, level=level, category=category
    )
    return JSONResponse(logs_data)

# ═══════════════════════════════════════════════════════════
#  API — User/Settings
# ═══════════════════════════════════════════════════════════
@app.post("/api/settings/change-password")
async def api_change_password(
    request: Request,
    user: str = Depends(get_current_user)
):
    """Change password."""
    try:
        body = await request.json()
        current = body.get("current_password", "")
        new = body.get("new_password", "")
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON"})
    
    if len(new) < 8:
        return JSONResponse(status_code=400, content={"detail": "Password must be 8+ characters"})
    
    user_data = await db.get_user(user)
    if not verify_password(current, user_data["password_hash"]):
        return JSONResponse(status_code=403, content={"detail": "Current password is wrong"})
    
    await db.change_password(user, hash_password(new))
    await broadcast_log("INFO", f"Password changed for '{user}'", "auth")
    return JSONResponse({"status": "ok"})

@app.get("/api/settings/api-key")
async def api_get_api_key(
    user: str = Depends(get_current_user)
):
    """Get API key."""
    user_data = await db.get_user(user)
    return JSONResponse({"api_key": user_data["api_key"]})

@app.post("/api/settings/regenerate-key")
async def api_regenerate_key(
    user: str = Depends(get_current_user)
):
    """Regenerate API key."""
    new_key = await db.regenerate_api_key(user)
    await broadcast_log("INFO", f"API key regenerated for '{user}'", "auth")
    return JSONResponse({"api_key": new_key})

# ═══════════════════════════════════════════════════════════
#  WEBSOCKET — Real-time Logs
# ═══════════════════════════════════════════════════════════
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming.
    Requires auth via token in query params.
    """
    # Auth check via token in query string
    token = websocket.query_params.get("token", "")
    if not token:
        try:
            cookie_header = websocket.headers.get("cookie", "")
            for c in cookie_header.split(";"):
                parts = c.strip().split("=", 1)
                if len(parts) == 2 and parts[0].strip() == "token":
                    token = parts[1]
                    break
        except Exception:
            pass
    
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    try:
        verify_token(token)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    ws_clients.append(websocket)
    
    try:
        # Send current state
        stats = await db.get_stats()
        await websocket.send_json({
            "type": "init",
            "stats": stats,
            "state": scrape_state,
        })
        
        # Keep connection alive and listen for pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"[WS] Client disconnected: {e}")
    finally:
        if websocket in ws_clients:
            ws_clients.remove(websocket)

# ═══════════════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════════════
@app.get("/api/health")
async def health():
    """Health check — no auth required."""
    return JSONResponse({
        "status": "ok", 
        "uptime": time.time(),
        "sources": len(ALL_SOURCES),
        "validator_running": validator_running,
    })

# ═══════════════════════════════════════════════════════════
#  BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════
async def run_scrape_cycle():
    """Full scrape -> validate -> store cycle."""
    global scrape_state
    
    if scrape_state["running"]:
        logger.info("[CYCLE] Already running, skipping...")
        return
    
    scrape_state["running"] = True
    start_time = time.time()
    
    try:
        await broadcast_log("INFO", f"Starting scrape cycle... ({len(ALL_SOURCES)} sources)", "scrape")
        
        # Step 1: Scrape all sources
        raw_proxies = await scrape_all(ALL_SOURCES, max_concurrent=100, log_callback=log_cb)
        total_scraped = sum(len(v) for v in raw_proxies.values())
        scrape_state["total_scraped"] = total_scraped
        
        if total_scraped == 0:
            await broadcast_log("WARNING", "Scraped 0 proxies — sources may be down", "scrape")
            scrape_state["running"] = False
            return
        
        await broadcast_log("INFO", f"Scraped {total_scraped} raw proxies (deduped)", "scrape")
        
        # Step 2: Validate
        total_alive = 0
        all_alive = []
        MAX_PER_PROTOCOL = 3000
        
        for protocol, proxies in raw_proxies.items():
            if not proxies:
                continue
            if total_alive > 100:
                break
            
            proxy_list = [(ip, port, proto) for ip, port, proto in proxies]
            
            if len(proxy_list) > MAX_PER_PROTOCOL:
                import random
                random.shuffle(proxy_list)
                proxy_list = proxy_list[:MAX_PER_PROTOCOL]
            
            await broadcast_log("INFO", f"Validating {len(proxy_list)} {protocol} proxies...", "scrape")
            
            chunk_size = 500
            for i in range(0, len(proxy_list), chunk_size):
                if total_alive > 100:
                    break
                chunk = proxy_list[i:i + chunk_size]
                alive = await validate_batch(chunk, max_concurrent=300, timeout=6)
                all_alive.extend(alive)
                total_alive += len(alive)
                
                if (i // chunk_size) % 2 == 0:
                    await broadcast_log("INFO", f"  {protocol}: {len(alive)} alive in chunk {i//chunk_size + 1}", "scrape")
        
        scrape_state["total_alive"] = total_alive
        
        # Step 3: Store
        if all_alive:
            new_count = await db.upsert_proxies(all_alive, source="auto-scrape")
            await broadcast_log("INFO", f"Stored {new_count} proxies to DB", "scrape")
        
        # Step 4: Log stats
        duration = time.time() - start_time
        http_count = len([p for p in all_alive if p["protocol"] == "http"])
        socks4_count = len([p for p in all_alive if p["protocol"] == "socks4"])
        socks5_count = len([p for p in all_alive if p["protocol"] == "socks5"])
        
        await db.log_scrape(total_scraped, total_alive, http_count,
                           socks4_count, socks5_count, duration, len(ALL_SOURCES))
        
        # Step 5: Cleanup old dead
        deleted = await db.cleanup_old(max_age_hours=12)
        
        scrape_state["cycle_count"] += 1
        scrape_state["last_run"] = int(time.time())
        
        await broadcast_log("INFO", 
            f"Cycle done in {duration:.1f}s | Raw: {total_scraped} | Alive: {total_alive} | Cleaned: {deleted}", "scrape")
        
    except Exception as e:
        logger.error(f"[CYCLE] Error: {e}")
        await broadcast_log("ERROR", f"Scrape cycle error: {str(e)[:200]}", "scrape")
    finally:
        scrape_state["running"] = False

async def run_validation_cycle():
    """Validate all alive proxies in DB."""
    try:
        await broadcast_log("INFO", "Starting validation cycle...", "validator")
        
        result = await db.get_proxies(alive_only=True, limit=5000, sort_by="last_checked", sort_order="ASC")
        proxies = result["proxies"]
        
        if not proxies:
            await broadcast_log("WARNING", "No proxies to validate", "validator")
            return
        
        total = len(proxies)
        proxy_list = [(p["ip"], p["port"], p["protocol"]) for p in proxies]
        
        alive_list = []
        dead_list = []
        batch_size = 500
        
        for i in range(0, total, batch_size):
            batch = proxy_list[i:i + batch_size]
            alive = await validate_batch(batch, max_concurrent=200, timeout=8)
            
            alive_ips = {(p["ip"], p["port"], p["protocol"]) for p in alive}
            for ip, port, proto in batch:
                if (ip, port, proto) not in alive_ips:
                    dead_list.append((ip, port, proto))
            
            alive_list.extend(alive)
            await broadcast_log("INFO", f"Validated {min(i+batch_size, total)}/{total}", "validator")
        
        if dead_list:
            await db.mark_dead(dead_list)
        
        await broadcast_log("INFO", f"Validation done: {len(alive_list)} alive, {len(dead_list)} dead", "validator")
        
    except Exception as e:
        logger.error(f"[VALIDATION] Error: {e}")
        await broadcast_log("ERROR", f"Validation error: {str(e)[:200]}", "validator")

# ═══════════════════════════════════════════════════════════
#  AUTO SCRAPE SCHEDULER
# ═══════════════════════════════════════════════════════════
async def auto_scrape_scheduler():
    """Run scrape cycle automatically every 5 minutes."""
    global auto_scrape_running
    
    # Wait a bit before first scrape
    await asyncio.sleep(15)
    
    while auto_scrape_running:
        try:
            if not scrape_state["running"]:
                await broadcast_log("INFO", "Auto-scrape: starting cycle...", "scrape")
                await run_scrape_cycle()
                await broadcast_log("INFO", "Auto-scrape: cycle completed", "scrape")
            else:
                logger.debug("[AUTO] Scrape already running, skipping")
        except Exception as e:
            logger.error(f"[AUTO] Error: {e}")
            await broadcast_log("ERROR", f"Auto-scrape error: {str(e)[:200]}", "scrape")
        
        # Wait 5 minutes before next cycle
        for _ in range(300):
            if not auto_scrape_running:
                return
            await asyncio.sleep(1)

# ═══════════════════════════════════════════════════════════
#  Static files & error handlers
# ═══════════════════════════════════════════════════════════
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return HTMLResponse("<h1>404 — Not Found</h1><p>This page does not exist.</p>", status_code=404)

@app.exception_handler(500)
async def server_error(request: Request, exc):
    return HTMLResponse("<h1>500 — Server Error</h1><p>Something went wrong.</p>", status_code=500)
