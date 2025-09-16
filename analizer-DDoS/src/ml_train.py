# src/ml_train.py
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "features_benign.csv"
MODEL_DIR = ROOT / "models"
MODEL_PATH = MODEL_DIR / "iforest.joblib"

CONTAM = float(os.getenv("ML_CONTAMINATION", "0.01"))
N_EST   = int(os.getenv("ML_N_ESTIMATORS", "200"))

# Misma selección/orden de features que en src/ml.py
FEATURE_KEYS = [
    "count",
    "rate",
    "rolling_mean",
    "rolling_std",
    "zscore",
    "delta_count",
    "ema",
    "hour_sin",
    "hour_cos",
]

def load_features(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        raise FileNotFoundError(f"No existe dataset de features: {csv_path}")
    df = pd.read_csv(csv_path)
    # Remove NAs and non-finite values
    for c in FEATURE_KEYS:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df = df.replace([np.inf, -np.inf], 0.0)
    return df

def train_and_save(df: pd.DataFrame, out_path: Path = MODEL_PATH):
    X = df[FEATURE_KEYS].values.astype(float)

    scaler = StandardScaler().fit(X)
    Xz = scaler.transform(X)

    iso = IsolationForest(
        n_estimators=N_EST,
        contamination=CONTAM,
        random_state=42,
        n_jobs=-1
    ).fit(Xz)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((scaler, iso), out_path)
    print(f"[OK] Modelo guardado en: {out_path}")

if __name__ == "__main__":
    df = load_features(DATA_CSV)
    train_and_save(df, MODEL_PATH)
