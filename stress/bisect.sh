#!/bin/bash
# Build an ISO with a subset of the placeholder edits applied, boot it, and
# report whether the game is alive.
#
#   stress/bisect.sh <game.iso> <first> <last>
#
# The subset is a slice of the placeholder set in file order. "Alive" is
# judged from the emulator's own PerfLog as well as a screenshot: a hung
# build sits at GS ~2% with a black screen, a working one renders at ~75%.
# A black screen alone is easy to mistake for a slow boot.
#
# Note what this tool could NOT find: the boot hang was a property of the
# whole file's compressed size, not of any record, so no slice isolated it.
# If the results here contradict each other, stop and read stress/README.md.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="$1"; LO=${2:-0}; HI=${3:-99999}
BIN="${ARMSX2:-/Users/alon-m2/Downloads/ps2_hacking/tools/armsx2/ARMSX2-2.6.8.app/Contents/MacOS/ARMSX2}"

python3 - "$SRC" "$LO" "$HI" <<'PY'
import json, sys, os
sys.path.insert(0, "tools")
import text as gametext
from make_workbook import script_blob
iso, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
blob = script_blob(iso)
edits = json.load(open("stress/placeholder.json"))
order = [u.uid for u in gametext.units(blob) if u.uid in edits]
subset = {u: edits[u] for u in order[lo:hi + 1]}
out, n = gametext.apply(blob, subset)
os.makedirs("work", exist_ok=True)
open("work/_bisect.bin", "wb").write(out)
print(f"  units {lo}..{hi}: {n} edits applied")
PY

tools/cricmp enc work/_bisect.bin work/_bisect.cmp >/dev/null 2>&1
rm -f build/bisect.iso; mkdir -p build
python3 tools/isopatch.py "$SRC" build/bisect.iso JPN.CVM BOOTDAT.CMP work/_bisect.cmp >/dev/null
exec stress/probe.sh "$PWD/build/bisect.iso" bisect
