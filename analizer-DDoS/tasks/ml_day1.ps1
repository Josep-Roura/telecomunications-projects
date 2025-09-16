# tasks/ml_day1.ps1
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = ".\.venv\Scripts\python.exe"

if (!(Test-Path $Py)) {
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install --upgrade pip
  pip install -r requirements.txt
}

Write-Host "1) Extrayendo features benignas desde SQLite (últimas horas)..."
& $Py -m src.ml_featurizer

Write-Host "2) Entrenando IsolationForest + StandardScaler..."
& $Py -m src.ml_train
