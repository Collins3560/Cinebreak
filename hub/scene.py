#!/usr/bin/env python3
"""
Cinebreak Hub - scene.py
Live PS5 jailbreak scene tracker. Queries GitHub for the projects that
matter, reports latest releases, and caches the matrix locally.

Usage: scene.py [--refresh] [--json]
"""
import json, os, subprocess, sys, datetime

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scene_cache.json")

# The scene, curated. Each entry: name, repo, kind, note
SOURCES = [
    ("BD-JB5 (upstream)",   "Gezine/BD-JB5",             "exploit", "our engine - BD-J sandbox escape, kernel offsets to 13.52"),
    ("Y2JB",                "Gezine/Y2JB",               "exploit", "YouTube userland entry, no disc needed"),
    ("Luac0re",             "Gezine/Luac0re",            "exploit", "mast1c0re-style Lua loader"),
    ("P2JB port",           "matem6/P2JB-Y2JB-Porting",  "exploit", "p2jb kernel port to Y2JB host"),
    ("etaHEN",              "etaHEN/etaHEN",             "payload", "AIO homebrew enabler for PS5 (toolbox/plugins/overlay/cheats)"),
    ("etaHEN cheats",       "etaHEN/PS5_Cheats",         "payload", "PS5 cheat database"),
    ("GoldHEN",             "GoldHEN/GoldHEN",           "payload", "PS4 homebrew enabler - PS5 support in 2026 builds"),
    ("ps5-linux",           "ps5-linux/ps5-linux-loader","payload", "boot Linux on PS5"),
    ("kexp",                "ufm42/kexp",                "exploit", "post-jailbreak all-in-one shellcode"),
    ("BD-J SDK",            "john-tornblom/bdj-sdk",     "sdk",    "build toolchain (GPL)"),
    ("PS5 payload SDK",     "ps5-payload-dev/sdk",       "sdk",    "prospero toolchain"),
    ("PS5 PayloadManager",  "cosmicflow2512/PS5-PayloadManager", "tool", "Windows payload manager (scene tooling)"),
]

def gh(args):
    try:
        r = subprocess.run(["gh", "api"] + args, capture_output=True, text=True, timeout=20)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:
        return None

def latest(repo):
    """Best-effort latest release/tag for a repo."""
    rel = gh([f"repos/{repo}/releases/latest"])
    if rel:
        return {"tag": rel.get("tag_name"), "date": rel.get("published_at"), "url": rel.get("html_url"),
                "assets": [a["name"] for a in rel.get("assets", [])][:6]}
    tag = gh([f"repos/{repo}/tags"])
    if tag:
        return {"tag": tag[0]["name"], "date": None, "url": f"https://github.com/{repo}/tags", "assets": []}
    return {"tag": "?", "date": None, "url": f"https://github.com/{repo}", "assets": []}

def scan():
    out = {"fetched": datetime.datetime.utcnow().isoformat() + "Z", "projects": []}
    for name, repo, kind, note in SOURCES:
        info = latest(repo)
        out["projects"].append({"name": name, "repo": repo, "kind": kind, "note": note, **info})
        print(f"  {'OK ' if info['tag'] != '?' else 'ERR'} {name:22s} {repo:32s} {info['tag']}", file=sys.stderr)
    return out

if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    js = "--json" in sys.argv
    if os.path.exists(CACHE) and not refresh:
        data = json.load(open(CACHE))
    else:
        if not js: print("[*] scanning scene (live GitHub)...")
        data = scan()
        json.dump(data, open(CACHE, "w"), indent=2)
    if js:
        print(json.dumps(data, indent=2))
    else:
        print("\n=== Scene matrix ===")
        for p in data["projects"]:
            print(f"{p['name']:22s} {p['tag']:12s} {p['date'] or '':10s} {p['kind']}")
