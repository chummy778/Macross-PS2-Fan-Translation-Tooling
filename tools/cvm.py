#!/usr/bin/env python3
"""Read CRI CVM containers, as used by Super Dimensional Fortress Macross (PS2).

A .CVM is a 0x1800-byte CRI header followed by an ordinary ISO 9660 image.
Nothing is encrypted in this title: the inner volume descriptor's "CD001"
signature is readable at 0x9801, which is exactly the standard 0x8001 shifted
by the header size. So the whole thing can be parsed with a plain ISO reader
that adds a constant offset -- no CRI tooling required.

Used as a library by extract_cvm.py; run directly to list a container.
"""
import os
import struct

HEADER = 0x1800          # CRI header ahead of the inner ISO
SECTOR = 2048
MAGIC = b"CVMH"


class Cvm:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        self.f.seek(0)
        self.has_header = self.f.read(4) == MAGIC
        # A few containers on this disc have no CVMH magic. Rather than
        # assume, locate the volume descriptor and derive the offset from it.
        self.base = HEADER if self.has_header else self._find_base()

    def _find_base(self):
        self.f.seek(0)
        blob = self.f.read(0x40000)
        i = blob.find(b"CD001")
        if i < 0:
            raise ValueError(f"{self.path}: no ISO 9660 volume descriptor found")
        return i - 1 - 16 * SECTOR

    def sector(self, n):
        self.f.seek(self.base + n * SECTOR)
        return self.f.read(SECTOR)

    def read(self, lba, length):
        self.f.seek(self.base + lba * SECTOR)
        return self.f.read(length)

    def _walk(self, lba, length, prefix=""):
        buf = b"".join(self.sector(lba + i)
                       for i in range((length + SECTOR - 1) // SECTOR))
        off = 0
        while off < len(buf):
            rlen = buf[off]
            if rlen == 0:
                # Directory records never straddle a sector boundary; a zero
                # length means "skip to the next sector".
                off = (off // SECTOR + 1) * SECTOR
                if off >= len(buf):
                    break
                continue
            ex_lba = struct.unpack_from("<I", buf, off + 2)[0]
            ex_len = struct.unpack_from("<I", buf, off + 10)[0]
            flags = buf[off + 25]
            idl = buf[off + 32]
            name = buf[off + 33:off + 33 + idl].decode("ascii", "replace")
            if name not in ("\x00", "\x01"):
                clean = name.split(";")[0]
                if flags & 2:
                    yield from self._walk(ex_lba, ex_len, prefix + clean + "/")
                else:
                    yield prefix + clean, ex_lba, ex_len
            off += rlen

    def files(self):
        pvd = self.sector(16)
        if pvd[1:6] != b"CD001":
            raise ValueError(f"{self.path}: bad volume descriptor")
        rec = pvd[156:190]
        return list(self._walk(struct.unpack_from("<I", rec, 2)[0],
                               struct.unpack_from("<I", rec, 10)[0]))

    def volume_id(self):
        return self.sector(16)[40:72].decode("ascii", "replace").strip()


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        c = Cvm(p)
        fs = c.files()
        print(f"{os.path.basename(p)}  vol={c.volume_id()!r}  "
              f"header={'CVMH' if c.has_header else 'none'} base={c.base:#x}  "
              f"{len(fs)} files")
