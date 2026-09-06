#!/usr/bin/env python3
"""Write a file back into the game ISO, through the nested containers.

The script lives three layers deep:

    disc ISO 9660  ->  JPN.CVM  ->  (CVMH header, then ISO 9660 at +0x1800)
                                ->  BOOTDAT.CMP

Because a CVM is just an ISO at a fixed offset, both layers can be walked
with the same directory-record parser, and the result is one absolute byte
offset into the outer image. A replacement can be written straight in with
no repacking so long as it fits the space the file was *allocated* -- whole
sectors, up to wherever the next file begins -- which is usually a little
more than its recorded length.

The source image is never touched: callers pass an output path, which is
copied from the original first.
"""
import os
import shutil
import struct
import sys

SECTOR = 2048
CVM_HEADER = 0x1800


def _walk(read_sector, lba, length, want, prefix="", rec_out=None):
    buf = b"".join(read_sector(lba + i)
                   for i in range((length + SECTOR - 1) // SECTOR))
    off = 0
    while off < len(buf):
        rlen = buf[off]
        if rlen == 0:
            off = (off // SECTOR + 1) * SECTOR
            if off >= len(buf):
                return None
            continue
        ex_lba = struct.unpack_from("<I", buf, off + 2)[0]
        ex_len = struct.unpack_from("<I", buf, off + 10)[0]
        flags = buf[off + 25]
        idl = buf[off + 32]
        name = buf[off + 33:off + 33 + idl].decode("ascii", "replace")
        if name not in ("\x00", "\x01"):
            clean = name.split(";")[0].upper()
            if flags & 2:
                hit = _walk(read_sector, ex_lba, ex_len, want,
                            prefix + clean + "/", rec_out)
                if hit:
                    return hit
            elif prefix + clean == want:
                if rec_out is not None:
                    # byte offset of this directory record, so its recorded
                    # length can be corrected after a shorter file is written
                    rec_out.append(lba * SECTOR + off)
                return ex_lba, ex_len
        off += rlen
    return None


def listing(f, base):
    """[(lba, length, path)] for every file in the ISO whose sector 0 is at
    `base`, so a file's real allocation can be measured from where the next
    one starts."""
    def read_sector(n):
        f.seek(base + n * SECTOR)
        return f.read(SECTOR)
    out = []

    def walk(lba, length, prefix=""):
        buf = b"".join(read_sector(lba + i)
                       for i in range((length + SECTOR - 1) // SECTOR))
        off = 0
        while off < len(buf):
            rlen = buf[off]
            if rlen == 0:
                off = (off // SECTOR + 1) * SECTOR
                if off >= len(buf):
                    return
                continue
            ex_lba = struct.unpack_from("<I", buf, off + 2)[0]
            ex_len = struct.unpack_from("<I", buf, off + 10)[0]
            flags = buf[off + 25]
            idl = buf[off + 32]
            name = buf[off + 33:off + 33 + idl].decode("ascii", "replace")
            if name not in ("\x00", "\x01"):
                clean = name.split(";")[0].upper()
                if flags & 2:
                    out.append((ex_lba, ex_len, prefix + clean + "/"))
                    walk(ex_lba, ex_len, prefix + clean + "/")
                else:
                    out.append((ex_lba, ex_len, prefix + clean))
            off += rlen

    pvd = read_sector(16)
    rec = pvd[156:190]
    walk(struct.unpack_from("<I", rec, 2)[0],
         struct.unpack_from("<I", rec, 10)[0])
    return out


def capacity(f, base, lba, length):
    """Bytes usable at `lba` without disturbing anything after it.

    A file owns whole sectors, and the next extent does not always begin
    immediately after the last one it needs. Using the recorded length as the
    limit throws that away -- here it is 416 bytes, which is the difference
    between a translation building and not."""
    starts = [l for l, _, _ in listing(f, base) if l > lba]
    end = min(starts) if starts else lba + (length + SECTOR - 1) // SECTOR
    return (end - lba) * SECTOR


def find(f, base, want, rec_out=None):
    """(lba, length) of `want` inside the ISO whose sector 0 is at `base`."""
    def read_sector(n):
        f.seek(base + n * SECTOR)
        return f.read(SECTOR)
    pvd = read_sector(16)
    if pvd[1:6] != b"CD001":
        raise ValueError(f"no ISO 9660 volume descriptor at {base:#x}")
    rec = pvd[156:190]
    hit = _walk(read_sector, struct.unpack_from("<I", rec, 2)[0],
                struct.unpack_from("<I", rec, 10)[0], want.upper(),
                rec_out=rec_out)
    if not hit:
        raise KeyError(f"{want} not found in the image at {base:#x}")
    return hit


def locate(image, cvm_name, inner_name):
    """Absolute (offset, capacity, directory-record offset) of a file.

    `cvm_name=None` addresses a file on the outer disc rather than one
    inside a container -- that is how the executable is reached, since the
    system messages the game shows before the first mission live in
    `SLPM_654.05` and not in `BOOTDAT.CMP`.
    """
    with open(image, "rb") as f:
        if cvm_name is None:
            rec = []
            lba, length = find(f, 0, inner_name, rec_out=rec)
            cap = capacity(f, 0, lba, length)
            return lba * SECTOR, cap, rec[0]
        cvm_lba, _ = find(f, 0, cvm_name)
        cvm_base = cvm_lba * SECTOR + CVM_HEADER
        rec = []
        lba, length = find(f, cvm_base, inner_name, rec_out=rec)
        cap = capacity(f, cvm_base, lba, length)
        return cvm_base + lba * SECTOR, cap, cvm_base + rec[0]


def patch(src_image, out_image, cvm_name, inner_name, data):
    if os.path.abspath(src_image) == os.path.abspath(out_image):
        raise ValueError("refusing to write over the source image")
    if not os.path.exists(out_image):
        shutil.copy2(src_image, out_image)
    off, cap, rec = locate(out_image, cvm_name, inner_name)
    if len(data) > cap:
        raise ValueError(
            f"{inner_name}: {len(data)} bytes will not fit the {cap} bytes "
            f"allocated to it ({len(data) - cap} over). The uncompressed "
            f"edits fit their slots; it is the *compressed* file that is too "
            f"big. Shorten a few lines, or reuse wording -- this codec pays "
            f"for novelty.")
    with open(out_image, "r+b") as f:
        f.seek(off)
        f.write(data)
        f.write(b"\x00" * (cap - len(data)))   # leave the tail clean
        # The recorded length MUST follow the data down. CRI's streaming
        # reader feeds the decompressor sector by sector and only reports the
        # read finished once the recorded length is consumed; leaving it at
        # the original size makes the game wait forever in UTL_NwIsEnd for
        # sectors the (now shorter) stream never asks for. This is what made
        # every sufficiently-shrunk build hang at a black screen.
        f.seek(rec + 10)
        f.write(struct.pack("<I", len(data)))            # little-endian
        f.write(struct.pack(">I", len(data)))            # and big-endian copy
    return off, cap


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("usage: isopatch.py <src.iso> <out.iso> <CVM> <INNER> <payload>")
        sys.exit(1)
    src, out, cvm, inner, payload = sys.argv[1:]
    blob = open(payload, "rb").read()
    off, cap = patch(src, out, cvm, inner, blob)
    print(f"{inner}: wrote {len(blob)} bytes at {off:#x} (capacity {cap})")
