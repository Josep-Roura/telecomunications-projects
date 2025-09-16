param(
    [switch]$Train,           # fuerza featurizer + entrenamiento ML
    [int]$FeatHours = 1,      # horas de histórico para features benignas
    [int]$Port = 8501,        # puerto del dashboard
    [switch]$NoBrowser        # no abrir navegador automáticamente
)

# -----------------------------
# Utilidades
# -----------------------------
function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg){ Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Test-Admin {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object System.Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Rutas
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

$VenvPath   = Join-Path $ScriptRoot ".venv"
$PyExe      = Join-Path $VenvPath "Scripts\python.exe"
$PipExe     = Join-Path $VenvPath "Scripts\pip.exe"

$ReqTxt     = Join-Path $ScriptRoot "requirements.txt"
$DbPath     = Join-Path $ScriptRoot "data\events.db"
$ModelsDir  = Join-Path $ScriptRoot "models"
$ModelPath  = Join-Path $ModelsDir "iforest.joblib"
$DashApp    = Join-Path $ScriptRoot "dashboard\app.py"

# Silenciar DeprecationWarnings (para esta sesión)
$env:PYTHONWARNINGS = "ignore::DeprecationWarning"

# -----------------------------
# 1) venv
# -----------------------------
if (!(Test-Path $VenvPath)) {
    Write-Info "Creando entorno virtual..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Err "No se pudo crear el venv"; exit 1 }
} else {
    Write-Info "Entorno virtual ya existe."
}

Write-Info "Activando venv..."
& "$VenvPath\Scripts\Activate.ps1"

# -----------------------------
# 2) requirements
# -----------------------------
if (!(Test-Path $ReqTxt)) {
    Write-Err "No existe requirements.txt en $ScriptRoot"
    exit 1
}

Write-Info "Instalando dependencias..."
& $PipExe install --upgrade pip | Out-Null
& $PipExe install -r $ReqTxt
if ($LASTEXITCODE -ne 0) { Write-Err "Fallo al instalar requirements"; exit 1 }
Write-Ok "Dependencias OK"

# -----------------------------
# 3) Inicializar DB
# -----------------------------
Write-Info "Inicializando la base de datos..."
& $PyExe -c "from src.db import init_db; init_db(); print('DB OK')"
if ($LASTEXITCODE -ne 0) { Write-Err "Fallo en init_db()"; exit 1 }
else { Write-Ok "DB OK" }

# -----------------------------
# 4) ML: featurizer + train si falta el modelo o si -Train
# -----------------------------
$NeedTrain = $Train -or (!(Test-Path $ModelPath))
if ($NeedTrain) {
    Write-Info "Preparando entrenamiento ML (IsolationForest)..."
    if (!(Test-Path $ModelsDir)) { New-Item -ItemType Directory -Path $ModelsDir | Out-Null }

    Write-Info "Extrayendo features benignas desde la BD (últimas $FeatHours h)..."
    $env:ML_FEAT_HOURS = "$FeatHours"
    & $PyExe -m src.ml_featurizer
    if ($LASTEXITCODE -ne 0) { Write-Err "Fallo en ml_featurizer"; exit 1 }

    Write-Info "Entrenando modelo ML y guardando en models/iforest.joblib..."
    & $PyExe -m src.ml_train
    if ($LASTEXITCODE -ne 0) { Write-Err "Fallo en ml_train"; exit 1 }
    Write-Ok "Modelo ML OK"
} else {
    Write-Info "Modelo ML existente: $ModelPath"
}

# -----------------------------
# 5) Lanzar detector (src.main)
# -----------------------------
Write-Info "Lanzando detector (src.main)..."
$Detector = Start-Process -FilePath $PyExe -ArgumentList "-m src.main" -PassThru -WindowStyle Minimized
if (!$Detector) { Write-Err "No se pudo lanzar el detector"; exit 1 }

# -----------------------------
# 6) Lanzar dashboard (Streamlit)
# -----------------------------
if (!(Test-Path $DashApp)) {
    Write-Err "No existe dashboard/app.py"
    exit 1
}
Write-Info "Lanzando dashboard en http://localhost:$Port ..."
$DashArgs = "-m streamlit run `"$DashApp`" --server.port $Port --server.headless true"
$Dashboard = Start-Process -FilePath $PyExe -ArgumentList $DashArgs -PassThru -WindowStyle Minimized
if (!$Dashboard) { Write-Err "No se pudo lanzar el dashboard"; exit 1 }

# -----------------------------
# 7) Info final y abrir navegador
# -----------------------------
$IsAdmin = Test-Admin
if ($IsAdmin) {
    Write-Ok "Permisos de Administrador detectados (bloqueos de firewall posibles)."
} else {
    Write-Warn "No estás en modo Administrador. Las reglas de firewall (netsh) pueden fallar."
}

Write-Ok ("Detector PID:  {0}" -f $Detector.Id)
Write-Ok ("Dashboard PID: {0}" -f $Dashboard.Id)

if (-not $NoBrowser) {
    Start-Process "http://localhost:$Port" | Out-Null
}

Write-Info "Pulsa Ctrl+C para cerrar esta ventana. Para detener procesos manualmente:
  stop-process -Id $($Detector.Id) -Force
  stop-process -Id $($Dashboard.Id) -Force"
