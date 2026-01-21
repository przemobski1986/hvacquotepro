param(
  [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$pidFile = Join-Path $backendDir ".dev_uvicorn.pid"

if (Test-Path $pidFile) {
  $pidText = (Get-Content $pidFile -Raw).Trim()
  if ($pidText -match "^\d+$") {
    $serverPid = [int]$pidText
    $p = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
    if ($p) {
      taskkill /PID $serverPid /F /T | Out-Null
    }
  }
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$pids = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($procId in $pids) {
  $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
  if ($p) {
    taskkill /PID $procId /F /T | Out-Null
  }
}

Write-Host "OK"
