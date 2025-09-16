param([int]$Port = 8510)

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".venv"
$Py   = Join-Path $Venv "Scripts\python.exe"
$Pip  = Join-Path $Venv "Scripts\pip.exe"

# 1) Crear/activar venv
if (!(Test-Path $Venv)) {
  Info "Creating virtual env..."
  python -m venv .venv
  if ($LASTEXITCODE -ne 0) { Err "venv creation failed"; exit 1 }
} else {
  Info "Virtual env already exists."
}

Info "Activating venv..."
& "$Venv\Scripts\Activate.ps1"

# 2) Instalar requirements
if (!(Test-Path (Join-Path $Root "requirements.txt"))) {
  Err "requirements.txt not found"
  exit 1
}
Info "Installing requirements..."
& $Pip install --upgrade pip | Out-Null
& $Pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { Err "pip install failed"; exit 1 } else { Ok "Dependencies OK" }

# 3) Inicializar DB
Info "Initializing database..."
& $Py -c "from src.db import init_db; init_db(); print('DB OK')"
if ($LASTEXITCODE -ne 0) { Err "init_db failed"; exit 1 } else { Ok "DB OK" }

# 3.1) Asegurar carpeta reports
$Reports = Join-Path $Root "reports"
if (!(Test-Path $Reports)) { New-Item -ItemType Directory -Path $Reports | Out-Null }

# 4) Lanzar dashboard Streamlit
$DashApp = Join-Path $Root "dashboard\app.py"
if (!(Test-Path $DashApp)) {
  Err "dashboard/app.py not found"
  exit 1
}

Info "Starting dashboard on http://localhost:$Port ..."
$Args = "-m streamlit run `"$DashApp`" --server.port $Port --server.headless true"
$Dash = Start-Process -FilePath $Py -ArgumentList $Args -PassThru -WindowStyle Minimized
if (-not $Dash) { Err "Failed to start dashboard"; exit 1 } else { Ok ("Dashboard PID: {0}" -f $Dash.Id) }

Info "Tip: schedule reports from the Dashboard (sidebar) or run:"
Write-Host "  $Py -m src.report --hours 24"
