import socket

HOST = "127.0.0.1"
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"Servidor escuchando en {HOST}:{PORT}")

conn, addr = server.accept()
print("Cliente conectado:", addr)

buffer = b""

while True:
    data = conn.recv(4096)
    if not data:
        break

    buffer += data
    while b"\n" in buffer:
        line, buffer = buffer.split(b"\n", 1)
        print("RECIBIDO:", line.decode())

conn.close()
