# 🎬 Cinebreak

A **one-shot, chainable PS5 jailbreak** built on [Gezine's BD-JB5](https://github.com/Gezine/BD-JB5) — a Blu-ray Disc Java sandbox escape — extended into a full *userland → kernel → root → homebrew* chain with automation tooling.

```
🎬 play the disc (BD-J sandbox escape)
   ↓
📡 RemoteJarLoader :9025
   ↓ push poops.jar
💥 Poopsploit — TheFlow NetControl kernel exploit → "Arbitrary R/W achieved"
   ↓
👑 AIO JB shellcode (ufm42) → root, syscall gate, dlsym
   ↓
🚀 elfldr :9021 → deploy any PS5 x86-64 ELF, runs with root
```

**Firmware:** kernel offsets 9.00 → 13.52. Explore at your own risk, on your own hardware, in a region where research is legal.

---

## ⚡ One-shot chain (the new part)

```bash
# 1. find your console
./ps5chain.py --find 192.168.1.0/24

# 2. run the whole chain and deploy an ELF
./ps5chain.py --chain <ps5-ip> --elf ./my_homebrew.elf
```

`ps5chain.py` finds the PS5, pushes the exploit, **watches the log for the kernel stage**, waits for `elfldr`, deploys your ELF, and streams everything live. Also ships:

| Tool | What it does |
|---|---|
| `ps5chain.py` | Full-chain orchestrator (find → exploit → deploy) |
| `ps5find.py` | Scans LAN for RemoteJarLoader :9025 / elfldr :9021 |
| `probe/` | A custom diagnostic payload (safe self-tests, kernel R/W check) |
| `tools/` | Local console simulators for testing without hardware |
| `CHAIN.md` | Every link of the chain mapped and documented |

## 🔨 Build the ISO

```bash
git clone https://github.com/john-tornblom/bdj-sdk bdj-sdk
# provide bdj-sdk/host/jdk8 + build its makefs/bdsigner host tools (see bdj-sdk README)
./build.sh          # → BD-JB5-2.0.iso (burn to BD-R/BD-RE)
```

## 📦 Payloads

| Payload | Purpose |
|---|---|
| `hello/` | Smoke test — proves the sandbox escape works |
| `probe/` | My diagnostic payload — safe system + kernel self-tests |
| `poops/` | The full chain — NetControl kernel exploit + kexp + AIO shellcode + ELF loader |

## 🙏 Credits — this is their work first

- **[Gezine](https://github.com/Gezine)** — BD-JB5, the entire BD-J sandbox escape and Poopsploit
- **[TheFlow](https://github.com/theofficialflow)** — NetControl kernel exploit, BD-J documentation, native code execution
- **[ufm42](https://github.com/ufm42)** — kexp + AIO all-in-one jailbreak shellcode
- **[john-tornblom](https://github.com/john-tornblom)** — bdj-sdk, ps5-payload-sdk, elfldr, makefs
- **[hammer-83](https://github.com/hammer-83)** — PS5 Remote JAR Loader reference
- **[kuba--](https://github.com/kuba--)** — zip, used in the unpatch payload

This repository is a **fork + tooling layer** over Gezine's MIT-licensed BD-JB5. All original copyright notices and licenses are preserved (see `LICENSE` and file headers). The build chain pulls in `john-tornblom/bdj-sdk` (GPL-3.0) as an external build dependency — clone it separately, its terms apply to it.

## ⚠️ Not a CFW
This is a per-boot jailbreak — reboot and you re-trigger. There is no PS5 custom firmware. Use for homebrew, research, and patches, on hardware you own.
