# src/report.py
import os
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.io as pio

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "events.db"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Periodo por defecto: últimas 24h (configurable por env)
HOURS = int(os.getenv("REPORT_HOURS", "24"))

# Notificación (opcional) por Telegram si ya tienes Notifier configurado
ENABLE_TELEGRAM = os.getenv("REPORT_TELEGRAM_NOTIFY", "false").strip().lower() in ("1", "true", "yes", "on")

def _severity(score: float) -> str:
    try:
        s = int(score)
    except Exception:
        s = 0
    if s >= 80: return "CRITICA"
    if s >= 50: return "ALTA"
    if s >= 20: return "MEDIA"
    if s >= 1:  return "BAJA"
    return "LIMPIA"

def load_dataframe(hours: int) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=[
            "timestamp","ip","count","time_window","level","lat","lon","country","org",
            "abuse_confidence","total_reports","last_reported_at"
        ])
    t_to = datetime.utcnow()
    t_from = t_to - timedelta(hours=hours)
    con = sqlite3.connect(str(DB_PATH))
    try:
        q = """
        SELECT
          e.timestamp, e.ip, e.count, e.time_window, e.level, e.lat, e.lon, e.country, e.org,
          t.abuse_confidence, t.total_reports, t.last_reported_at
        FROM events e
        LEFT JOIN ti_abuse t ON t.ip = e.ip
        WHERE e.timestamp >= ? AND e.timestamp <= ?
        ORDER BY e.timestamp ASC
        """
        df = pd.read_sql_query(q, con, params=(
            t_from.strftime("%Y-%m-%d %H:%M:%S"),
            t_to.strftime("%Y-%m-%d %H:%M:%S"),
        ))
    finally:
        con.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for c in ("count","time_window","lat","lon","abuse_confidence","total_reports"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df["severity"] = df["abuse_confidence"].apply(_severity)
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return df

def build_report(df: pd.DataFrame, hours: int) -> str:
    # KPIs
    total_alerts = len(df)
    last_min = 0
    uniq_ips = df["ip"].nunique() if "ip" in df.columns else 0
    max_count = int(df["count"].max()) if "count" in df.columns and not df["count"].isna().all() and not df.empty else 0
    if not df.empty and "timestamp" in df.columns:
        now_ts = pd.Timestamp.utcnow().tz_localize(None)
        last_min = len(df[df["timestamp"] >= (now_ts - pd.Timedelta(minutes=1))])

    # Top IPs
    fig_top_html = ""
    if not df.empty and "ip" in df.columns and "count" in df.columns:
        _top = (df.groupby("ip", as_index=False)["count"].sum()
                  .sort_values("count", ascending=False).head(15))
        if not _top.empty:
            _fig_top = px.bar(_top, x="ip", y="count", title="Top IPs por total de peticiones")
            fig_top_html = pio.to_html(_fig_top, full_html=False, include_plotlyjs='cdn')

    # Serie temporal
    fig_time_html = ""
    if not df.empty and "timestamp" in df.columns:
        _df_min = df.copy()
        _df_min["minute"] = _df_min["timestamp"].dt.floor("min")
        _agg = _df_min.groupby("minute").size().reset_index(name="alerts")
        if not _agg.empty:
            _fig_time = px.line(_agg, x="minute", y="alerts", markers=True, title="Alertas por minuto")
            fig_time_html = pio.to_html(_fig_time, full_html=False, include_plotlyjs=False)

    # Mapa
    fig_map_html = ""
    if all(c in df.columns for c in ["lat","lon","ip"]) and not df.empty:
        _map_df = df.dropna(subset=["lat","lon"])
        if not _map_df.empty:
            _fig_map = px.scatter_geo(
                _map_df,
                lat="lat", lon="lon",
                hover_name="ip",
                hover_data={"country": True, "org": True, "count": True, "abuse_confidence": "abuse_confidence" in df.columns},
                size="count" if "count" in _map_df.columns else None,
                projection="natural earth",
                title="Distribución geográfica de alertas"
            )
            fig_map_html = pio.to_html(_fig_map, full_html=False, include_plotlyjs=False)

    # Tabla (hasta 500 últimas)
    cols_show = [c for c in ["timestamp","ip","count","time_window","level","severity","abuse_confidence","total_reports","country","org"] if c in df.columns]
    table_html = ""
    if cols_show and not df.empty:
        _tbl = df.sort_values("timestamp", ascending=False)[cols_show].head(500).to_html(index=False)
        table_html = f"<h3>Últimas alertas</h3>{_tbl}"

    # HTML final
    html_report = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Informe DDoS – Últimas {hours}h</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; color: #111; }}
h1, h2, h3 {{ margin: 0.6em 0 0.3em; }}
.card {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 10px 0; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap: 10px; }}
.kpi {{ border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fafafa; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ border: 1px solid #eaeaea; padding: 6px 8px; text-align: left; }}
th {{ background: #f5f5f5; }}
footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
</style>
</head>
<body>
  <h1>Informe de Detección DDoS</h1>
  <div class="card">
    <div><strong>Periodo:</strong> últimas {hours} horas</div>
    <div><strong>Generado:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
  </div>

  <div class="card">
    <h2>KPIs</h2>
    <div class="kpi-grid">
      <div class="kpi"><strong>Total alertas</strong><div>{total_alerts}</div></div>
      <div class="kpi"><strong>Alertas último minuto</strong><div>{last_min}</div></div>
      <div class="kpi"><strong>IPs distintas</strong><div>{uniq_ips}</div></div>
      <div class="kpi"><strong>Máx. peticiones</strong><div>{max_count}</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Top IPs</h2>
    {fig_top_html or "<em>Sin datos suficientes</em>"}
  </div>

  <div class="card">
    <h2>Serie temporal</h2>
    {fig_time_html or "<em>Sin datos suficientes</em>"}
  </div>

  <div class="card">
    <h2>Mapa</h2>
    {fig_map_html or "<em>Sin datos geolocalizados</em>"}
  </div>

  <div class="card">
    {table_html or "<h3>Últimas alertas</h3><em>No hay registros</em>"}
  </div>

  <footer>
    Generado por el DDoS Analyzer · HTML autocontenido.
  </footer>
</body>
</html>
    """.strip()
    return html_report

def notify_telegram(df: pd.DataFrame, hours: int, html_path: Path, csv_path: Path):
    if not ENABLE_TELEGRAM:
        return
    try:
        # Import perezoso para no romper si Notifier no existe
        from .notifier import Notifier
        n = Notifier()
        total_alerts = len(df)
        uniq_ips = df["ip"].nunique() if "ip" in df.columns else 0
        msg = (
            f"📊 Informe DDoS generado\n"
            f"Periodo: últimas {hours}h\n"
            f"Alertas: {total_alerts}\n"
            f"IPs únicas: {uniq_ips}\n"
            f"HTML: {html_path.name}\n"
            f"CSV: {csv_path.name}"
        )
        n.send_telegram(msg)
    except Exception:
        pass

def run(hours: int = HOURS):
    df = load_dataframe(hours)
    ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    html = build_report(df, hours)
    html_path = REPORTS_DIR / f"report_{ts_name}_{hours}h.html"
    csv_path = REPORTS_DIR / f"report_{ts_name}_{hours}h.csv"
    # Guardar
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    df.to_csv(csv_path, index=False)
    # Notificar (opcional)
    notify_telegram(df, hours, html_path, csv_path)
    print(f"[OK] Reporte generado: {html_path}")
    print(f"[OK] CSV generado: {csv_path}")

if __name__ == "__main__":
    run()
