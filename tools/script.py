#!/usr/bin/env python3
"""Read and write the game's script records inside a decompressed BOOTDAT.

Record layout, established in docs/FORMATS.md:

    [6 ASCII digits: speaker/voice id][Shift-JIS text]\\x00[NUL padding]

`0x0a` inside the text is a line break. Records sit in NUL-padded slots, so
the space actually available to a replacement is usually a little more than
the original text -- `slack` below measures that, and it is free capacity
that needs no pointer fixups.

Used as a library by the extractor, the builder and the stress harness.
"""
import os
import re
import sys

# A record id is six characters: three digits of category, then three that
# are either digits or SPACES. The spaces are not padding to be tidied away --
# `STR_GetIdx` explicitly tests byte 3 for 0x20 and yields index 0 for it, and
# the whole Global Report narration (660 records) uses that form. Matching
# only `[0-9]{6}` silently drops it, and the loss is invisible until someone
# plays the intro. The id must not be part of a longer number.
RECORD = re.compile(rb'(?<![0-9])([0-9]{3}[0-9 ]{3})([^\x00]{2,600})\x00')
JP = re.compile(r'[぀-ヿ一-鿿]')


class Record:
    __slots__ = ("index", "offset", "rid", "text", "raw_len", "slot_len")

    def __init__(self, index, offset, rid, text, raw_len, slot_len):
        self.index = index
        self.offset = offset          # offset of the text, after the id
        self.rid = rid                # 6-digit speaker/voice id
        self.text = text              # decoded Shift-JIS
        self.raw_len = raw_len        # bytes the original text occupies
        self.slot_len = slot_len      # bytes to the next record (incl. padding)

    @property
    def slack(self):
        """Spare bytes in the slot beyond the original text."""
        return self.slot_len - self.raw_len

    @property
    def budget(self):
        """Bytes a replacement may use without moving anything."""
        return self.slot_len


def parse(blob):
    """All records carrying Japanese, in file order."""
    hits = []
    for m in RECORD.finditer(blob):
        try:
            text = m.group(2).decode("shift_jis")
        except UnicodeDecodeError:
            continue
        if not JP.search(text):
            continue                  # ids also appear in binary data
        hits.append((m.start(), m.group(1).decode(), text, len(m.group(2))))

    out = []
    for i, (start, rid, text, raw) in enumerate(hits):
        text_off = start + 6
        # The usable slot is the text plus only the NUL padding that directly
        # follows it. Measuring to the next *record* instead would span
        # pointer tables and other data sitting between clusters of records --
        # that is not free space, and writing into it corrupts the file.
        end = text_off + raw
        pad = 0
        while end + pad < len(blob) and blob[end + pad] == 0:
            pad += 1
        out.append(Record(i, text_off, rid, text, raw, raw + pad))
    return out


def apply(blob, edits):
    """Write {record_index: replacement_text} into a copy of `blob`.

    Raises if a replacement will not fit its slot -- growing records needs the
    container's pointer tables rewritten, which is a separate problem.
    """
    b = bytearray(blob)
    recs = parse(blob)
    by_index = {r.index: r for r in recs}
    written = 0
    for idx, new_text in edits.items():
        r = by_index[idx]
        data = new_text.encode("shift_jis", "strict")
        if len(data) > r.budget:
            raise ValueError(
                f"record {idx} ({r.rid}): {len(data)} bytes needs "
                f"{len(data) - r.budget} more than the {r.budget}-byte slot")
        b[r.offset:r.offset + len(data)] = data
        for i in range(r.offset + len(data), r.offset + r.slot_len):
            b[i] = 0
        written += 1
    return bytes(b), written


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    import gamedata

    if len(sys.argv) < 2:
        gamedata.usage(__file__)
    recs = parse(gamedata.script_blob(sys.argv[1]))
    total = sum(r.raw_len for r in recs)
    slack = sum(r.slack for r in recs)
    print(f"{len(recs)} records, {len(set(r.rid for r in recs))} speaker ids")
    print(f"{sum(len(r.text) for r in recs)} characters, {total} text bytes")
    print(f"{slack} bytes of slot slack ({slack / max(1, total):.1%} spare)")
    for r in recs[:5]:
        print(f"  [{r.index:>4}] {r.rid} {r.raw_len:>3}b (+{r.slack} slack) {r.text[:44]}")
