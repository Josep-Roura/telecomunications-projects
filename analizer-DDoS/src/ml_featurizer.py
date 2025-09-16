# src/ml_featurizer.py
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "events.db"
OUT_CSV = ROOT / "data" / "features_benign.csv"

HOURS = int(os.getenv("ML_FEAT_HOURS", "1"))
ROLL_N = int(os.getenv("ML_FEAT_ROLL", "5"))

def _load_events(hours: int) -> pd.DataFrame:
    """
    Lee eventos de las últimas 'hours' desde SQLite.
    Espera como mínimo: timestamp (TEXT), ip (TEXT), count (INTEGER), time_window (INTEGER).
    Opcionales: level, etc. (se ignoran).
    """
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["timestamp", "ip", "count", "time_window"])

    t_to = datetime.utcnow()
    t_from = t_to - timedelta(hours=hours)

    con = sqlite3.connect(str(DB_PATH))
    try:
        q = """
        SELECT timestamp, ip, count, time_window
        FROM events
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY ip ASC, timestamp ASC
        """
        df = pd.read_sql_query(q, con, params=(
            t_from.strftime("%Y-%m-%d %H:%M:%S"),
            t_to.strftime("%Y-%m-%d %H:%M:%S"),
        ))
    finally:
        con.close()

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True).dt.tz_convert(None)
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(float)
    df["time_window"] = pd.to_numeric(df["time_window"], errors="coerce").fillna(1).astype(float)
    df = df.dropna(subset=["timestamp", "ip"]).reset_index(drop=True)
    return df

def _encode_hour(ts: pd.Series) -> pd.DataFrame:
    hour = ts.dt.hour.astype(float)
    return pd.DataFrame({
        "hour_sin": np.sin(2 * np.pi * hour / 24.0),
        "hour_cos": np.cos(2 * np.pi * hour / 24.0),
    })

def _feature_engineer(df: pd.DataFrame, roll_n: int) -> pd.DataFrame:
    """
    Calcula features por IP ordenadas temporalmente.
    """
    if df.empty:
        cols = ["timestamp","ip","count","time_window","rate","rolling_mean","rolling_std","zscore","delta_count","ema","hour_sin","hour_cos"]
        return pd.DataFrame(columns=cols)

    df = df.sort_values(["ip", "timestamp"]).reset_index(drop=True)
    df["rate"] = df["count"] / df["time_window"].replace(0, 1)

    # rolling por IP
    def by_ip(group: pd.DataFrame) -> pd.DataFrame:
        g = group.copy()
        g["rolling_mean"] = g["count"].rolling(roll_n, min_periods=1).mean()
        g["rolling_std"]  = g["count"].rolling(roll_n, min_periods=1).std().fillna(0.0)
        g["zscore"] = (g["count"] - g["rolling_mean"]) / (g["rolling_std"] + 1e-6)
        g["delta_count"] = g["count"].diff().fillna(0.0)
        # EMA (suavizado) — alpha heurístico
        alpha = 2 / (roll_n + 1)
        g["ema"] = g["count"].ewm(alpha=alpha, adjust=False).mean()
        return g

    df = df.groupby("ip", group_keys=False).apply(by_ip)

    # codificación cíclica de la hora
    enc = _encode_hour(df["timestamp"])
    df = pd.concat([df, enc], axis=1)

    cols = ["timestamp","ip","count","time_window","rate","rolling_mean","rolling_std","zscore","delta_count","ema","hour_sin","hour_cos"]
    return df[cols]

def build_features_csv(hours: int = HOURS, roll_n: int = ROLL_N, out_csv: Path = OUT_CSV) -> Path:
    ev = _load_events(hours)
    feats = _feature_engineer(ev, roll_n)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    feats.to_csv(out_csv, index=False)
    return out_csv

if __name__ == "__main__":
    path = build_features_csv(HOURS, ROLL_N, OUT_CSV)
    print(f"[OK] Features guardadas en: {path}")
