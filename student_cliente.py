import socket, json, time
import threading
import os
from pynput import mouse

HOST, PORT = "192.168.11.234", 9999

nombre_equipo = socket.gethostname()
try:
    nombre_usuario = os.getlogin()
except:
    nombre_usuario = os.getenv('USERNAME') or os.getenv('USER') or "Desconocido"

USER = f"{nombre_equipo} - {nombre_usuario}"

def send_json(sock, obj):
    try:
        sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
    except BrokenPipeError:
        print("Error: Conexión perdida con el servidor.")
        raise SystemExit(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect((HOST, PORT))
except ConnectionRefusedError:
    print(f"No se pudo conectar al servidor en {HOST}:{PORT}")
    raise SystemExit(1)

send_json(sock, {"type": "HELLO", "role": "student", "user": USER})
print(f"Conectado. Equipo: {nombre_equipo} Usuario: {nombre_usuario}")

mouse_px_1s = 0
last_pos = None
last_move_time = time.time()
lock = threading.Lock()

def on_move(x, y):
    global mouse_px_1s, last_pos, last_move_time
    with lock:
        last_move_time = time.time()
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
        idle_ms = int((time.time() - last_move_time) * 1000)

    send_json(sock, {"type": "METRICS", "mouse_px_1s": value, "idle_ms": idle_ms, "ts": time.time()})
