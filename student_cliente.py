import socket, json, time
from pynput import mouse
import threading

HOST, PORT = "127.0.0.1", 9999
USER = "Ana"

def send_json(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# Registro
send_json(sock, {"type": "HELLO", "role": "student", "user": USER})

mouse_px_1s = 0
last_pos = None
lock = threading.Lock()

def on_move(x, y):
    global mouse_px_1s, last_pos
    with lock:
        if last_pos is None:
            last_pos = (x, y)
            return
        lx, ly = last_pos
        mouse_px_1s += abs(x - lx) + abs(y - ly)
        last_pos = (x, y)

listener = mouse.Listener(on_move=on_move)
listener.start()

print("Enviando movimiento real del ratón cada 1s...")

while True:
    time.sleep(1)
    with lock:
        value = mouse_px_1s
        mouse_px_1s = 0

    send_json(sock, {"type": "METRICS", "mouse_px_1s": value})
