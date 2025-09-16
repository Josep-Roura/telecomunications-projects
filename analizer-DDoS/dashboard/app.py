# dashboard/app.py
import os
import io
import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Pathing: permitir importar src.* desde /dashboard
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src import db
from src.response import block_ip_windows, unblock_ip_windows  # no-op en Linux si no existe
# (Opcional) si quieres re-chequear reputación desde UI
try:
    from src.ti_abuseipdb import AbuseIPDB
except Exception:
    AbuseIPDB = None

# ──────────────────────────────────────────────────────────────────────────────
# Config general
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="DDoS Detection – Live Dashboard", layout="wide")

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "").strip()
ML_DEFAULT_THR = float(os.getenv("ML_SCORE_THRESHOLD", "0.5"))

# Rutas
BASE_DATA_PATH = ROOT / "data" / "events.csv"
ENRICHED_DATA_PATH = ROOT / "data" / "events_enriched.csv"
DB_PATH = ROOT / "data" / "events.db"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TASKS_DIR = ROOT / "tasks"
RUN_REPORT_PS1 = TASKS_DIR / "run_report.ps1"
SCHED_TASK_NAME = "DDoS-GenerateDailyReport"

# ──────────────────────────────────────────────────────────────────────────────
# Auth simple (opcional)
# ──────────────────────────────────────────────────────────────────────────────
def _check_auth() -> bool:
    if not DASHBOARD_PASSWORD:
        return True
    if "auth_ok" not in st.session_state:
        st.session_state["auth_ok"] = False
    if st.session_state["auth_ok"]:
        return True
    with st.sidebar:
        st.markdown("### 🔐 Login")
        pwd = st.text_input("Password", type="password")
        if st.button("Entrar"):
            if pwd == DASHBOARD_PASSWORD:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("Password incorrecto")
    return False

if not _check_auth():
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Inicio
# ──────────────────────────────────────────────────────────────────────────────
st.title("🔒 DDoS Detection – Live Dashboard")
db.init_db()  # asegura/migra esquema

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar: ajustes generales
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Ajustes")
REFRESH_SEC = st.sidebar.slider("Auto-refresh (segundos)", 2, 30, 5)
source = st.sidebar.radio("Fuente de datos", ["SQLite (recomendado)", "CSV"], index=0)

# Filtros
with st.sidebar.expander("Filtros", expanded=True):
    ip_filter = st.text_input("Filtrar por IP (contiene)", value="")
    date_from = st.date_input("Desde", value=None)
    date_to = st.date_input("Hasta", value=None)
    sev_sel = st.multiselect(
        "Criticidad (AbuseIPDB)",
        ["CRITICA", "ALTA", "MEDIA", "BAJA", "LIMPIA"],
        default=[]
    )
    # ── ML (nuevo)
    ml_thr = st.slider("Umbral ML score", 0.0, 5.0, ML_DEFAULT_THR, 0.05,
                       help="Mayor = más anómalo")
    use_ml_filter = st.checkbox("Filtrar por ML (>= umbral)", value=False)

# ──────────────────────────────────────────────────────────────────────────────
# Utilidades de carga de datos
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_COLS = ["timestamp", "ip", "count", "time_window", "level"]
ENRICHED_COLS = ["timestamp", "ip", "count", "time_window", "level", "lat", "lon", "country", "org"]

def severity(score: int) -> str:
    if score is None: score = 0
    if score >= 80: return "CRITICA"
    if score >= 50: return "ALTA"
    if score >= 20: return "MEDIA"
    if score >= 1:  return "BAJA"
    return "LIMPIA"

def _read_csv_robust(path: Path, expected_cols):
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=expected_cols)
    try:
        df = pd.read_csv(path)
        if expected_cols[0] not in df.columns:
            df = pd.read_csv(path, header=None, names=expected_cols)
    except Exception:
        df = pd.read_csv(path, header=None, names=expected_cols)
    return df

