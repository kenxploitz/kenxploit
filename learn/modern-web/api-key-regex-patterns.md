# API Key / Secret Regex Patterns — For JS/Config/Env Hunting
## Last Updated: Mon Jul 06 2026

## AWS
AKIA[0-9A-Z]{16}                                       # AWS Access Key ID
eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+                   # AWS Session Token (JWT-like)
aws_access_key_id|aws_secret_access_key                 # AWS Config keys

## GCP
AIza[0-9A-Za-z\-_]{35}                                  # Google API Key
"type": "service_account"                                # GCP Service Account

## Azure
azure_storage_account|azure_storage_access_key           # Azure Storage

## GitHub
ghp_[0-9a-zA-Z]{36}                                     # GitHub Personal Access Token
gho_[0-9a-zA-Z]{36}                                     # GitHub OAuth Access Token
ghu_[0-9a-zA-Z]{36}                                     # GitHub User-to-Server Token
ghs_[0-9a-zA-Z]{36}                                     # GitHub Server-to-Server
github_pat_[0-9a-zA-Z_]{82}                             # GitHub Fine-Grained PAT

## Stripe
sk_live_[0-9a-zA-Z]{24,}                                # Stripe Secret Key
pk_live_[0-9a-zA-Z]{24,}                                # Stripe Publishable Key
sk_test_[0-9a-zA-Z]{24,}                                # Stripe Test Secret

## Slack
xox[baprs]-[0-9a-zA-Z\-]{10,48}                        # Slack Token

## Discord
[ MN][A-Za-z\d]{23,25}\.[A-Za-z\d]{6}\.[A-Za-z\d\-_]{27}  # Discord Token

## Firebase
AIza[0-9A-Za-z\-_]{35}                                  # Firebase API Key
firebase_url|firebase_database_url                      # Firebase URL

## SendGrid / Twilio
SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}             # SendGrid API Key
AC[0-9a-f]{32}                                          # Twilio Account SID

## Mailchimp / Mailgun
key-[0-9a-f]{32}                                        # Mailchimp API Key
mailgun_api_key|mailgun_secret                          # Mailgun

## OpenAI / LLM
sk-[0-9a-zA-Z]{20,}                                     # OpenAI API Key
sk-ant-[0-9a-zA-Z]{20,}                                 # Anthropic API Key

## Generic
api[_-]?key|api[_-]?secret|api[_-]?token                # Generic API keys
-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----    # Private keys
JWT|Bearer\s+[A-Za-z0-9\-\._]+                         # JWT tokens

## Database
mongodb://[^/]+                                          # MongoDB URI
mysql://[^/]+                                            # MySQL URI
postgresql://[^/]+                                       # PostgreSQL URI
redis://[^/]+                                            # Redis URI

## Password patterns
password\s*[=:]\s*['"][^'"]+['"]                         # Password in config
passwd|pwd|pass\s*[=:]\s*['"][^'"]+['"]                 # Password variations

