from pathlib import Path
from datetime import datetime

# Definimos la cabecera que debe tener el CSV
HEADER = "timestamp,ip,count,time_window,level\n"

class CSVStorage:
    def __init__(self, path: str):
        """
        Inicializa el almacenamiento en CSV.
        Si el archivo no existe o está vacío, se crea con la cabecera.
        Si existe pero no tiene la cabecera correcta, se corrige.
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if (not self.path.exists()) or (self.path.stat().st_size == 0):
            # Si el archivo no existe o está vacío, creamos con cabecera
            self.path.write_text(HEADER, encoding="utf-8")
        else:
            try:
                # Leer primera línea para verificar cabecera
                first = self.path.open("r", encoding="utf-8").readline()
                if not first.strip().lower().startswith("timestamp,ip,count,time_window,level"):
                    # Si la cabecera no es correcta, reescribir con la cabecera arriba
                    content = self.path.read_text(encoding="utf-8")
                    self.path.write_text(HEADER + content, encoding="utf-8")
            except Exception:
                # Si algo falla, recrear con cabecera
                self.path.write_text(HEADER, encoding="utf-8")

    def write_event(self, ip: str, count: int, time_window: int, level: str = "SUSPICIOUS"):
        """
        Escribe un evento de detección en el CSV.
        Cada línea contiene: timestamp, ip, count, time_window, level
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts},{ip},{count},{time_window},{level}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
        return line
