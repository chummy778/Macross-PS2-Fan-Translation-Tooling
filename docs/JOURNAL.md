# Journal

How this actually went, for whoever does the next one. Written to be useful
rather than flattering: the dead ends are here because they cost the most
time, and a list of things that worked would not have saved any of it.

## The one thing to take away

**When a bisection produces a contradiction, stop bisecting.**

A full-coverage stress build hung at boot. Bisecting the edits gave: record 0
alone boots, records 1–66 boot, records 0–66 hang — deterministically, three
runs each. Those three facts cannot all be about a record, because the
combined file is byte-for-byte the union of two files that each boot. That
contradiction was visible early and was worth acting on immediately; instead
it got treated as a puzzle to bisect harder, and hours went into it.

Sorted by **compressed size** rather than by which records changed, the same
data separated perfectly: everything ≥196,602 bytes booted, everything
≤196,562 hung. Predicted and confirmed in an unrelated part of the file.

The cause: the patcher wrote a shorter compressed stream but left the ISO
directory record claiming the original length. CRI's streaming reader feeds
the decompressor sector by sector and only reports the read complete once the
*recorded* length is consumed, so the game waited forever for sectors that
were never coming. The fix is three lines — shrink the recorded length with
the data, both the little- and big-endian copies.

Two lessons, in order of value:

1. The variable was not in the set being split. Bisection assumes the fault is
   a member of the set; when the results are inconsistent, that assumption is
   what is wrong.
2. **Get the program counter.** PINE cannot report it, but a save state
   carries the full CPU state and 32 MB of RAM. `tools/p2s.py` +
   `tools/stack.py` + `tools/symbols.py` turned one save state into:

   ```
   _start → main → MAIN_Init → main_InitGui → UTL_NwIsEnd
          → CRS_NwGetStat → decReadServer → CRS_NwRdRingBuf
   ```

   Not a text path at all — a file read that never ends. That took minutes and
   named the subsystem exactly. It should have been the *second* thing tried,
   not the twentieth.

## The second trap: measuring the wrong thing

A full placeholder build compressed to 145,676 bytes against the original's
198,240, so "will a translation fit the disc?" looked settled. It was not.
Two errors were stacked:

1. **Full coverage does not predict partial coverage.** Translating the short,
   repetitive lines first -- the menus, the acknowledgements, the twelve clock
   bearings that differ by one character -- makes the file **grow**. Those
   lines cost almost nothing compressed; their English replacements are novel
   text. That is the natural order to work in, and it is the worst case.
2. **Generated filler flatters the codec.** Lorem ipsum cycles sixty words. A
   real translation is full of distinct domain vocabulary. The gap is not huge
   at full coverage (150,522 vs 149,642) but it is exactly what decides
   whether a partial build fits, and a synthetic sweep never reproduced the
   failure that the real 290-string translation hit.

`stress/sizesweep.py` now measures both orderings *and* the real
`english.json`, and says which number to trust.

The fix was not to write shorter English. `JPN.CVM` has zero spare bytes, so
the container gets rebuilt: sectors inserted, file extents renumbered, the
volume size and the CVMH size updated, and the whole thing relocated into the
199 MB that `ETC.CVM` wastes on zeros. The disc had the room all along.

**If the data does not fit the disc, change the disc.** Asking a translator
to trim sentences to satisfy a compressor is solving the wrong problem.

## What paid off

**Searching first.** CRICMP is a custom CRI LZ codec; nothing stock touches
it. One GitHub search found `zeesworth/cricmp`, which names this exact game
and ships a *recompressor* as well as a decompressor. That is the whole
hardest problem, solved in minutes. The obvious routes were all dead — the
romhacking.net thread and the Shenmue Dojo link were unreachable, and the
ZenHAX regulars had concluded in 2022 that no tool existed.

**The debug symbols.** `SLPM_654.05` ships a full `.symtab` — 17,423 usable
symbols. `g_pad_buf`, `STR_GetIdx`, `STR_Init`, `padRead` were all found by
name instead of by searching. Check for this before doing anything clever; it
is rare and it changes the whole shape of the work.

