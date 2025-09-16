from datetime import datetime
from pathlib import Path

class AlertStorage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_alert(self, text: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} | {text}"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return line
