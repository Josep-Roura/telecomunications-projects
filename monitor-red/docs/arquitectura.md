# Arquitectura del Proyecto: Monitor de Red en Tiempo Real con Python

Este documento describe la arquitectura del proyecto "Monitor de Red en Tiempo Real con Python". El objetivo de este proyecto es escanear la red local para identificar dispositivos conectados, obtener información sobre ellos y medir la latencia de respuesta.

## Estructura del Código

El código se compone de varias funciones clave:

### 1. Obtener IP Local

Esta función obtiene la dirección IP local y la máscara de subred de la interfaz de red activa. Luego, convierte esta información en una red IPv4.

### 2. Escaneo ARP

Esta función realiza un escaneo ARP en la red especificada para identificar dispositivos conectados. Utiliza la librería `scapy` para enviar paquetes ARP y recibir respuestas.

### 3. Obtener Proveedor de MAC

Esta función consulta una API externa para obtener el proveedor del dispositivo basado en su dirección MAC.

### 4. Medir Latencia

Esta función mide la latencia de respuesta de un dispositivo en la red utilizando la librería `ping3`.

### Ejecución del Código

El código principal obtiene la red local y realiza el escaneo ARP.

## Dependencias

El proyecto utiliza las siguientes librerías:

- `scapy`
- `ping3`
- `prettytable`
- `requests`
- `ipaddress`
- `netifaces`

## Conclusión

Este proyecto proporciona una herramienta útil para monitorear la red local en tiempo real, identificando dispositivos conectados y midiendo su latencia de respuesta.
