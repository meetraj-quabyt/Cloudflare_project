# CloudShare Architecture

## Data flow

```
React frontend
    |
    | HTTPS REST API
    v
FastAPI backend
    |
    | Metadata, authorization, event tracking
    v
Cloudflare D1 (SQL)

File transfer:
React browser <---- direct upload/download ----> Cloudflare R2
```

## Deployment architecture

- FastAPI runs on Cloudflare Workers via Python Workers (pywrangler).
- D1 is accessed through the Worker binding `env.DB` (async prepare/run/first/all).
- R2 is accessed via its S3-compatible API using presigned URLs generated with AWS Signature V4 (pure Python, no boto3 dependency in Workers). Local dev may use boto3.
- Secrets (R2 keys) are stored as Wrangler secrets / environment variables, never committed.

## Download tracking semantics

- A generated download URL does NOT prove a download occurred.
- A download request does NOT prove the recipient received the entire file.
- Client-reported completion events are labelled `client_reported`, not server-verified.
- The successful download counter increments only on the first client-reported completion (idempotent).
- Download limit (max_downloads) is enforced against the successful-download counter at initiation; a small race window exists under concurrency and is documented.

## Local development

- Backend: `uvicorn app.main:app` from backend/ (uses SQLite fallback).
- Frontend: `npm run dev` from frontend/ (proxies /api to localhost:8000).
- Tests: pytest (backend), vitest (frontend).

## Known limitations

- Rate limiting is in-process and not globally consistent across serverless instances; use Cloudflare Rate Limiting rules or Durable Objects for production.
- R2 presigned URLs remain valid until expiry even after share link revocation; keep TTLs short.
- Download completion is client-reported, not cryptographically verified.