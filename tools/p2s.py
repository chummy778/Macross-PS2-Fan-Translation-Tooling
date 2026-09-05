#!/usr/bin/env python3
"""Read members out of a PCSX2/ARMSX2 savestate (`.p2s`).

A `.p2s` is a zip, but modern builds compress members with **zstd** (method
93), which Python's `zipfile` refuses. The members are plain zstd frames, so
the local header is parsed by hand and the payload piped through `zstd -d`.

This is how the emulator's own view of the machine is obtained without a
debugger: `eeMemory.bin` is the full 32 MB of EE RAM, and `PCSX2 Internal
Structures.dat` carries the CPU registers, including the program counter.
"""
import struct
import subprocess
import sys
import zipfile

STORED, ZSTD = 0, 93


def read(path, name):
    with zipfile.ZipFile(path) as z:
        info = z.getinfo(name)
    with open(path, "rb") as f:
        f.seek(info.header_offset)
        hdr = f.read(30)
        n, m = struct.unpack_from("<HH", hdr, 26)
        f.seek(info.header_offset + 30 + n + m)
        blob = f.read(info.compress_size)
    if info.compress_type == STORED:
        return blob
    if info.compress_type != ZSTD:
        raise NotImplementedError(f"{name}: zip method {info.compress_type}")
    p = subprocess.run(["zstd", "-d", "-c", "-q"], input=blob,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.stdout


def members(path):
    with zipfile.ZipFile(path) as z:
        return [i.filename for i in z.infolist()]


if __name__ == "__main__":
    src = sys.argv[1]
    if len(sys.argv) == 2:
        for m in members(src):
            print(m)
    else:
        data = read(src, sys.argv[2])
        out = sys.argv[3] if len(sys.argv) > 3 else None
        if out:
            open(out, "wb").write(data)
            print(f"{sys.argv[2]}: {len(data)} bytes -> {out}")
        else:
            sys.stdout.buffer.write(data)