**Reading `STR_GetIdx` instead of guessing at the format.** Its first
instruction is `lb $a1, 3($a0)` compared against `0x20` — *if byte 3 is a
space, the index is zero*. That one instruction says record ids are three
digits plus three characters that may be **spaces**. The extractor had been
matching `[0-9]{6}`, which finds 2,015 records and looks complete. It was
missing **660** — the entire Global Report narration, a 50% undercount. Ten
minutes of disassembly beat a day of pattern-guessing.

**The stress harness.** Replacing every string with a placeholder carrying
its own row number is what caught the hang, the undercount, and the second
text format. Single hand-patched lines all worked fine throughout — they
prove almost nothing.

## Dead ends and traps

**`EECycleRate = 1` is a 1.5× overclock, not a speed-up.** It made the
emulator slower. The log said so and it got ignored. If a setting seems
ignored, check whether the emulator *stripped it* when it rewrote the ini —
that is the fastest way to spot a wrong key name. (Muting took three attempts
for exactly this reason: `OutputVolume` is not a key, `StandardVolume` is
right for upstream PCSX2 but this build keeps it under `[SPU2/Output]`, and
`Backend = Null` is silently ignored. The answer is `OutputMuted = true`.)

**The hardware renderer is the performance trap.** Metal and Vulkan both
pegged the GPU at 100% while EE/GS/VU idled: 15 fps. The multithreaded
*software* renderer runs the same scene at 59.9 fps with the GPU at 1%.

**"No native arm64 build exists" was wrong.** Only the official releases were
checked, and ARMSX2 was dismissed from a search summary calling it
"Android-focused" without opening the repo. Rosetta cost a 4× slowdown for
days. Open the repository.

**Slot arithmetic, measured wrong.** The first extractor measured a record's
free space to the *next record*, which spans pointer tables and other data
sitting between clusters. It reported 267% spare capacity. The real figure —
counting only the NUL padding that directly follows the text — is about 7%,
and writing to the first number would have corrupted the file. Free space is
what is provably padding, not what happens to lie in between.

**Verification that filters like the extractor does.** The record parser
keeps only entries containing Japanese, which is how it tells records from
binary data that happens to decode. Re-parsing a *translated* file therefore
finds nothing, and the verification reports total failure. Verify by reading
back at the offsets the original established (`text.py:read_at`).

**A texture that looks like text.** `STAGE:P-01` renders in Latin on the
stage title card, which was taken as proof the font has Latin glyphs. It
proves nothing — the whole card is a TIM2 texture. The conclusion happened to
be right, and the evidence was worthless. The real proof came from the stress
build rendering Latin sentences in the dialogue box.

**Menu labels pulse when highlighted.** A screenshot caught `TUTORIAL` blank
mid-animation and it looked like the patch had destroyed a menu entry. It had
not. Take a second screenshot before believing the first.

## Working notes

- Boot to a playable state takes ~30 s; sample liveness **twice, late**
  (45 s and 80 s). A slow boot and a hang look identical at 20 s.
- A hung build still runs: 59.9 fps, EE ~26%, **GS 2-3%** and a black screen,
  versus GS ~75% when rendering. The GS figure is the reliable tell, and a
  screenshot under ~5 KB is a black frame.
- `padRead` refills the pad buffer every frame, so a single write is lost —
  hold a button by writing in a tight loop. Reading the buffer back is *not* a
  check; it always reads `ff ff`. Check the screen.
- Menu navigation over PINE is unreliable at short hold times; d-pad presses
  need ~0.5 s. Budget real time for reaching a specific screen, and prefer
  verifying a string that appears early.
- The game wraps text on character count, not word boundaries. Long English
  lines break mid-word.

## If you are starting the next one

Do these in order, before anything else:

1. Look for a `.symtab` in the main executable.
2. Search GitHub and the forums for the container and codec names.
3. Get screenshots and input scripted end-to-end, and prove it by reaching a
   known screen.
4. Work out how to read the program counter and a call stack from a save
   state. You will need it, and you do not want to be building it while
   debugging something else.
5. Only then start on the text.
