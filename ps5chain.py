#!/usr/bin/env python3
"""
ps5chain.py - BD-JB5 full chain orchestrator
Chain: BD-J sandbox escape -> Poopsploit (NetControl kexploit) -> kernel R/W
       -> AIO shellcode -> elfldr :9021 -> deploy ELF
"""
import socket, sys, time, threading, subprocess, os

JAR_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payloads/poops/poops.jar")
JAR_PORT   = 9025   # RemoteJarLoader (BD-JB5)
ELFLDR_PORT = 9021  # elfldr after kernel exploit
LOG_PORT   = 18194  # RemoteLogger (UDP)

MARKERS = ["Arbitrary R/W achieved", "AIO JB", "elfldr", "kexp", "complete", "ready"]

def find_ps5(net):
    """Scan subnet for RemoteJarLoader."""
    import ipaddress, concurrent.futures
    print(f"[*] scanning {net} for RemoteJarLoader :{JAR_PORT} ...")
    def probe(ip):
        s = socket.socket(); s.settimeout(0.7)
        try:
            return (ip, True) if s.connect_ex((ip, JAR_PORT)) == 0 else None
        finally:
            s.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
        for r in ex.map(probe, [str(h) for h in ipaddress.ip_network(net, strict=False).hosts()]):
            if r:
                print(f"[+] FOUND PS5 at {r[0]}")
                return r[0]
    return None

def push_jar(ip, jar=JAR_PATH):
    data = open(jar, 'rb').read()
    s = socket.socket(); s.settimeout(15)
    s.connect((ip, JAR_PORT))
    s.sendall(data)
    s.close()
    print(f"[+] pushed {jar} ({len(data)} bytes) -> {ip}:{JAR_PORT}")

def log_watch(ip, stop_event, timeout=180):
    """Stream BD-J logs; flag when kernel-stage markers appear."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    s.sendto(b"REGISTER", (ip, LOG_PORT))
    deadline = time.time() + timeout
    hits = set()
    while not stop_event.is_set() and time.time() < deadline:
        try:
            data, _ = s.recvfrom(4096)
            line = data.decode('utf-8', 'replace').strip()
            if line and line not in ("HEARTBEAT", "HEARTBEAT_ACK", "<<EOM>>"):
                print(f"  [log] {line}", flush=True)
                for m in MARKERS:
                    if m.lower() in line.lower():
                        hits.add(m)
        except socket.timeout:
            continue
    return hits

def wait_port(ip, port, timeout=240):
    print(f"[*] waiting for elfldr on {ip}:{port} (kernel stage may take a while)...")
    end = time.time() + timeout
    while time.time() < end:
        s = socket.socket(); s.settimeout(1.5)
        try:
            if s.connect_ex((ip, port)) == 0:
                s.close()
                print(f"[+] elfldr is UP on {ip}:{port}")
                return True
        finally:
            s.close()
        time.sleep(3)
    print("[-] elfldr never came up (wrong firmware? exploit failed?)")
    return False

def deploy_elf(ip, elf):
    data = open(elf, 'rb').read()
    s = socket.socket(); s.settimeout(30)
    s.connect((ip, ELFLDR_PORT))
    s.sendall(data)
    s.close()
    print(f"[+] deployed ELF ({len(data)} bytes) -> {ip}:{ELFLDR_PORT}")

def chain(ip, elf=None, watch_timeout=180):
    print(f"\n===== BD-JB5 FULL CHAIN @ {ip} =====")
    stop = threading.Event()
    watcher = threading.Thread(target=log_watch, args=(ip, stop, watch_timeout), daemon=True)
    watcher.start()
    push_jar(ip)
    time.sleep(2)
    if wait_port(ip, ELFLDR_PORT):
        if elf and os.path.exists(elf):
            deploy_elf(ip, elf)
        else:
            print("[*] elfldr up - no ELF specified (pass --elf /path/to/homebrew.elf)")
        print("[+] CHAIN COMPLETE - root homebrew running")
    stop.set()
    watcher.join(timeout=2)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="BD-JB5 full chain: sandbox escape -> kernel -> elfldr -> ELF")
    p.add_argument("--find", metavar="NET", help="scan subnet e.g. 192.168.1.0/24")
    p.add_argument("--chain", metavar="IP", help="run the full chain against a PS5 IP")
    p.add_argument("--elf", metavar="PATH", help="ELF homebrew to deploy once elfldr is up")
    p.add_argument("--jar", default=JAR_PATH, help="payload jar (default poops.jar)")
    a = p.parse_args()
    if a.find:
        ip = find_ps5(a.find)
        if not ip:
            sys.exit("[-] no PS5 found")
        if not a.chain:
            a.chain = ip
    if not a.chain:
        p.print_help(); sys.exit(1)
    chain(a.chain, a.elf)
