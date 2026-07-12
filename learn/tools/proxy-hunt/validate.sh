#!/bin/bash
# ============================================================
# KENXPROXY - Fast Parallel Validator v2.0
# Verifikasi proxy beneran bisa dipake (HTTP request test)
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BASE_DIR="/home/keandra/kenxploit/tools/proxy-hunt"
RAW_DIR="${BASE_DIR}/raw"
VERIFIED_DIR="${BASE_DIR}/verified"
mkdir -p "$VERIFIED_DIR"

THREADS=80
TIMEOUT=8

# Validate single HTTP proxy - test beneran lewat proxy
validate_http() {
    local proxy="$1"
    local result
    result=$(curl -sk --proxy "http://${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 4)) \
        -o /dev/null -w "%{http_code}|%{time_total}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000|0")
    
    local code=$(echo "$result" | cut -d'|' -f1)
    local latency=$(echo "$result" | cut -d'|' -f2)
    
    if [[ "$code" == "200" ]]; then
        echo "VALID|${proxy}|http|${latency}"
    fi
}

# Validate single SOCKS4 proxy
validate_socks4() {
    local proxy="$1"
    local result
    result=$(curl -sk --socks4 "${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 4)) \
        -o /dev/null -w "%{http_code}|%{time_total}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000|0")
    
    local code=$(echo "$result" | cut -d'|' -f1)
    local latency=$(echo "$result" | cut -d'|' -f2)
    
    if [[ "$code" == "200" ]]; then
        echo "VALID|${proxy}|socks4|${latency}"
    fi
}

# Validate single SOCKS5 proxy - double check
validate_socks5() {
    local proxy="$1"
    
    # Test 1: httpbin
    local r1
    r1=$(curl -sk --socks5-hostname "${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 4)) \
        -o /dev/null -w "%{http_code}|%{time_total}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000|0")
    
    local code1=$(echo "$r1" | cut -d'|' -f1)
    local latency=$(echo "$r1" | cut -d'|' -f2)
    
    if [[ "$code1" == "200" ]]; then
        # Test 2: ipinfo (double verify)
        local code2
        code2=$(curl -sk --socks5-hostname "${proxy}" \
            --connect-timeout "$TIMEOUT" \
            --max-time $((TIMEOUT + 4)) \
            -o /dev/null -w "%{http_code}" \
            "http://ipinfo.io/json" 2>/dev/null || echo "000")
        
        if [[ "$code2" == "200" ]]; then
            echo "VALID|${proxy}|socks5|${latency}"
        fi
    fi
}

export -f validate_http validate_socks4 validate_socks5
export TIMEOUT

# Run validation in parallel
run_validate() {
    local type=$1
    local input=$2
    local output=$3
    
    if [[ ! -s "$input" ]]; then
        echo -e "${RED}[!] $input kosong${NC}"
        return
    fi
    
    local total=$(wc -l < "$input")
    echo -e "${YELLOW}[*] Validating ${total} ${type^^} proxy (threads: ${THREADS})...${NC}"
    
    # Use xargs for parallel
    > "${output}.tmp"
    
    cat "$input" | xargs -P "$THREADS" -I {} bash -c "validate_${type} '{}'" >> "${output}.tmp" 2>/dev/null
    
    # Parse valid results
    grep "^VALID" "${output}.tmp" | cut -d'|' -f2,3,4 | sort -t'|' -k3 -n > "$output"
    
    local valid=$(wc -l < "$output" 2>/dev/null || echo 0)
    echo -e "${GREEN}[+] ${type^^} valid: ${valid}/${total}${NC}"
    
    rm -f "${output}.tmp"
}

echo -e "${CYAN}"
echo "============================================"
echo "  KENXPROXY - Proxy Validator v2.0"
echo "  Threads: ${THREADS} | Timeout: ${TIMEOUT}s"
echo "============================================"
echo -e "${NC}"

# Get my IP for reference
MY_IP=$(curl -sk --max-time 5 "http://ifconfig.me/ip" 2>/dev/null || echo "unknown")
echo -e "${CYAN}[*] My IP: ${MY_IP}${NC}"
echo ""

# Validate all types in parallel (run all 3 at same time)
run_validate "http" "${RAW_DIR}/raw_http.txt" "${VERIFIED_DIR}/http_verified.txt" &
PID_HTTP=$!

run_validate "socks4" "${RAW_DIR}/raw_socks4.txt" "${VERIFIED_DIR}/socks4_verified.txt" &
PID_S4=$!

run_validate "socks5" "${RAW_DIR}/raw_socks5.txt" "${VERIFIED_DIR}/socks5_verified.txt" &
PID_S5=$!

wait $PID_HTTP $PID_S4 $PID_S5

# Merge all verified
> "${VERIFIED_DIR}/all_verified.txt"
for f in "${VERIFIED_DIR}/http_verified.txt" "${VERIFIED_DIR}/socks4_verified.txt" "${VERIFIED_DIR}/socks5_verified.txt"; do
    if [[ -s "$f" ]]; then
        cat "$f" >> "${VERIFIED_DIR}/all_verified.txt"
    fi
done

# Final stats
V_HTTP=$(wc -l < "${VERIFIED_DIR}/http_verified.txt" 2>/dev/null || echo 0)
V_S4=$(wc -l < "${VERIFIED_DIR}/socks4_verified.txt" 2>/dev/null || echo 0)
V_S5=$(wc -l < "${VERIFIED_DIR}/socks5_verified.txt" 2>/dev/null || echo 0)
V_ALL=$((V_HTTP + V_S4 + V_S5))

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  VERIFICATION COMPLETE${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  HTTP:    ${V_HTTP}${NC}"
echo -e "${GREEN}  SOCKS4:  ${V_S4}${NC}"
echo -e "${GREEN}  SOCKS5:  ${V_S5}${NC}"
echo -e "${GREEN}  TOTAL:   ${V_ALL} verified proxies${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${YELLOW}[*] Files saved:${NC}"
echo "    ${VERIFIED_DIR}/http_verified.txt"
echo "    ${VERIFIED_DIR}/socks4_verified.txt"
echo "    ${VERIFIED_DIR}/socks5_verified.txt"
echo "    ${VERIFIED_DIR}/all_verified.txt"
echo ""

# Show top 15 fastest
echo -e "${CYAN}[*] Top 15 Fastest Proxies:${NC}"
sort -t'|' -k3 -n "${VERIFIED_DIR}/all_verified.txt" | head -15 | while IFS='|' read -r proxy type latency; do
    printf "    ${GREEN}✓${NC} %-25s %-8s %ss\n" "$proxy" "$type" "$latency"
done
