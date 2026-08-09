#!/usr/bin/env python3
"""BD-JB5 LAN scanner - finds PS5s with RemoteJarLoader (:9025) or elfldr (:9021) open."""
import socket, sys, ipaddress, concurrent.futures

PORTS = {9025: "RemoteJarLoader (BD-JB5)", 9021: "elfldr"}

def probe(ip):
    for port, name in PORTS.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        try:
            if s.connect_ex((ip, port)) == 0:
                return ip, port, name
        finally:
            s.close()
    return None

def main():
    net = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.0/24"
    print(f"[*] Scanning {net} for BD-JB5 services...")
    hosts = [str(h) for h in ipaddress.ip_network(net, strict=False).hosts()]
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
        for r in ex.map(probe, hosts):
            if r:
                found.append(r)
                print(f"[+] {r[0]}:{r[1]} -> {r[2]}")
    if not found:
        print("[-] Nothing found. Is the BD-J payload running?")
    return 0 if found else 1

if __name__ == "__main__":
    main()
