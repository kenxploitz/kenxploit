# OSINT Advanced Techniques — Complete Guide
## Last Updated: 2026-07-10

## OSINT Framework Lengkap

### 1. DOMAIN & INFRASTRUCTURE RECON

#### ASN Discovery
```bash
# Find company's IP ranges
amass intel -org "company name"
bgp.he.net → search company name
ipinfo.io → search IP/ASN
asnlookup.com → free API
```

#### Reverse Whois Loop
```bash
# Find more domains from same owner
viewdns.info/reversewhois/
whoxy.com (historical whois)
reversewhois.io
domaineye.com/reverse-whois
# Loop: find new domain → whois → reverse whois → more domains
```

#### Certificate Transparency Deep
```bash
# crt.sh - all certs for domain
curl -sk "https://crt.sh/?q=%25.domain.com&output=json" | jq -r '.[].name_value' | sort -u

# Time correlation attack
# Same cert renewal time = same server/company
# Find domains renewed at same time → related domains

# Favicon hash → find same tech stack
curl -sk target/favicon.ico | python3 -c "import sys,mmh3,codecs;print(mmh3.hash(codecs.encode(sys.stdin.buffer.read(),'base64')))"
# Then search: shodan search "http.favicon.hash:HASH"
```

#### Tracker Correlation
```bash
# Same Google Analytics ID = same owner
# Same Adsense ID = same owner
# Tools: BuiltWith, SpyOnWeb, PublicWWW
# Search: site:publicwww.com "UA-XXXXXXX-X"
```

#### VHost Discovery
```bash
# Find hidden sites on same IP
ffuf -u http://IP -H "Host: FUZZ.domain.com" -w subdomains.txt -ac
gobuster vhost -u https://domain.com -w subdomains.txt
```

#### CORS Brute Force
```bash
# Discover subdomains via CORS reflection
ffuf -w subdomains.txt -u http://target -H 'Origin: http://FUZZ.target.com' -mr "Access-Control-Allow-Origin"
```

#### Passive Takeover
```bash
# Subdomain pointing to cloud IP you now own
# Spawn VM in DigitalOcean → check if any subdomain points to your new IP
# Use Virustotal subdomain records
```

### 2. EMAIL & CREDENTIAL OSINT

#### Email Enumeration — 10+ Sources
```bash
theHarvester -d domain.com -b all
hunter.io → pattern + verified emails
phonebook.cz → emails + phones
skrapp.io → email finder
rocketreach.co → employee directory
apollo.io → B2B database
snov.io → email finder
minelead.io → free API
emailhippo → verification
clearbit → company enrichment
```

#### Email Pattern Analysis
```
Common patterns:
- firstname.lastname@company.com (most common)
- flastname@company.com
- firstname.l@company.com
- firstname@company.com
- f.lastname@company.com
- first_last@company.com

Once pattern confirmed → enumerate all employees
```

#### Credential Breach Search
```bash
# Online databases
haveibeenpwned.com → email/phone
dehashed.com → email/username/name/IP/phone
snusbase.com → multi-search
leakcheck.io → fast lookup
intelx.io → dark web + breaches
crackstation.net → hash cracking

# Tool-based
h8mail -t target@email.com
holehe target@email.com (120+ services)
```

#### Credential Validation
```bash
# SMTP verification
telnet mx.domain.com 25
VRFY admin
EXPN root

# Check if email registered on services
holehe target@email.com
socialscan target@email.com
```

### 3. SOCIAL MEDIA DEEP DIVE

#### LinkedIn Intelligence
```bash
# Company employees
linkedin.com/search/results/people/?currentCompany=ID

# Extract: name, title, location, skills, certifications, education
# Key people: CTO (tech stack), DevOps (infra), Security (tools), IT Manager (topology)

# Ex-employees → old access, internal info
# Skills → tech stack: AWS, K8s, Terraform, Python, Laravel, React
```

#### GitHub Deep
```bash
# Find all company repos
github.com/orgs/company/repositories

# Find secrets
trufflehog github --org=company --only-verified
gitleaks detect --source /tmp/repo -v

# Search: .env, wp-config, config.php, database.yml, credentials, *.pem, *.key
# Search: password, secret, key, token, api_key in commit messages
# Search: CI/CD configs, Dockerfile, docker-compose.yml

# Developer repos → personal projects → same patterns
```

#### Telegram OSINT
```bash
# Bot API
curl -sk "https://api.telegram.org/botTOKEN/getMe"
curl -sk "https://api.telegram.org/botTOKEN/getUpdates"

# Search groups/channels
telesint -g keyword
tgstat.ru → channel search
tchannels.me → directory

# Phone lookup
telesint -n +62xxx
```

#### Discord OSINT
```bash
# Server info
curl -sk "https://discord.com/api/v9/invites/CODE?with_counts=true"

# Webhook abuse (if found)
curl -sk -X POST "https://discord.com/api/webhooks/ID/TOKEN" -d "content=test"
```

#### Face Recognition
```bash
pimeyes.com → face search
facecheck.id → reverse face search
search4faces.com → social media face match
```

### 4. SHODAN & CENSYS MASTERY

