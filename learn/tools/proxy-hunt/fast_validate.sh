#!/bin/bash
# ============================================================
# KENXPROXY - Ultra Fast Validator v3.0
# 150 threads, 5s timeout, fast fail
# ============================================================

BASE_DIR="/home/keandra/kenxploit/tools/proxy-hunt/raw"
OUT_DIR="/home/keandra/kenxploit/tools/proxy-hunt/verified"
mkdir -p "$OUT_DIR"

THREADS=150
TIMEOUT=5

validate_http() {
    local proxy="$1"
    local code
    code=$(curl -sk --proxy "http://${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 2)) \
        -o /dev/null -w "%{http_code}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000")
    [[ "$code" == "200" ]] && echo "$proxy"
}

validate_socks4() {
    local proxy="$1"
    local code
    code=$(curl -sk --socks4 "${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 2)) \
        -o /dev/null -w "%{http_code}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000")
    [[ "$code" == "200" ]] && echo "$proxy"
}

validate_socks5() {
    local proxy="$1"
    local code
    code=$(curl -sk --socks5-hostname "${proxy}" \
        --connect-timeout "$TIMEOUT" \
        --max-time $((TIMEOUT + 2)) \
        -o /dev/null -w "%{http_code}" \
        "http://httpbin.org/ip" 2>/dev/null || echo "000")
    [[ "$code" == "200" ]] && echo "$proxy"
}

export -f validate_http validate_socks4 validate_socks5
export TIMEOUT

run_batch() {
    local type=$1
    local input=$2
    local output=$3
    
    local total=$(wc -l < "$input")
    echo -e "\n[*] Validating ${total} ${type^^} proxy (threads: ${THREADS}, timeout: ${TIMEOUT}s)..."
    
    cat "$input" | xargs -P "$THREADS" -I {} bash -c "validate_${type} '{}'" > "$output" 2>/dev/null
    
    local valid=$(wc -l < "$output")
    echo "[+] ${type^^} verified: ${valid}/${total} ($(echo "scale=1; $valid * 100 / $total" | bc)%)"
}

echo "============================================"
echo "  KENXPROXY Ultra Fast Validator v3.0"
echo "  Threads: ${THREADS} | Timeout: ${TIMEOUT}s"
echo "============================================"

# Run all 3 in parallel
run_batch "http" "${BASE_DIR}/raw_http_final.txt" "${OUT_DIR}/http_verified_final.txt" &
PID1=$!

run_batch "socks4" "${BASE_DIR}/raw_socks4_final.txt" "${OUT_DIR}/socks4_verified_final.txt" &
PID2=$!

run_batch "socks5" "${BASE_DIR}/raw_socks5_final.txt" "${OUT_DIR}/socks5_verified_final.txt" &
PID3=$!

wait $PID1 $PID2 $PID3

# Merge
cat "${OUT_DIR}/http_verified_final.txt" \
    "${OUT_DIR}/socks4_verified_final.txt" \
    "${OUT_DIR}/socks5_verified_final.txt" | sort -u > "${OUT_DIR}/all_verified_final.txt"

# Stats
V_HTTP=$(wc -l < "${OUT_DIR}/http_verified_final.txt")
V_S4=$(wc -l < "${OUT_DIR}/socks4_verified_final.txt")
V_S5=$(wc -l < "${OUT_DIR}/socks5_verified_final.txt")
V_ALL=$(wc -l < "${OUT_DIR}/all_verified_final.txt")

echo ""
echo "============================================"
echo "  VERIFICATION COMPLETE"
echo "============================================"
echo "  HTTP:    ${V_HTTP}"
echo "  SOCKS4:  ${V_S4}"
echo "  SOCKS5:  ${V_S5}"
echo "  TOTAL:   ${V_ALL} verified proxies"
echo "============================================"
echo ""
echo "[*] Files:"
echo "    ${OUT_DIR}/http_verified_final.txt"
echo "    ${OUT_DIR}/socks4_verified_final.txt"
echo "    ${OUT_DIR}/socks5_verified_final.txt"
echo "    ${OUT_DIR}/all_verified_final.txt"
