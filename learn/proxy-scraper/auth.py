"""
KenXploit Proxy Scraper — Authentication Module
JWT-based auth with bcrypt password hashing, API key support
"""
import os
import secrets
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
import bcrypt
from fastapi import HTTPException, Request, status

logger = logging.getLogger("auth")

# ─── Configuration ───────────────────────────────────────────
SECRET_KEY = None
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # 8 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30
SECRET_FILE = "/home/kenxploit/proxy-scraper/.secret"

def init_auth():
    """Initialize or load secret key."""
    global SECRET_KEY
    if SECRET_KEY is not None:
        return
    
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "r") as f:
            SECRET_KEY = f.read().strip()
        logger.info("[AUTH] Loaded existing secret key")
    else:
        SECRET_KEY = secrets.token_hex(64)
        os.makedirs(os.path.dirname(SECRET_FILE), exist_ok=True)
        with open(SECRET_FILE, "w") as f:
            f.write(SECRET_KEY)
        os.chmod(SECRET_FILE, 0o600)
        logger.info("[AUTH] Generated new secret key")

def get_secret() -> str:
    if SECRET_KEY is None:
        init_auth()
    return SECRET_KEY

# ─── Password Hashing ────────────────────────────────────────
def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ─── JWT Tokens ──────────────────────────────────────────────
def create_token(username: str, remember: bool = False) -> str:
    """Create JWT access token."""
    expiry_minutes = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 if remember else ACCESS_TOKEN_EXPIRE_MINUTES
    expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    payload = {
        "sub": username,
        "exp": expiry,
        "iat": int(time.time()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, get_secret(), algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    """Verify JWT token and return username."""
    try:
        payload = jwt.decode(token, get_secret(), algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─── FastAPI Dependencies ────────────────────────────────────
async def get_current_user(request: Request) -> str:
    """Extract and verify user from request (cookie or header)."""
    token = request.cookies.get("token")
    
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            from database import verify_api_key
            user = await verify_api_key(api_key)
            if user:
                return user
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_token(token)

async def optional_user(request: Request) -> Optional[str]:
    """Try to get user but don't fail if not authenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

# ─── Initialization ──────────────────────────────────────────
init_auth()
