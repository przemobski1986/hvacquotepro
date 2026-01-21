Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$env:DATABASE_URL = "sqlite:///./app.db"

alembic upgrade head
python .\scripts_seed_admin.py
python .\scripts_seed_smoke_data.py

uvicorn app.main:app --reload --log-level debug
