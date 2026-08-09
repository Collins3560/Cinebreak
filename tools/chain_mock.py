#!/usr/bin/env python3
"""Full-chain mock: simulates BD-JB5 -> kexploit -> elfldr progression."""
import socket, threading, time

def jar_server():
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 9025)); s.listen(5)
    while True:
        conn, addr = s.accept()
        data = b""
        while True:
            c = conn.recv(65536)
            if not c: break
            data += c
        conn.close()
        print(f"[MOCK] jar received: {len(data)} bytes (magic {data[:4]})", flush=True)

def log_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 18194)); s.settimeout(0.5)
    client, phase = None, 0
    while True:
        try:
            data, addr = s.recvfrom(4096)
            msg = data.decode('utf-8', 'replace')
            if msg == "REGISTER":
                client = addr; phase = 0
                s.sendto(b"[poops] BD-J Poopsploit 1.8 starting\n", addr)
        except socket.timeout:
            pass
        if client and phase == 0:
            time.sleep(3)
            s.sendto(b"[poops] triggerUcredTripleFree finished\n", client)
            s.sendto(b"[poops] Arbitrary R/W achieved.\n", client)
            s.sendto(b"[kexp] PS5 AIO JB Shellcode by ufm42\n", client)
            phase = 1
            print("[MOCK] kernel stage logged", flush=True)
            threading.Thread(target=elf_server, daemon=True).start()
        if client and phase == 1:
            time.sleep(0.3); phase = 2

def elf_server():
    time.sleep(4)
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 9021)); s.listen(5)
    print("[MOCK] elfldr :9021 UP", flush=True)
    while True:
        conn, addr = s.accept()
        data = b""
        while True:
            c = conn.recv(65536)
            if not c: break
            data += c
        conn.close()
        if data:
            print(f"[MOCK] elfldr deployed {len(data)} bytes (magic {data[:4]})", flush=True)

threading.Thread(target=jar_server, daemon=True).start()
threading.Thread(target=log_server, daemon=True).start()
print("[MOCK] chain simulation running", flush=True)
time.sleep(180)
