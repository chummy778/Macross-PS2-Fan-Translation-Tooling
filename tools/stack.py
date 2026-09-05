#!/usr/bin/env python3
"""Recover a call stack from a savestate's EE RAM.

PINE cannot report the program counter, but a savestate carries both the
registers and all 32 MB of RAM. Walking up from `sp` and labelling every
word that lands inside a known function gives the chain of return addresses
-- enough to see what the machine is actually stuck on.

    python3 tools/stack.py "Macross (Japan).iso" <eeMemory.bin> <sp> [words]
"""
import struct
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import gamedata
import symbols

if len(sys.argv) < 4:
    gamedata.usage(__file__)
ee = open(sys.argv[2], "rb").read()
sp = int(sys.argv[3], 0) & 0x1FFFFFFF
n = int(sys.argv[4], 0) if len(sys.argv) > 4 else 512
t = symbols.Table(sys.argv[1])
seen = []
for i in range(n):
    a = sp + i * 4
    v, = struct.unpack_from("<I", ee, a)
    if 0x100000 <= v < 0x400000:
        lab = t.label(v)
        if not lab.startswith("0x") and lab not in seen:
            seen.append(lab)
            print(f"  {a:#010x}  {v:#010x}  {lab}")
