import socket

HOST = "127.0.0.1"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

print("Panel conectado...")

buffer = b""

while True:
    data = sock.recv(4096)
    if not data:
        break

    buffer += data
    while b"\n" in buffer:
        line, buffer = buffer.split(b"\n", 1)
        print("PANEL:", line.decode())
