from scan_net import * 
from scan_ports import *

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