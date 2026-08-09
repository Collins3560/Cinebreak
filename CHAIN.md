# BD-JB5 FULL CHAIN — from Blu-ray to root homebrew

## The chain (5 links)

```
1. BD-JB5-2.0.iso (burned BD-R/BD-RE, FW <= 13.52)
   └─ BD-J sandbox escape (userland code exec in the BD-J VM)
        │
2. RemoteJarLoader :9025 — console waits for payloads over LAN
   └─ push poops.jar (BD-J Poopsploit 1.8)
        │
3. Poopsploit — TheFlow NetControl kernel exploit
   └─ ucred triple-free -> kqueue pointer leak -> pipebuf corruption
   └─ "Arbitrary R/W achieved" (full kernel read/write)
        │
4. AIO JB shellcode (ufm42) + kexp
   └─ rootvnode patch (root filesystem), syscall gate patch, dlsym patch
   └─ sceKernelJitCreateSharedMemory, loads kexp + elfldr
        │
5. elfldr :9021 — ELF server
   └─ deploy any PS5 x86-64 ELF homebrew -> runs with root
```

## Firmware support (kernel offsets in Poopsploit)

| Range | Offsets present |
|---|---|
| 9.00 - 9.60 | yes |
| 10.00 - 10.71 | yes |
| 11.00 - 11.52 | yes |
| 12.00 - 12.52 | yes |
| 13.00 - 13.52 | yes |

## One-shot usage

```bash
~/ps5dev/ps5chain.py --find 192.168.1.0/24            # locate console
~/ps5dev/ps5chain.py --chain <ps5-ip> --elf ./my.elf   # full chain + deploy
```

## Artifacts
- ISO:      ~/ps5dev/BD-JB5/BD-JB5-2.0.iso
- Payloads: helloworld.jar / probe.jar / poops.jar
- ELF ldr:  elfldr-ps5-0.23.elf (embedded in poops.jar)
- kexp:     kexp_2026_05_25.bin (embedded in poops.jar)

## Verified locally
Full progression simulated and orchestrated end-to-end:
jar 178685 bytes (PK magic) -> kernel markers -> elfldr :9021 ->
ELF 397000 bytes (7fELF magic) — byte-exact both sides.
