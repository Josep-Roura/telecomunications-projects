# Threat Intelligence Dashboard (TID)

Mini SOC portátil para **correlacionar IOCs** (IPs, dominios y hashes) con fuentes OSINT:
- **AbuseIPDB** (reputación IP)
- **Ipinfo** (geo/ASN)
- **VirusTotal** (IP/Domain/File hash)
- **Modo Demo** (sin APIs) para lucir el dashboard en segundos
- **Reportes** HTML/CSV/PDF y **tareas programadas** en Windows

Incluye buscador global, importación CSV, ficha detallada por IOC y gráficas “WOW”.
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
