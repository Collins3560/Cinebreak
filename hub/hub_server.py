#!/usr/bin/env python3
"""
Cinebreak Hub - hub_server.py
Zero-dependency local dashboard: scene status + console discovery.
Serves JSON at /api/status and a minimal HTML page at /.
Usage: hub_server.py [--port 8777]
"""
import json, os, subprocess, sys, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HUB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HUB)

def scene_data():
    p = os.path.join(HUB, "scene_cache.json")
    if os.path.exists(p):
        return json.load(open(p))
    r = subprocess.run([sys.executable, os.path.join(HUB, "scene.py")], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout.split("=== Scene matrix ===")[0].strip()) or {}
    except Exception:
        return {"error": "scene cache unavailable"}

def console_scan(net="192.168.1.0/24"):
    try:
        sys.path.insert(0, ROOT)
        from ps5find import probe
        import ipaddress, concurrent.futures
        hosts = [str(h) for h in ipaddress.ip_network(net, strict=False).hosts()]
        found = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
            for r in ex.map(probe, hosts):
                if r: found.append({"ip": r[0], "port": r[1], "service": r[2]})
        return found
    except Exception as e:
        return [{"error": str(e)}]

HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Cinebreak Hub</title>
<style>body{font-family:ui-monospace,monospace;background:#0d1117;color:#c9d1d9;margin:2rem}
h1{color:#58a6ff}.ok{color:#3fb950}.warn{color:#d29922}table{border-collapse:collapse;width:100%}
td,th{border:1px solid #30363d;padding:.4rem .8rem;text-align:left}th{background:#161b22}
a{color:#58a6ff;text-decoration:none}.card{background:#161b22;padding:1rem;border-radius:8px;margin-bottom:1rem}</style></head>
<body><h1>🎬 Cinebreak Hub</h1>
<div class="card"><h3>🖥️ Console discovery</h3><pre id="consoles">scanning...</pre></div>
<div class="card"><h3>🌐 Scene status</h3><table><tr><th>project</th><th>latest</th><th>date</th><th>kind</th></tr><tbody id="scene"></tbody></table></div>
<script>
fetch('/api/consoles?net=192.168.1.0/24').then(r=>r.json()).then(d=>{
  document.getElementById('consoles').textContent =
    d.length? d.map(c=>`[+] ${c.ip}:${c.port} -> ${c.service}`).join('\\n') : '[-] no console found';
});
fetch('/api/scene').then(r=>r.json()).then(d=>{
  document.getElementById('scene').innerHTML =
    (d.projects||[]).map(p=>`<tr><td><a href="${p.url}">${p.name}</a></td>
      <td class="ok">${p.tag}</td><td>${(p.date||'').slice(0,10)}</td><td>${p.kind}</td></tr>`).join('');
});
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/scene":
            b = json.dumps(scene_data()).encode()
        elif u.path.startswith("/api/consoles"):
            q = urllib.parse.parse_qs(u.query); b = json.dumps(console_scan(q.get("net", ["192.168.1.0/24"])[0])).encode()
        else:
            b = HTML.encode()
        self.send_response(200); self.send_header("Content-Type", "application/json" if b[:1] == b"{" else "text/html")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

if __name__ == "__main__":
    port = 8777
    if len(sys.argv) > 2 and sys.argv[1] == "--port": port = int(sys.argv[2])
    print(f"[+] Cinebreak Hub on http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
