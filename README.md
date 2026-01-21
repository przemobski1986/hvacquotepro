# HVACQuotePro MVP (FastAPI + PostgreSQL) — PL/EN, VPS-ready

This repository is a production-oriented MVP backend for **HVACQuotePro**:
- Multi-tenant (tenant_id on every record)
- JWT auth (access + refresh)
- RBAC (admin / sales / manager)
- CRUD: Clients, Sites, Deals, Quotes, Quote params, Quote lines, Totals
- Rule engine stubs for BOM (ready to extend)
- PDF generation job stubs (ready to extend)
- i18n for PL/EN responses (Accept-Language header)
- Alembic migrations
- Docker Compose for VPS deployment

## 1) Quick start (local)
Requirements: Docker + Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
```

Open:
- API docs: http://localhost:8000/docs

## 2) Create first tenant + admin
```bash
docker compose exec api python -m app.scripts.bootstrap_admin
```

It prints:
- tenant_id
- admin email/password

## 3) Auth flow
- `POST /api/v1/auth/login` -> access token + refresh cookie
- Use `Authorization: Bearer <access_token>` for API calls
- `POST /api/v1/auth/refresh` -> new access token

## 4) VPS deployment (simple)
1. Provision VPS (Ubuntu 22.04+)
2. Install Docker + Compose
3. Upload repo, set `.env` for your domain/DB secrets
4. Run `docker compose up -d --build`
5. Put Nginx/Caddy in front (TLS)

See `deploy/NGINX.md` for a minimal Nginx reverse proxy config.

## 5) Language (PL/EN)
Send header:
- `Accept-Language: pl` or `Accept-Language: en`

## 6) Next steps
- Implement BOM rule engine (see `app/services/rules.py`)
- Implement PDF worker (see `app/services/pdf.py`)
- Add frontend (Next.js) consuming the OpenAPI

