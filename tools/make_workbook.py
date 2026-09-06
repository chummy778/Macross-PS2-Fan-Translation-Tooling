#!/usr/bin/env python3
"""Generate the translation workbook from the user's own copy of the game.

The repository deliberately ships **no game script**. The Japanese text is
the publisher's, so it is extracted on the translator's machine from their
own disc and never committed. What the repository does carry is
`translation/english.json` -- English and translator notes keyed by string
id, with no Japanese in it -- and this script seeds the workbook from it, so
existing work shows up alongside the lines still to do.

    python3 tools/make_workbook.py "Macross (Japan).iso"

Writes `work/workbook.csv`, which is gitignored. Edit it in any spreadsheet
(or `tools/editor.py`), then feed it to `tools/build.py`.

The `caption` column says whether a line is shown on screen as well as
spoken. Most in-mission radio dialogue ships as `off`; setting it to `on`
subtitles that line. `tools/build.py --subtitles` turns them all on at once.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import text as gametext
import verify
from gamedata import CRICMP, need_cricmp, script_blob  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
FIELDS = ["id", "kind", "speaker", "budget_bytes", "caption",
          "japanese", "english", "notes"]


def load_english(paths):
    """Merge English layers in order; later layers win.

    The machine translation lives in its own file so it never contaminates
    the hand-checked baseline. Seeding the workbook from both is opt-in.
    """
    if isinstance(paths, str):
        paths = [paths]
    out = {}
    for p in paths:
        if os.path.exists(p):
            out.update(json.load(open(p, encoding="utf-8")))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iso")
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "work/workbook.csv"))
    ap.add_argument("--english", action="append", metavar="JSON",
                    help="English layer to seed from; repeatable. "
                         "Defaults to translation/english.json.")
    ap.add_argument("--mtl", action="store_true",
                    help="also seed from translation/english-mtl.json")
    ap.add_argument("--all", action="store_true",
                    help="include strings that are already English")
    args = ap.parse_args()

    ok, lines = verify.check(args.iso)
    if not ok:
        print("\n".join(lines))
        sys.exit("this is not the supported image; refusing to extract")

    layers = args.english or [os.path.join(ROOT, "translation/english.json")]
    if args.mtl:
        layers.append(os.path.join(ROOT, "translation/english-mtl.json"))
    en = load_english(layers)
    us = gametext.units(script_blob(args.iso))
    if not args.all:
        us = [u for u in us if u.needs_translation]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        for u in us:
            e = en.get(u.uid, {})
            cap = e.get("caption", u.captioned)
            w.writerow({
                "id": u.uid, "kind": u.kind, "speaker": u.speaker,
                "budget_bytes": u.budget,
                "caption": "on" if cap else "off",
                "japanese": u.text,
                "english": e.get("en", ""), "notes": e.get("note", ""),
            })
    done = sum(1 for u in us if en.get(u.uid, {}).get("en"))
    print(f"{args.out}: {len(us)} strings, {done} already translated "
          f"({done / max(1, len(us)):.0%})")
    print("This file contains the game's Japanese script. Do not commit it.")


if __name__ == "__main__":
    main()
