#!/usr/bin/env python3
"""Check that a disc image is the version this patch was built against.

Hashing 1.2 GB to answer "is this the right game?" is wasteful and tells you
little when it fails. Hashing the two files the patch actually depends on --
the main ELF and the script container -- is fast, and says *which* part is
unexpected, so a wrong region or a re-release is distinguishable from a bad
dump.

    python3 tools/verify.py "Macross (Japan).iso"
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import isopatch

KNOWN = {
    "SLPM-65405": {
        "title": "Chou Jikuu Yousai Macross (Japan)",
        "SLPM_654.05": ("84ff167ee9612966e5027beabb7b920e7cf18920", 4262380),
        "BOOTDAT.CMP": ("51d3ea46a2e59a2123fcb2bc9add53f5630b0374", 198240),
    },
}


def _read(img, name, cvm=None):
    with open(img, "rb") as f:
        if cvm:
            lba, _ = isopatch.find(f, 0, cvm)
            base = lba * isopatch.SECTOR + isopatch.CVM_HEADER
            l, n = isopatch.find(f, base, name)
            off = base + l * isopatch.SECTOR
        else:
            l, n = isopatch.find(f, 0, name)
            off = l * isopatch.SECTOR
        f.seek(off)
        return f.read(n)


def check(img, edition="SLPM-65405"):
    """(ok, [lines]) -- never raises for a merely wrong image."""
    want = KNOWN[edition]
    lines, ok = [], True
    for name, cvm in (("SLPM_654.05", None), ("BOOTDAT.CMP", "JPN.CVM")):
        try:
            d = _read(img, name, cvm)
        except (KeyError, ValueError) as e:
            lines.append(f"  {name}: not found ({e})")
            ok = False
            continue
        got = hashlib.sha1(d).hexdigest()
        exp, size = want[name]
        if got == exp and len(d) == size:
            lines.append(f"  {name}: ok")
        else:
            ok = False
            lines.append(f"  {name}: MISMATCH\n"
                         f"      expected {exp} ({size} bytes)\n"
                         f"      found    {got} ({len(d)} bytes)")
    return ok, lines


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: verify.py <game.iso>")
    ok, lines = check(sys.argv[1])
    print(f"{KNOWN['SLPM-65405']['title']} (SLPM-65405)")
    print("\n".join(lines))
    print("\nThis is the supported image." if ok else
          "\nThis is NOT the supported image. The patch would not be safe to "
          "apply.\nA different region or re-release needs its own hashes.")
    sys.exit(0 if ok else 1)
