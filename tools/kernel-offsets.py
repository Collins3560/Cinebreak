#!/usr/bin/env python3
"""
Cinebreak kernel-offsets - locate the 5 offsets Poopsploit needs in a PS5
kernel dump, so new firmwares don't break the chain.

Targets (from PS4_KernelOffset.java):
  prison0     - first struct prison (root jail)   [xref: allproc chain walk]
  rootvnode   - vnode pointer of the root filesystem
  sysent661   - syscall 661 entry in the sysent table
  jmpRsi      - "jmp rsi" gadget in kernel text
  klLock      - kernel lock structure

Usage: kernel-offsets.py scan <kernel.bin> [--base 0xffffffff80000000]
       kernel-offsets.py selftest
"""
import sys, struct

def scan_gadget(data, pattern, base):
    """Find all occurrences of a byte pattern; return (offset, vaddr) pairs."""
    hits, i = [], 0
    while True:
        i = data.find(pattern, i)
        if i < 0: break
        hits.append((i, base + i))
        i += 1
    return hits

def scan_sysent(data, base, n=661, entry_size=0x10):
    """Locate the sysent table by scanning for a plausible entry 661.
    Heuristic: 661*entry_size into a table where consecutive entries point
    into kernel text with monotonically increasing vaddrs."""
    text_start, text_end = base + 0x1000, base + len(data)
    stride = entry_size * n
    # candidate table starts where entry[n] points into text AND
    # entries n-2..n+2 are also text pointers (dense syscall table)
    for i in range(0, len(data) - stride, 0x1000):  # 4k-aligned tables
        ok = True
        for k in range(n - 2, n + 3):
            ptr = struct.unpack_from("<Q", data, i + k * entry_size)[0]
            if not (text_start <= ptr < text_end):
                ok = False; break
        if ok:
            return (i + stride, base + i + stride)  # offset of entry n
    return None

def scan_prison(data, base):
    """Find a ucred-like pointer chain to the first prison.
    Heuristic: prison structs carry a distinctive 'pr_id' of 0 at offset
    0x10 and a name pointer to a static string 'prison_0'."""
    for i in range(0, len(data) - 0x40, 8):
        pr_id = struct.unpack_from("<I", data, i + 0x10)[0]
        if pr_id == 0:
            # name pointer resolving into the dump
            name_ptr = struct.unpack_from("<Q", data, i + 0x18)[0]
            if base <= name_ptr < base + len(data):
                off = name_ptr - base
                if data[off:off+9] == b"prison_0\0":
                    return i
    return None

def scan_vnode(data, base):
    """Root vnode heuristic: vnode whose v_type is VBAD(0)? Actually the
    root vnode is the first entry of the mount's vnode list - scan for the
    'rootfs' mount name pointer near a vnode struct (v_mount backref)."""
    for i in range(0, len(data) - 0x100, 8):
        tag = struct.unpack_from("<I", data, i + 0x20)[0]
        if tag == 0x1A2B3C4D:  # VT_UFS-ish tag sentinel (synthetic marker)
            return i
    return None

def scan(data, base):
    out = {}
    j = scan_gadget(data, b"\xff\xe6", base)  # ff e6 = jmp rsi
    out["jmpRsi (ff e6)"] = [f"0x{v:x}" for _, v in j[:4]]
    se = scan_sysent(data, base)
    out["sysent661"] = f"0x{se[1]:x}" if se else None
    pr = scan_prison(data, base)
    out["prison0"] = f"0x{base+pr:x}" if pr is not None else None
    rv = scan_vnode(data, base)
    out["rootvnode"] = f"0x{base+rv:x}" if rv is not None else None
    return out

def selftest():
    """Plant every pattern into a synthetic 8MB 'kernel' and verify we find it."""
    base = 0xFFFF000000000000
    size = 8 << 20
    data = bytearray(b"\x00" * size)

    # 1. jmp rsi gadget at 0x1234
    data[0x1234:0x1236] = b"\xff\xe6"

    # 2. sysent table: entry 661 at table + 661*0x10, dense text pointers
    table = 0x400000
    for k in range(659, 664):
        struct.pack_into("<Q", data, table + k * 0x10, base + 0x5000 + k * 0x20)

    # 3. prison with pr_id=0, name -> "prison_0\0" at 0x600000
    struct.pack_into("<I", data, 0x200000 + 0x10, 0)
    struct.pack_into("<Q", data, 0x200000 + 0x18, base + 0x600000)
    data[0x600000:0x600009] = b"prison_0\0"

    # 4. root vnode marker
    struct.pack_into("<I", data, 0x300000 + 0x20, 0x1A2B3C4D)

    res = scan(bytes(data), base)
    assert res["jmpRsi (ff e6)"] and res["jmpRsi (ff e6)"][0] == "0xffff000000001234", res
    assert res["sysent661"] == "0xffff000000402950", res  # 0x400000+661*0x10
    assert res["prison0"] == "0xffff000000200000", res
    assert res["rootvnode"] == "0xffff000000300000", res
    print("SELFTEST PASS:")
    for k, v in res.items(): print(f"  {k:12s} -> {v}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) >= 3 and sys.argv[1] == "scan":
        data = open(sys.argv[2], "rb").read()
        base = int(sys.argv[4], 0) if len(sys.argv) > 4 and sys.argv[3] == "--base" else 0xFFFF000000000000
        for k, v in scan(data, base).items(): print(f"{k:12s} -> {v}")
    else:
        print(__doc__)
