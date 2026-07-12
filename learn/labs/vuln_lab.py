#!/usr/bin/env python3
"""
KENXPLOIT VULNERABLE LAB — Multi-vuln Flask app for practice
Endpoint: http://localhost:5000
"""
import os, subprocess, sqlite3, base64, pickle, html
from flask import Flask, request, render_template_string, send_file, jsonify, make_response
from jinja2 import Template
import uuid

app = Flask(__name__)
app.secret_key = 'super_secret_key_12345'

# ========== DATABASE SETUP ==========
def init_db():
    conn = sqlite3.connect('/tmp/vuln_lab.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY,
        flag TEXT
    )''')
    # Insert sample data
    try:
        c.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'admin123', 'admin')")
        c.execute("INSERT OR IGNORE INTO users VALUES (2, 'user', 'userpass', 'user')")
        c.execute("INSERT OR IGNORE INTO users VALUES (3, 'guest', 'guest123', 'guest')")
        c.execute("INSERT OR IGNORE INTO secrets VALUES (1, 'CTF{kenxploit_mastered_sqli_2026}')")
        c.execute("INSERT OR IGNORE INTO secrets VALUES (2, 'CTF{flag_2_ssrf_to_metadata}')")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

# ========== HELPER ==========
def get_db():
    conn = sqlite3.connect('/tmp/vuln_lab.db')
    return conn

# ========== 1. SSTI VULNERABILITY (Jinja2) ==========
@app.route('/ssti')
def ssti():
    name = request.args.get('name', 'World')
    template = f"<h1>Hello {name}!</h1><p>How are you today?</p>"
    return render_template_string(template)

@app.route('/ssti/advanced')
def ssti_advanced():
    template_str = request.args.get('tmpl', '<h1>Default Template</h1>')
    template = Template(template_str)
    return template.render()

# ========== 2. COMMAND INJECTION ==========
@app.route('/cmd')
def cmd_injection():
    ip = request.args.get('ip', '127.0.0.1')
    cmd = f"ping -c 2 {ip}"
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return f"<pre>{result.decode()}</pre>"
    except Exception as e:
        return f"<pre>Error: {e}</pre>"

@app.route('/cmd/blind')
def cmd_blind():
    ip = request.args.get('ip', '127.0.0.1')
    cmd = f"ping -c 1 {ip} > /dev/null 2>&1"
    try:
        subprocess.check_call(cmd, shell=True, timeout=5)
        return "Host is alive!"
    except:
        return "Host is down or error"

# ========== 3. SQL INJECTION ==========
@app.route('/sqli')
def sqli():
    uid = request.args.get('id', '1')
    conn = get_db()
    query = f"SELECT id, username, role FROM users WHERE id = {uid}"
    try:
        cursor = conn.execute(query)
        row = cursor.fetchone()
        if row:
            return f"ID: {row[0]}, Username: {row[1]}, Role: {row[2]}"
        else:
            return "User not found"
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

@app.route('/sqli/login')
def sqli_login():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    conn = get_db()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    try:
        cursor = conn.execute(query)
        row = cursor.fetchone()
        if row:
            return f"Login successful! Welcome {row[1]} (role: {row[3]})"
        else:
            return "Login failed"
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

# ========== 4. LFI / PATH TRAVERSAL ==========
@app.route('/lfi')
def lfi():
    file = request.args.get('file', '/etc/hostname')
    try:
        with open(file, 'r') as f:
            content = f.read()
        return f"<pre>{html.escape(content)}</pre>"
    except Exception as e:
        return f"Error: {e}"

# ========== 5. FILE UPLOAD ==========
UPLOAD_DIR = '/tmp/vuln_uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = file.filename
            filepath = os.path.join(UPLOAD_DIR, filename)
            file.save(filepath)
            return f"File uploaded to {filepath}"
    return '''
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit">
    </form>
    '''

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_DIR, filename))

# ========== 6. SSRF ==========
@app.route('/ssrf')
def ssrf():
    import urllib.request
    url = request.args.get('url', 'http://127.0.0.1:5000/')
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            content = resp.read()
            return f"<pre>{html.escape(content.decode(errors='replace'))}</pre>"
    except Exception as e:
        return f"Error: {e}"

# ========== 7. JWT (custom fake JWT check) ==========
@app.route('/jwt')
def jwt_check():
    import json, base64
    token = request.args.get('token', '')
    try:
        parts = token.split('.')
        header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
        payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return jsonify({"header": header, "payload": payload})
    except Exception as e:
        return f"Token error: {e}"

@app.route('/jwt/verify')
def jwt_verify():
    import hashlib, json, base64
    token = request.args.get('token', '')
    secret = "weak_secret_123"
    try:
        parts = token.split('.')
        header_b64 = parts[0]
        payload_b64 = parts[1]
        sig = parts[2]
        # Accept 'none' algorithm
        header_decoded = json.loads(base64.urlsafe_b64decode(header_b64 + '=' * (4 - len(header_b64) % 4)))
        if header_decoded.get('alg') == 'none':
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * (4 - len(payload_b64) % 4)))
            if payload.get('role') == 'admin':
                return f"✅ GRANTED: Admin access! Flag: CTF{jwt_master_2026}"
            return f"✅ Accepted (no signature), but role is {payload.get('role')}"
        # HMAC verification with weak secret
        msg = f"{header_b64}.{payload_b64}"
        expected_sig = base64.urlsafe_b64encode(hashlib.sha256(f"{msg}.{secret}".encode()).digest()).decode().rstrip('=')
        if sig == expected_sig:
            payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * (4 - len(payload_b64) % 4)))
            return jsonify({"status": "verified", "payload": payload})
        return "Invalid signature"
    except Exception as e:
        return f"Error: {e}"

# ========== 8. XXE ==========
@app.route('/xxe', methods=['POST'])
def xxe():
    import lxml.etree as ET
    xml_data = request.data
    try:
        tree = ET.fromstring(xml_data)
        return f"Parsed: {ET.tostring(tree).decode()}"
    except Exception as e:
        return f"Error: {e}"

# ========== 9. DESERIALIZATION (Pickle) ==========
@app.route('/pickle', methods=['POST'])
def pickle_deser():
    import pickle
    data = request.data
    try:
        obj = pickle.loads(data)
        return f"Deserialized: {obj}"
    except Exception as e:
        return f"Error: {e}"

# ========== 10. API/GRAPHQL-like ==========
@app.route('/api/users')
def api_users():
    uid = request.args.get('id')
    conn = get_db()
    if uid:
        query = f"SELECT id, username, role FROM users WHERE id = {uid}"
    else:
        query = "SELECT id, username, role FROM users"
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        return jsonify([{"id": r[0], "username": r[1], "role": r[2]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        conn.close()

# ========== 11. PROTOTYPE POLLUTION (simulated) ==========
@app.route('/proto', methods=['POST'])
def proto_pollution():
    import json
    data = request.get_json(silent=True) or {}
    # Simulated vulnerable merge
    result = {"user": "guest", "role": "user"}
    for key in data:
        result[key] = data[key]
    if result.get('role') == 'admin':
        return f"🎉 You are admin! Flag: CTF{prototype_pollution_done}"
    return jsonify(result)

# ========== 12. WAF BYPASS PRACTICE ==========
@app.route('/waf')
def waf():
    input_str = request.args.get('input', '')
    # Simulated WAF: blocks basic SQLi keywords
    blocked = ['union', 'select', 'or ', 'and ', 'sleep', 'insert', 'drop', '--', '#']
    for kw in blocked:
        if kw.lower() in input_str.lower():
            return f"🚫 Blocked by WAF: keyword '{kw}' detected"
    # Pass through to SQL query
    conn = get_db()
    query = f"SELECT id, username, role FROM users WHERE username = '{input_str}'"
    try:
        cursor = conn.execute(query)
        row = cursor.fetchone()
        if row:
            return f"User: {row[1]}, Role: {row[2]}"
        return "Not found"
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

# ========== 13. RACE CONDITION ==========
race_balance = {"user": 100}
race_lock = False

@app.route('/race/transfer')
def race_transfer():
    global race_balance
    amount = int(request.args.get('amount', 0))
    if race_balance['user'] >= amount and amount > 0:
        race_balance['user'] -= amount
        return f"Transferred {amount}! Balance: {race_balance['user']}"
    return f"Insufficient balance. Balance: {race_balance['user']}"

@app.route('/race/reset')
def race_reset():
    global race_balance
    race_balance = {"user": 100}
    return "Reset to 100"

# ========== 14. OPEN REDIRECT ==========
@app.route('/redirect')
def open_redirect():
    url = request.args.get('url', '/')
    return f'<html><body><p>Redirecting to <a href="{url}">{url}</a></p><script>window.location="{url}";</script></body></html>'

# ========== 15. DEBUG/ACTUATOR ==========
@app.route('/actuator')
def actuator():
    return jsonify({
        "_links": {
            "self": "/actuator",
            "health": "/actuator/health",
            "env": "/actuator/env",
            "heapdump": "/actuator/heapdump",
            "loggers": "/actuator/loggers"
        }
    })

@app.route('/actuator/health')
def actuator_health():
    return jsonify({"status": "UP"})

@app.route('/actuator/env')
def actuator_env():
    import os
    safe_env = {k: v for k, v in os.environ.items() if not k.startswith('SECRET')}
    return jsonify(safe_env)

@app.route('/actuator/heapdump')
def actuator_heapdump():
    return "heapdump simulation: sensitive data would be here"

# ========== HOME ==========
@app.route('/')
def home():
    return """
    <h1>🔥 KENXPLOIT VULNERABLE LAB 🔥</h1>
    <ul>
        <li><a href="/ssti?name={{7*7}}">SSTI</a></li>
        <li><a href="/ssti/advanced?tmpl={{7*7}}">SSTI Advanced</a></li>
        <li><a href="/cmd?ip=127.0.0.1">Command Injection</a></li>
        <li><a href="/cmd/blind?ip=127.0.0.1">Command Injection (Blind)</a></li>
        <li><a href="/sqli?id=1">SQL Injection</a></li>
        <li><a href="/sqli/login?username=admin&password=admin123">SQL Login</a></li>
        <li><a href="/lfi?file=/etc/passwd">LFI</a></li>
        <li><a href="/upload">File Upload</a></li>
        <li><a href="/ssrf?url=http://127.0.0.1:5000/">SSRF</a></li>
        <li><a href="/jwt?token=eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4ifQ.">JWT</a></li>
        <li><a href="/api/users">API Users</a></li>
        <li><a href="/actuator">Actuator</a></li>
        <li><a href="/race/reset">Race Condition (reset)</a></li>
        <li><a href="/redirect?url=http://evil.com">Open Redirect</a></li>
    </ul>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
