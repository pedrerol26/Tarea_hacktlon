import socket
import json
import time
from pynput import mouse

HOST = "127.0.0.1"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

mouse_px = 0
last = None

def send_json(obj):
    sock.sendall((json.dumps(obj) + "\n").encode("utf-8"))

def on_move(x, y):
    global mouse_px, last
    if last is None:
        last = (x, y)
        return

    lx, ly = last
    mouse_px += abs(x - lx) + abs(y - ly)
    last = (x, y)

listener = mouse.Listener(on_move=on_move)
listener.start()

print("Cliente alumno enviando métricas...")

while True:
    time.sleep(1)

    payload = {
        "type": "METRICS",
        "user": "Roberto",
        "mouse_px_1s": mouse_px,
        "idle_ms": 0
    }

    send_json(payload)
    mouse_px = 0
