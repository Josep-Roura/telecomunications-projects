# src/response.py
import platform
import subprocess

def block_ip_windows(ip: str, rule_name_prefix: str = "DDOS-Block") -> bool:
    """
    Crea una regla de firewall en Windows para bloquear la IP de entrada (dir=in).
    Ejecutar como Administrador.
    """
    if platform.system().lower() != "windows":
        return False
    rule = f"{rule_name_prefix}-{ip}"
    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={rule}", "dir=in", "action=block", f"remoteip={ip}"
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except Exception:
        return False

def unblock_ip_windows(ip: str, rule_name_prefix: str = "DDOS-Block") -> bool:
    """
    Elimina la regla de firewall creada previamente.
    """
    if platform.system().lower() != "windows":
        return False
    rule = f"{rule_name_prefix}-{ip}"
    cmd = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule}"]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except Exception:
        return False