def _load_from_csv():
    # Si existe el enriquecido, úsalo
    if ENRICHED_DATA_PATH.exists():
        df = _read_csv_robust(ENRICHED_DATA_PATH, ENRICHED_COLS)
    else:
        df = _read_csv_robust(BASE_DATA_PATH, DEFAULT_COLS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

def _load_from_db():
    if not DB_PATH.exists():
        return pd.DataFrame(columns=ENRICHED_COLS + ["abuse_confidence","total_reports","last_reported_at","severity","ml_score","ml_flag"])
    con = sqlite3.connect(str(DB_PATH))
    try:
        where = []
        params = []
        if ip_filter:
            where.append("e.ip LIKE ?"); params.append(f"%{ip_filter}%")
        if date_from:
            where.append("e.timestamp >= ?"); params.append(f"{pd.Timestamp(date_from).strftime('%Y-%m-%d')} 00:00:00")
        if date_to:
            where.append("e.timestamp <= ?"); params.append(f"{pd.Timestamp(date_to).strftime('%Y-%m-%d')} 23:59:59")
        wh = ("WHERE " + " AND ".join(where)) if where else ""
        q = f"""
            SELECT
              e.timestamp, e.ip, e.count, e.time_window, e.level,
              e.lat, e.lon, e.country, e.org,
              t.abuse_confidence, t.total_reports, t.last_reported_at,
              e.ml_score, e.ml_flag, e.blocked
            FROM events e
            LEFT JOIN ti_abuse t ON t.ip = e.ip
            {wh}
            ORDER BY e.timestamp ASC
        """
        df = pd.read_sql_query(q, con, params=params)
        # enriquecimientos derivados
        if "abuse_confidence" in df.columns:
            df["severity"] = df["abuse_confidence"].apply(lambda s: severity(int(s) if pd.notna(s) else 0))
        return df
    finally:
        con.close()

@st.cache_data(ttl=2)
def load_data_cached(src_key: str):
    if src_key == "CSV":
        df = _load_from_csv()
    else:
        df = _load_from_db()

    # Tipados
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
    for c in ("count","time_window","lat","lon","abuse_confidence","total_reports","ml_score","ml_flag"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "ml_flag" in df.columns:
        df["ml_flag"] = df["ml_flag"].fillna(0).astype(int)

    # Orden
    if not df.empty and "timestamp" in df.columns:
        df = df.sort_values("timestamp").reset_index(drop=True)

    # Filtro de severidad
    if "severity" in df.columns and sev_sel:
        df = df[df["severity"].isin(sev_sel)]

    # Filtro ML
    if "ml_score" in df.columns and use_ml_filter:
        df = df[df["ml_score"] >= ml_thr]

    return df

df = load_data_cached("CSV" if source == "CSV" else "DB")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar: Exportar / Guardar reportes
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar.expander("📤 Exportar", expanded=False):
    # CSV con filtros aplicados (descarga)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label="⬇️ Descargar CSV (filtros aplicados)",
        data=csv_buf.getvalue(),
        file_name=f"ddos_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # KPIs para el informe HTML
    total_alerts = len(df)
    now_ts = pd.Timestamp.utcnow().tz_localize(None)
    last_min = len(df[df["timestamp"] >= (now_ts - pd.Timedelta(minutes=1))]) if "timestamp" in df.columns else 0
    uniq_ips = df["ip"].nunique() if "ip" in df.columns else 0
    max_count = int(df["count"].max()) if "count" in df.columns and not df["count"].isna().all() else 0

    # Gráfico Top IPs (HTML)
    fig_top_html = ""
    if "ip" in df.columns and "count" in df.columns and not df.empty:
        _top = (df.groupby("ip", as_index=False)["count"].sum()
                  .sort_values("count", ascending=False).head(15))
        if not _top.empty:
            _fig_top = px.bar(_top, x="ip", y="count", title="Top IPs por total de peticiones")
            fig_top_html = pio.to_html(_fig_top, full_html=False, include_plotlyjs='cdn')

    # Serie temporal (HTML)
    fig_time_html = ""
    if "timestamp" in df.columns and not df.empty:
        _df_min = df.copy()
        _df_min["minute"] = _df_min["timestamp"].dt.floor("min")
        _agg = _df_min.groupby("minute").size().reset_index(name="alerts")
        if not _agg.empty:
            _fig_time = px.line(_agg, x="minute", y="alerts", markers=True, title="Alertas por minuto")
            fig_time_html = pio.to_html(_fig_time, full_html=False, include_plotlyjs=False)

    # Mapa (HTML)
    fig_map_html = ""
    if all(c in df.columns for c in ["lat","lon","ip"]):
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

    cols_show_export = [c for c in ["timestamp","ip","count","time_window","level","severity","abuse_confidence","total_reports","country","org","ml_score","ml_flag"] if c in df.columns]
    table_html = ""
    if cols_show_export:
        _tbl = df.sort_values("timestamp", ascending=False)[cols_show_export].head(500).to_html(index=False)
        table_html = f"<h3>Últimas alertas</h3>{_tbl}"

    html_report = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Informe DDoS – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
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

    # Botones de descarga directa
    st.download_button(
        label="🧾 Descargar Informe HTML (filtros aplicados)",
        data=html_report.encode("utf-8"),
        file_name=f"ddos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
        use_container_width=True
    )

    # GUARDAR (HTML+CSV) en /reports
    st.markdown("---")
    st.markdown("**💾 Guardar informe en carpeta `/reports`**")
    hours = st.number_input("Rango del informe en horas (para el nombre)", min_value=1, max_value=168, value=24, step=1)
    if st.button("Guardar HTML + CSV en /reports"):
        ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = REPORTS_DIR / f"report_{ts_name}_{hours}h.html"
        csv_path  = REPORTS_DIR / f"report_{ts_name}_{hours}h.csv"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        df.to_csv(csv_path, index=False)
        st.success(f"Guardado 👍  {html_path.name} y {csv_path.name}")
        st.info(f"Ruta: {REPORTS_DIR}")

# ──────────────────────────────────────────────────────────────────────────────
# 📅 Programar reportes (schtasks)
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar.expander("📅 Programar reportes", expanded=False):
    st.write("Crea una tarea diaria de Windows que ejecuta el reporte HTML+CSV en `/reports`.")
    colA, colB = st.columns(2)
    hour = colA.number_input("Hora", min_value=0, max_value=23, value=8, step=1)
    minute = colB.number_input("Minuto", min_value=0, max_value=59, value=0, step=5)
    hours_range = st.number_input("Rango del informe (horas)", min_value=1, max_value=168, value=24, step=1)
    notify = st.checkbox("Notificar por Telegram", value=False)
    task_name = st.text_input("Nombre de la tarea", value=SCHED_TASK_NAME)

    def _schtasks_exists(name: str) -> bool:
        try:
            r = os.popen(f'schtasks /Query /TN "{name}"').read()
            return "ERROR:" not in r
        except Exception:
            return False

    def _create_or_update_task(name: str, hh: int, mm: int, hrs: int, notify_flag: bool):
        if not RUN_REPORT_PS1.exists():
            st.error(f"No existe {RUN_REPORT_PS1}. Crea el archivo tasks/run_report.ps1.")
            return False
        time_str = f"{hh:02d}:{mm:02d}"
        ps_cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{RUN_REPORT_PS1}" -Hours {hrs} ' + ( "-Notify" if notify_flag else "" )
        args = f'schtasks /Create /SC DAILY /ST {time_str} /TN "{name}" /TR \'{ps_cmd}\' /F'
        r = os.popen(args).read()
        if "SUCCESS" in r.upper():
            st.success(f"Tarea '{name}' programada a las {time_str} (diaria).")
            return True
        else:
            st.error(f"Error creando tarea:\n{r}")
            return False

    def _delete_task(name: str):
        r = os.popen(f'schtasks /Delete /TN "{name}" /F').read()
        if "SUCCESS" in r.upper():
            st.success(f"Tarea '{name}' eliminada.")
            return True
        else:
            st.error(f"No se pudo eliminar:\n{r}")
            return False

    c1, c2, c3 = st.columns(3)
    if c1.button("✅ Crear/Actualizar"):
        _create_or_update_task(task_name, int(hour), int(minute), int(hours_range), bool(notify))
    if c2.button("🗑️ Eliminar"):
        if _schtasks_exists(task_name):
            _delete_task(task_name)
        else:
            st.info("La tarea no existe.")
    if c3.button("▶️ Ejecutar ahora"):
        if not RUN_REPORT_PS1.exists():
            st.error(f"No existe {RUN_REPORT_PS1}.")
        else:
            try:
                import subprocess
                cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_REPORT_PS1),
                       "-Hours", str(int(hours_range))]
                if notify:
                    cmd.append("-Notify")
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0:
                    st.success("Reporte generado ahora. Revisa la carpeta /reports.")
                    if r.stdout.strip():
                        st.code(r.stdout.strip(), language="text")
                else:
                    st.error("Fallo al ejecutar el reporte ahora.")
                    st.code((r.stderr or r.stdout)[:2000], language="text")
            except Exception as e:
                st.error(f"Error ejecutando el reporte: {e}")

    exists = _schtasks_exists(task_name)
    st.caption(f"Estado de la tarea '{task_name}': {'🟢 EXISTE' if exists else '🔴 NO EXISTE'}")

