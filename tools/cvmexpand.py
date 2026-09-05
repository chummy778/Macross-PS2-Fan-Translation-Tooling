#!/usr/bin/env python3
"""Give a file inside a CVM more room, by rebuilding and relocating the CVM.

Why this is needed: `BOOTDAT.CMP` is allocated 97 sectors and `JPN.CVM` is
packed solid -- zero spare bytes, the container is exactly its declared
volume plus the 0x1800 header. So any build whose recompressed script comes
out larger than 198,656 bytes simply cannot be written in place, and that is
not a rare corner: translating the short, highly repetitive lines first
*grows* the file, because those lines cost almost nothing compressed while
their English replacements are novel.

The disc makes the fix easy. `ETC.CVM` is 199 MB of zeros, is absent from
`0FLIST.DIR`, and nothing opens it. So the rebuilt CVM goes there and the
directory records are repointed. Inside the CVM the layout is equally
friendly: the volume descriptor, both path tables and the root directory all
sit at sectors 16-21, below the first file at sector 22, and there are no
subdirectories -- so widening a file means shifting the sectors after it and
renumbering file extents, with no metadata to relocate.

Everything ISO 9660 stores twice (extent, length, volume size) is written in
both byte orders; missing one of those is a silent corruption that only
shows up on real hardware.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import isopatch

SECTOR = isopatch.SECTOR
CVM_HEADER = isopatch.CVM_HEADER
CVMH_SIZE = 0x20          # big-endian total byte size of the .CVM


def _records(buf):
    """(offset, name) of every directory record in a directory extent."""
    off = 0
    while off < len(buf):
        rlen = buf[off]
        if rlen == 0:
            off = (off // SECTOR + 1) * SECTOR
            if off >= len(buf):
                return
            continue
        idl = buf[off + 32]
        name = buf[off + 33:off + 33 + idl].decode("ascii", "replace")
        yield off, name.split(";")[0].upper()
        off += rlen


def _set_extent(buf, off, lba):
    struct.pack_into("<I", buf, off + 2, lba)
    struct.pack_into(">I", buf, off + 6, lba)


def _set_length(buf, off, n):
    struct.pack_into("<I", buf, off + 10, n)
    struct.pack_into(">I", buf, off + 14, n)


def _get(buf, off):
    return (struct.unpack_from("<I", buf, off + 2)[0],
            struct.unpack_from("<I", buf, off + 10)[0])


def _root(inner):
    pvd = inner[16 * SECTOR:17 * SECTOR]
    rec = pvd[156:190]
    return (struct.unpack_from("<I", rec, 2)[0],
            struct.unpack_from("<I", rec, 10)[0])


def allocation(image, cvm_name, inner_name):
    """(bytes allocated, bytes the file records) for a file inside a CVM."""
    off, cap, _ = isopatch.locate(image, cvm_name, inner_name)
    with open(image, "rb") as f:
        cvm_lba, _n = isopatch.find(f, 0, cvm_name)
        lba, length = isopatch.find(f, cvm_lba * SECTOR + CVM_HEADER, inner_name)
    return cap, length


def expand(image, cvm_name, inner_name, want_bytes, spare_name="ETC.CVM"):
    """Ensure `inner_name` has at least `want_bytes` of allocation.

    Returns the new allocation in bytes. A no-op if it already fits.
    """
    cap, _ = allocation(image, cvm_name, inner_name)
    need = (want_bytes + SECTOR - 1) // SECTOR
    have = cap // SECTOR
    if need <= have:
        return cap
    extra = need - have

    with open(image, "r+b") as f:
        cvm_lba, cvm_len = isopatch.find(f, 0, cvm_name)
        spare_lba, spare_len = isopatch.find(f, 0, spare_name)
        f.seek(cvm_lba * SECTOR)
        cvm = bytearray(f.read(cvm_len))
        inner = bytearray(cvm[CVM_HEADER:])

        rlba, rlen = _root(inner)
        root = bytearray(inner[rlba * SECTOR:rlba * SECTOR + rlen])
        target = None
        for off, name in _records(root):
            if name == inner_name.upper():
                target = off
        if target is None:
            raise KeyError(f"{inner_name} not in {cvm_name}")
        t_lba, _t_len = _get(root, target)
        tail = t_lba + have          # first sector after the file's allocation

        # widen: insert zeroed sectors after the file, shift everything below
        inner = (inner[:tail * SECTOR]
                 + bytearray(extra * SECTOR)
                 + inner[tail * SECTOR:])
        for off, name in _records(root):
            lba, _l = _get(root, off)
            if lba >= tail:
                _set_extent(root, off, lba + extra)
        inner[rlba * SECTOR:rlba * SECTOR + rlen] = root

        pvd = bytearray(inner[16 * SECTOR:17 * SECTOR])
        vol = struct.unpack_from("<I", pvd, 80)[0] + extra
        struct.pack_into("<I", pvd, 80, vol)
        struct.pack_into(">I", pvd, 84, vol)
        inner[16 * SECTOR:17 * SECTOR] = pvd

        cvm = bytearray(cvm[:CVM_HEADER]) + inner
        struct.pack_into(">I", cvm, CVMH_SIZE, len(cvm))

        # relocate into the dummy container's space
        new_sectors = (len(cvm) + SECTOR - 1) // SECTOR
        if new_sectors > spare_len // SECTOR:
            raise ValueError(f"{spare_name} has no room for the rebuilt "
                             f"{cvm_name} ({new_sectors} sectors needed)")
        f.seek(spare_lba * SECTOR)
        f.write(cvm)
        f.write(b"\x00" * (new_sectors * SECTOR - len(cvm)))

        # repoint both outer directory records: the CVM to its new home, and
        # the dummy to what is left of the space, so nothing overlaps
        orlba, orlen = _root(_OuterView(f))
        f.seek(orlba * SECTOR)
        oroot = bytearray(f.read(orlen))
        for off, name in _records(oroot):
            if name == cvm_name.upper():
                _set_extent(oroot, off, spare_lba)
                _set_length(oroot, off, len(cvm))
            elif name == spare_name.upper():
                _set_extent(oroot, off, spare_lba + new_sectors)
                _set_length(oroot, off,
                            spare_len - new_sectors * SECTOR)
        f.seek(orlba * SECTOR)
        f.write(oroot)

    return expand_result(image, cvm_name, inner_name)


class _OuterView:
    """Just enough of a file object for _root() to read the outer PVD."""
    def __init__(self, f):
        self.f = f

    def __getitem__(self, sl):
        self.f.seek(sl.start)
        return self.f.read(sl.stop - sl.start)


def expand_result(image, cvm_name, inner_name):
    return allocation(image, cvm_name, inner_name)[0]


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: cvmexpand.py <image.iso> <CVM> <INNER>  "
                 "(reports the current allocation)")
    cap, length = allocation(*sys.argv[1:4])
    print(f"{sys.argv[3]}: {length} bytes recorded, {cap} allocated "
          f"({cap // SECTOR} sectors)")
