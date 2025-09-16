"""
src/report.py
Genera reportes (HTML y CSV) de los IOCs en la base de datos.
"""

import sqlite3
import pandas as pd
import argparse
import json
from datetime import datetime
from pathlib import Path

from src.config import DB_PATH, REPORTS_DIR


def load_data(hours: int = 24) -> pd.DataFrame:
    """Carga IOCs de las últimas X horas desde la base de datos."""
    con = sqlite3.connect(str(DB_PATH))
    try:
        query = """
        SELECT ioc_type, value, ti_score, first_seen, last_seen
        FROM ioc
        WHERE last_seen >= datetime('now', ?)
        ORDER BY last_seen DESC;
        """
        df = pd.read_sql_query(query, con, params=(f"-{hours} hours",))
    finally:
        con.close()

    if not df.empty:
        df["first_seen"] = pd.to_datetime(df["first_seen"])
        df["last_seen"] = pd.to_datetime(df["last_seen"])
    return df


def generate_report(hours: int = 24):
    """Genera CSV y HTML a partir de los datos de la DB."""
    df = load_data(hours)

    # Crear carpeta de salida
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = REPORTS_DIR / f"report_{ts}.csv"
    html_path = REPORTS_DIR / f"report_{ts}.html"

    if df.empty:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<h2>No hay IOCs registrados en el periodo seleccionado.</h2>")
        df.to_csv(csv_path, index=False)
    else:
        df.to_csv(csv_path, index=False)

        html_table = df.to_html(index=False, classes="table table-striped")
        html_doc = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Threat Intel Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                th {{ background: #f4f4f4; }}
            </style>
        </head>
        <body>
            <h1>Threat Intelligence Report</h1>
            <p>Periodo analizado: últimas {hours} horas</p>
            {html_table}
        </body>
        </html>
        """
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    return {"csv": str(csv_path), "html": str(html_path)}


def main():
    parser = argparse.ArgumentParser(description="Generador de reportes de IOCs")
    parser.add_argument("--hours", type=int, default=24, help="Periodo en horas (default=24)")
    args = parser.parse_args()

    paths = generate_report(args.hours)
    print(json.dumps(paths))  # Para integrarlo en la dashboard


if __name__ == "__main__":
    main()
