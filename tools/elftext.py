#!/usr/bin/env python3
"""The Japanese still left in the executable.

`BOOTDAT.CMP` holds the game's script. It does not hold the *system*
messages -- memory card prompts, save and load results, HDD errors, joystick
calibration -- which live as plain Shift-JIS in `SLPM_654.05` itself. A
player meets them before the first mission, which is why the game still
looked half-translated long after the script was done.

Finding them needs a strict test. A byte-range scan for Shift-JIS lead bytes
"finds" thousands of hits in this file and every one of them is a float or a
pointer that happens to decode; that mistake has been made twice on this
project already. What separates real prose from noise is **hiragana
density**: a genuine Japanese sentence is dense in the kana range, and
binary data is not.

Strings are patched **in place**, so a replacement must fit the original
string plus the NUL padding that follows it -- and must leave one byte for
its own terminator, exactly as in `text.py`.

    python3 tools/elftext.py "Macross (Japan).iso"
"""
import os
import sys

MIN_JP = 6          # at least this many non-ASCII characters
MIN_HIRA = 0.40     # at least this share of them hiragana


class Str:
    __slots__ = ("uid", "offset", "budget", "text")

    def __init__(self, offset, budget, text):
        self.uid = f"elf-{offset:06x}"
        self.offset = offset
        self.budget = budget
        self.text = text


def _budget(d, off, raw):
    """The string plus the NUL run that follows it."""
    e = off + len(raw)
    n = 0
    while e + n < len(d) and d[e + n] == 0:
        n += 1
    return len(raw) + n


def strings(d):
    """Every genuine Japanese system message in the ELF image."""
    out = []
    i = 0
    while i < len(d):
        j = d.find(b"\x00", i)
        if j < 0:
            break
        raw = d[i:j]
        if 8 <= len(raw) <= 400:
            try:
                t = raw.decode("shift_jis")
            except UnicodeDecodeError:
                t = None
            if t:
                jp = [c for c in t if c > "\x7f"]
                hira = sum(1 for c in t if "ぁ" <= c <= "ん")
                if len(jp) >= MIN_JP and hira / max(1, len(jp)) >= MIN_HIRA:
                    out.append(Str(i, _budget(d, i, raw), t))
        i = j + 1
    return out


def apply(d, edits):
    """Write {uid: replacement} into the ELF image, in place."""
    b = bytearray(d)
    by = {s.uid: s for s in strings(d)}
    n = 0
    for uid, new in edits.items():
        s = by.get(uid)
        if s is None:
            continue                     # not an ELF string; someone else's
        data = new.encode("shift_jis", "strict")
        if len(data) >= s.budget:        # one byte belongs to the terminator
            raise ValueError(f"{uid}: {len(data)} bytes does not fit the "
                             f"{s.budget}-byte slot (1 byte is the NUL)")
        b[s.offset:s.offset + len(data)] = data
        for k in range(s.offset + len(data), s.offset + s.budget):
            b[k] = 0
        n += 1
    return bytes(b), n


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import gamedata
    if len(sys.argv) < 2:
        gamedata.usage(__file__)
    d = open(gamedata.elf_path(sys.argv[1]), "rb").read()
    ss = strings(d)
    print(f"{len(ss)} Japanese system strings, "
          f"{sum(len(s.text) for s in ss)} characters, "
          f"{sum(s.budget for s in ss)} bytes of slot")
