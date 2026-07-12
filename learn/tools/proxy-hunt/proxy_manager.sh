#!/bin/bash
# ============================================================
# KENXPROXY - Proxy Scraper & Validator v2.0
# Scrape dari 20+ sumber, verifikasi beneran, output bersih
# Usage: bash proxy_manager.sh [scrape|validate|status|rotate|clean]
# ============================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

# Directories
BASE_DIR="/home/keandra/kenxploit/tools/proxy-hunt"
RAW_DIR="${BASE_DIR}/raw"
VERIFIED_DIR="${BASE_DIR}/verified"
LOG_DIR="${BASE_DIR}/logs"
mkdir -p "$RAW_DIR" "$VERIFIED_DIR" "$LOG_DIR"

# Files
RAW_HTTP="${RAW_DIR}/raw_http.txt"
RAW_SOCKS4="${RAW_DIR}/raw_socks4.txt"
RAW_SOCKS5="${RAW_DIR}/raw_socks5.txt"
VERIFIED_HTTP="${VERIFIED_DIR}/http_verified.txt"
VERIFIED_SOCKS4="${VERIFIED_DIR}/socks4_verified.txt"
VERIFIED_SOCKS5="${VERIFIED_DIR}/socks5_verified.txt"
VERIFIED_ALL="${VERIFIED_DIR}/all_verified.txt"
LOG_FILE="${LOG_DIR}/proxy_$(date +%Y%m%d_%H%M%S).log"
FAILED_FILE="${VERIFIED_DIR}/failed.txt"

# Config
TIMEOUT=8
VALIDATE_TIMEOUT=10
THREADS=100
TEST_URL="http://httpbin.org/ip"
TEST_URLS=("http://httpbin.org/ip" "http://ip-api.com/json" "http://ipinfo.io/json" "http://ifconfig.me/ip")

# ============================================================
# PROXY SOURCES - 30+ sumber publik
# ============================================================
declare -a HTTP_SOURCES=(
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
    "https://raw.githubusercontent.com/proxylist-to/proxy-list/main/proxies/http.txt"
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt"
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt"
    "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/http.txt"
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt"
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/generated/http_proxies.txt"
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt"
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/https.txt"
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt"
    "https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/http_proxies.txt"
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt"
    "https://raw.githubusercontent.com/ProxySurf/ProxySurf/main/http.txt"
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http_proxies.txt"
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt"
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt"
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=yes&anonymity=elite"
    "https://www.proxy-list.download/api/v1/get?type=http"
    "https://www.proxy-list.download/api/v1/get?type=https"
)

declare -a SOCKS4_SOURCES=(
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt"
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt"
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt"
    "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks4.txt"
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt"
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt"
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt"
    "https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/socks4_proxies.txt"
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt"
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4_proxies.txt"
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all"
)

declare -a SOCKS5_SOURCES=(
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt"
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt"
    "https://raw.githubusercontent.com/ALIILAPROXY/Proxy-List/main/socks5.txt"
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt"
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt"
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt"
    "https://raw.githubusercontent.com/ErcinDedeworken/proxies/main/socks5_proxies.txt"
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt"
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5_proxies.txt"
    "https://raw.githubusercontent.com/ProxySurf/ProxySurf/main/socks5.txt"
    "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt"
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all"
)

# ============================================================
# FUNCTIONS
# ============================================================

banner() {
    echo -e "${CYAN}"
    cat << 'BANNER'
    ██╗  ██╗███████╗███╗   ██╗██╗  ██╗██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
    ██║ ██╔╝██╔════╝████╗  ██║╚██╗██╔╝██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
    █████╔╝ █████╗  ██╔██╗ ██║ ╚███╔╝ ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝
    ██╔═██╗ ██╔══╝  ██║╚██╗██║ ██╔██╗ ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝
    ██║  ██╗███████╗██║ ╚████║██╔╝ ██╗██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝
                    Proxy Scraper & Validator v2.0
BANNER
    echo -e "${NC}"
}

