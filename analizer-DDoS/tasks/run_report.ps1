# tasks/run_report.ps1
param(
  [int]$Hours = 24,
  [switch]$Notify = $false
)

$ErrorActionPreference = "Stop"

# Ir a la raíz del proyecto (carpeta padre de /tasks)
$Proj = Split-Path -Parent $PSScriptRoot
Set-Location $Proj

# Python del venv
$VenvPython = Join-Path $Proj ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
  Write-Host "⚙️  Creando entorno virtual .venv ..."
  python -m venv .venv
  & $VenvPython -m pip install --upgrade pip
  if (Test-Path "$Proj\requirements.txt") {
    & $VenvPython -m pip install -r "$Proj\requirements.txt"
  }
}

# Variables de entorno para el proceso de reporte
$env:REPORT_HOURS = "$Hours"
$env:REPORT_TELEGRAM_NOTIFY = ($Notify.IsPresent).ToString().ToLower()

# Ejecutar generador
& $VenvPython -m src.report
