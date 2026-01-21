param(
  [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

powershell -ExecutionPolicy Bypass -File .\stop_dev.ps1 -Port $Port
powershell -ExecutionPolicy Bypass -File .\run_dev.ps1 -Port $Port
