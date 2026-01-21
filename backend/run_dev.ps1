param(
  [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $backendDir

$dbPath = Join-Path $backendDir "app.db"
$dbUrl = "sqlite:///" + ($dbPath -replace "\\","/")

$env:DATABASE_URL = $dbUrl
$env:APP_ENV = "dev"
$env:PYTHONPATH = $backendDir

python -m alembic upgrade head

python -m app.seeds.seed_dev

$cmd = "python -m uvicorn app.main:app --reload --log-level debug --host 127.0.0.1 --port $Port"
Start-Process -FilePath "cmd.exe" -ArgumentList @("/k", $cmd) -WorkingDirectory $backendDir | Out-Null

Start-Sleep -Milliseconds 700
$listenerPid = (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess)
if ($listenerPid) {
  Set-Content -Encoding ASCII -Path (Join-Path $backendDir ".dev_uvicorn.pid") -Value $listenerPid
  Write-Host "OK (uvicorn in new window) PID=$listenerPid port=$Port"
} else {
  Write-Host "OK (uvicorn in new window) port=$Port (PID not detected)"
}
