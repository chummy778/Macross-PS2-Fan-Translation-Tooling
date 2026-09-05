#!/usr/bin/env python3
"""Fill every script record with traceable placeholder text.

This is a stress test, not a translation. The point is to prove that all
2,015 records survive the whole pipeline -- edit, recompress, patch the ISO,
boot, render -- rather than only the handful reached by hand.

Every placeholder starts with its own unit id, e.g. "R0421 lorem ipsum
...". Generic filler would prove that *something* rendered; a row number
proves the *right* text rendered in the *right* place, which is exactly what
breaks silently when offsets or slot maths are wrong.

It covers **both** text formats via `tools/text.py` -- dialogue records and
the offset-table pools that hold stage titles and menus. Placeholding only
the records leaves every title card in Japanese and looks like success.

Sizing aims at ~1.9x the Japanese character count -- roughly what real
English costs -- and is then clamped to what the record's slot can hold, so
overflow is a build error rather than an unnoticed truncation.

    python3 stress/make_placeholder.py "Macross (Japan).iso" [out.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import text as gametext
from make_workbook import script_blob

LIPSUM = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua ut enim ad minim "
    "veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat duis aute irure dolor in reprehenderit voluptate"
).split()


def placeholder(tag, jp_chars, budget):
    target = min(budget, max(6, int(jp_chars * 1.9)))
    head = f"{tag} "
    if len(head) > target:
        return head.strip()[:target]
    out = head
    i = len(head)
    while len(out) < target:
        w = LIPSUM[i % len(LIPSUM)]
        if len(out) + len(w) + 1 > target:
            break
        out += w + " "
        i += 1
    return (out.strip() or head.strip())[:budget]


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: make_placeholder.py <game.iso> [out.json]')
    iso = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        HERE, "placeholder.json")
    blob = script_blob(iso)
    us = [u for u in gametext.units(blob) if u.needs_translation]
    edits = {}
    for n, u in enumerate(us):
        edits[u.uid] = placeholder(f"R{n:04d}", len(u.text), u.budget)
    with open(out_path, "w") as f:
        json.dump(edits, f, indent=0)
    used = sum(len(v) for v in edits.values())
    cap = sum(u.budget for u in us)
    print(f"{len(edits)} placeholders -> {out_path}")
    print(f"{used} of {cap} available bytes used ({used / cap:.0%})")


if __name__ == "__main__":
    main()