log() {
    local msg="[$(date '+%H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

# ============================================================
# SCRAPE - Download proxy dari semua sumber
# ============================================================
scrape_proxy() {
    local type=$1
    shift
    local -a sources=("$@")
    local output_file
    
    case "$type" in
        http)   output_file="$RAW_HTTP" ;;
        socks4) output_file="$RAW_SOCKS4" ;;
        socks5) output_file="$RAW_SOCKS5" ;;
    esac
    
    > "$output_file"
    local total=0
    
    log "${YELLOW}[*] Scraping ${type^^} proxy dari ${#sources[@]} sumber...${NC}"
    
    for url in "${sources[@]}"; do
        local fname=$(basename "$url" | cut -d'?' -f1)
        local count=0
        
        # Download dengan timeout
        local content
        content=$(curl -sk --connect-timeout 10 --max-time 20 \
            -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
            "$url" 2>/dev/null || true)
        
        if [[ -n "$content" ]]; then
            # Extract IP:PORT pattern
            echo "$content" | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}' >> "$output_file" 2>/dev/null || true
            count=$(echo "$content" | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}' 2>/dev/null | wc -l | tr -d '[:space:]')
            [[ -z "$count" ]] && count=0
            total=$((total + count))
        fi
        
        if [[ $count -gt 0 ]]; then
            log "  ${GREEN}[+]${NC} ${fname}: ${count} proxy"
        else
            log "  ${RED}[-]${NC} ${fname}: gagal/kosong"
        fi
    done
    
    # Deduplicate & clean
    if [[ -f "$output_file" ]]; then
        # Remove invalid IPs, deduplicate
        awk -F: '
        {
            ip=$1; port=$2
            n=split(ip, octet, ".")
            if (n==4 && octet[1]<=255 && octet[2]<=255 && octet[3]<=255 && octet[4]<=255 && port>=1 && port<=65535)
                print
        }' "$output_file" | sort -u > "${output_file}.tmp"
        mv "${output_file}.tmp" "$output_file"
        local unique=$(wc -l < "$output_file")
        log "${GREEN}[+] Total ${type^^} unik: ${unique} proxy${NC}"
    fi
}

scrape_all() {
    log "${MAGENTA}========================================${NC}"
    log "${MAGENTA}  PHASE 1: SCRAPING PROXY${NC}"
    log "${MAGENTA}========================================${NC}"
    
    scrape_proxy "http" "${HTTP_SOURCES[@]}"
    scrape_proxy "socks4" "${SOCKS4_SOURCES[@]}"
    scrape_proxy "socks5" "${SOCKS5_SOURCES[@]}"
    
    local total_http=$(wc -l < "$RAW_HTTP" 2>/dev/null || echo 0)
    local total_s4=$(wc -l < "$RAW_SOCKS4" 2>/dev/null || echo 0)
    local total_s5=$(wc -l < "$RAW_SOCKS5" 2>/dev/null || echo 0)
    local total=$((total_http + total_s4 + total_s5))
    
    log ""
    log "${CYAN}[*] TOTAL RAW PROXY: ${total}${NC}"
    log "${CYAN}    HTTP:   ${total_http}${NC}"
    log "${CYAN}    SOCKS4: ${total_s4}${NC}"
    log "${CYAN}    SOCKS5: ${total_s5}${NC}"
}

# ============================================================
# VALIDATE - Verifikasi proxy beneran bisa dipake
# ============================================================

