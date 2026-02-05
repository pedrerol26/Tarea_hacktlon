import socket, json

HOST, PORT = "127.0.0.1", 9999

def send_json(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
send_json(sock, {"type":"HELLO", "role":"panel", "user":"PROFE"})

buf = b""
while True:
    data = sock.recv(4096)
    if not data:
        break
    buf += data
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        line = line.decode("utf-8", errors="ignore").strip()
        if line:
            print("PANEL:", line)
