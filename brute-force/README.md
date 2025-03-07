# Brute Force Email Password Finder

This project attempts to find the correct password for an email account using a brute force method. It reads passwords from a dictionary file and tries each one until it finds the correct password.

## Requirements

- Python 3.x
- `smtplib` library (included in Python standard library)
- A dictionary file containing possible passwords

## Usage

1. Clone the repository or download the script.
2. Ensure you have a dictionary file with possible passwords.
3. Run the script:

```bash
python brute_force_email.py
```

4. Enter the email address and the path to the dictionary file when prompted.

## Code Explanation

The script uses the `smtplib` library to connect to an SMTP server and attempt to log in using each password from the dictionary file. It stops when the correct password is found or the dictionary is exhausted.

### Key Parts of the Code

- **SMTP Server Configuration**: Sets the SMTP server and port.
- **File Handling**: Converts the relative path to an absolute path and checks if the file exists.
- **Password Testing Loop**: Reads passwords from the file, strips whitespace, and attempts to log in.
- **Error Handling**: Catches and handles file not found errors and other exceptions.

## Disclaimer

This script is for educational purposes only. Unauthorized access to email accounts is illegal and unethical. Use this script responsibly and only on accounts you own or have explicit permission to test.
