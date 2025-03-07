# Keylogger with Email Sending

This project is a Python keylogger that records user keystrokes and saves them in a `text.txt` file. Every 20 keystrokes, the file is automatically sent via email to the configured recipient.

## 📌 Features
- Captures pressed keys and stores them in `text.txt`.
- Detects special keys (`Enter`, `Shift`, `Ctrl`, etc.) and logs them correctly.
- Automatically sends the log file via email every 20 keystrokes.
- Uses `pynput` for keyboard input capture.
- Utilizes `smtplib` for sending emails via Gmail.

## 🚀 Installation
### 1. Clone the Repository
```sh
git clone https://github.com/Josep-Roura/telecomunications-projects.git
cd your_repository
```

### 2. Install Dependencies
Ensure you have Python 3 installed and run:
```sh
pip install pynput
```

## 📧 Email Configuration
To send emails using Gmail:
1. **Enable two-step verification** on your Google account.
2. **Generate an application-specific password** at [Google Security](https://myaccount.google.com/security).
3. **Replace your password in the script** with the generated application password.

Modify this line in `main.py`:
```python
sesion_smtp.login('your_email@gmail.com', 'YOUR_APPLICATION_PASSWORD')
```

⚠ **Do not use your real Gmail password in the code.**

## 🛠️ Usage
Run the script with:
```sh
python main.py
```
The keylogger will start recording keystrokes, and every 20 keystrokes, it will send the `text.txt` file to your email.

## ⚠️ Legal Warning
This software is intended **only for educational purposes and security testing**. **Do not use it on systems without explicit consent**, as it may violate privacy and cybersecurity laws.

---
**Author:** Josep Roura
📧 Contact: joseprouraf@gmail.com

