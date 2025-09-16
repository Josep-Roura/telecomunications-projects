# Threat Intelligence Dashboard (TID)

Mini SOC portátil para **correlacionar IOCs** (IPs, dominios y hashes) con fuentes OSINT:
- **AbuseIPDB** (reputación IP)
- **Ipinfo** (geo/ASN)
- **VirusTotal** (IP/Domain/File hash)
- **Modo Demo** (sin APIs) para lucir el dashboard en segundos
- **Reportes** HTML/CSV/PDF y **tareas programadas** en Windows

Incluye buscador global, importación CSV, ficha detallada por IOC y gráficas.
> En los gráficos de barras, los nombres largos (p. ej. hashes) se **acortan** para mantener el tamaño; el **hover** muestra el valor completo.

---

## ✨ Demo rápida (sin claves)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Inicializa DB y genera datos de demo
python -m src.main --init-db
python -m src.seed_demo --ips 40 --domains 15 --hashes 12

# Lanza el dashboard
python -m streamlit run dashboard/app.py
````

---

## 📦 Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` con tus claves (no lo subas a Git):

```env
ABUSEIPDB_KEY=YOUR_ABUSEIPDB_API_KEY
IPINFO_TOKEN=YOUR_IPINFO_TOKEN
VT_API_KEY=YOUR_VIRUSTOTAL_API_KEY

TI_CACHE_TTL=86400
ABUSE_MAX_AGE_DAYS=180
DASHBOARD_PASSWORD=
```

> **Recomendado**: añade `data/` y `reports/` a `.gitignore` para no versionar la base de datos ni reportes.

---

## 🧭 Uso

### CLI (resolver IOCs y guardar en DB)

```powershell
python -m src.main --init-db
python -m src.main --ioc-ip 8.8.8.8
python -m src.main --ioc-domain example.com
python -m src.main --ioc-hash 44d88612fea8a8f36de82e1278abb02f
```

### Dashboard

```powershell
python -m streamlit run dashboard/app.py
```

Funciones clave:

* **Buscador global** (IP/Domain/Hash)
* **Importar CSV** (`ioc_type,value`)
* **Modo Demo** (puebla la DB sin APIs)
* **Reportes**: generar ahora (HTML/CSV/PDF) o **programar** en Windows (schtasks)

---

## 📥 CSV de ejemplo

`sample_iocs.csv`

```csv
ioc_type,value
ip,8.8.8.8
ip,1.1.1.1
ip,185.220.101.1
domain,example.com
domain,malware-traffic-analysis.net
hash,44d88612fea8a8f36de82e1278abb02f
```

---

## 🧾 Reportes

Generación manual:

```powershell
python -m src.report --hours 24         # HTML/CSV
python -m src.report_pdf --hours 24     # PDF con KPIs y tabla
```

Programar (desde el dashboard → barra lateral) una **tarea diaria** con `schtasks` (requiere permisos).

---

## 📊 Qué verás en la UI

* **KPIs** y tabla de IOCs recientes (IP/Domain/Hash, score, país/ASN, últimos vistos)
* **Top IOC por TI score** (etiquetas acortadas; hover con valor completo)
* **IPs por país** (barras)
* **Ficha IOC** con pestañas:

  * **Visión general**
  * **Fuentes** (JSON crudo por proveedor)
  * **Mapa** (para IPs si hay coordenadas)
  * **Detalle VirusTotal** (incluye resultados por motor para hashes)
  * **Exportar JSON**

---

## 🧱 Estructura (resumen)

```
threat-intel-dashboard/
├─ dashboard/
│  └─ app.py                # Streamlit UI (modo demo, CSV, reportes, gráficos)
├─ src/
│  ├─ config.py             # Rutas, carga .env
│  ├─ db.py                 # SQLite (ioc, ioc_attrs, etc.)
│  ├─ report.py             # Reporte HTML/CSV
│  ├─ report_pdf.py         # Reporte PDF (logo + KPIs + tabla)
│  ├─ seed_demo.py          # Generador de datos demo (sin APIs)
│  └─ ti/
│     ├─ base.py            # Modelos IOC/TIResult
│     ├─ cache.py           # Caché simple por fuente
│     ├─ resolve.py         # Orquestación de fuentes y TI score
│     ├─ abuseipdb.py       # IP reputation
│     ├─ ipinfo.py          # Geo/ASN
│     └─ virustotal.py      # IP/Domain/File hash
├─ data/                    # (DB) *ignorar en Git*
├─ reports/                 # (salida de reportes) *ignorar en Git*
├─ assets/                  # logo.png (opcional)
├─ .env.example
└─ requirements.txt
```

---

## 🔐 Buenas prácticas

* **No subir** `.env`, `data/` ni `reports/`.
* Limitar llamadas a APIs (TTL de caché).
* Validar IOCs (regex) antes de resolver.
* Añadir **logo** en `assets/logo.png` para branding del PDF/UI.

---

## 🛣️ Roadmap sugerido

* Integrar **Shodan** y **AlienVault OTX**
* **Rate limiting/backoff** por fuente
* **Histórico de score** por IOC (línea temporal)
* **Alertas** por Telegram/Slack (webhooks)
* **ML explicable** (Isolation Forest) y visualización de anomalías
* **Mapa mundial** con heatmap (folium/plotly)

---

## 🧾 Licencia

**MIT** — úsalo y compártelo con atribución.
