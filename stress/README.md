# Stress harness

Fills all 2,015 script records with traceable placeholders (`R0421 lorem…`)
and plays the result. The row number is embedded deliberately: generic filler
proves *something* rendered, a row number proves the *right* text rendered in
the *right* place.

```sh
python3 stress/make_placeholder.py     # -> stress/placeholder.json
./stress/bisect.sh <first> <last>      # build a subset, boot it, report liveness
./stress/probe.sh  <built.iso> <tag>   # boot an existing ISO, sample twice
```

**Status: passing.** All 2,015 records replaced, booted, and verified on
screen — `R1513 sed do eiusmod tempor…` and `R1517 incididunt ut labore…`
render in the briefing with the correct speaker portraits, correct order and
automatic word wrap. 59.9 fps, GS 76%.

## The bug it caught, and why the obvious diagnosis was wrong

A full build hung at boot: black screen, GS 2-3%, unresponsive, while an
unmodified build ran at 59.9 fps. Every early instinct pointed at the text —
and every one of them was wrong:

- **Not compression.** Round-trips through the reference decoder byte-exact.
- **Not slot arithmetic.** No record's write span reaches the next record's id.
- **Not the data reaching the game.** With the hung build running, the
  decompressed image was located in EE RAM at `0x00585e60` and compared
  against the patched file: **all 316,988 bytes identical**. The game had
  exactly the bytes intended and still hung.
- **Not ASCII-vs-Japanese**, and **not length** — padding every replacement
  to its exact original byte count still hung.

The bisect looked impossible and that was the real clue:

| edits | result |
|---|---|
| record 0 alone | renders |
| records 1–66 | renders |
| **records 0–66** | **hangs, 3/3** |
| records 100–166 (same count) | renders |

`{0..66}` is byte-for-byte the union of two builds that each boot. No record
can explain that. Re-ordered by **compressed size**, the table is perfectly
separable — every case ≥196,602 bytes boots, every case ≤196,562 hangs,
whichever records changed. Confirmed by prediction in an unrelated region of
the file: 196,610 boots, 196,516 hangs.

## The cause

`isopatch` wrote the shorter stream but left the ISO directory record
claiming the **original 198,240 bytes**, zero-padding the tail. CRI's
streaming reader feeds the decompressor sector by sector and only reports the
read complete once the recorded length is consumed, so the game waited
forever for sectors the shortened stream never asked for.

The stack, recovered from a savestate, says it plainly:

```
_start → main → MAIN_Init → main_InitGui → UTL_NwIsEnd
       → CRS_NwGetStat → decReadServer → CRS_NwRdRingBuf → nwRdRingBufAdx
```

Not a text path at all — a file read that never ends. **Fix: shrink the
recorded length with the data** (`tools/isopatch.py` now writes both the
little- and big-endian copies in the directory record).

## What to take from this

The decisive move was not more bisecting — it was getting the **program
counter and call stack**. PINE cannot report PC, but a savestate carries the
full CPU state and all 32 MB of RAM; `tools/p2s.py`, `tools/stack.py` and
`tools/symbols.py` turn one into a labelled call stack in a few seconds. That
took minutes and named the subsystem exactly, after hours of bisection had
produced a table that could not be true.

When a bisect yields a contradiction — A works, B works, A∪B fails — stop
bisecting. The variable is not in the set you are splitting.