# Validate single HTTP proxy
validate_http() {
    local proxy=$1
    local ip=$(echo "$proxy" | cut -d: -f1)
    local port=$(echo "$proxy" | cut -d: -f2)
    
    # Test 1: Basic connectivity via curl
    local result
    result=$(curl -sk --proxy "http://${proxy}" \
        --connect-timeout "$VALIDATE_TIMEOUT" \
        --max-time $((VALIDATE_TIMEOUT + 5)) \
        -o /dev/null -w "%{http_code}|%{time_total}|%{remote_ip}" \
        "$TEST_URL" 2>/dev/null || echo "000|0|fail")
    
    local status=$(echo "$result" | cut -d'|' -f1)
    local latency=$(echo "$result" | cut -d'|' -f2)
    local remote_ip=$(echo "$result" | cut -d'|' -f3)
    
    # Must get 200 and IP must differ from proxy IP (meaning traffic routed through proxy)
    if [[ "$status" == "200" ]]; then
        # Test 2: Verify IP actually changed (proxy is working)
        local my_ip
        my_ip=$(curl -sk --max-time 5 "http://ifconfig.me/ip" 2>/dev/null || echo "unknown")
        
        if [[ "$remote_ip" != "$my_ip" && "$remote_ip" != "fail" && -n "$remote_ip" ]]; then
            echo "VALID|${proxy}|http|${latency}|${remote_ip}"
            return 0
        fi
    fi
    
    echo "FAIL|${proxy}|http|0|0"
    return 1
}

# Validate single SOCKS4 proxy
validate_socks4() {
    local proxy=$1
    
    # Test via curl with socks4
    local result
    result=$(curl -sk --socks4 "${proxy}" \
        --connect-timeout "$VALIDATE_TIMEOUT" \
        --max-time $((VALIDATE_TIMEOUT + 5)) \
        -o /dev/null -w "%{http_code}|%{time_total}|%{remote_ip}" \
        "$TEST_URL" 2>/dev/null || echo "000|0|fail")
    
    local status=$(echo "$result" | cut -d'|' -f1)
    local latency=$(echo "$result" | cut -d'|' -f2)
    local remote_ip=$(echo "$result" | cut -d'|' -f3)
    
    if [[ "$status" == "200" && "$remote_ip" != "fail" ]]; then
        echo "VALID|${proxy}|socks4|${latency}|${remote_ip}"
        return 0
    fi
    
    echo "FAIL|${proxy}|socks4|0|0"
    return 1
}

# Validate single SOCKS5 proxy
validate_socks5() {
    local proxy=$1
    
    # Test via curl with socks5
    local result
    result=$(curl -sk --socks5-hostname "${proxy}" \
        --connect-timeout "$VALIDATE_TIMEOUT" \
        --max-time $((VALIDATE_TIMEOUT + 5)) \
        -o /dev/null -w "%{http_code}|%{time_total}|%{remote_ip}" \
        "$TEST_URL" 2>/dev/null || echo "000|0|fail")
    
    local status=$(echo "$result" | cut -d'|' -f1)
    local latency=$(echo "$result" | cut -d'|' -f2)
    local remote_ip=$(echo "$result" | cut -d'|' -f3)
    
    if [[ "$status" == "200" && "$remote_ip" != "fail" ]]; then
        # Double check dengan test URL kedua
        local check2
        check2=$(curl -sk --socks5-hostname "${proxy}" \
            --connect-timeout "$VALIDATE_TIMEOUT" \
            --max-time $((VALIDATE_TIMEOUT + 5)) \
            -o /dev/null -w "%{http_code}" \
            "http://ip-api.com/json" 2>/dev/null || echo "000")
        
        if [[ "$check2" == "200" ]]; then
            echo "VALID|${proxy}|socks5|${latency}|${remote_ip}"
            return 0
        fi
    fi
    
    echo "FAIL|${proxy}|socks5|0|0"
    return 1
}