# ──────────────────────────────────────────────────────────────────────────────
# KPIs
# ──────────────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total alertas", f"{len(df):,}")
now = pd.Timestamp.utcnow().tz_localize(None)
col2.metric("Último minuto", f"{len(df[df['timestamp'] >= (now - pd.Timedelta(minutes=1))])}" if "timestamp" in df.columns else "0")
col3.metric("IPs distintas", df["ip"].nunique() if "ip" in df.columns else 0)
col4.metric("Máx. peticiones", int(df["count"].max()) if "count" in df.columns and not df["count"].isna().all() else 0)

if "ml_flag" in df.columns and len(df):
    pct = 100.0 * (df["ml_flag"].sum() / len(df))
    st.metric("Marcados por ML (%)", f"{pct:.1f}%")

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Tabla principal
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("🧾 Últimas alertas")
cols_show = [c for c in [
    "timestamp","ip","count","time_window","level",
    "severity","abuse_confidence","total_reports","country","org",
    "ml_score","ml_flag","blocked"
] if c in df.columns]
table_df = df.sort_values("timestamp", ascending=False)[cols_show].head(300)

def _row_style(row):
    sty = [""]*len(row)
    # colorear por severidad si existe
    if "severity" in row:
        sev = str(row.get("severity") or "")
        color = ""
        if sev == "CRITICA": color = "#ffcccc"
        elif sev == "ALTA":  color = "#ffe6cc"
        elif sev == "MEDIA": color = "#fff6cc"
        elif sev == "BAJA":  color = "#f2ffcc"
        if color:
            sty = [f"background-color: {color}"]*len(row)
    # resaltar ML flag
    if "ml_flag" in row and int(row["ml_flag"]) == 1:
        sty = [s + "; font-weight: 600" if s else "font-weight: 600" for s in sty]
    # bloqueados
    if "blocked" in row and int(row["blocked"]) == 1:
        sty = [s + "; border-left: 4px solid #b00" if s else "border-left: 4px solid #b00" for s in sty]
    return sty

