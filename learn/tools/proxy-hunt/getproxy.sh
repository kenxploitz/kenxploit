#!/bin/bash
# ============================================================
# GETPROXY - Quick proxy picker untuk pentesting
# Usage: 
#   bash getproxy.sh           → random 1 proxy (all types)
#   bash getproxy.sh http      → random 1 HTTP proxy
#   bash getproxy.sh socks5    → random 1 SOCKS5 proxy
#   bash getproxy.sh 10        → random 10 proxy (all types)
#   bash getproxy.sh socks4 5  → random 5 SOCKS4 proxy
# ============================================================

PROXY_FILE="/home/keandra/kenxploit/tools/proxy-hunt/proxies_final.txt"

if [[ ! -f "$PROXY_FILE" ]]; then
    echo "[!] Proxy file not found: $PROXY_FILE"
    exit 1
fi

TYPE="${1:-all}"
COUNT="${2:-1}"

# If first arg is a number, treat as count
if [[ "$TYPE" =~ ^[0-9]+$ ]]; then
    COUNT="$TYPE"
    TYPE="all"
fi

case "$TYPE" in
    http)
        grep "^http://" "$PROXY_FILE" | shuf -n "$COUNT"
        ;;
    socks4)
        grep "^socks4://" "$PROXY_FILE" | shuf -n "$COUNT"
        ;;
    socks5)
        grep "^socks5://" "$PROXY_FILE" | shuf -n "$COUNT"
        ;;
    all|*)
        shuf -n "$COUNT" "$PROXY_FILE"
        ;;
esac
