#!/usr/bin/env python3
"""Get the files the tools need out of the user's own disc image.

Nothing extracted from the game is committed, so every tool has to be able to
start from an ISO. This is the one place that knows how: hand it the disc and
it returns the decompressed script or the main ELF, caching both under
`work/` (which is gitignored).

Paths are accepted either way round -- an ISO, or a file already extracted --
so the same argument works whether someone is running the shipping pipeline
or poking at a blob by hand.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import isopatch

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
WORK = os.path.join(ROOT, "work")
CRICMP = os.path.join(ROOT, "tools", "cricmp")

CRICMP_HELP = """tools/cricmp is missing.

It is a third-party tool and is not committed here -- it is someone else's
code, and a prebuilt binary would only work on one platform. Build it once:

    git clone https://github.com/zeesworth/cricmp
    cd cricmp && make            # or: cc -O2 -o cricmp *.c
    cp cricmp {dest}
"""

USAGE = """this tool needs the game.

Pass your own copy of the disc image:

    python3 {tool} "Macross (Japan).iso"

Nothing from the game is committed to this repository, so there is no default
file to fall back on."""


def need_cricmp():
    if not (os.path.exists(CRICMP) and os.access(CRICMP, os.X_OK)):
        sys.exit(CRICMP_HELP.format(dest=CRICMP))


def usage(tool):
    sys.exit(USAGE.format(tool=os.path.relpath(tool, ROOT)))


def is_iso(path):
    """True if this looks like an ISO 9660 image rather than a loose file."""
    try:
        with open(path, "rb") as f:
            f.seek(0x8001)
            return f.read(5) == b"CD001"
    except OSError:
        return False


def script_blob(path, cache=None):
    """The decompressed BOOTDAT, from an ISO or from an already-extracted file."""
    if not is_iso(path):
        data = open(path, "rb").read()
        if data[:6] == b"CRICMP":          # a .CMP that still needs unpacking
            need_cricmp()
            os.makedirs(WORK, exist_ok=True)
            out = os.path.join(WORK, "_loose.bin")
            subprocess.run([CRICMP, "dec", path, out], check=True,
                           stdout=subprocess.DEVNULL)
            return open(out, "rb").read()
        return data                        # already decompressed

    need_cricmp()
    off, cap, _ = isopatch.locate(path, "JPN.CVM", "BOOTDAT.CMP")
    with open(path, "rb") as f:
        f.seek(off)
        packed = f.read(cap)
    os.makedirs(WORK, exist_ok=True)
    tmp = cache or os.path.join(WORK, "_bootdat.cmp")
    with open(tmp, "wb") as f:
        f.write(packed)
    out = tmp + ".bin"
    subprocess.run([CRICMP, "dec", tmp, out], check=True,
                   stdout=subprocess.DEVNULL)
    return open(out, "rb").read()


def elf_path(path):
    """Path to the main ELF, extracting it from an ISO if that is what we got."""
    if not is_iso(path):
        return path
    with open(path, "rb") as f:
        lba, length = isopatch.find(f, 0, "SLPM_654.05")
        f.seek(lba * isopatch.SECTOR)
        data = f.read(length)
    os.makedirs(WORK, exist_ok=True)
    out = os.path.join(WORK, "SLPM_654.05")
    with open(out, "wb") as f:
        f.write(data)
    return out
