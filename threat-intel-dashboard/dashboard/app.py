import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import json
import sys, subprocess
from pathlib import Path
from datetime import time as dtime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.config import DB_PATH, REPORTS_DIR

st.set_page_config(page_title="Threat Intelligence Dashboard", layout="wide")

# ====== Encabezado con logo si existe ======
logo_path = None
for p in [ROOT / "assets" / "logo.png", ROOT / "assets" / "logo.jpg"]:
    if p.exists():
        logo_path = p
        break

colH1, colH2 = st.columns([0.15, 0.85])
with colH1:
    if logo_path:
        st.image(str(logo_path))
with colH2:
    st.title("Threat Intelligence Dashboard")
    st.markdown(
        "Integración multi-fuente: **AbuseIPDB** + **Ipinfo** + **VirusTotal** (IPs, dominios y hashes). "
        "Incluye buscador, importación CSV, reportes y **modo demo** para presentación."
    )

# =========================
# Helpers
# =========================
def short_label(value: str, max_len: int = 20) -> str:
    """
    Acorta etiquetas largas para ejes de gráficos sin perder contexto,
    preservando inicio y final. Ej: 64-char SHA256 -> 'abcd1234…9f8e7d'
    """
    if value is None:
        return ""
    s = str(value)
    if len(s) <= max_len:
        return s
    head, tail = 10, 6
    if head + tail + 1 > max_len:
        head = max_len // 2 - 1
        tail = max_len - head - 1
    return f"{s[:head]}…{s[-tail:]}"

