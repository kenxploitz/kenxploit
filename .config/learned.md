# KenXploit Learning Database

---

## Teknik Exploit Yang Berhasil

### 1. Express.js Registration + Dashboard Access
- **Cek**: POST /register with email, password, confirmPassword
- **Exploit**: Registration creates user, returns JWT cookie, redirects to /dashboard
- **Impact**: User-level access, API key management, billing, profile
- **Kapan work**: Express app with open registration
- **JWT Format**: token cookie with HS256, payload includes id, email, role, iat, exp

### 2. Internal Service Discovery via Port Scan
- **Cek**: Port scan on origin server IP
- **Exploit**: Found internal ports on origin server
- **Impact**: Direct access to internal services bypassing nginx
- **Chain**: Origin IP → port scan → admin panel, API gateway

### 3. Stack Trace Disclosure via Invalid POST Body
- **Cek**: POST JSON to form-urlencoded-only endpoint
- **Exploit**: Send Content-Type: application/json to endpoint that only accepts urlencoded
- **Impact**: Full server path disclosure including source code location
- **Kapan work**: Express app with different body parsers for different routes

### 4. JWT Token Extraction from Dashboard
- **Cek**: Register account, capture Set-Cookie header
- **Exploit**: JWT token contains user ID, email, and ROLE
- **Impact**: User enumeration, role discovery (developer vs admin)
- **Kapan work**: Express apps with JWT auth storing role in payload

### 5. API Key Exposure in Server-side Rendered HTML
- **Cek**: Dashboard page HTML source
- **Exploit**: API keys are rendered server-side in the keys tab content
- **Impact**: Full API key access without needing to generate/copy
- **Kapan work**: Express apps that render sensitive data in initial HTML

### 6. OAuth Open Redirect Account Takeover
- **Cek**: OAuth state parameter accepts any domain
- **Exploit**: Manipulate state parameter to redirect auth code to attacker domain
- **Impact**: Full account takeover via stolen auth code
- **Kapan work**: OAuth implementations with weak state validation

### 7. SQL Query Information Disclosure
- **Cek**: Send invalid UUID/ID to API endpoint
- **Exploit**: Full SQL query leaked in error response
- **Impact**: Database schema disclosure, table names, column names
- **Kapan work**: Frameworks with debug mode or verbose error handling

### 8. Cloudflare AES Challenge Bypass
- **Cek**: Analyze anti-bot cookie encryption
- **Exploit**: Decrypt AES-128-CBC cookie with hardcoded key/IV
- **Impact**: Bypass Cloudflare managed challenge
- **Kapan work**: Custom Cloudflare implementations with static encryption keys

### 9. IDOR in API Endpoints
- **Cek**: Enumerate IDs in list endpoint
- **Exploit**: Access other users' data by changing ID parameter
- **Impact**: Full data access across all users
- **Kapan work**: APIs without proper authorization checks

### 10. Unauthenticated API Access
- **Cek**: Test API endpoints without auth tokens
- **Exploit**: CRUD operations available without authentication
- **Impact**: Full data manipulation (read, create, update, delete)
- **Kapan work**: APIs missing authentication middleware

---

## WAF Bypass Techniques

### Cloudflare
- AES-128-CBC cookie decryption
- Per-request ciphertext analysis
- Challenge token replay

### Generic WAF
- Case variation (SeLeCt, UnIoN)
- Comment injection (/*!50000SELECT*/)
- HTTP header injection
- HTTP method confusion
- Content-type switching
- Chunked encoding bypass
- JSON bypass
- Unicode normalization
- IP rotation
- HTTP/2 smuggling

---

## Race Condition Techniques

### Best Tools
- aiohttp with TCPConnector(limit=0, force_close=True)
- Python asyncio for parallel requests
- golang for high-concurrency testing

### Target Types
- Balance transfer
- Coupon redemption
- Vote manipulation
- Order creation
- File upload

---

## JWT Attack Reference

### Algorithm Confusion
- RS256 → HS256 confusion
- None algorithm bypass
- Key injection via jku/kid

### Common Weaknesses
- Hardcoded secrets
- Predictable secrets
- Missing signature verification
- Algorithm bypass

---

## PHP Exploit Chains

### PHPUnit CVE-2017-9841
- Path: /vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php
- Method: POST with PHP code
- Impact: Instant RCE

### Laravel Ignition CVE-2021-3129
- Path: /_ignition/execute-solution
- Method: PHP filter chain
- Impact: RCE via log poisoning

### PHPGGC Deserialization
- Framework-specific gadget chains
- phar:// protocol abuse
- Impact: RCE via deserialization

---

## SSRF Advanced Techniques

### Cloud Metadata
- AWS: http://169.254.169.254/latest/meta-data/
- GCP: http://metadata.google.internal/computeMetadata/v1/
- Azure: http://169.254.169.254/metadata/instance

### Protocol Smuggling
- gopher:// for Redis/Memcached
- dict:// for service enumeration
- file:// for local file read

---

## Notes

- Always chain vulnerabilities for maximum impact
- One deep exploit > 10 shallow findings
- Document technique, not target
- Focus on RCE > SQLi > LFI > SSRF