# Batch validate using xargs + parallel
validate_batch() {
    local type=$1
    local input_file=$2
    local output_file=$3
    
    if [[ ! -f "$input_file" || ! -s "$input_file" ]]; then
        log "${RED}[!] File $input_file kosong/tidak ada${NC}"
        return
    fi
    
    local total=$(wc -l < "$input_file")
    log "${YELLOW}[*] Validating ${total} ${type^^} proxy (threads: ${THREADS}, timeout: ${VALIDATE_TIMEOUT}s)...${NC}"
    
    # Use xargs for parallel execution
    > "${output_file}.tmp"
    > "${FAILED_FILE}.${type}"
    
    local count=0
    local valid=0
    
    while IFS= read -r proxy; do
        [[ -z "$proxy" ]] && continue
        ((count++))
        
        # Run validation in background (batch of THREADS)
        (
            case "$type" in
                http)   validate_http "$proxy" ;;
                socks4) validate_socks4 "$proxy" ;;
                socks5) validate_socks5 "$proxy" ;;
            esac
        ) >> "${output_file}.tmp" &
        
        # Limit concurrent threads
        if (( count % THREADS == 0 )); then
            wait
            # Progress update
            local current_valid=$(grep -c "^VALID" "${output_file}.tmp" 2>/dev/null || echo 0)
            printf "\r  ${CYAN}[*] Progress: %d/%d | Valid: %d${NC}" "$count" "$total" "$current_valid"
        fi
    done < "$input_file"
    
    wait
    echo ""
    
    # Parse results
    grep "^VALID" "${output_file}.tmp" | cut -d'|' -f2,3,4,5 > "$output_file" 2>/dev/null || true
    grep "^FAIL" "${output_file}.tmp" | cut -d'|' -f2 >> "${FAILED_FILE}.${type}" 2>/dev/null || true
    
    valid=$(wc -l < "$output_file" 2>/dev/null || echo 0)
    
    # Sort by latency (fastest first)
    if [[ -s "$output_file" ]]; then
        sort -t'|' -k3 -n "$output_file" > "${output_file}.sorted"
        mv "${output_file}.sorted" "$output_file"
    fi
    
    log "${GREEN}[+] ${type^^} valid: ${valid}/${total}${NC}"
    rm -f "${output_file}.tmp" 2>/dev/null
}

validate_all() {
    log ""
    log "${MAGENTA}========================================${NC}"
    log "${MAGENTA}  PHASE 2: VERIFIKASI PROXY${NC}"
    log "${MAGENTA}========================================${NC}"
    log ""
    
    validate_batch "http" "$RAW_HTTP" "$VERIFIED_HTTP"
    validate_batch "socks4" "$RAW_SOCKS4" "$VERIFIED_SOCKS4"
    validate_batch "socks5" "$RAW_SOCKS5" "$VERIFIED_SOCKS5"
    
    # Merge all verified
    > "$VERIFIED_ALL"
    [[ -s "$VERIFIED_HTTP" ]] && while IFS='|' read -r proxy type latency rip; do
        echo "http://${proxy} | latency: ${latency}s | exit_ip: ${rip}"
    done < "$VERIFIED_HTTP" >> "$VERIFIED_ALL"
    
    [[ -s "$VERIFIED_SOCKS4" ]] && while IFS='|' read -r proxy type latency rip; do
        echo "socks4://${proxy} | latency: ${latency}s | exit_ip: ${rip}"
    done < "$VERIFIED_SOCKS4" >> "$VERIFIED_ALL"
    
    [[ -s "$VERIFIED_SOCKS5" ]] && while IFS='|' read -r proxy type latency rip; do
        echo "socks5://${proxy} | latency: ${latency}s | exit_ip: ${rip}"
    done < "$VERIFIED_SOCKS5" >> "$VERIFIED_ALL"
    
    show_status
}

