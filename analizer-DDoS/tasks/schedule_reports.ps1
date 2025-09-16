# tasks/schedule_report.ps1
param(
  [string]$Hour = "08",
  [string]$Minute = "00",
  [string]$TaskName = "DDoS-GenerateDailyReport"
)

$ErrorActionPreference = "Stop"

# Rutas
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent $root  # carpeta raíz del repo

# Python del venv
$venvPython = Join-Path $proj ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  Write-Host "Creando venv..."
  python -m venv (Join-Path $proj ".venv")
}

# Acción: ejecutar el módulo de reportes
$action = New-ScheduledTaskAction -Execute $venvPython -Argument "-m src.report"

# Trigger diario a la hora indicada
$timeStr = "{0}:{1}" -f $Hour, $Minute
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::ParseExact($timeStr, "HH:mm", $null))

# Ajustes de la tarea
$settings = New-ScheduledTaskSettingsSet -Compatibility Win8 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden:$false

try {
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Genera informe DDoS diario (HTML + CSV) en ./reports" -Force
  Write-Host "Tarea programada '$TaskName' registrada para las $timeStr todos los días."
} catch {
  Write-Host "Error creando tarea: $($_.Exception.Message)"
  exit 1
}
