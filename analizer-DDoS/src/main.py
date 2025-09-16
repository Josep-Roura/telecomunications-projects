# src/main.py
from __future__ import annotations
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque

from dotenv import load_dotenv

# DB y listas
from . import db

# Opcionales (si existen en tu repo)
try:
    from .geo import geo_lookup
except Exception:
    geo_lookup = None

try:
    from .ti_abuseipdb import AbuseIPDB
except Exception:
    AbuseIPDB = None

try:
    from .response import block_ip_windows
except Exception:
    def block_ip_windows(ip: str) -> bool:
        return False

# === ML
from .ml import score_vector

load_dotenv()

MY_IP = os.getenv("MY_IP", "0.0.0.0")
REQUEST_THRESHOLD = int(os.getenv("REQUEST_THRESHOLD", "5"))
TIME_WINDOW = int(os.getenv("TIME_WINDOW", "5"))
BLOCK_TIME = int(os.getenv("BLOCK_TIME", "15"))

# Auto-bloqueo clásico (por nivel/umbral), si lo tenías
AUTO_BLOCK_ENABLED = os.getenv("AUTO_BLOCK_ENABLED", "false").lower() == "true"
AUTO_BLOCK_MIN_SCORE = int(os.getenv("AUTO_BLOCK_MIN_SCORE", "50"))

# === ML config
ML_ENABLED = os.getenv("ML_ENABLED", "true").lower() == "true"
ML_SCORE_THRESHOLD = float(os.getenv("ML_SCORE_THRESHOLD", "0.5"))
ML_AUTOBLOCK_ENABLED = os.getenv("ML_AUTOBLOCK_ENABLED", "false").lower() == "true"
ML_AUTOBLOCK_MIN_SCORE = float(os.getenv("ML_AUTOBLOCK_MIN_SCORE", "0.8"))

# TI
ti = AbuseIPDB() if AbuseIPDB else None

# Estado por IP para features rolling
ROLL_N = 5  # mismo valor que ML_FEAT_ROLL por coherencia
per_ip_counts = defaultdict(lambda: deque(maxlen=ROLL_N))
per_ip_last = {}  # última cuenta por IP
per_ip_ema = {}   # EMA simple por IP

def _ema(prev: float, x: float, alpha: float) -> float:
    return (alpha * x) + (1 - alpha) * prev

def build_features(ip: str, count: int, time_window: int) -> dict:
    """
    Construye features compatibles con FEATURE_KEYS (src/ml.py).
    """
    # actualizar estructura
    per_ip_counts[ip].append(count)
    rolling = list(per_ip_counts[ip])
    rolling_mean = sum(rolling) / max(1, len(rolling))
    # std poblacional simple
    if len(rolling) > 1:
        mu = rolling_mean
        rolling_std = (sum((c - mu) ** 2 for c in rolling) / len(rolling)) ** 0.5
    else:
        rolling_std = 0.0
    rate = count / max(1, time_window)
    last = per_ip_last.get(ip, 0.0)
    delta = float(count - last)
    per_ip_last[ip] = float(count)

    # EMA
    alpha = 2 / (ROLL_N + 1)
    ema_prev = per_ip_ema.get(ip, float(count))
    ema_now = _ema(ema_prev, float(count), alpha)
    per_ip_ema[ip] = ema_now

    # hora codificada
    now = datetime.utcnow()
    hour = now.hour
    import math
    hour_sin = math.sin(2 * math.pi * hour / 24.0)
    hour_cos = math.cos(2 * math.pi * hour / 24.0)

    zscore = (count - rolling_mean) / (rolling_std + 1e-6)

    return {
        "count": float(count),
        "rate": float(rate),
        "rolling_mean": float(rolling_mean),
        "rolling_std": float(rolling_std),
        "zscore": float(zscore),
        "delta_count": float(delta),
        "ema": float(ema_now),
        "hour_sin": float(hour_sin),
        "hour_cos": float(hour_cos),
    }

def process_detection(ip: str, count: int):
    """
    Llamar a esta función cuando, para una IP, el número de peticiones en la
    ventana TIME_WINDOW supere la regla o quieras registrar el evento.
    """
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    level = "SUSPICIOUS" if count > REQUEST_THRESHOLD else "INFO"

    # === ML scoring
    ml_score, ml_flag = None, 0
    if ML_ENABLED:
        feats = build_features(ip, count, TIME_WINDOW)
        try:
            ml_score = score_vector(feats)
            ml_flag = 1 if (ml_score is not None and ml_score >= ML_SCORE_THRESHOLD) else 0
        except Exception as e:
            ml_score, ml_flag = None, 0

    # TI (opcional)
    ab_conf = tot_rep = None
    last_rep = None
    if ti:
        info = ti.check(ip)
        if info:
            try:
                ab_conf = int(info.get("abuseConfidenceScore", 0))
                tot_rep = int(info.get("totalReports", 0))
                last_rep = info.get("lastReportedAt")
                import time as _t
                db.upsert_ti(ip, ab_conf, tot_rep, last_rep, int(_t.time()))
            except Exception:
                pass

    # Geo (opcional)
    lat = lon = None
    country = org = None
    if geo_lookup:
        try:
            g = geo_lookup(ip)
            lat = g.get("lat"); lon = g.get("lon")
            country = g.get("country"); org = g.get("org")
        except Exception:
            pass

    # Política de decisión final (ML + regla clásica), respetando allowlist
    from .db import in_allowlist, in_blocklist, add_block
    allow = in_allowlist(ip)
    rule_flag = (count > REQUEST_THRESHOLD)
    final_flag = (ml_flag == 1) or rule_flag

    # Auto-bloqueo ML (opcional)
    blocked = 0
    if not allow and final_flag:
        if ML_AUTOBLOCK_ENABLED and (ml_score is not None) and (ml_score >= ML_AUTOBLOCK_MIN_SCORE):
            add_block(ip, reason=f"ML autoblock score={ml_score:.2f}")
            blocked = 1
            try:
                block_ip_windows(ip)  # requiere admin
            except Exception:
                pass

    # Registrar evento
    db.insert_event(
        timestamp=ts,
        ip=ip,
        count=count,
        time_window=TIME_WINDOW,
        level=level,
        lat=lat, lon=lon, country=country, org=org,
        abuse_confidence=ab_conf, total_reports=tot_rep, last_reported_at=last_rep,
        blocked=blocked,
        ml_score=ml_score,
        ml_flag=ml_flag
    )

# ------------- Ejemplo de bucle detector -------------
# Integra aquí tu captura real (Scapy, pcap, etc.)
# Este loop simula detecciones periódicas a modo de ejemplo.

def main():
    print("[*] DDoS Analyzer running (ML enabled: %s, thr=%.2f)" % (ML_ENABLED, ML_SCORE_THRESHOLD))
    db.init_db()
    # TODO: sustituir por tu lógica real de conteo/trigger
    # Ejemplo: simular dos IPs con distintos counts cada TIME_WINDOW
    ip_list = ["8.8.8.8", "1.1.1.1"]
    while True:
        for ip in ip_list:
            # reemplaza esto por tu contador real en ventana
            import random
            count = random.choice([2,3,5,8,12,20])
            process_detection(ip, count)
        time.sleep(TIME_WINDOW)

if __name__ == "__main__":
    main()
