# src/ml.py
from __future__ import annotations
import os
from pathlib import Path
import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional

# Ruta del modelo entrenado
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "iforest.joblib"

# Orden canónico de features que usaremos (coinciden con la extracción)
FEATURE_KEYS: List[str] = [
    "count",             # eventos/paquetes en la ventana (o métrica equivalente)
    "rate",              # count / time_window
    "rolling_mean",      # media móvil (por IP)
    "rolling_std",       # std móvil (por IP)
    "zscore",            # (count - rolling_mean) / (rolling_std + 1e-6)
    "delta_count",       # diferencia vs ventana anterior
    "ema",               # media móvil exponencial
    "hour_sin",          # codificación cíclica hora
    "hour_cos",
]

def load_model(model_path: Path = MODEL_PATH):
    """
    Carga (scaler, modelo) desde joblib. Lanza excepción si no existe.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo ML no encontrado: {model_path}")
    scaler, iso = joblib.load(model_path)
    return scaler, iso

def ensure_vector(x_dict: Dict[str, float], keys: List[str] = FEATURE_KEYS) -> np.ndarray:
    """
    Convierte un dict de features en vector ordenado y sin NaNs.
    """
    vec = np.array([float(x_dict.get(k, 0.0) or 0.0) for k in keys], dtype=float).reshape(1, -1)
    # saneo básico
    vec[~np.isfinite(vec)] = 0.0
    return vec

def score_vector(x_dict: Dict[str, float], model_path: Path = MODEL_PATH) -> float:
    """
    Devuelve un ML score (float). Mayor = más anómalo.
    """
    scaler, iso = load_model(model_path)
    x = ensure_vector(x_dict)
    xz = scaler.transform(x)
    # IsolationForest: más negativo = más normal. Invertimos signo para que mayor = más anómalo
    score = -iso.decision_function(xz)[0]
    return float(score)
