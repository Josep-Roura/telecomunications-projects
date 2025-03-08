# DDoS Attack Detection System

This project is a **DDoS Attack Detection System** developed in **Python** using **Scapy** for network traffic monitoring. The system identifies potential DDoS attacks by analyzing incoming network traffic, detecting IPs that exceed a predefined request threshold, and sending alerts via **Telegram**. Additionally, all alerts are logged in a `.txt` file for reference.

---

## 🚀 Features

✅ Real-time network traffic monitoring.  
✅ Detects IP addresses exceeding the request threshold.  
✅ Sends alerts to a Telegram group.  
✅ Logs all alerts in a `.txt` file for later analysis.  
✅ Implements a **temporary IP blocking system** to prevent repeated alerts.  

---

## 🛠️ Requirements

Before running the project, ensure you have the following dependencies installed:

- **Python 3.x**
- **Scapy**
- **Requests**

### Install Dependencies
```
pip install scapy requests
```

---

## 📂 Project Structure
```
├── src
│   ├── main.py           # Main detection script
│   ├── alerts.txt        # Log file for alert messages
├── docs
│   ├── manual-user.md    # User manual documentation
├── README.md             # Project documentation
```

---

## ⚙️ Configuration

### 1. Telegram Bot Configuration
1. Go to **Telegram** and search for `@BotFather`.
2. Use the command `/newbot` to create a new bot.
3. Follow the steps to obtain your **bot token**.
4. Add your bot to a Telegram group and send any message in the group.
5. Visit this URL to obtain the **group ID**:  
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
6. Note down the **bot token** and **group ID** for the next step.

### 2. System Configuration
In the `main.py` file, modify the following values:

```python
# Configuration
MY_IP = "192.168.1.34"    # Your local IP address
REQUEST_THRESHOLD = 5      # Number of requests allowed in the time window
TIME_WINDOW = 5            # Time window (in seconds) for analyzing traffic
BLOCK_TIME = 15            # Time (in seconds) to block an IP after an alert

# Telegram Configuration
TOKEN = "<YOUR_BOT_TOKEN>"
CHAT_ID = "<YOUR_GROUP_ID>"
```

---

## ▶️ How to Run

1. Clone this repository:
```
git clone <repository_link>
cd <project_folder>
```

2. Run the detection system:
```
python src/main.py
```

3. The terminal will display network activity, and alerts will be sent to your Telegram group if suspicious activity is detected.

---

## 📄 Log File (`alerts.txt`)
Each detected attack will be logged in `alerts.txt` with the following format:
```
ALERT: The IP 192.168.0.10 has sent 6 requests in the last 5 seconds.
ALERT: The IP 10.0.0.5 has sent 8 requests in the last 5 seconds.
```

---

## 🚨 Important Notes

- The system only monitors incoming traffic directed to your IP address.
- Ensure your Python environment has the necessary permissions to run `Scapy` and access network interfaces.
- Running the system as **Administrator** or **Root** may be required for full functionality.

---

## 📈 Future Improvements

🔹 Implement log file rotation to manage large volumes of alerts.  
🔹 Add email alert integration for additional security notifications.  
🔹 Improve IP filtering and threat intelligence integration for smarter detection.

---

## 🤝 Contributing
Contributions are welcome! Feel free to submit issues, feature requests, or pull requests to improve the system.

---

## 📧 Contact
If you have any questions or suggestions, feel free to reach out. I'm open to feedback and collaboration!

