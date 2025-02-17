import scapy.all as scapy
from scapy.all import ARP, Ether, srp
import ping3
import prettytable
import requests
import ipaddress
import netifaces

def get_ip_local():
    """
    Obtiene la IP local y la máscara de subred del dispositivo actual,
    y calcula la red en formato CIDR (Ej: 192.168.1.0/24).
    
    Retorna:
        str: Red en formato CIDR o None si falla.
    """
    try:
        gateways = netifaces.gateways().get('default', {})
        if not gateways or netifaces.AF_INET not in gateways:
            raise ValueError("No se pudo detectar la interfaz de red.")

        interfaz = gateways[netifaces.AF_INET][1]
        ip_info = netifaces.ifaddresses(interfaz).get(netifaces.AF_INET, [{}])[0]
        ip, mascara = ip_info.get('addr'), ip_info.get('netmask')

        if not ip or not mascara:
            raise ValueError("No se pudo obtener la IP o la máscara de subred.")

        return str(ipaddress.IPv4Network(f"{ip}/{mascara}", strict=False))
    
    except Exception as e:
        print(f"Error detectado en la red: {e}")
        return None


def arp_scan(ipNet):
    """
    Realiza un escaneo ARP en la red especificada para detectar dispositivos conectados.
    
    Parámetros:
        ipNet (str): Red en formato CIDR donde se realizará el escaneo.
    """
    print(f"🔍 Escaneando la red {ipNet}...")

    solicitud = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ipNet)
    respuesta, _ = srp(solicitud, timeout=2, verbose=False)
    
    dispositivos = []
    mac_cache = {}  # Cache para evitar múltiples solicitudes a la API de MAC

    for _, recibido in respuesta: 
        mac = recibido.hwsrc
        if mac not in mac_cache:
            mac_cache[mac] = obtener_proveedor_MAC(mac)
        
        dispositivos.append({
            "ip": recibido.psrc,
            "mac": mac,
            "proveedor": mac_cache[mac],
            "latencia": ping_address(recibido.psrc)
        })

    if dispositivos:
        table = prettytable.PrettyTable()
        table.field_names = ["IP", "MAC", "Proveedor", "Latencia"]
        for dispositivo in dispositivos:
            table.add_row([dispositivo['ip'], dispositivo['mac'], dispositivo['proveedor'], dispositivo['latencia']])
        
        print("\n📡 Dispositivos encontrados en la red:")
        print(table)
    else:
        print("No se encontraron dispositivos en la red.")


def obtener_proveedor_MAC(mac):
    """
    Consulta la API de macvendors.com para obtener el fabricante de un dispositivo.
    
    Parámetros:
        mac (str): Dirección MAC del dispositivo.
    
    Retorna:
        str: Nombre del fabricante o "Desconocido" si no se encuentra información.
    """
    try:
        response = requests.get(f'https://api.macvendors.com/{mac}', timeout=3)
        return response.text if response.status_code == 200 else "Desconocido"
    except requests.RequestException:
        return "Desconocido"


def ping_address(ip):
    """
    Mide la latencia de respuesta de un dispositivo en la red.
    
    Parámetros:
        ip (str): Dirección IP del dispositivo.
    
    Retorna:
        int: Latencia en milisegundos, o "No responde" si no hay respuesta.
    """
    latencia = ping3.ping(ip, timeout=2, unit="ms")
    return round(latencia * 1000) if latencia is not None else "No responde"


if __name__ == "__main__":
    ip_address = get_ip_local()

    if ip_address:
        try:
            IPv4_IP = ipaddress.IPv4Network(ip_address)
            arp_scan(ip_address)
        except ValueError:
            print("No es correcta la IP")
    else:
        print("No se pudo obtener la red local.")