#### Shodan Queries
```bash
# Find all company services
shodan search "org:Company Name"
shodan search "hostname:domain.com"
shodan search "ssl.cert.subject.CN:domain.com"

# Find specific vulns
shodan search "Apache/2.4.49" → CVE-2021-41773
shodan search "nginx/1.18.0" → path traversal
shodan search "http.favicon.hash:HASH" → same tech

# Find databases
shodan search "port:6379" → Redis
shodan search "port:27017" → MongoDB
shodan search "port:9200" → Elasticsearch
shodan search "port:5601" → Kibana
```

#### Censys Queries
```bash
# Find hosts
censys search "domain.com"
censys search "services.service_name:HTTP and services.http.response.html_title:Company"

# Certificate search
censys search "parsed.subject.common_name:domain.com"
```

### 5. DARK WEB MONITORING

#### Sources
```bash
# Clearnet accessible
ahmia.fi → Tor search engine
darksearch.io → dark web search
breachforums.is → breach database
exploit.in → Russian forum

# Telegram leak channels
# Search: "domain.com" or "company name"

# Tools
spiderfoot → automated OSINT with Tor support
```

### 6. IMAGE OSINT

```bash
# Reverse image search
Google Images → images.google.com
Yandex Images → yandex.com/images (best for faces)
TinEye → tineye.com (exact match)

# EXIF extraction
exiftool image.jpg → GPS, camera, date, software

# Geolocation from photo
# Look for: landmarks, signs, license plates, vegetation, architecture
```

### 7. PHONE NUMBER OSINT

```bash
# Name lookup
TrueCaller → name + carrier
GetContact → name tags

# Validation
numverify.com → carrier + location

# Social media
whatsapp → save number → check profile
telegram → search number
google → "+62xxx-xxxx-xxxx"
```

### 8. DATA CORRELATION PATTERNS

#### Pattern 1: Email → LinkedIn → GitHub → Creds → Infra
```
Email from theHarvester → LinkedIn (name+title+skill) → GitHub (commits, secrets)
→ Creds leak (password) → Login to infra
```

#### Pattern 2: Domain → Tech Stack → CVE → Exploit
```
whatweb detect Laravel → /version.txt Laravel 5.6 → CVE-2018-15133 → phpggc
```

#### Pattern 3: Job Posting → Tech Stack → Vulnerable Surface
```
DevOps job: AWS, K8s → check S3 bucket, kubeconfig, docker.sock
Backend job: Laravel → check .env, debug mode, /_ignition
```

#### Pattern 4: Employee → Email Pattern → Password Breach → Credential Stuffing
```
Name: Budi Santoso (LinkedIn) → pattern: b.santoso@company.com (hunter)
→ DeHashed: password "santoso123" → try login
```

#### Pattern 5: CT Logs → Subdomain → Dev Site → Weak Security
```
crt.sh: dev.company.com, staging.company.com
→ dev sites have weaker security, debug mode, test creds
```

#### Pattern 6: Google Dork → Exposed File → Credential → Infrastructure
```
site:company.com ext:sql → database.sql with user data
site:company.com ".env" "APP_KEY" → Laravel env
```

#### Pattern 7: Shodan → Open Port → Service Version → Exploit
```
Shodan: company.com:3306 MySQL 5.5 (end of life)
Shodan: company.com:22 OpenSSH 7.4 (CVE-2024-6387 possible)
```

#### Pattern 8: GitHub Commit → Internal URL → Credentials
```
Commit: "fix payment" → diff shows STRIPE_API_KEY and API_URL
Use key to access Stripe → company payment data
```

#### Pattern 9: Privacy Policy → Third-Party → Known Vulnerability
```
Privacy policy mentions SendGrid → search SendGrid API key in GitHub
Privacy policy mentions Stripe → search Stripe key in code
```

#### Pattern 10: App Reverse → API Keys → Internal Access
```
Download company APK → apktool d → extract API keys, endpoints
strings app.apk | grep -iE 'api|http|secret|key|token'
```

### 9. AUTOMATED OSINT TOOLS

```bash
# Full recon
rengine → web-based recon framework
osmedeus → automated offensive security
reconftw → automated recon
bbot → blacklantern security scanner

# Domain recon
subfinder + amass + assetfinder + httpx + nuclei

# Social
sherlock username (400+ sites)
maigret username (2500+ sites)
holehe email (120+ services)

# Secrets
trufflehog → git secrets
gitleaks → git secrets
git-dumper → .git dump

# Infrastructure
shodan → internet-wide scan
censys → host/cert search
fofa → cyberspace search
quake → 360 search
```

### 10. OSINT WORKFLOW CHECKLIST

```
[ ] 1. WHOIS → registrar, admin email, name servers
[ ] 2. DNS → all records, zone transfer attempt
[ ] 3. CT Logs → all subdomains ever issued
[ ] 4. Subdomain enum → 10+ sources, brute force
[ ] 5. Port scan → all discovered hosts
[ ] 6. Tech stack → whatweb, headers, cookies
[ ] 7. Google dorks → exposed files, credentials
[ ] 8. Shodan/Censys → open services, versions
[ ] 9. Wayback → hidden endpoints, old pages
[ ] 10. GitHub/GitLab → secrets, configs, endpoints
[ ] 11. LinkedIn → employees, tech stack from skills
[ ] 12. Email enum → pattern, verification
[ ] 13. Breach check → credential leaks
[ ] 14. Social media → username, face recognition
[ ] 15. Dark web → breach databases, leak channels
[ ] 16. Cloud assets → S3, Azure, GCP buckets
[ ] 17. Mobile app → reverse engineering, API keys
[ ] 18. Correlate ALL data → find attack vectors
```
