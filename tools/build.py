#!/usr/bin/env python3
"""Build a patched disc image from the translation.

    python3 tools/build.py "Macross (Japan).iso" "Macross (EN).iso"
    python3 tools/build.py in.iso out.iso --csv work/workbook.csv
    python3 tools/build.py in.iso out.iso --subtitles

Translations come from `translation/english.json`; a workbook CSV, if given,
takes precedence line by line, so a translator can try edits without
committing them first.

`--subtitles` additionally captions the in-mission radio dialogue, which the
game speaks but does not display. That is a one-byte edit per line, not a
code patch -- see `tools/text.py`. Individual lines can be overridden with
the workbook's `caption` column.

The source image is opened read-only and never written -- the output is a
copy. Every replacement is checked against its byte budget before anything
is built, so an over-long line is a clear error naming the line, not a
truncated sentence discovered in-game.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
import cvmexpand
import isopatch
import text as gametext
import verify
from make_workbook import CRICMP, ROOT, need_cricmp, script_blob


TRUE = {"1", "on", "yes", "true", "y"}
FALSE = {"0", "off", "no", "false", "n"}


def load_edits(english_paths, csv_path):
    """(text edits, caption overrides) from English layers and a CSV.

    `english_paths` is a list, applied in order, each layer overriding the
    one before. That is how the machine translation is kept separate from
    the hand-checked UI strings instead of being merged into them: the
    baseline ships on its own, and `english-mtl.json` layers on top only
    when the user asks for it.
    """
    if isinstance(english_paths, str):
        english_paths = [english_paths]
    edits, caps = {}, {}
    for english_path in english_paths:
        if not os.path.exists(english_path):
            continue
        for uid, e in json.load(open(english_path, encoding="utf-8")).items():
            if e.get("en"):
                edits[uid] = e["en"]
            if "caption" in e:
                caps[uid] = bool(e["caption"])
    if csv_path:
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("english", "").strip():
                    edits[row["id"]] = row["english"]
                v = (row.get("caption") or "").strip().lower()
                if v in TRUE:
                    caps[row["id"]] = True
                elif v in FALSE:
                    caps[row["id"]] = False
    return edits, caps


def check_budgets(blob, edits):
    by_id = {u.uid: u for u in gametext.units(blob)}
    problems = []
    for uid, s in edits.items():
        u = by_id.get(uid)
        if u is None:
            problems.append(f"  {uid}: no such string in this image")
            continue
        try:
            n = len(s.encode("shift_jis"))
        except UnicodeEncodeError as e:
            problems.append(f"  {uid}: {e.reason} -- cannot be encoded "
                            f"(Shift-JIS only): {s[:40]!r}")
            continue
        if n > u.budget:
            problems.append(f"  {uid}: {n} bytes, {n - u.budget} over the "
                            f"{u.budget}-byte slot: {s[:60]!r}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iso")
    ap.add_argument("out")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--english", action="append", metavar="JSON",
                    help="English layer; repeatable, later layers win. "
                         "Defaults to translation/english.json.")
    ap.add_argument("--mtl", action="store_true",
                    help="also apply translation/english-mtl.json, the "
                         "machine translation of the full script")
    ap.add_argument("--subtitles", action="store_true",
                    help="also caption the spoken in-mission radio dialogue")
    args = ap.parse_args()

    if os.path.abspath(args.iso) == os.path.abspath(args.out):
        sys.exit("refusing to write over the source image")

    ok, lines = verify.check(args.iso)
    print("\n".join(lines))
    if not ok:
        sys.exit("this is not the supported image; refusing to patch")

    need_cricmp()
    before = os.path.getsize(args.iso)
    blob = script_blob(args.iso)
    layers = args.english or [os.path.join(ROOT, "translation/english.json")]
    if args.mtl:
        layers.append(os.path.join(ROOT, "translation/english-mtl.json"))
    edits, caps = load_edits(layers, args.csv)
    if not edits and not (caps or args.subtitles):
        sys.exit("no translated lines found -- nothing to build")

    problems = check_budgets(blob, edits)
    if problems:
        print(f"\n{len(problems)} line(s) will not fit:")
        print("\n".join(problems[:40]))
        sys.exit("nothing was written")

    patched, n = gametext.apply(blob, edits)

    original = gametext.units(blob)
    wanted = {}
    if args.subtitles:
        wanted = {u.uid: True for u in original if u.kind == "record"}
    wanted.update(caps)                       # explicit per-line wins
    patched, captioned = gametext.set_captions(patched, wanted, ref=original)
    work = os.path.join(ROOT, "work")
    os.makedirs(work, exist_ok=True)
    dec, cmp_ = os.path.join(work, "_patched.bin"), os.path.join(work, "_patched.cmp")
    open(dec, "wb").write(patched)
    subprocess.run([CRICMP, "enc", dec, cmp_], check=True,
                   stdout=subprocess.DEVNULL)

    if os.path.exists(args.out):
        os.remove(args.out)
    shutil.copy2(args.iso, args.out)
    data = open(cmp_, "rb").read()

    # The script's 97 sectors are not always enough. Translating the short,
    # repetitive lines first makes the file *grow*, because those lines cost
    # almost nothing compressed and their English replacements are novel. When
    # that happens, rebuild the container with room to spare rather than
    # asking the translator to write shorter sentences.
    cap = cvmexpand.allocation(args.out, "JPN.CVM", "BOOTDAT.CMP")[0]
    if len(data) > cap:
        room = max(len(data), len(patched) + isopatch.SECTOR)
        cap = cvmexpand.expand(args.out, "JPN.CVM", "BOOTDAT.CMP", room)
        print(f"\nscript outgrew its {198656}-byte slot; rebuilt JPN.CVM with "
              f"{cap} bytes for it ({cap // isopatch.SECTOR} sectors)")
    off, cap = isopatch.patch(args.iso, args.out, "JPN.CVM", "BOOTDAT.CMP", data)

    # Prove it: read the file back out of the finished image, decompress it
    # with the reference decoder, and confirm the strings are really there.
    back = script_blob(args.out, cache=os.path.join(work, "_check.cmp"))
    if back != patched:
        sys.exit("the patched image does not read back as built")
    got = gametext.read_at(back, gametext.units(blob))
    wrong = [k for k, v in edits.items() if got.get(k) != v]
    if wrong:
        sys.exit(f"{len(wrong)} lines did not survive the round trip, "
                 f"e.g. {wrong[:3]}")

    assert os.path.getsize(args.iso) == before, "source image was modified"
    head = cap - len(data)
    print(f"\n{n} lines written, {len(data)} bytes compressed of {cap} "
          f"available -- {head} bytes spare")
    if captioned:
        print(f"{captioned} spoken radio lines switched to captioned")
    print("all lines verified by reading them back out of the finished image")
    print(f"{args.out}")


if __name__ == "__main__":
    main()
