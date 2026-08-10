#!/usr/bin/env python3
"""
Cinebreak Hub - autoload.py
Build a USB autoload package for PS5 homebrew (kstuff-style autoload.txt).
Format: payload.elf / !milliseconds-delay / ?port timeout poll (wait).

Usage: autoload.py build <flowfile> <outdir>
       autoload.py demo
"""
import os, sys, zipfile, datetime

def build(flow, outdir):
    """flow: list of (payload_path, delay_ms_after) tuples + waits"""
    os.makedirs(outdir, exist_ok=True)
    lines, files = [], []
    for step in flow:
        kind = step[0]
        if kind == "payload":
            path, delay = step[1], step[2]
            files.append(path)
            lines.append(os.path.basename(path))
            if delay: lines.append(f"!{delay}")
        elif kind == "wait":
            port, timeout, poll = step[1], step[2], step[3]
            lines.append(f"?{port} {timeout} {poll}")
    autoload = "\n".join(lines) + "\n"
    zpath = os.path.join(outdir, "ps5_autoloader.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("autoload.txt", autoload)
        for f in set(files):
            if os.path.exists(f):
                z.write(f, os.path.basename(f))
    print(f"[+] {zpath}")
    print(f"[+] autoload.txt:\n{autoload}")
    return zpath

def demo():
    """Demo flow using payloads from this repo's build tree."""
    base = os.path.expanduser("~/ps5dev")
    flow = [
        ("payload", f"{base}/BD-JB5/payloads/poops/poops.jar", 1500),
        ("wait", 9021, 60, 500),
        ("payload", f"{base}/BD-JB5/payloads/cinebreak-shell/cinebreak-shell.jar", 1000),
    ]
    build(flow, "/tmp/autoload_demo")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    elif len(sys.argv) == 4 and sys.argv[1] == "build":
        # flowfile: one step per line: P <path> <delay> | W <port> <timeout> <poll>
        flow = []
        for line in open(sys.argv[2]):
            t = line.split()
            if not t: continue
            if t[0] == "P": flow.append(("payload", t[1], int(t[2]) if len(t) > 2 else 0))
            elif t[0] == "W": flow.append(("wait", int(t[1]), int(t[2]), int(t[3])))
        build(flow, sys.argv[3])
    else:
        print(__doc__)
