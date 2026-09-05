#!/usr/bin/env python3
"""Disassemble a function of the main ELF by name or address.

The title ships with `.symtab`, so calls and globals can be labelled instead
of left as bare addresses -- which is what makes reading these routines
practical at all.

    python3 tools/disasm.py "Macross (Japan).iso" STR_GetIdx
    python3 tools/disasm.py "Macross (Japan).iso" 0x1a1510 0x120
"""
import struct
import os
import sys

import capstone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import gamedata
import symbols


def segments(d):
    phoff, = struct.unpack_from("<I", d, 0x1c)
    phent, phnum = struct.unpack_from("<HH", d, 0x2a)
    out = []
    for i in range(phnum):
        o = phoff + i * phent
        typ, off, vaddr, _, fsz, msz, _, _ = struct.unpack_from("<8I", d, o)
        if typ == 1:
            out.append((vaddr, off, fsz))
    return out


def read(d, vaddr, n):
    for va, off, fsz in segments(d):
        if va <= vaddr < va + fsz:
            k = vaddr - va
            return d[off + k:off + k + min(n, fsz - k)]
    raise KeyError(f"{vaddr:#x} not in any loadable segment")


def main():
    if len(sys.argv) < 3:
        gamedata.usage(__file__)
    game = sys.argv[1]
    d = open(gamedata.elf_path(game), "rb").read()
    t = symbols.Table(game)
    arg = sys.argv[2]
    try:
        addr = int(arg, 0)
        size = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
    except ValueError:
        hit = [s for s in t.syms if s[1] == arg] or t.find(arg)
        if not hit:
            sys.exit(f"no symbol matching {arg!r}")
        addr, name, size, _ = hit[0]
        size = int(sys.argv[3], 0) if len(sys.argv) > 3 else (size or 0x100)
        print(f"; {name} @ {addr:#010x} ({size} bytes)")
    md = capstone.Cs(capstone.CS_ARCH_MIPS,
                     capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    md.detail = False
    code = read(d, addr, size)
    pos = 0
    while pos < len(code):
        got = list(md.disasm(code[pos:], addr + pos, 1))
        if not got:                      # R5900 MMI opcodes capstone lacks
            import struct as _s
            w, = _s.unpack_from("<I", code, pos)
            print(f"  {addr + pos:#010x}  .word     {w:#010x}")
            pos += 4
            continue
        ins = got[0]
        pos += ins.size
        note = ""
        for tok in ins.op_str.replace(",", " ").split():
            if tok.startswith("0x"):
                try:
                    v = int(tok.split("(")[0], 16)
                except ValueError:
                    continue
                lab = t.label(v)
                if not lab.startswith("0x"):
                    note = f"   ; {lab}"
        print(f"  {ins.address:#010x}  {ins.mnemonic:<9} {ins.op_str}{note}")


main()
