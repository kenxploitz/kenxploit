"""
KenXploit Proxy Scraper — Main Entry Point v2
"""
import os
import sys
import logging

# Make sure we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
log_dir = "/home/kenxploit/proxy-scraper"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, 'scraper.log')),
    ]
)

logger = logging.getLogger("main")
logger.info("=" * 60)
logger.info("  KenXploit Proxy Scraper v2.0")
logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8899,
        log_level="info",
        access_log=True,
        workers=1,
        ws_ping_interval=30,
        ws_ping_timeout=10,
        forwarded_allow_ips="*",
        proxy_headers=True,
    )
