# HVACQuotePro

Backend MVP (FastAPI) + timekeeping smoke tests.

## Lokalny start (Windows / PowerShell)

cd .\backend
uvicorn app.main:app --reload --log-level debug

OpenAPI:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/openapi.json

## Smoke tests (izolowane, SQLite)
Uruchamia pipeline na app_smoke.db i porcie 8001 (migracje + seed + testy).

cd .\backend
powershell -ExecutionPolicy Bypass -File .\run_smoke_isolated.ps1

## CI
GitHub Actions uruchamia workflow backend-ci dla zmian w backend/**.


