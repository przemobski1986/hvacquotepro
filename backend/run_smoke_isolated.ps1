Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$ErrorActionPreference = "Stop"

python .\check_no_func_now.py

$env:DATABASE_URL = "sqlite:///./app_smoke.db"
$env:SMOKE_BASE = "http://127.0.0.1:8001"

alembic upgrade head
python .\scripts_seed_admin.py
python .\scripts_seed_smoke_data.py

$uv = Start-Process -FilePath "powershell" -ArgumentList @(
  "-NoProfile",
  "-Command",
  "cd `"$PSScriptRoot`"; uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level warning"
) -PassThru

Start-Sleep -Seconds 2

try {
  python .\run_smoke.py
} finally {
  if ($uv -and -not $uv.HasExited) {
    Stop-Process -Id $uv.Id -Force
  }
}