# ============================================================
# STATUS - Show stats
# ============================================================
show_status() {
    log ""
    log "${MAGENTA}========================================${NC}"
    log "${MAGENTA}  PROXY STATUS${NC}"
    log "${MAGENTA}========================================${NC}"
    
    local raw_http=$(wc -l < "$RAW_HTTP" 2>/dev/null || echo 0)
    local raw_s4=$(wc -l < "$RAW_SOCKS4" 2>/dev/null || echo 0)
    local raw_s5=$(wc -l < "$RAW_SOCKS5" 2>/dev/null || echo 0)
    local val_http=$(wc -l < "$VERIFIED_HTTP" 2>/dev/null || echo 0)
    local val_s4=$(wc -l < "$VERIFIED_SOCKS4" 2>/dev/null || echo 0)
    local val_s5=$(wc -l < "$VERIFIED_SOCKS5" 2>/dev/null || echo 0)
    local total_raw=$((raw_http + raw_s4 + raw_s5))
    local total_val=$((val_http + val_s4 + val_s5))
    
    log ""
    log "${WHITE}┌─────────────────────────────────────────────────┐${NC}"
    log "${WHITE}│           RAW PROXY (belum diverifikasi)        │${NC}"
    log "${WHITE}├─────────────────────────────────────────────────┤${NC}"
    log "${WHITE}│  HTTP:    ${CYAN}$(printf '%6s' "$raw_http")${WHITE}                              │${NC}"
    log "${WHITE}│  SOCKS4:  ${CYAN}$(printf '%6s' "$raw_s4")${WHITE}                              │${NC}"
    log "${WHITE}│  SOCKS5:  ${CYAN}$(printf '%6s' "$raw_s5")${WHITE}                              │${NC}"
    log "${WHITE}│  TOTAL:   ${YELLOW}$(printf '%6s' "$total_raw")${WHITE}                              │${NC}"
    log "${WHITE}├─────────────────────────────────────────────────┤${NC}"
    log "${WHITE}│           VERIFIED PROXY (aktif & tested)       │${NC}"
    log "${WHITE}├─────────────────────────────────────────────────┤${NC}"
    log "${WHITE}│  HTTP:    ${GREEN}$(printf '%6s' "$val_http")${WHITE}                              │${NC}"
    log "${WHITE}│  SOCKS4:  ${GREEN}$(printf '%6s' "$val_s4")${WHITE}                              │${NC}"
    log "${WHITE}│  SOCKS5:  ${GREEN}$(printf '%6s' "$val_s5")${WHITE}                              │${NC}"
    log "${WHITE}│  TOTAL:   ${GREEN}$(printf '%6s' "$total_val")${WHITE}                              │${NC}"
    log "${WHITE}└─────────────────────────────────────────────────┘${NC}"
    log ""
    
    if [[ $total_val -gt 0 ]]; then
        log "${GREEN}[+] File lokasi:${NC}"
        log "    Raw:       ${RAW_DIR}/"
        log "    Verified:  ${VERIFIED_DIR}/"
        log "    Logs:      ${LOG_DIR}/"
        log ""
        log "${CYAN}[*] Top 10 Fastest Verified Proxy:${NC}"
        head -10 "$VERIFIED_ALL" 2>/dev/null | while read -r line; do
            log "    ${GREEN}✓${NC} $line"
        done
    fi
}

# ============================================================
# CLEAN - Remove dead proxies, keep only verified
# ============================================================
clean_proxies() {
    log "${YELLOW}[*] Cleaning proxy lists...${NC}"
    
    for file in "$VERIFIED_HTTP" "$VERIFIED_SOCKS4" "$VERIFIED_SOCKS5"; do
        if [[ -f "$file" ]]; then
            local before=$(wc -l < "$file")
            # Remove duplicates
            sort -u "$file" > "${file}.tmp"
            mv "${file}.tmp" "$file"
            local after=$(wc -l < "$file")
            log "  [+] $(basename $file): ${before} -> ${after}"
        fi
    done
    
    log "${GREEN}[+] Clean complete${NC}"
}

