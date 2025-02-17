import scapy.all as scapy
from scapy.all import ARP, Ether, srp
import ping3
import prettytable
import requests
import ipaddress
import netifaces


def get_ip_local():
    try:
        # Obtain Local IP Address
        interfaz = netifaces.gateways()['default'][netifaces.AF_INET][1]  # Interfaz activa

        ip_info = netifaces.ifaddresses(interfaz)[netifaces.AF_INET][0]  # Info de IP

        ip = ip_info['addr']  # IP local

        mascara = ip_info['netmask']  # Máscara de subred

        # Convertimos IP + Máscara en una red (Ej: 192.168.1.0/24)
        red = ipaddress.IPv4Network(f"{ip}/{mascara}", strict=False)

        return str(red)
    
    except Exception as e:
        print(f"Error detectado en la re {e}")

def arp_scan(ipNet):
    print(f"Escaneando la red {ipNet}...")
    solicitud = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ipNet) # Creamos un paquete al ARP destinacion broadcast

    respuesta, _ = srp(solicitud, timeout=2, verbose=False) # Con srp enviamos el paquete y recojemos la respuesta
    
    dispositivos = []

    for enviado, recibido in respuesta: 
        dispositivos.append({
            "ip": recibido.psrc, 
            "mac": recibido.hwsrc,
            "proveedor": obtener_proveedor_MAC(recibido.hwsrc),
            "latencia": ping_address(recibido.psrc)
            })

    # Mostrar resultados
    if dispositivos:
        table = prettytable.PrettyTable()
        table.field_names = ["IP", " MAC", "Proveedor", "Latencia"]
        for dispositivo in dispositivos:
            table.add_row([dispositivo['ip'], dispositivo['mac'], dispositivo['proveedor'], dispositivo['latencia']])
        print(f"Dispositivos encontrados en la red: {ipNet}")
        print(table)
        
    else:
        print("No se encontraron dispositivos en la red.")


def obtener_proveedor_MAC(mac):
    try:
        vendor = requests.get(url=f'https://api.macvendors.com/{mac}', timeout=3)

        if vendor.status_code == 200:
            return vendor.text
        else:
            return "Desconocido"
        
    except requests.RequestException:
        return "Desconocido"

    
def ping_address(ip):
    latencia = ping3.ping(ip, timeout=2, unit="ms")
    if latencia is not None:
        return round(latencia * 1000)
    else:
        return "No responde"


ip_address = get_ip_local()

try:
    IPv4_IP = ipaddress.IPv4Network(ip_address)
    arp_scan(ip_address)    

except ValueError:
    print("No es correcta la IP")
