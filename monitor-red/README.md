# Monitor de Red en Tiempo Real con Python

# Monitor de Red en Tiempo Real con Python

Este proyecto es una herramienta para monitorear la red local en tiempo real utilizando Python. Permite escanear la red para identificar dispositivos conectados, obtener información sobre ellos y medir la latencia de respuesta.

## Requisitos

- Python 3.x
- Bibliotecas de Python:
    - scapy
    - ping3
    - prettytable
    - requests
    - netifaces

Puedes instalar las bibliotecas necesarias utilizando pip:

```sh
pip install scapy ping3 prettytable requests netifaces
```

## Uso

El script realiza las siguientes funciones:

1. Obtiene la dirección IP local y la máscara de subred.
2. Realiza un escaneo ARP para identificar dispositivos en la red.
3. Obtiene el proveedor del dispositivo a partir de su dirección MAC.
4. Mide la latencia de respuesta de cada dispositivo.

### Ejecución

Para ejecutar el script, simplemente corre el archivo Python:

```sh
python src/main.py
```

### Resultado Ejemplo

```
Escaneando la red 172.20.10.0/28...
Dispositivos encontrados en la red: 172.20.10.0/28
+-------------+-------------------+-----------------+----------+
|      IP     |         MAC       |    Proveedor    | Latencia |
+-------------+-------------------+-----------------+----------+
| 172.20.10.2 | 0F:7F:7B:57:37:C5 | Intel Corporate |   472 ms |
| 172.20.10.1 | 1F:CD:53:F4:DE:A7 |   Desconocido   |   783 ms |
+-------------+-------------------+-----------------+----------+
```

# Net Monitor in real time with python

This project is a tool for monitoring the local network in real-time using Python. It allows you to scan the network to identify connected devices, obtain information about them, and measure their response latency.

## Requirements

- Python 3.x
- Python libraries:
    - scapy
    - ping3
    - prettytable
    - requests
    - netifaces

You can install the required libraries using pip:

```sh
pip install scapy ping3 prettytable requests netifaces
```

## Usage

The script performs the following functions:

1. Obtains the local IP address and subnet mask.
2. Performs an ARP scan to identify devices on the network.
3. Retrieves the device vendor from its MAC address.
4. Measures the response latency of each device.

### Execution

To run the script, simply execute the Python file:

```sh
python src/main.py
```

### Example Output

```
Escaneando la red 172.20.10.0/28...
Dispositivos encontrados en la red: 172.20.10.0/28
+-------------+-------------------+-----------------+----------+
|      IP     |         MAC       |    Proveedor    | Latencia |
+-------------+-------------------+-----------------+----------+
| 172.20.10.2 | 0F:7F:7B:57:37:C5 | Intel Corporate |   472 ms |
| 172.20.10.1 | 1F:CD:53:F4:DE:A7 |   Desconocido   |   783 ms |
+-------------+-------------------+-----------------+----------+
```