# ============================================================
# ROTATE - Pick random verified proxy
# ============================================================
rotate_proxy() {
    local type=${1:-"all"}
    local count=${2:-1}
    
    local file
    case "$type" in
        http)   file="$VERIFIED_HTTP" ;;
        socks4) file="$VERIFIED_SOCKS4" ;;
        socks5) file="$VERIFIED_SOCKS5" ;;
        all)    file="$VERIFIED_ALL" ;;
    esac
    
    if [[ ! -f "$file" || ! -s "$file" ]]; then
        log "${RED}[!] Tidak ada verified proxy untuk ${type}${NC}"
        return 1
    fi
    
    log "${CYAN}[*] Random ${type^^} proxy:${NC}"
    shuf -n "$count" "$file" | while read -r line; do
        echo "    ${GREEN}→${NC} $line"
    done
}

# ============================================================
# EXPORT - Export untuk tools lain
# ============================================================
export_proxies() {
    local format=${1:-"plain"}
    local output="${VERIFIED_DIR}/export_$(date +%Y%m%d_%H%M%S).txt"
    
    case "$format" in
        plain)
            # ip:port format
            cat "$VERIFIED_HTTP" "$VERIFIED_SOCKS4" "$VERIFIED_SOCKS5" 2>/dev/null | \
                cut -d'|' -f1 | sort -u > "$output"
            ;;
        curl)
            # --proxy format
            while IFS='|' read -r proxy type latency rip; do
                echo "--proxy ${type}://${proxy}"
            done < "$VERIFIED_HTTP" > "$output"
            while IFS='|' read -r proxy type latency rip; do
                echo "--proxy socks4://${proxy}"
            done < "$VERIFIED_SOCKS4" >> "$output"
            while IFS='|' read -r proxy type latency rip; do
                echo "--proxy socks5://${proxy}"
            done < "$VERIFIED_SOCKS5" >> "$output"
            ;;
        python)
            # Python requests format
            echo "# Verified proxies - $(date)" > "$output"
            echo "PROXIES = [" >> "$output"
            while IFS='|' read -r proxy type latency rip; do
                echo "    {'http': 'http://${proxy}', 'https': 'http://${proxy}'}," >> "$output"
            done < "$VERIFIED_HTTP"
            while IFS='|' read -r proxy type latency rip; do
                echo "    {'http': 'socks4://${proxy}', 'https': 'socks4://${proxy}'}," >> "$output"
            done < "$VERIFIED_SOCKS4"
            while IFS='|' read -r proxy type latency rip; do
                echo "    {'http': 'socks5://${proxy}', 'https': 'socks5://${proxy}'}," >> "$output"
            done < "$VERIFIED_SOCKS5"
            echo "]" >> "$output"
            ;;
    esac
    
    log "${GREEN}[+] Exported ke: ${output}${NC}"
}

# ============================================================
# MAIN
# ============================================================
banner

case "${1:-help}" in
    scrape)
        scrape_all
        ;;
    validate)
        validate_all
        ;;
    status)
        show_status
        ;;
    clean)
        clean_proxies
        ;;
    rotate)
        rotate_proxy "${2:-all}" "${3:-5}"
        ;;
    export)
        export_proxies "${2:-plain}"
        ;;
    all)
        scrape_all
        validate_all
        ;;
    help|*)
        echo -e "${WHITE}Usage:${NC}"
        echo "  bash proxy_manager.sh scrape     - Scrape proxy dari 30+ sumber"
        echo "  bash proxy_manager.sh validate   - Verifikasi semua raw proxy"
        echo "  bash proxy_manager.sh all        - Scrape + validate (full run)"
        echo "  bash proxy_manager.sh status     - Show stats"
        echo "  bash proxy_manager.sh clean      - Remove duplicates"
        echo "  bash proxy_manager.sh rotate [type] [count] - Random proxy"
        echo "  bash proxy_manager.sh export [format] - Export (plain/curl/python)"
        echo ""
        echo -e "${CYAN}Proxy Types: http, socks4, socks5, all${NC}"
        echo -e "${CYAN}Output: ${VERIFIED_DIR}/${NC}"
        ;;
esac
