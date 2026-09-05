#!/usr/bin/env python3
"""Symbol table of the main ELF, which unusually ships with `.symtab`.

17,423 named addresses beat any amount of guessing: `nearest(addr)` turns a
raw program counter or pointer out of the emulator into `function+0x1c`.

    python3 tools/symbols.py "Macross (Japan).iso" 0x1a1510   # what lives here
    python3 tools/symbols.py "Macross (Japan).iso" STR_GetIdx # where is this
"""
import bisect
import os
import struct
import sys


def load(path):
    d = open(path, "rb").read()
    shoff, = struct.unpack_from("<I", d, 0x20)
    shent, shnum, shstr = struct.unpack_from("<HHH", d, 0x2e)
    secs = []
    for i in range(shnum):
        o = shoff + i * shent
        name, typ, _, addr, off, size, link, _, _, esz = \
            struct.unpack_from("<10I", d, o)
        secs.append((name, typ, addr, off, size, link, esz))
    strtab_off = secs[shstr][3]

    def sname(n):
        e = d.index(b"\0", strtab_off + n)
        return d[strtab_off + n:e].decode()

    syms = []
    for name, typ, addr, off, size, link, esz in secs:
        if typ != 2:                      # SHT_SYMTAB
            continue
        stroff = secs[link][3]
        for j in range(size // esz):
            o = off + j * esz
            nm, val, sz, info, _, shndx = struct.unpack_from("<IIIBBH", d, o)
            if not nm or not val:
                continue
            e = d.index(b"\0", stroff + nm)
            syms.append((val, d[stroff + nm:e].decode(), sz, info & 0xf))
    syms.sort()
    return syms


class Table:
    def __init__(self, path):
        """`path` may be the disc image or an already-extracted ELF."""
        import gamedata
        self.syms = load(gamedata.elf_path(path))
        self.addrs = [s[0] for s in self.syms]

    def nearest(self, addr):
        i = bisect.bisect_right(self.addrs, addr) - 1
        if i < 0:
            return None
        a, name, size, kind = self.syms[i]
        return name, addr - a, size, kind

    def label(self, addr):
        hit = self.nearest(addr)
        if not hit or hit[1] > 0x20000:
            return f"{addr:#010x}"
        name, delta, _, _ = hit
        return f"{name}+{delta:#x}" if delta else name

    def find(self, needle):
        n = needle.lower()
        return [s for s in self.syms if n in s[1].lower()]


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import gamedata
    if len(sys.argv) < 2:
        gamedata.usage(__file__)
    t = Table(sys.argv[1])
    print(f"{len(t.syms)} symbols", file=sys.stderr)
    for arg in sys.argv[2:]:
        try:
            print(f"{arg}: {t.label(int(arg, 0))}")
        except ValueError:
            for a, nm, sz, k in t.find(arg)[:25]:
                print(f"  {a:#010x} {sz:>6}  {nm}")
