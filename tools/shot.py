#!/usr/bin/env python3
"""Take a screenshot of a running PCSX2, entirely through PINE.

PINE has no screenshot opcode, but a PCSX2 save state is a zip that contains
a `Screenshot.png` of the moment it was taken. So: ask PINE to save a state,
then pull the PNG out of the resulting .p2s. Nothing touches the OS screen,
nothing else on the machine can appear in the capture, and it is fully
scriptable -- the same posture the FM Towns project used with Tsugaru's `SS`.

    python3 tools/shot.py out.png [slot]
"""
import glob
import os
import shutil
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from pine import Pine, PineError

STATES = os.path.expanduser("~/Library/Application Support/PCSX2/sstates")


def newest_state(before):
    """The .p2s written since `before`, waiting briefly for it to appear."""
    for _ in range(60):
        cands = [p for p in glob.glob(os.path.join(STATES, "*.p2s"))
                 if os.path.getmtime(p) > before - 1]
        if cands:
            newest = max(cands, key=os.path.getmtime)
            # let PCSX2 finish writing before we open it
            size = -1
            while size != os.path.getsize(newest):
                size = os.path.getsize(newest)
                time.sleep(0.2)
            return newest
        time.sleep(0.25)
    return None


def capture(out_png, slot=1):
    p = Pine()
    t0 = time.time()
    p.save_state(slot)
    state = newest_state(t0)
    if not state:
        raise RuntimeError(f"no save state appeared in {STATES}")
    with zipfile.ZipFile(state) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".png")]
        if not names:
            raise RuntimeError(f"{state} has no screenshot inside "
                               f"(contents: {z.namelist()[:5]})")
        with z.open(names[0]) as src, open(out_png, "wb") as dst:
            shutil.copyfileobj(src, dst)
    return out_png, state


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "shot.png"
    slot = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    try:
        png, state = capture(out, slot)
        print(f"{png}  ({os.path.getsize(png)} bytes) from {os.path.basename(state)}")
    except (PineError, RuntimeError) as e:
        print(f"failed: {e}")
        sys.exit(1)
