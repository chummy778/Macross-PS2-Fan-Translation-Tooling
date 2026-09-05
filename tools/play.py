#!/usr/bin/env python3
"""Drive the game's controller from a script, over PINE.

`padRead` refills `g_pad_buf` every frame, so a single write is always lost.
Holding a button therefore means writing the same value in a tight loop for
as long as the press should last. Reading the buffer back is not a check --
it always reads `ff ff` for exactly this reason. Check the screen instead.

Buttons are ACTIVE LOW.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tools"))
from pine import Pine

PAD = 0x007B8A00
B1 = {"select": 0, "l3": 1, "r3": 2, "start": 3,
      "up": 4, "right": 5, "down": 6, "left": 7}
B2 = {"l2": 0, "r2": 1, "l1": 2, "r1": 3,
      "triangle": 4, "circle": 5, "cross": 6, "square": 7}


def press(p, name, hold=0.35):
    """Hold one button down for `hold` seconds."""
    b1, b2 = 0xFF, 0xFF
    if name in B1:
        b1 &= ~(1 << B1[name]) & 0xFF
    elif name in B2:
        b2 &= ~(1 << B2[name]) & 0xFF
    else:
        raise KeyError(name)
    end = time.time() + hold
    while time.time() < end:
        p.write8(PAD + 2, b1)
        p.write8(PAD + 3, b2)
    p.write8(PAD + 2, 0xFF)
    p.write8(PAD + 3, 0xFF)


if __name__ == "__main__":
    p = Pine()
    for name in sys.argv[1:]:
        press(p, name)
        time.sleep(0.4)
