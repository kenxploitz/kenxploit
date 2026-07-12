#!/bin/bash

# ============================================================
# KenXploit Uninstaller
# ============================================================
# Universal uninstaller for Linux & macOS
# - Remove wrapper from /usr/local/bin
# - Remove local wrapper
# - Clean PATH from shell config
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

KENXPLOIT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")" && pwd)"
BIN_DIR="/usr/local/bin"
WRAPPER="$BIN_DIR/kenxploit"
LOCAL_WRAPPER="$KENXPLOIT_DIR/kenxploit-wrapper"

banner() {
  echo -e "${CYAN}"
  echo "╔══════════════════════════════════════════════╗"
  echo "║         KenXploit Uninstaller                ║"
  echo "║   Remove KenXploit from PATH                 ║"
  echo "╚══════════════════════════════════════════════╝"
  echo -e "${NC}"
}

info()    { echo -e "  ${GREEN}[+]${NC} $1"; }
warn()    { echo -e "  ${YELLOW}[!]${NC} $1"; }
success() { echo -e "  ${GREEN}[✓]${NC} $1"; }
fail()    { echo -e "  ${RED}[x]${NC} $1"; }

# ============================================================

banner

# --- Cek root ---
if [ "$EUID" -ne 0 ] && [ "$(uname)" != "Darwin" ]; then
  fail "Requires root privileges."
  warn  "Run with: sudo ./uninstall.sh"
  exit 1
fi

REMOVED=0

# --- Step 1: Hapus wrapper dari /usr/local/bin ---
info "Removing wrapper from /usr/local/bin..."
if [ -f "$WRAPPER" ]; then
  rm -f "$WRAPPER"
  success "Removed: $WRAPPER"
  REMOVED=1
else
  warn "Not found: $WRAPPER"
fi

# --- Step 2: Hapus wrapper lokal ---
info "Removing local wrapper..."
if [ -f "$LOCAL_WRAPPER" ]; then
  rm -f "$LOCAL_WRAPPER"
  success "Removed: $LOCAL_WRAPPER"
  REMOVED=1
else
  warn "Not found: $LOCAL_WRAPPER"
fi

# --- Step 3: Bersihkan PATH dari shell config ---
info "Cleaning PATH from shell config..."

for RC_FILE in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
  if [ -f "$RC_FILE" ] && grep -q "# KenXploit" "$RC_FILE" 2>/dev/null; then
    sed -i '/# KenXploit/d' "$RC_FILE" 2>/dev/null
    sed -i "\|$KENXPLOIT_DIR|d" "$RC_FILE" 2>/dev/null
    success "Cleaned: $RC_FILE"
    REMOVED=1
  fi
done

# --- Step 4: Dependencies ---
info "Python dependencies..."
if [ -f "$KENXPLOIT_DIR/requirements.txt" ]; then
  warn "Dependencies kept (not removed)"
  echo "  To remove manually: pip uninstall -r requirements.txt"
fi

# --- Done ---
echo ""
if [ "$REMOVED" -eq 1 ]; then
  echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║       Uninstall Complete!                     ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
else
  echo -e "${YELLOW}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${YELLOW}║       Nothing to remove                       ║${NC}"
  echo -e "${YELLOW}╚══════════════════════════════════════════════╝${NC}"
fi
echo ""
echo "  KenXploit directory: $KENXPLOIT_DIR"
echo "  To delete everything: rm -rf $KENXPLOIT_DIR"
echo ""
warn "Open a new terminal to apply PATH changes."
echo ""