# =========================
# Sidebar: resolver / importar / demo / reportes
# =========================
st.sidebar.header("🔍 Consultar/Resolver IOC")
ioc_type_side = st.sidebar.radio("Tipo", ["ip", "domain", "hash"], horizontal=True)
ioc_value_side = st.sidebar.text_input("Valor (IP, dominio o hash)")
if st.sidebar.button("Resolver IOC"):
    if not ioc_value_side.strip():
        st.sidebar.warning("Introduce un valor.")
    else:
        cmd = [sys.executable, "-m", "src.main", f"--ioc-{ioc_type_side}", ioc_value_side.strip()]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            st.sidebar.success(r.stdout or "OK")
        else:
            st.sidebar.error(r.stderr or "Fallo al resolver")

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Importar CSV de IOCs")
st.sidebar.caption("Formato: columnas `ioc_type,value` (ip|domain|hash)")
csv_file = st.sidebar.file_uploader("Selecciona CSV", type=["csv"])
if csv_file is not None:
    try:
        df_up = pd.read_csv(csv_file)
        if not {"ioc_type","value"}.issubset(set(df_up.columns)):
            st.sidebar.error("El CSV debe tener columnas: ioc_type,value")
        else:
            go = st.sidebar.button("Procesar CSV")
            if go:
                total = len(df_up)
                prog = st.sidebar.progress(0.0, text="Resolviendo IOCs...")
                ok, fail = 0, 0
                for i, row in df_up.iterrows():
                    t = str(row["ioc_type"]).strip().lower()
                    v = str(row["value"]).strip()
                    if t not in ("ip","domain","hash") or not v:
                        fail += 1
                        prog.progress((i+1)/total, text=f"Saltado {i+1}/{total}")
                        continue
                    cmd = [sys.executable, "-m", "src.main", f"--ioc-{t}", v]
                    try:
                        r = subprocess.run(cmd, capture_output=True, text=True)
                        if r.returncode == 0:
                            ok += 1
                        else:
                            fail += 1
                    except Exception:
                        fail += 1
                    prog.progress((i+1)/total, text=f"Procesado {i+1}/{total}")
                st.sidebar.success(f"Importación finalizada: OK={ok}, KO={fail}")
    except Exception as e:
        st.sidebar.error(f"Error leyendo CSV: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("🎭 Modo Demo (sin APIs)")
demo_ips   = st.sidebar.slider("IPs demo", 0, 100, 25, 5)
demo_dom   = st.sidebar.slider("Dominios demo", 0, 50, 12, 2)
demo_hash  = st.sidebar.slider("Hashes demo", 0, 50, 10, 2)
if st.sidebar.button("Generar datos demo"):
    r = subprocess.run(
        [sys.executable, "-m", "src.seed_demo", "--ips", str(demo_ips), "--domains", str(demo_dom), "--hashes", str(demo_hash)],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        st.sidebar.success(r.stdout.strip())
    else:
        st.sidebar.error(r.stderr or "Fallo generando demo (revisa permisos)")

st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Programar reportes (Windows)")
st.sidebar.caption("Crea una tarea diaria que ejecute reportes HTML/CSV/PDF en /reports")
rep_hours = st.sidebar.selectbox("Ventana (horas)", [6,12,24,48,72], index=2)
rep_time = st.sidebar.time_input("Hora local", value=dtime(9,0))
task_name = "TID_Reports_Daily"
create_task = st.sidebar.button("Crear/Actualizar tarea")
delete_task = st.sidebar.button("Eliminar tarea")
run_now     = st.sidebar.button("Ejecutar ahora (HTML/CSV)")
run_pdf     = st.sidebar.button("Generar PDF ahora")

if create_task:
    py = sys.executable
    cmd = f'"{py}" -m src.report --hours {rep_hours}'
    sch = ["schtasks", "/Create", "/TN", task_name, "/TR", cmd, "/SC", "DAILY", "/ST", rep_time.strftime("%H:%M"), "/F"]
    r = subprocess.run(sch, capture_output=True, text=True, shell=False)
    st.sidebar.success("Tarea programada/actualizada correctamente." if r.returncode == 0 else (r.stderr or "Error creando tarea (Admin)"))

if delete_task:
    r = subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"], capture_output=True, text=True, shell=False)
    st.sidebar.success("Tarea eliminada." if r.returncode == 0 else (r.stderr or "No se pudo eliminar (¿no existe?)."))

if run_now:
    r = subprocess.run([sys.executable, "-m", "src.report", "--hours", str(rep_hours)], capture_output=True, text=True)
    if r.returncode == 0:
        info = json.loads(r.stdout.strip())
        st.sidebar.success(f"Reporte generado: {info.get('html')}")
    else:
        st.sidebar.error(r.stderr or "Fallo generando reporte.")

if run_pdf:
    r = subprocess.run([sys.executable, "-m", "src.report_pdf", "--hours", str(rep_hours)], capture_output=True, text=True)
    if r.returncode == 0:
        info = json.loads(r.stdout.strip())
        st.sidebar.success(f"PDF generado: {info.get('pdf')}")
    else:
        st.sidebar.error(r.stderr or "Fallo generando PDF.")

# =========================
# Carga de datos desde DB
# =========================
def load_table():
    con = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query("""
            SELECT ioc_type, value, first_seen, last_seen, ti_score
            FROM ioc
            ORDER BY last_seen DESC;
        """, con)
        perf_ip = pd.read_sql_query("""
            SELECT value, json
            FROM ioc_attrs
            WHERE ioc_type='ip' AND source='profile';
        """, con)
        perf_domain = pd.read_sql_query("""
            SELECT value, json
            FROM ioc_attrs
            WHERE ioc_type='domain' AND source='profile';
        """, con)
        perf_hash = pd.read_sql_query("""
            SELECT value, json
            FROM ioc_attrs
            WHERE ioc_type='hash' AND source='profile';
        """, con)
    finally:
        con.close()

    meta_ip, meta_dom, meta_hash = {}, {}, {}
    for _, row in perf_ip.iterrows():
        try: meta_ip[row["value"]] = json.loads(row["json"])
        except Exception: pass
    for _, row in perf_domain.iterrows():
        try: meta_dom[row["value"]] = json.loads(row["json"])
        except Exception: pass
    for _, row in perf_hash.iterrows():
        try: meta_hash[row["value"]] = json.loads(row["json"])
        except Exception: pass

    if not df.empty:
        df["first_seen"] = pd.to_datetime(df["first_seen"])
        df["last_seen"]  = pd.to_datetime(df["last_seen"])
        df["country"] = df.apply(lambda r: (meta_ip.get(r["value"]) or {}).get("country") if r["ioc_type"]=="ip" else None, axis=1)
        df["org"]     = df.apply(lambda r: (meta_ip.get(r["value"]) or {}).get("org") if r["ioc_type"]=="ip" else None, axis=1)
        df["file_type"] = df.apply(lambda r: (meta_hash.get(r["value"]) or {}).get("type_description") if r["ioc_type"]=="hash" else None, axis=1)
        df["file_size"] = df.apply(lambda r: (meta_hash.get(r["value"]) or {}).get("size") if r["ioc_type"]=="hash" else None, axis=1)
    return df

def load_attrs(ioc_type: str, value: str) -> dict:
    con = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query("""
            SELECT source, json, updated_at
            FROM ioc_attrs
            WHERE ioc_type=? AND value=?
            ORDER BY source ASC
        """, con, params=(ioc_type, value))
    finally:
        con.close()
    out = {}
    for _, row in df.iterrows():
        try:
            out[row["source"]] = {"updated_at": row["updated_at"], "data": json.loads(row["json"])}
        except Exception:
            out[row["source"]] = {"updated_at": row["updated_at"], "data": row["json"]}
    return out

df = load_table()

# =========================
# Buscador global + ficha
# =========================
st.markdown("### 🧭 Buscador global")
col_s1, col_s2, col_s3 = st.columns([1, 3, 1])
with col_s1:
    ioc_type_q = st.selectbox("Tipo", ["ip", "domain", "hash"])
with col_s2:
    ioc_value_q = st.text_input("Valor (IP, dominio o hash)")
with col_s3:
    view_btn = st.button("Ver ficha")

if view_btn and ioc_value_q.strip():
    val = ioc_value_q.strip()
    row = None
    if not df.empty:
        candidates = df[(df["ioc_type"] == ioc_type_q) & (df["value"] == val)]
        if not candidates.empty:
            row = candidates.iloc[0]

    st.markdown("---")
    st.subheader(f"🗂️ Ficha IOC: `{ioc_type_q}` → **{val}**")

    ti_score = int(row["ti_score"]) if row is not None else None
    country = row["country"] if (row is not None and ioc_type_q == "ip") else None
    org     = row["org"]     if (row is not None and ioc_type_q == "ip") else None
    file_type = row["file_type"] if (row is not None and ioc_type_q == "hash") else None
    file_size = row["file_size"] if (row is not None and ioc_type_q == "hash") else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TI score", ti_score if ti_score is not None else "-")
    c2.metric("País", country if country else ("N/A" if ioc_type_q != "ip" else "-"))
    c3.metric("Org/ASN", org if org else ("N/A" if ioc_type_q != "ip" else "-"))
    c4.metric("Último registro", row["last_seen"].strftime("%Y-%m-%d %H:%M:%S") if row is not None else "-")

    attrs = load_attrs(ioc_type_q, val)

    tabs = st.tabs(["Visión general", "Fuentes", "Mapa", "Detalle VirusTotal", "Exportar"])
    with tabs[0]:
        st.write("**Resumen**")
        st.json({
            "ioc_type": ioc_type_q,
            "value": val,
            "ti_score": ti_score,
            "country": country if ioc_type_q=="ip" else None,
            "org": org if ioc_type_q=="ip" else None,
            "file_type": file_type if ioc_type_q=="hash" else None,
            "file_size": file_size if ioc_type_q=="hash" else None,
        })
        if not df.empty:
            top_rel = df[df["ioc_type"] == ioc_type_q].sort_values("ti_score", ascending=False).head(15).copy()
            if not top_rel.empty:
                top_rel["label"] = top_rel["value"].apply(short_label)
                fig = px.bar(
                    top_rel,
                    x="label",
                    y="ti_score",
                    title=f"Top {ioc_type_q}s por TI score",
                )
                fig.update_traces(
                    hovertemplate="<b>%{customdata}</b><br>TI score=%{y}<extra></extra>",
                    customdata=top_rel["value"]
                )
                st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.write("**Datos por fuente** (raw JSON)")
        if not attrs:
            st.info("No hay atributos almacenados para este IOC todavía.")
        else:
            for src, payload in attrs.items():
                st.markdown(f"**Fuente: `{src}`** (updated_at: {payload.get('updated_at')})")
                st.json(payload.get("data"))
        st.markdown("---")
        if st.button("↻ Re-resolver IOC (refrescar caché)"):
            cmd = [sys.executable, "-m", "src.main", f"--ioc-{ioc_type_q}", val]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                st.success("IOC re-resuelto. Vuelve a pulsar 'Ver ficha' para recargar.")
            else:
                st.error(r.stderr or "Fallo al re-resolver")

    with tabs[2]:
        if ioc_type_q == "ip":
            ip_attrs = attrs.get("profile", {}).get("data", {}) or {}
            lat, lon = ip_attrs.get("lat"), ip_attrs.get("lon")
            if lat is None or lon is None:
                ipinfo = attrs.get("ipinfo", {}).get("data", {}) or {}
                loc = (ipinfo.get("loc") or ",").split(",")
                try:
                    lat = float(loc[0]); lon = float(loc[1])
                except Exception:
                    lat, lon = None, None
            if lat is not None and lon is not None:
                st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
            else:
                st.info("No hay coordenadas disponibles para esta IP.")
        else:
            st.info("El mapa aplica solo a IPs.")

    with tabs[3]:
        st.write("**Detalle VirusTotal**")
        vt = attrs.get("virustotal", {}).get("data") or {}
        if not vt:
            st.info("No hay datos de VirusTotal para este IOC.")
        else:
            stats = (vt.get("last_analysis_stats") or
                     (((vt.get("data") or {}).get("attributes") or {}).get("last_analysis_stats")))
            if stats:
                st.subheader("Estadísticas de análisis")
                st.json(stats)
            if ioc_type_q == "hash":
                st.subheader("Metadatos de fichero")
                meta = {
                    "type_description": vt.get("type_description"),
                    "meaningful_name": vt.get("meaningful_name"),
                    "md5": vt.get("md5"),
                    "sha1": vt.get("sha1"),
                    "sha256": vt.get("sha256"),
                    "size": vt.get("size"),
                }
                st.json(meta)
                eng = vt.get("last_analysis_results") or (((vt.get("data") or {}).get("attributes") or {}).get("last_analysis_results"))
                if isinstance(eng, dict) and eng:
                    rows = [{"engine": e, "category": r.get("category"), "result": r.get("result")} for e, r in eng.items()]
                    df_eng = pd.DataFrame(rows).sort_values(["category","engine"])
                    st.markdown("**Resultados por motor (VT):**")
                    st.dataframe(df_eng, use_container_width=True, height=360)
                else:
                    st.info("Sin resultados detallados de motores para este hash.")

    with tabs[4]:
        export_payload = {
            "ioc_type": ioc_type_q,
            "value": val,
            "summary": {
                "ti_score": ti_score, "country": country if ioc_type_q=="ip" else None,
                "org": org if ioc_type_q=="ip" else None,
                "file_type": file_type if ioc_type_q=="hash" else None,
                "file_size": file_size if ioc_type_q=="hash" else None,
                "last_seen": row["last_seen"].strftime("%Y-%m-%d %H:%M:%S") if row is not None else None,
            },
            "sources": {k: v.get("data") for k, v in attrs.items()},
        }
        json_bytes = json.dumps(export_payload, indent=2).encode("utf-8")
        st.download_button("⬇️ Descargar JSON de la ficha", data=json_bytes,
                           file_name=f"ioc_{ioc_type_q}_{val}.json", mime="application/json")
    st.stop()

# =========================
# Tabla general + gráficos
# =========================
st.markdown("---")
st.subheader("📊 IOCs recientes")

if df.empty:
    st.info("Aún no hay IOCs. Usa el panel lateral para resolver/importar o genera **Modo Demo**.")
else:
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        f_type = st.multiselect("Tipo", options=["ip", "domain", "hash"], default=["ip", "domain", "hash"])
    with c2:
        min_score = st.slider("TI score mínimo", 0, 100, 0, step=5)
    with c3:
        limit = st.number_input("Límite filas", 50, 2000, 500, step=50)

    df_f = df[df["ioc_type"].isin(f_type)]
    df_f = df_f[df_f["ti_score"] >= min_score]
    df_f = df_f.head(limit)

    show_cols = ["ioc_type", "value", "ti_score", "country", "org", "last_seen"]
    st.dataframe(df_f[show_cols], use_container_width=True, height=420)

    col1, col2 = st.columns(2)
    with col1:
        top = df_f.sort_values("ti_score", ascending=False).head(15).copy()
        if not top.empty:
            top["label"] = top["value"].apply(short_label)
            fig = px.bar(
                top,
                x="label",
                y="ti_score",
                color="ioc_type",
                title="Top IOC por TI score",
            )
            fig.update_traces(
                hovertemplate="<b>%{customdata}</b><br>TI score=%{y}<extra></extra>",
                customdata=top["value"]
            )
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        by_country = (
            df_f[df_f["ioc_type"] == "ip"]
            .groupby("country", dropna=True).size().reset_index(name="IPs")
        )
        if not by_country.empty:
            fig2 = px.bar(
                by_country.sort_values("IPs", ascending=False).head(15),
                x="country",
                y="IPs",
                title="IPs por país (snapshot)"
            )
            st.plotly_chart(fig2, use_container_width=True)
