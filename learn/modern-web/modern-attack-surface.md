# Modern Web Attack Surface — Complete Recon & Exploit Map
## Last Updated: Mon Jul 06 2026

## NEXT.JS (App Router / Pages Router)
### Attack Surface:
- /_next/data/ — JSON data endpoints
- /_next/image?url= — Image optimization SSRF
- /_next/static/ — Static files (source maps?)
- /api/ — API routes
- /_rsc/ — React Server Components endpoint
- /__rsc/ — Alternative RSC endpoint
- Middleware bypass via path traversal
- Flight protocol deserialization (CVE-2025-55182)
- WebSocket upgrade SSRF (CVE-2026-44578)
- Middleware redirect SSRF (CVE-2025-57822)

## NUXT.JS
### Attack Surface:
- /api/ — API endpoints
- /_nuxt/ — Static files
- SSR injection via asyncData/fetch

## NEST.JS
### Attack Surface:
- /api, /graphql, /docs, /swagger
- /graphql with introspection
- TypeORM raw SQL injection
- Mass assignment via @Body()

## EXPRESS / FASTIFY / KOA
### Attack Surface:
- /debug, /__admin, /metrics
- Prototype pollution (qs, body-parser)
- Deserialization (cookie-session, express-session)
- SSRF via axios, fetch
- Path traversal via res.sendFile

## PYTHON FASTAPI
### Attack Surface:
- /docs (Swagger UI), /redoc, /openapi.json
- Path traversal in path params
- SQL injection via ORM raw queries
- SSRF via httpx
- Mass assignment via Pydantic

## PYTHON FLASK
### Attack Surface:
- /console (Werkzeug debug PIN)
- /__debug__, /admin/console
- SSTI via Jinja2 (RCE chain)
- File upload → pickle deserialization

## PYTHON DJANGO
### Attack Surface:
- /admin/
- /__debug__ (if DEBUG=True)
- SECRET_KEY crack → session forge
- SQL injection via raw()/extra()
- Mass assignment via ?is_staff=true

## SPRING BOOT 3
### Attack Surface:
- /actuator, /actuator/env, /actuator/heapdump
- /actuator/loggers (change log level)
- /swagger-ui.html, /v3/api-docs
- SpEL injection in request params
- CVE-2026-22733 — auth bypass

## .NET CORE / BLAZOR
### Attack Surface:
- /swagger, /health, /healthchecks
- /env, /__admin
- ViewState deserialization (CVE-2024-28938)
- SSRF via HttpClient
- Blazor Server SignalR hub: /_blazor

## GO (GIN / ECHO / FIBER)
### Attack Surface:
- /debug/pprof/, /debug/vars, /metrics
- /health, /ready
- Command injection via exec.Command
- SSRF via net/http.Get
- SSTI via html/template

## RUBY / RAILS 7
### Attack Surface:
- /rails/info, /rails/info/properties
- /rails/console, /rails/mailers
- /sidekiq, /admin
- YAML deserialization
- ERB SSTI
- Mass assignment

## CLOUD-NATIVE / K8s
### Attack Surface:
- K8s API server (6443)
- etcd (2379)
- kubelet (10250)
- Dashboard (8001)
- Container escape via privileged pod
- Service account token abuse
- CVE-2026-0093, CVE-2026-1483

## SERVERLESS
### Attack Surface:
- Function URLs (guessable)
- Environment variable injection
- Event injection (S3 → Lambda, SQS → Lambda)
- SSRF via HTTP clients

## WEBSOCKET ATTACKS
### Attack Surface:
- SQLi via WebSocket messages
- SSRF via WebSocket URLs
- Auth bypass via WebSocket (no auth check)
- Rate limit bypass via WebSocket

## GRAPHQL
### Attack Surface:
- Introspection query
- Batching (rate limit bypass)
- SQLi via GraphQL
- CSRF via GraphQL
- Deep recursion DoS

