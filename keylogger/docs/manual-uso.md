# 📖 User Manual - Keylogger with Email Sending

This manual explains how to install, configure, and run the Python keylogger, which records keystrokes and sends a log file to a configured email address.

## 📌 **Prerequisites**
- Python 3 installed on your system.
- A Gmail account for sending emails.
- Access to your Google account security settings to generate an application-specific password.

---

## 🚀 **Installation**
### 1️⃣ Clone the repository
```sh
git clone https://github.com/Josep-Roura/telecomunications-projects.git
cd your_repository
```

### 2️⃣ Install dependencies
Run the following command to install `pynput`:
```sh
pip install pynput
```

---

## ⚙️ **Email Configuration**
To allow the keylogger to send emails, you need to configure Gmail credentials.

### 1️⃣ **Generate an application password in Gmail**
1. Go to [Google Security](https://myaccount.google.com/security).
2. Enable two-step verification (if not already enabled).
3. In the "App Passwords" section, generate a new password and save it.

### 2️⃣ **Configure `main.py`**
Open the file and modify these lines with your information:
```python
EMAIL_SENDER = 'your_email@gmail.com'  # Replace with your email address
EMAIL_RECEIVER = 'destination_email@gmail.com'  # Replace with the recipient email address
EMAIL_PASSWORD = 'YOUR_APPLICATION_PASSWORD'  # Replace with your application password
```

---

## ▶️ **Run the Keylogger**
Once configured, run the script with:
```sh
python main.py
```

The keylogger will run in the background, recording pressed keys. Every 20 keystrokes, it will send the `log.txt` file to the configured email address.

---

## ⚠️ **Legal Warning**
This software should be used **only for educational and security purposes**. **Do not use it on systems without consent**, as it may violate privacy and cybersecurity laws.

---
📌 **Author:** Josep Roura Fernandez
📧 **Contact:** joseprouraf@gmail.com

