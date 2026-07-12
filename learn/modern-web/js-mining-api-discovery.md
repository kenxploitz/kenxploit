# JS Mining & API Discovery — Modern Web Recon
## Last Updated: Mon Jul 06 2026

## JavaScript Analysis for Hidden Endpoints

### 1. Extract all JS URLs from page
curl -sk "http://target" | grep -oE '(src|href)="[^"]*\.js[^"]*"' | cut -d'"' -f2,4

### 2. Fetch and analyze each JS file for API endpoints
curl -sk "http://target/static/app.js" | grep -oE '(/api/[a-zA-Z0-9_/?=&]+)' | sort -u

### 3. Find API keys, tokens, secrets in JS
curl -sk "http://target/static/app.js" | grep -oE \
  '(AIza[0-9A-Za-z-_]{35}|sk_live_[0-9a-zA-Z]+|pk_live_[0-9a-zA-Z]+|eyJ[a-zA-Z0-9_-]+\.[eyJ[a-zA-Z0-9_-]+|ghp_[a-zA-Z0-9]+|xox[abprs]-[0-9a-zA-Z-]+|AKIA[0-9A-Z]+|SG\.[a-zA-Z0-9_-]+|-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----)'

### 4. Source Map Analysis
# Find sourcemap reference
curl -sk "http://target" | grep -oE 'sourceMappingURL=[^"]+'
# Download and parse
curl -sk "http://target/static/app.js.map" -o app.js.map
python3 -c "
import json
with open('app.js.map') as f:
    data = json.load(f)
    for s in data.get('sources', []):
        print(s)
    for c in data.get('sourcesContent', []):
        if c and ('api/' in c or 'secret' in c.lower() or 'token' in c.lower()):
            print(c[:500])
"

### 5. API Endpoint Brute Force with Kiterunner-style
# Use ffuf with API wordlist
ffuf -w /usr/share/wordlists/api.txt -u "http://target/api/FUZZ" -c -t 50

### 6. GraphQL Endpoint Discovery
curl -sk "http://target/graphql?query={__schema{types{name}}}"
# Try various paths:
for path in graphql api/graphql v1/graphql v2/graphql v3/graphql gql query; do
  code=$(curl -sk -o /dev/null -w '%{http_code}' "http://target/$path")
  echo "$path -> $code"
done

### 7. WebSocket Endpoint Discovery
for path in ws wss socket ws/v1 ws/v2 chat stream notification; do
  echo "Trying ws://target/$path"
done

### 8. Hidden Parameters via JS Analysis
# Look for: state, token, session, redirect, url, next, goto, return
# In JS: grep for these as object keys or URL params
curl -sk "http://target/static/app.js" | grep -oE '("[a-z_]+":\s*")' | sort -u

### 9. Firebase Discovery
curl -sk "http://target" | grep -oE 'firebase.*app[^"]*' | sort -u
# Check Firebase DB: https://<project>.firebaseio.com/.json

### 10. S3 Bucket Discovery from JS
curl -sk "http://target/static/app.js" | grep -oE '[a-zA-Z0-9._-]+\.s3\.amazonaws\.com|[a-zA-Z0-9._-]+\.s3-website[^"]*|s3://[a-zA-Z0-9._-]+'
