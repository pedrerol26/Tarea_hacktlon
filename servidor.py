import socket
import threading
import json
import time
import asyncio
import websockets

TCP_HOST = "0.0.0.0"
TCP_PORT = 9999

WS_HOST = "0.0.0.0"
WS_PORT = 8765

lock = threading.Lock()
latest_by_user = {}   # user -> {"mouse_px_1s":..., "idle_ms":..., "ts":..., "state":...}

ws_clients = set()
ws_loop = None  # asyncio loop donde viven los websockets


def compute_state(m):
    idle = int(m.get("idle_ms", 0))
    mouse = int(m.get("mouse_px_1s", 0))

    if idle >= 30000:
        return "AUSENTE"
    if mouse >= 200 and idle < 5000:
        return "MUY_ACTIVO"
    if mouse > 0:
        return "ACTIVO"
    return "QUIETO"


def tcp_send_json(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))


def broadcast_ws(obj):
    """Broadcast a todos los WebSocket conectados (llamado desde hilos TCP)."""
    global ws_loop
    if ws_loop is None:
        return

    msg = json.dumps(obj, ensure_ascii=False)

    async def _send_all():
        dead = []
        for ws in list(ws_clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            ws_clients.discard(ws)

    asyncio.run_coroutine_threadsafe(_send_all(), ws_loop)


def handle_student(conn, addr):
    buf = b""
    role = None
    user = None
    print(f"[TCP] Conectado: {addr}")

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
                    tcp_send_json(conn, {"type": "ERROR", "msg": "JSON inválido"})
                    continue

                if msg.get("type") == "HELLO":
                    role = msg.get("role")
                    user = msg.get("user", "UNKNOWN")

                    if role != "student":
                        tcp_send_json(conn, {"type": "ERROR", "msg": "Este puerto TCP es solo para students"})
                        role = None
                        continue

                    tcp_send_json(conn, {"type": "INFO", "msg": f"Registrado student: {user}"})
                    print(f"[TCP] Student registrado: {user}")
                    continue

                if role is None:
                    tcp_send_json(conn, {"type": "ERROR", "msg": "Primero manda HELLO"})
                    continue

                if msg.get("type") == "METRICS":
                    m = {
                        "mouse_px_1s": int(msg.get("mouse_px_1s", 0)),
                        "idle_ms": int(msg.get("idle_ms", 0)),
                        "ts": float(msg.get("ts", time.time())),
                    }
                    state = compute_state(m)

                    with lock:
                        latest_by_user[user] = {**m, "state": state}

                    print("[TCP] METRICS de", user, "mouse=", m["mouse_px_1s"], "idle=", m["idle_ms"], "state=", state)

                    broadcast_ws({
                        "type": "STATE",
                        "user": user,
                        "state": state,
                        "mouse_px_1s": m["mouse_px_1s"],
                        "idle_ms": m["idle_ms"],
                        "ts": m["ts"],
                    })

    finally:
        try:
            conn.close()
        except:
            pass
        print(f"[TCP] Desconectado: {addr} ({user})")


def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_HOST, TCP_PORT))
    server.listen(200)
    print(f"[TCP] Students en {TCP_HOST}:{TCP_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_student, args=(conn, addr), daemon=True).start()


async def ws_handler(websocket, path=None):
    print("[WS] Panel conectado", path)
    ws_clients.add(websocket)

    # snapshot al conectar
    with lock:
        snapshot = [
            {"type": "STATE", "user": u, **data}
            for u, data in latest_by_user.items()
        ]
    for item in snapshot:
        await websocket.send(json.dumps(item, ensure_ascii=False))

    try:
        async for _ in websocket:
            pass
    finally:
        ws_clients.discard(websocket)
        print("[WS] Panel desconectado")


async def ws_main():
    global ws_loop
    ws_loop = asyncio.get_running_loop()
    print(f"[WS] Panel en ws://{WS_HOST}:{WS_PORT}")

    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await asyncio.Future()  # forever


def main():
    threading.Thread(target=tcp_server, daemon=True).start()
    asyncio.run(ws_main())


if __name__ == "__main__":
    main()
