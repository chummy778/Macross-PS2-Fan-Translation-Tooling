#!/bin/bash
# Boot an already-built ISO and sample liveness twice, late, so that a slow
# boot is not mistaken for a hang.
#
#   stress/probe.sh <built.iso> [tag]
set -uo pipefail
cd "$(dirname "$0")/.."
ISO="$1"; TAG="${2:-probe}"
BIN="${ARMSX2:-/Users/alon-m2/Downloads/ps2_hacking/tools/armsx2/ARMSX2-2.6.8.app/Contents/MacOS/ARMSX2}"
LOG="$HOME/Library/Application Support/ARMSX2/logs/emulog.txt"
mkdir -p work/shots
pkill -f ARMSX2 2>/dev/null; sleep 2; : > "$LOG" 2>/dev/null
nohup "$BIN" -batch -- "$ISO" >/tmp/probe.log 2>&1 &
START=$(date +%s)
for W in 45 80; do
  while [ "$(date +%s)" -lt "$(( START + W ))" ]; do sleep 2; done
  python3 - "$TAG" "$W" <<'PY'
import os, sys
sys.path.insert(0, "tools")
import shot
shot.STATES = os.path.expanduser("~/Library/Application Support/ARMSX2/sstates")
try:
    p, _ = shot.capture(f"work/shots/{sys.argv[1]}_{sys.argv[2]}.png", 12)
    n = os.path.getsize(p)
    print(f"    t={sys.argv[2]}s  {n:>7}B  {'HUNG' if n < 5000 else 'RENDERING'}")
except Exception as e:
    print(f"    t={sys.argv[2]}s  capture failed: {e}")
PY
done
grep PerfLog "$LOG" 2>/dev/null | tail -1 | sed 's/^/    /'
pkill -f ARMSX2 2>/dev/null
