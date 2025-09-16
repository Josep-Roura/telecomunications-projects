from pathlib import Path
from datetime import datetime

HEADER = "timestamp,ip,count,time_window,level,lat,lon,country,org\n"

class CSVEnrichedStorage:
    def __init__(self, path: str = "./data/events_enriched.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if (not self.path.exists()) or (self.path.stat().st_size == 0):
            self.path.write_text(HEADER, encoding="utf-8")
        else:
            try:
                first = self.path.open("r", encoding="utf-8").readline().strip().lower()
                if not first.startswith("timestamp,ip,count,time_window,level,lat,lon,country,org"):
                    content = self.path.read_text(encoding="utf-8")
                    self.path.write_text(HEADER + content, encoding="utf-8")
            except Exception:
                self.path.write_text(HEADER, encoding="utf-8")

    def write(self, ip: str, count: int, time_window: int, level: str,
              lat, lon, country, org):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Normaliza None → vacío
        lat = "" if lat is None else lat
        lon = "" if lon is None else lon
        country = "" if country is None else str(country).replace(",", " ")
        org = "" if org is None else str(org).replace(",", " ")
        line = f"{ts},{ip},{count},{time_window},{level},{lat},{lon},{country},{org}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
        return line