try:
    st.dataframe(table_df.style.apply(_row_style, axis=1), use_container_width=True, height=420)
except Exception:
    st.dataframe(table_df, use_container_width=True, height=420)

# ──────────────────────────────────────────────────────────────────────────────
# Gráficos
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("📈 Gráficos")

gcol1, gcol2 = st.columns(2)

with gcol1:
    st.markdown("**Top IPs por total de peticiones**")
    if "ip" in df.columns and "count" in df.columns and not df.empty:
        _top = (df.groupby("ip", as_index=False)["count"].sum()
                  .sort_values("count", ascending=False).head(15))
        if not _top.empty:
            fig = px.bar(_top, x="ip", y="count")
            st.plotly_chart(fig, use_container_width=True)

with gcol2:
    st.markdown("**Top IPs por ML score (máximo)**")
    if "ip" in df.columns and "ml_score" in df.columns and not df.empty:
        _top_ml = (df.groupby("ip", as_index=False)["ml_score"]
                     .max()
                     .sort_values("ml_score", ascending=False)
                     .head(15))
        if not _top_ml.empty:
            fig_ml = px.bar(_top_ml, x="ip", y="ml_score")
            st.plotly_chart(fig_ml, use_container_width=True)

st.markdown("**⏱️ Alertas por minuto**")
if "timestamp" in df.columns and not df.empty:
    df_min = df.copy()
    df_min["minute"] = df_min["timestamp"].dt.floor("min")
    agg = df_min.groupby("minute").size().reset_index(name="alerts")
    fig_line = px.line(agg, x="minute", y="alerts", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("**🗺️ Mapa de IPs sospechosas**")
if all(c in df.columns for c in ["lat","lon","ip"]):
    map_df = df.dropna(subset=["lat","lon"])
    if not map_df.empty:
        fig_map = px.scatter_geo(
            map_df,
            lat="lat", lon="lon",
            hover_name="ip",
            hover_data={"country": True, "org": True, "count": True,
                        "abuse_confidence": "abuse_confidence" in df.columns,
                        "ml_score": "ml_score" in df.columns,
                        "lat": False, "lon": False},
            size="count" if "count" in map_df.columns else None,
            projection="natural earth",
        )
        st.plotly_chart(fig_map, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Acciones laterales: listas y firewall
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar.expander("Acciones sobre IP", expanded=False):
    default_ip = df["ip"].iloc[-1] if "ip" in df.columns and len(df) else ""
    target_ip = st.text_input("IP objetivo", value=default_ip, key="ip_target")
    reason = st.text_input("Motivo (opcional)", value="Manual action", key="ip_reason")

    c1, c2 = st.columns(2)
    if c1.button("➕ Blocklist"):
        if target_ip:
            db.add_block(target_ip, reason)
            st.success(f"{target_ip} añadida a blocklist")
            st.rerun()
    if c2.button("➖ Quitar Blocklist"):
        if target_ip:
            db.del_block(target_ip)
            st.success(f"{target_ip} eliminada de blocklist")
            st.rerun()

    c3, c4 = st.columns(2)
    if c3.button("✅ Allowlist"):
        if target_ip:
            db.add_allow(target_ip, reason)
            st.success(f"{target_ip} añadida a allowlist")
            st.rerun()
    if c4.button("❌ Quitar Allowlist"):
        if target_ip:
            db.del_allow(target_ip)
            st.success(f"{target_ip} eliminada de allowlist")
            st.rerun()

    st.markdown("---")
    if st.button("🧱 Bloquear en Windows (netsh)"):
        ok = block_ip_windows(target_ip) if target_ip else False
        st.success(f"Regla creada para {target_ip}") if ok else st.error("Fallo al crear regla (¿Admin?)")

    if st.button("🔓 Desbloquear en Windows"):
        ok = unblock_ip_windows(target_ip) if target_ip else False
        st.success(f"Regla eliminada para {target_ip}") if ok else st.error("Fallo al eliminar regla (¿Admin?)")

    st.markdown("---")
    # 🔄 Rechequear reputación ahora (opcional)
    if st.button("🔄 Rechequear reputación (AbuseIPDB)"):
        if not AbuseIPDB:
            st.error("Módulo no disponible")
        else:
            ti = AbuseIPDB()
            if not ti.enabled():
                st.error("No hay ABUSEIPDB_KEY en .env")
            else:
                info = ti.check(target_ip)
                if info is None:
                    st.error("No se pudo obtener reputación (rate limit o fallo de red)")
                else:
                    ac = int(info.get("abuseConfidenceScore", 0))
                    tr = int(info.get("totalReports", 0))
                    lr = info.get("lastReportedAt")
                    import time as _t
                    db.upsert_ti(target_ip, ac, tr, lr, int(_t.time()))
                    st.success(f"Reputación actualizada: score={ac}, reports={tr}")
                    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Listas de control
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🛡️ Blocklist / Allowlist")
bl = db.list_blocklist()
al = db.list_allowlist()
bl_df = pd.DataFrame(bl, columns=["ip","reason","created_at"])
al_df = pd.DataFrame(al, columns=["ip","reason","created_at"])
colA, colB = st.columns(2)
with colA:
    st.write("**Blocklist**")
    st.dataframe(bl_df, use_container_width=True, height=250)
with colB:
    st.write("**Allowlist**")
    st.dataframe(al_df, use_container_width=True, height=250)

# ──────────────────────────────────────────────────────────────────────────────
# Auto-refresh
# ──────────────────────────────────────────────────────────────────────────────
st.caption(f"Fuente: {source} • Auto-actualizando cada {REFRESH_SEC}s")
time.sleep(REFRESH_SEC)
st.rerun()
