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

```
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

```
python src/main.py
```

### Resultado Ejemplo
'''
Escaneando la red 172.20.10.0/28...
Dispositivos encontrados en la red: 172.20.10.0/28
+-------------+-------------------+-----------------+----------+
|      IP     |         MAC       |    Proveedor    | Latencia |
+-------------+-------------------+-----------------+----------+
| 172.20.10.2 | 0F:7F:7B:57:37:C5 | Intel Corporate |   472    |
| 172.20.10.1 | 1F:CD:53:F4:DE:A7 |   Desconocido   |   783    |
+-------------+-------------------+-----------------+----------+
'''