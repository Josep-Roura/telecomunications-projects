from scapy.all import sniff, conf

def list_interfaces():
    """
    Devuelve las interfaces de red disponibles.
    Útil para depurar en qué interfaz está escuchando Scapy.
    """
    try:
        return conf.ifaces.data
    except Exception:
        return {}

def start_capture(callback, iface: str | None = None):
    """
    callback(packet_dict: {"ip_src": str, "ip_dst": str})
    iface: nombre de interfaz (e.g., "Wi-Fi", "Ethernet", "wlan0").
           Si None, Scapy elige automáticamente.
    """
    def _scapy_cb(pkt):
        if pkt.haslayer("IP"):
            try:
                callback({"ip_src": pkt["IP"].src, "ip_dst": pkt["IP"].dst})
            except Exception:
                pass

    # quitamos filter="ip" para evitar problemas en Windows
    sniff(prn=_scapy_cb, store=0, iface=iface)
