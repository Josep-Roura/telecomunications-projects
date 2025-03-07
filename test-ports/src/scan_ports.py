import nmap

def scan_with_nmap(ip):
    nm = nmap.PortScanner()
    print(f"🔍 Escaneando {ip} con Nmap...\n")
    nm.scan(ip, '1-1024')  # Escanea puertos del 1 al 1024

    for host in nm.all_hosts():
        print(f"📡 Resultados para {host}:")
        for proto in nm[host].all_protocols():
            print(f"  Protocolo: {proto}")
            ports = nm[host][proto].keys()
            for port in sorted(ports):
                state = nm[host][proto][port]['state']
                print(f"  ⚡ Puerto {port}: {state}")

# Escanear una IP dentro de la red local
# scan_with_nmap(target_ip)
