#!/usr/bin/env python3
"""Compare a decompressed file against what actually landed in EE RAM.

The point is to check the *game's* decompressor against the reference one.
A patch can round-trip perfectly through `tools/cricmp` and still be decoded
differently by the title's own LZ routine, and the only place that shows up
is RAM. Sampling windows is not enough -- a single wrong byte is the whole
bug -- so this compares the entire image.

    python3 tools/ramdiff.py <eeMemory.bin> <expected.bin>
"""
import sys

ee, exp = open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()
anchor = exp[:32]
at = ee.find(anchor)
if at < 0:
    print("expected image not present in RAM at all (never decompressed?)")
    sys.exit(2)
print(f"image found at EE {at:#010x}")
got = ee[at:at + len(exp)]
bad = [i for i in range(len(exp)) if got[i] != exp[i]]
if not bad:
    print(f"all {len(exp)} bytes identical")
    sys.exit(0)
print(f"{len(bad)} of {len(exp)} bytes differ; first at {bad[0]:#x}")
f = bad[0]
lo = max(0, f - 16)
print(f"  expected {exp[lo:f+32].hex(' ')}")
print(f"  in RAM   {got[lo:f+32].hex(' ')}")
sys.exit(1)
