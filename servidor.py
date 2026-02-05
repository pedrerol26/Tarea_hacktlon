import socket
import threading
import json

HOST, PORT = "127.0.0.1", 9999

panels = set()          # sockets de panel
students = {}           # sock -> username
lock = threading.Lock() # para proteger estructuras compartidas

def send_json(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))

def broadcast_to_panels(obj):
    dead = []
    with lock:
        targets = list(panels)
    for p in targets:
        try:
            send_json(p, obj)
        except Exception:
            dead.append(p)
    if dead:
        with lock:
            for p in dead:
                panels.discard(p)
                try: p.close()
                except: pass

def handle_client(conn, addr):
    print(f"[+] Conectado: {addr}")
    buf = b""
    role = None
    user = None

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data

            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    send_json(conn, {"type": "ERROR", "msg": "JSON inválido"})
                    continue

                # 1) Registro
                if msg.get("type") == "HELLO":
                    role = msg.get("role")
                    user = msg.get("user", "UNKNOWN")

                    with lock:
                        if role == "panel":
                            panels.add(conn)
                        elif role == "student":
                            students[conn] = user
                        else:
                            role = None

                    if role:
                        print(f"[+] Registrado {role}: {user}")
                        send_json(conn, {"type": "INFO", "msg": f"Registrado como {role}"})
                    else:
                        send_json(conn, {"type": "ERROR", "msg": "role debe ser 'panel' o 'student'"})
                    continue

                # Si aún no se registró, no aceptamos datos
                if role is None:
                    send_json(conn, {"type": "ERROR", "msg": "Primero manda HELLO"})
                    continue

                # 2) Por ahora: si llega METRICS, reenviamos al panel (para probar)
                if msg.get("type") == "METRICS":
                    msg_out = {"type": "METRICS_SEEN", "user": user, "data": msg}
                    broadcast_to_panels(msg_out)

    finally:
        # Limpieza al desconectar
        with lock:
            panels.discard(conn)
            if conn in students:
                print(f"[-] Student desconectado: {students[conn]}")
                del students[conn]
        try:
            conn.close()
        except:
            pass
        print(f"[-] Desconectado: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(200)
    print(f"Servidor en {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
