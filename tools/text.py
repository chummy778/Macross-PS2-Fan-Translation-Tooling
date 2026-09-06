#!/usr/bin/env python3
"""Every translatable string in BOOTDAT, in one model.

The file holds two formats and it is easy to ship a "complete" translation
that silently misses the second one:

* **records** -- `[6 ASCII digits][Shift-JIS]\\x00`, dialogue and briefings.
* **pool strings** -- an offset table followed by NUL-terminated strings:
  stage titles, menus, save/load prompts.

A full record replacement leaves every stage title card in Japanese, which
is exactly the kind of gap that only shows up when someone plays past the
first mission. Both are exposed here as `Unit`s with a stable id.

Both are written **in place**: the pool's offsets point at string *starts*,
which do not move, so a replacement is safe as long as it fits the byte
budget. Japanese costs two bytes per character and ASCII one, so English at
roughly twice the character count still fits.
"""
import struct
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import script
import strtab


class Unit:
    __slots__ = ("uid", "kind", "offset", "budget", "text", "speaker")

    # A record id is six characters and every one of them is load-bearing:
    #
    #     bytes 0-1  display priority   (STR_GetDispPri)
    #     byte  2    caption attribute  (STR_GetDispAttr)
    #     bytes 3-5  voice index        (STR_GetIdx, spaces mean zero)
    #
    # Byte 2 is what decides whether a spoken line also appears on screen.
    # `STR_GetDispAttr` returns 1/2/3 for '1'/'2'/'3' and 0 for anything
    # else, and `NAVI_DispNarrationExec` draws the caption only when bit 0
    # of that value is set. So '1' means captioned and '0' means voice only.

    def __init__(self, uid, kind, offset, budget, text, speaker):
        self.uid = uid
        self.kind = kind          # "record" | "string"
        self.offset = offset      # byte offset of the text itself
        self.budget = budget      # bytes a replacement may occupy
        self.text = text
        self.speaker = speaker    # 6-digit id, or the pool it belongs to

    @property
    def needs_translation(self):
        return any(c > "\x7f" for c in self.text)

    @property
    def captioned(self):
        """True if this line is shown on screen as well as spoken."""
        return self.kind == "record" and self.speaker[2] in "13"

    @property
    def id_offset(self):
        """Offset of the 6-character id, which sits just before the text."""
        return self.offset - 6


def _trailing_nuls(blob, end, limit):
    n = 0
    while end + n < len(blob) and blob[end + n] == 0 and n < limit:
        n += 1
    return n


def units(blob):
    out = []
    rec_starts = {}
    for r in script.parse(blob):
        # Keyed by file offset, not by position in the list. An index shifts
        # the moment the parser learns to see a record it used to miss, which
        # would silently re-point every line of an existing translation at the
        # wrong string. The offset is a property of the game, not of the tool.
        uid = f"rec-{r.offset - 6:06x}"
        rec_starts[r.offset - 6] = uid
        out.append(Unit(uid, "record", r.offset, r.slot_len, r.text, r.rid))

    for base, end, strs in strtab.pools(blob):
        n = struct.unpack_from("<I", blob, base)[0] // 4
        offs = struct.unpack_from(f"<{n}I", blob, base)
        seen = set()
        for i, (o, s) in enumerate(zip(offs, strs)):
            start = base + o
            if start in rec_starts or not s:
                continue          # already exposed as a record
            # A table may point several entries at one string. That is one
            # string, not several: exposing it twice would let a translator
            # write two different English texts to the same bytes, and the
            # second would silently win. Keep the first entry's id.
            if start in seen:
                continue
            seen.add(start)
            raw = len(s.encode("shift_jis"))
            # room is the string plus the NULs before the next string starts
            nxt = min((base + p for p in offs if base + p > start), default=end)
            budget = raw + _trailing_nuls(blob, start + raw, nxt - start - raw)
            out.append(Unit(f"str-{base:06x}-{i:03d}", "string",
                            start, budget, s, f"pool:{base:#08x}"))
    out.sort(key=lambda u: u.offset)
    return out


def read_at(blob, us):
    """{uid: text} read from `blob` at the offsets of `us`.

    `units()` cannot be used to check a *translated* file: the record parser
    keeps only entries containing Japanese, which is how it tells records
    apart from binary data that happens to decode, so every successfully
    translated line would look like it had vanished. Verification therefore
    reads back at the offsets the original file established.
    """
    out = {}
    for u in us:
        end = blob.find(b"\x00", u.offset, u.offset + u.budget)
        if end < 0:
            end = u.offset + u.budget
        try:
            out[u.uid] = blob[u.offset:end].decode("shift_jis")
        except UnicodeDecodeError:
            out[u.uid] = None
    return out


def set_captions(blob, wanted, ref=None):
    """Turn captions on or off per record: {uid: bool}.

    This is a one-byte edit per line and needs no code patch -- the engine
    already renders the caption, times it to the voice clip via
    `SND_GetVoicePlayTime`, and holds it for exactly that long. The developers
    built the whole thing and then marked most in-mission radio lines as voice
    only. Flipping byte 2 of the id turns them back on.

    Nothing else reads byte 2, so this does not disturb the voice lookup or
    the display priority.

    Pass `ref` -- the unit list parsed from the *untranslated* file -- when
    `blob` has already been translated. The record parser keeps only entries
    containing Japanese (that is how it tells records from binary data that
    happens to decode), so re-parsing a translated file silently loses every
    line that has been done, and those are exactly the lines a translator
    most wants captioned.
    """
    b = bytearray(blob)
    by_id = {u.uid: u for u in (ref if ref is not None else units(blob))}
    changed = 0
    for uid, on in wanted.items():
        u = by_id.get(uid)
        if u is None or u.kind != "record":
            continue
        if u.captioned == bool(on):
            continue
        b[u.id_offset + 2] = ord("1") if on else ord("0")
        changed += 1
    return bytes(b), changed


def apply(blob, edits):
    """Write {uid: replacement} in place. Raises if one will not fit."""
    b = bytearray(blob)
    by_id = {u.uid: u for u in units(blob)}
    written = 0
    for uid, new in edits.items():
        u = by_id.get(uid)
        if u is None:
            raise KeyError(f"no such string: {uid}")
        data = new.encode("shift_jis", "strict")
        if len(data) > u.budget:
            raise ValueError(f"{uid}: {len(data)} bytes needs "
                             f"{len(data) - u.budget} more than its "
                             f"{u.budget}-byte slot")
        b[u.offset:u.offset + len(data)] = data
        for i in range(u.offset + len(data), u.offset + u.budget):
            b[i] = 0
        written += 1
    return bytes(b), written


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import gamedata

    if len(sys.argv) < 2:
        gamedata.usage(__file__)
    us = units(gamedata.script_blob(sys.argv[1]))
    todo = [u for u in us if u.needs_translation]
    print(f"{len(us)} translatable strings "
          f"({sum(1 for u in us if u.kind == 'record')} records, "
          f"{sum(1 for u in us if u.kind == 'string')} pool strings)")
    print(f"{len(todo)} contain Japanese, "
          f"{sum(len(u.text) for u in todo)} characters")
    print(f"{sum(u.budget for u in us)} bytes of writable slot")
