from scapy.all import sniff
from datetime import datetime, timedelta
import requests
import os

# Traffic log dictionaries
traffic_log = {}
blocked_ips = {}  # Temporarily blocked IPs to avoid repeated alerts

# Configuration
MY_IP = "0.0.0.0"
REQUEST_THRESHOLD = 5      # Number of requests allowed within the time window
TIME_WINDOW = 5            # Time window (in seconds) for analyzing traffic
BLOCK_TIME = 15            # Time (in seconds) for blocking IPs after sending an alert

# Telegram Configuration (MODIFY)
TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

# Function to send alerts to Telegram
def send_telegram_alert(message):
    """
    Sends an alert message to a Telegram group using the provided bot token and chat ID.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    
    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            print("Alert successfully sent to Telegram.")
        else:
            print(f"Error sending alert to Telegram: {response.text}")
    except Exception as e:
        print(f"Failed to connect to Telegram: {e}")

# Function to write alerts to a log file
def write_alert(alert):
    """
    Writes alert messages to a log file.
    Ensures data is immediately written by flushing the file buffer.
    """
    try:
        with open("./alerts.txt", "a", encoding="utf-8") as file:
            file.write(alert + "\n")
            file.flush()  # Ensures data is written immediately
    except Exception as e:
        print(f"Failed to write alert to file: {e}")

# Callback function for packet analysis
def packet_callback(packet):
    """
    Analyzes incoming network packets. 
    Tracks request timestamps and triggers alerts if suspicious activity is detected.
    """
    if packet.haslayer("IP"):
        ip_src = packet["IP"].src
        ip_dst = packet["IP"].dst
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Only analyze incoming traffic directed to our IP (excluding outgoing requests)
        if ip_dst == MY_IP and ip_src != MY_IP:
            print(f"Incoming Traffic - Source IP: {ip_src} --> Destination IP: {ip_dst} ; Time: {timestamp}")
            
            if ip_src not in traffic_log:
                traffic_log[ip_src] = []
            
            traffic_log[ip_src].append(timestamp)

    # Clean outdated requests from the log
    now = datetime.now()
    for ip in list(traffic_log.keys()):
        traffic_log[ip] = [
            t for t in traffic_log[ip]
            if now - datetime.strptime(t, "%Y-%m-%d %H:%M:%S") <= timedelta(seconds=TIME_WINDOW)
        ]
        if not traffic_log[ip]:
            del traffic_log[ip]

    # Detection of suspicious IPs with temporary blocking system
    for ip, requests in traffic_log.items():
        if len(requests) > REQUEST_THRESHOLD:

            # Block IP temporarily to avoid repeated alerts
            if ip not in blocked_ips or now - blocked_ips[ip] > timedelta(seconds=BLOCK_TIME):
                alert_msg = f"ALERT: The IP {ip} has sent {len(requests)} requests in the last {TIME_WINDOW} seconds."
                print(alert_msg)
                send_telegram_alert(alert_msg)
                write_alert(alert_msg)

                # Mark IP as blocked for the specified block time
                blocked_ips[ip] = now

if __name__ == "__main__":
    write_alert("System initialized - DDoS Attack Detection Started")
    print("Monitoring network traffic for potential DDoS attacks...")
    sniff(filter="ip", prn=packet_callback, store=0)
