# 🛡️ DDoS Analyzer with Machine Learning & Dashboard

Este proyecto es un **sistema de detección de ataques DDoS** desarrollado en **Python**.  
Integra captura de tráfico en tiempo real, análisis híbrido (reglas + ML), base de datos para eventos, alertas vía Telegram y un dashboard interactivo en **Streamlit**.  

---

## ✨ Características principales

- 📡 **Captura en tiempo real** con [Scapy](https://scapy.net/).  
- 🧠 **Detección híbrida**:  
  - Umbrales configurables (requests/time window).  
  - Modelo de **Isolation Forest** para anomalías.  
- 💾 **Base de datos SQLite** para eventos y blocklist.  
- 📊 **Dashboard interactivo** con [Streamlit](https://streamlit.io/):  
  - KPIs de tráfico y anomalías.  
  - Listado de eventos sospechosos.  
  - Gráficos de evolución temporal.  
  - Bloqueo manual de IPs.  
  - Exportación y programación de reportes.  
- 📲 **Alertas en Telegram** en tiempo real.  
- ⚡ **Script de arranque unificado** (`start-all.ps1`) que inicializa entorno, BD, detector y dashboard.  

---

## 📂 Estructura del proyecto

```

analizer-DDoS/
│── src/
│   ├── main.py          # Núcleo: captura, análisis y alertas
│   ├── capture.py       # Funciones de captura de tráfico
│   ├── db.py            # Gestión SQLite (eventos, blocklist, reportes)
│   ├── ml.py            # ML: Isolation Forest + features
│   ├── config.py        # Configuración vía .env
│── dashboard/
│   ├── app.py           # Dashboard Streamlit
│── models/
│   ├── iforest.joblib   # Modelo ML entrenado
│── data/
│   ├── events.db        # Base de datos local
│── start-all.ps1        # Script para lanzar todo
│── requirements.txt     # Dependencias
│── .env.example         # Ejemplo configuración
│── README.md

````

---

## ⚙️ Instalación y configuración

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/<usuario>/analizer-DDoS.git
   cd analizer-DDoS

2. Crear entorno virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Windows
   source .venv/bin/activate      # Linux/Mac
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables en `.env`:

   ```ini
   MY_IP=192.168.1.34
   REQUEST_THRESHOLD=5
   TIME_WINDOW=5
   BLOCK_TIME=15
   TELEGRAM_TOKEN=xxxxx
   TELEGRAM_CHAT_ID=yyyyy
   ```

---

## ▶️ Uso

### Opción rápida (recomendada)

Ejecutar:

```powershell
.\start-all.ps1
```

Esto inicializa:

* Entorno virtual
* Base de datos `events.db`
* Detector en `src/main.py`
* Dashboard en `http://localhost:8501`

### Opción manual

1. Lanzar el detector:

   ```bash
   python -m src.main
   ```
2. Abrir el dashboard:

   ```bash
   streamlit run dashboard/app.py
   ```

---

## 📊 Dashboard

El panel de control incluye:

* Tabla de eventos en tiempo real.
* Gráficos de tráfico y anomalías.
* Filtro por IP, score ML, fecha.
* Botón de **bloquear IPs**.
* Exportar reportes CSV/PDF.
* Programar reportes automáticos.

---

## 📧 Alertas en Telegram

Cada vez que se detecta una anomalía:

* Se guarda en la BD.
* Se envía un mensaje automático al grupo configurado.

Ejemplo:

```
🚨 ALERTA DDoS 🚨
IP: 8.8.8.8
Score ML: 0.87
Requests: 120 en 5s
```

---

## 🔮 Roadmap

* 🔧 Mejorar calibración ML con datasets reales.
* 📨 Añadir más canales de alerta (Slack, Email).
* 🐳 Dockerizar para despliegue fácil.
* 🌍 Integrar Threat Intelligence (IP reputation).
* ⚔️ Firewall auto-block nativo.

---

## 🤝 Contribuciones

Las PRs y sugerencias son bienvenidas.
Si tienes ideas de mejora, abre un *issue* o un *pull request*.

---

## 📜 Licencia

MIT License – libre para usar, modificar y compartir.

---

## 👨‍💻 Autor

**Josep Roura Fernandez**
Estudiante de Ingeniería de Telecomunicaciones y apasionado por la **ciberseguridad aplicada**.

* [LinkedIn](https://www.linkedin.com/in/josep-roura-fernandez)
* [GitHub](https://github.com/Josep-Roura/)
