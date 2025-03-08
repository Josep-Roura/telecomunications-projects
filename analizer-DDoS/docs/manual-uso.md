# User Manual - DDoS Attack Detection System

This guide will help you configure, run, and use the **DDoS Attack Detection System** effectively.

---

## 📋 Table of Contents
- [1. Overview](#overview)
- [2. Installation](#installation)
- [3. Configuration](#configuration)
- [4. Running the System](#running-the-system)
- [5. Understanding the Output](#understanding-the-output)
- [6. Troubleshooting](#troubleshooting)
- [7. FAQs](#faqs)

---

## 🔎 1. Overview
The DDoS Attack Detection System is designed to:
- Monitor network traffic in real-time.
- Identify IP addresses that exceed the configured request threshold.
- Send alerts to a Telegram group for immediate notification.
- Log alerts in a `.txt` file for record-keeping.

This system is intended for educational and security monitoring purposes only.

---

## ⚙️ 2. Installation

### Step 1: Install Python 3
Ensure you have **Python 3.x** installed on your system. You can download it from [here](https://www.python.org/downloads/).

### Step 2: Install Dependencies
Run the following command in your terminal to install the required libraries:
```bash
pip install scapy requests
```

---

## 🛠️ 3. Configuration

### Step 1: Telegram Bot Setup
1. Open **Telegram** and search for `@BotFather`.
2. Use the command `/newbot` and follow the instructions to create a new bot.
3. Save the **bot token** provided.
4. Add the bot to your Telegram group and send any message in the group.
5. Use this URL to obtain your **group ID**:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
6. Copy the **group ID** from the JSON response.

### Step 2: System Configuration
In the `main.py` file, modify the following values:

```python
# Configuration
MY_IP = "<YOUR_LOCAL_IP>"       # Your local IP address
REQUEST_THRESHOLD = 5            # Max requests allowed within the time window
TIME_WINDOW = 5                  # Time window (in seconds) for request analysis
BLOCK_TIME = 15                  # Block duration for repeated alerts

# Telegram Configuration
TOKEN = "<YOUR_BOT_TOKEN>"
CHAT_ID = "<YOUR_GROUP_ID>"
```

**Note:** Your IP address can be found using the `ipconfig` (Windows) or `ifconfig` (Linux/Mac) command.

---

## ▶️ 4. Running the System

### Step 1: Navigate to the Project Directory
Use the terminal to go to the project folder:
```bash
cd <path_to_project>/src
```

### Step 2: Run the Detection System
Run the following command:
```bash
python main.py
```

### Step 3: Monitor Alerts
- Alerts will be displayed in the terminal.
- Alerts will be sent to your Telegram group.
- Alerts will be saved in `alerts.txt` for reference.

---

## 📋 5. Understanding the Output

### Terminal Output Example
```
Incoming Traffic - Source IP: 192.168.1.20 --> Destination IP: 192.168.1.34 ; Time: 2025-03-08 13:34:22
ALERT: The IP 192.168.1.20 has sent 8 requests in the last 5 seconds.
```

### Telegram Alert Example
```
ALERT: The IP 192.168.1.20 has sent 8 requests in the last 5 seconds.
```

### Log File Output (`alerts.txt`)
```
ALERT: The IP 192.168.1.20 has sent 8 requests in the last 5 seconds.
ALERT: The IP 10.0.0.5 has sent 10 requests in the last 5 seconds.
```

---

## 🐞 6. Troubleshooting

### Problem: The script doesn't detect any traffic.
✅ Ensure you are connected to the correct network.  
✅ Verify that your IP address in `MY_IP` is correct.  
✅ Try running the script with **Administrator privileges**.  

### Problem: No alerts are sent to Telegram.
✅ Check that the **bot token** and **group ID** are correctly configured.  
✅ Ensure your bot has been added to the Telegram group and has permission to send messages.  

### Problem: The log file (`alerts.txt`) remains empty.
✅ Ensure the file path is correct.  
✅ Verify that the script is not constantly overwriting the file.  
✅ Add `file.flush()` in the `write_alert()` function if delays occur.

---

## ❓ 7. FAQs

**Q: Can this system detect outgoing DDoS attacks from my network?**  
A: No, this system is designed to monitor **incoming traffic only** to detect possible DDoS attacks targeting your IP address.

**Q: Can I adjust the request threshold or block time?**  
A: Yes, modify the values in the `main.py` configuration section to suit your network environment.

**Q: What happens if an IP keeps sending requests after being blocked?**  
A: The IP will remain blocked until the block timer expires. You can adjust the `BLOCK_TIME` value for longer or shorter delays.

**Q: Does the system require Administrator or Root permissions?**  
A: Yes, in some environments `Scapy` may require elevated permissions to access network interfaces correctly.

---

## 📧 Support
If you encounter issues or have questions, feel free to reach out through the project repository or contact me directly.

**Author:** Josep Roura Fernandez  
**Email:** joseprouraf@gmail.com