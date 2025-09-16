# tools/migrate_csv_to_db.py
from pathlib import Path
import sqlite3
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DB = DATA / "events.db"

# decide qué CSV usar (enriquecido si existe)
CSV = DATA / "events_enriched.csv" if (DATA / "events_enriched.csv").exists() else (DATA / "events.csv")

DATA.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  ip TEXT NOT NULL,
  count INTEGER NOT NULL,
  time_window INTEGER NOT NULL,
  level TEXT NOT NULL,
  lat REAL,
  lon REAL,
  country TEXT,
  org TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_ip ON events(ip);
"""

def read_csv_any(csv_path: Path) -> pd.DataFrame:
    # Detecta si tiene cabecera o no
    sample = pd.read_csv(csv_path, nrows=1)
    if "timestamp" not in sample.columns:
        if "events_enriched" in str(csv_path):
            cols = ["timestamp","ip","count","time_window","level","lat","lon","country","org"]
        else:
            cols = ["timestamp","ip","count","time_window","level"]
        df = pd.read_csv(csv_path, header=None, names=cols)
    else:
        df = pd.read_csv(csv_path)

    # Normaliza tipos
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    for c in ("count","time_window"):
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ("lat","lon"):
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

    # Completa columnas faltantes
    for c in ["lat","lon","country","org"]:
        if c not in df.columns: df[c] = None
    return df.dropna(subset=["timestamp"])

if __name__ == "__main__":
    con = sqlite3.connect(str(DB))
    con.executescript(SCHEMA)
    df = read_csv_any(CSV)
    print(f"Insertando {len(df)} filas desde {CSV.name} a {DB.name} …")
    df.to_sql("events", con, if_exists="append", index=False)
    con.close()
    print("Hecho.")
