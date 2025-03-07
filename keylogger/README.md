# Keylogger con Envío de Correos

Este proyecto es un keylogger en Python que registra las teclas presionadas por el usuario y las guarda en un archivo `text.txt`. Cada 20 teclas registradas, el archivo se envía automáticamente por correo electrónico al destinatario configurado.

## 📌 Características
- Captura las teclas presionadas y las almacena en `text.txt`.
- Detecta teclas especiales (`Enter`, `Shift`, `Ctrl`, etc.) y las almacena correctamente.
- Envía automáticamente el archivo de registro por correo electrónico cada 20 teclas presionadas.
- Usa `pynput` para la captura del teclado.
- Utiliza `smtplib` para enviar los correos con Gmail.

## 🚀 Instalación
### 1. Clonar el repositorio
```sh
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```

### 2. Instalar dependencias
Asegúrate de tener Python 3 instalado y ejecuta:
```sh
pip install pynput
```

## 📧 Configuración del Correo Electrónico
Para enviar correos usando Gmail:
1. **Habilita la verificación en dos pasos** en tu cuenta de Google.
2. **Genera una contraseña de aplicación** en [Google Security](https://myaccount.google.com/security).
3. **Reemplaza tu contraseña en el script** con la contraseña de aplicación generada.

En el archivo `main.py`, modifica esta línea:
```python
sesion_smtp.login('tu_email@gmail.com', 'TU_CONTRASEÑA_DE_APLICACIÓN')
```

⚠ **No uses tu contraseña real de Gmail en el código.**

## 🛠️ Uso
Ejecuta el script con:
```sh
python main.py
```
El keylogger comenzará a capturar las teclas y, cada 20 pulsaciones, enviará el archivo `text.txt` a tu correo.

## ⚠️ Advertencia Legal
Este software debe usarse **solo para propósitos educativos y pruebas de seguridad**. **No lo uses en sistemas sin consentimiento explícito**, ya que puede violar leyes de privacidad y ciberseguridad.

---
**Autor:** Tu Nombre  
📧 Contacto: tu_email@gmail.com

