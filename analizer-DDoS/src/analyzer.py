from collections import defaultdict, deque
from datetime import datetime, timedelta
from .config import settings

class TrafficAnalyzer:
    """
    Mantiene una ventana deslizante de timestamps por IP origen.
    Detecta IPs que superan el umbral en la ventana.
    Implementa bloqueo temporal para evitar alertas repetidas.
    """
    def __init__(self, request_threshold: int = None, time_window: int = None, block_time: int = None):
        self.req_th = request_threshold or settings.REQUEST_THRESHOLD
        self.window_s = time_window or settings.TIME_WINDOW
        self.block_s = block_time or settings.BLOCK_TIME

        self.traffic = defaultdict(lambda: deque())   # ip -> deque[timestamps]
        self.blocked = {}                              # ip -> last_block_time

    def _now(self):
        return datetime.now()

    def register(self, ip_src: str, ip_dst: str, my_ip: str) -> list[str]:
        """
        Registra un paquete entrante y devuelve lista de mensajes de alerta a emitir (si procede).
        """
        alerts = []
        ts = self._now()

        # Solo tráfico entrante hacia mi IP
        if ip_dst == my_ip and ip_src != my_ip:
            dq = self.traffic[ip_src]
            dq.append(ts)

            # limpia ventana
            limit = ts - timedelta(seconds=self.window_s)
            while dq and dq[0] < limit:
                dq.popleft()

            # ¿supera umbral?
            if len(dq) > self.req_th:
                last_block = self.blocked.get(ip_src)
                if not last_block or (ts - last_block) > timedelta(seconds=self.block_s):
                    msg = f"ALERT: The IP {ip_src} has sent {len(dq)} requests in the last {self.window_s} seconds."
                    alerts.append(msg)
                    self.blocked[ip_src] = ts

        # Garbage collect IPs sin eventos
        stale = [ip for ip, dq in self.traffic.items() if not dq]
        for ip in stale:
            del self.traffic[ip]

        return alerts
