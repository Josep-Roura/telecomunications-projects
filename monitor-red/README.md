# Real-Time Network Monitor with Python

This project is a tool for monitoring the local network in real-time using Python. It allows you to scan the network to identify connected devices, gather information about them, and measure their response latency.

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
Scanning network 172.20.10.0/28...
Devices found in the network: 172.20.10.0/28
+-------------+-------------------+-----------------+----------+
|      IP     |         MAC       |     Vendor      | Latency  |
+-------------+-------------------+-----------------+----------+
| 172.20.10.2 | 0F:7F:7B:57:37:C5 | Intel Corporate |   472 ms |
| 172.20.10.1 | 1F:CD:53:F4:DE:A7 |    Unknown      |   783 ms |
+-------------+-------------------+-----------------+----------+
```

