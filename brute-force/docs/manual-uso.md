# Email Password Brute Force Script

This script attempts to brute force an email account's password using a dictionary attack. It reads passwords from a specified file and tries each one until it finds the correct password or exhausts the list.

## Requirements

- Python 3.x
- `smtplib` module (included in Python standard library)
- A dictionary file containing potential passwords, one per line

## Configuration

The script is configured to use Gmail's SMTP server. You can change the SMTP server and port by modifying the `SMTP_SERVER` and `SMTP_PORT` variables.
