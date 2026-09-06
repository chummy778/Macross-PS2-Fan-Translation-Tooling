#!/usr/bin/env python3
"""Find the offset-table string pools in BOOTDAT.

There are *two* text formats in this file, and the record parser only sees
one of them. The other is the classic layout:

    [u32 off0][u32 off1]...[NUL-terminated Shift-JIS strings]

with offsets relative to the first table entry, so `off0` is also the table's
own length. That is what holds the stage names, which are not records and
survive a full record replacement untouched -- which is how the gap was
noticed in the first place.

These strings are referenced *by offset*, so unlike records they cannot be
edited in place at a different length without rewriting the table -- but the
table sits right there, which makes that cheap.

    python3 tools/strtab.py [file]
"""
import struct
import os
import sys

JP = set(range(0x81, 0xA0)) | set(range(0xE0, 0xF0))


def _string_at(d, o):
    e = d.find(b"\x00", o)
    if e < 0 or e - o > 200:
        return None
    raw = d[o:e]
    if not raw:
        return ""
    try:
        return raw.decode("shift_jis")
    except UnicodeDecodeError:
        return None


def pools(d, min_entries=4):
    """Every plausible [offsets][strings] pool, as (base, end, [strings]).

    **Offsets are not sorted.** A table may point several of its entries at
    the same string, and it may point back at a string it already used, so
    the list dips. Requiring `offs == sorted(offs)` looks like a cheap
    sanity check and is in fact a content assumption: it throws away every
    pool that reuses a string, which here is most of them -- 1,368 runs and
    about 5,930 characters of live text, including the mission objectives.

    What actually holds, and is checked instead:

    * `off0` is the table's own byte length, so the first string starts
      immediately after the table;
    * every offset points into the string area, never back into the table;
    * every offset lands on a string *start* -- the byte before it is the
      NUL that ended the previous string. This is the structural invariant
      that sortedness was standing in for, and it is much stronger.
    """
    out = []
    covered = set()
    for base in range(0, len(d) - 16, 4):
        if base in covered:
            continue
        first, = struct.unpack_from("<I", d, base)
        # off0 must be the table's own length: a whole number of entries,
        # landing exactly on the first string.
        if first < min_entries * 4 or first % 4 or base + first >= len(d):
            continue
        n = first // 4
        offs = struct.unpack_from(f"<{n}I", d, base)
        # every entry points into the string area, in bounds
        if any(o < first for o in offs):
            continue
        if any(base + o >= len(d) for o in offs):
            continue
        # every entry lands on a string start, not mid-string
        if any(o != first and d[base + o - 1] != 0 for o in offs):
            continue
        strs = [_string_at(d, base + o) for o in offs]
        if any(s is None for s in strs):
            continue
        if sum(1 for s in strs if s) < min_entries:
            continue
        if not any(any(c > "\x7f" for c in s) for s in strs):
            continue          # want real text, not a table of empty strings
        # unsorted, so the end is the furthest string, not the last entry
        last = max(range(len(offs)), key=lambda i: offs[i])
        end = base + offs[last] + len(strs[last].encode("shift_jis")) + 1
        out.append((base, end, strs))
        covered.update(range(base, end))
    return out


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import gamedata

    if len(sys.argv) < 2:
        gamedata.usage(__file__)
    d = gamedata.script_blob(sys.argv[1])
    ps = pools(d)
    total = sum(len(s) for _, _, ss in ps for s in ss)
    print(f"{len(ps)} string pools, "
          f"{sum(len(ss) for _, _, ss in ps)} strings, {total} characters")
    for base, end, ss in ps:
        shown = " | ".join(s for s in ss[:4] if s)
        print(f"  {base:#08x}..{end:#08x}  {len(ss):>4} strings   {shown[:64]}")
