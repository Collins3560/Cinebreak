#!/usr/bin/env python3
"""Mock PS5-side servers: TCP jar loader (9025) + UDP log server (18194)"""
import socket, threading, time

def jar_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 9025)); s.listen(1)
    conn, addr = s.accept()
    data = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk: break
        data += chunk
    conn.close()
    print(f"[JAR-SRV] received {len(data)} bytes | magic {data[:4]} | manifest: {b'META-INF/MANIFEST.MF' in data[:1024]}")

def log_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 18194)); s.settimeout(0.5)
    client, last_beat = None, 0
    while True:
        try:
            data, addr = s.recvfrom(4096)
            msg = data.decode('utf-8', 'replace')
            if msg == "REGISTER":
                client, last_beat = addr, time.time()
                s.sendto(b"[probe] payload booted inside BD-J sandbox\n", addr)
                s.sendto(b"HEARTBEAT", addr)
            elif msg == "HEARTBEAT_ACK":
                last_beat = time.time()
        except socket.timeout:
            pass
        if client and time.time() - last_beat > 2:
            s.sendto(b"HEARTBEAT", client); last_beat = time.time()

threading.Thread(target=jar_server, daemon=True).start()
threading.Thread(target=log_server, daemon=True).start()
print("[MOCK] servers up")
time.sleep(120)
