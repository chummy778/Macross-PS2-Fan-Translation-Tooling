# Formats — Super Dimensional Fortress Macross (PS2, SLPM-65405)

What is known so far, and how it was established. Written as findings land,
so later sections are less settled than earlier ones.

## Disc

Plain ISO 9660, 11 files. The interesting ones:

| File | Size | What |
|---|---|---|
| `SLPM_654.05` | 4.2 MB | main ELF — **ships with debug symbols** |
| `JPN.CVM` | 23 MB | Japanese data — **contains the script** |
| `BIN.CVM` | 240 MB | models, animation, mission data |
| `ADXJ.CVM` | 456 MB | CRI ADX audio |
| `MOV.CVM` | 306 MB | Sofdec video |
| `ETC.CVM` | 199 MB | **all zeros** — a dummy, and absent from `0FLIST.DIR` |

## CVM containers

A `.CVM` is a `CVMH` header followed by an ordinary **ISO 9660 image at
offset `0x1800`**. Nothing is encrypted in this title: the inner volume
descriptor's `CD001` signature sits at `0x9801`, exactly the standard
`0x8001` shifted by the header. So `tools/cvm.py` reads them with a plain
ISO parser plus a constant offset — no CRI tooling needed.

Independently corroborated by a [ZenHAX
thread](https://www.zenhax.com/viewtopic.php@t=16564.html) on this same
game ("delete first 0x1800 byte then rename to .iso").

`tools/extract_cvm.py` unpacks all of them: 691 files.

## CRICMP compression

Every `.CMP` is CRI's `CRICMP` v2.10:

```
+0x00  "CRICMP\0\0"
+0x08  "2.10\0\0\0\0"
+0x10  u32  header size (0x20)
+0x14  u32  uncompressed size
```

It is a custom LZ, so no stock codec touches it. Japanese is partly legible
in the *compressed* stream because literals pass through unchanged, with
back-references cutting words in half (a two-byte character split by a
`<cf><ff>` match token) — misleading if you mistake it for a plaintext region.

**Solved by [`zeesworth/cricmp`](https://github.com/zeesworth/cricmp)**,
which names this exact game in its README and provides both a decompressor
and, importantly for patching, a **recompressor**. All 374 `.CMP` files
decompress with output length matching the header's stated size exactly —
374/374, no mismatches.

Finding this took one GitHub repo search. The trail was worth recording
because the obvious routes were dead: the romhacking.net thread and the
Shenmue Dojo link inside the ZenHAX thread are both unreachable (403/504),
and as of 2022 the ZenHAX regulars concluded "no one made any script or
tool about it".

## Where the text is

**Nearly all of it is in one file: `JPN.CVM/BOOTDAT.CMP`** -- the exception
being the 52 system messages in the executable, see below. (198 KB compressed,
316,988 bytes decompressed).

This was worth checking carefully, because a naive Shift-JIS scan finds
"text" in 323 files. Almost all of it is model and animation data that
happens to decode — the `VF1*_AC` files (Valkyrie variants) yield dense
runs of rare, unrelated kanji with no kana between them. Scoring runs by
*hiragana and particle density* rather than mere decodability separates
them cleanly: `BOOTDAT` scores 2,221 prose runs, every other file 13 or
fewer. The `BRF_AUTH_*` / `GLB_AUTH_*` files, despite promising names, hold
no text — they are cutscene authoring data.

### Record format

Records are self-delimiting and, refreshingly, use **no character table and
no per-record encoding**:

```
[6 ASCII digits: speaker/voice id][Shift-JIS text]\x00[NUL padding]
```

`0x0a` inside the text is a line break. Records are preceded by u32 pointer
tables (the container is nested MRG archives — `[count][align][offsets…]`
— not yet fully unpicked, and not needed for extraction).

Extracted: **2,015 records, 180 distinct speaker IDs, 41,669 characters.**

```
0x0003e0  [081009]  <Shift-JIS text>  00
0x000418  [081092]  <Shift-JIS text>  00 00
0x0016a2  [081   ]  <Shift-JIS text, 0a line break>  00 00
```

(Examples are redacted: the script is the publisher's and is not
distributed here. Run `tools/text.py` against your own copy to see it.)

## Open questions

- The nested MRG structure. Extraction does not need it; **patching with
  longer text probably does**, since growing a record means moving what
  follows and fixing the pointers that reference it.
- ~~Whether 41,669 characters is the *whole* game's text. The ELF was scanned
  and holds **no prose** (only dense-kanji noise), so the script is not
  split between the two.~~ **Wrong.** `SLPM_654.05` holds **52 Japanese
  system messages** -- memory card, save/load, HDD, joystick calibration --
  in plain Shift-JIS. They are the first thing a player sees, before the
  first mission, and they made the game look half-translated long after the
  script was finished. `tools/elftext.py` finds them and `build.py` patches
  them in place. The original scan missed them because it looked for
  *density* of kanji rather than for real sentences. Still unaudited: menu and HUD labels, which are
  likely **textures** rather than text, and would need art edits.
- ~~Whether the font has Latin glyphs~~ — **answered: it does.** See Font.

## Emulator control (verified)

**ARMSX2** (`https://github.com/ARMSX2/ARMSX2`), the native **arm64** macOS
build. Official PCSX2 ships x86_64 only, which ran this game at 15 fps under
Rosetta on an M2 Max.

| Need | How | Verified |
|---|---|---|
| Boot | `ARMSX2 -batch -- game.iso` | yes |
| Memory read/write | **PINE** unix socket, `tools/pine.py` | yes |
| Screenshots | savestate via PINE, extract `Screenshot.png` from the `.p2s` zip (`tools/shot.py`) | yes |
| Input | **PINE writes to `g_pad_buf`** (`0x007b8a00`) | yes |
| Speed | 59.9 fps locked | yes |

No OS-level screen capture or synthetic keystrokes are used at any point.

### Settings that matter

- **`Renderer = 13` (software).** The hardware path is the single biggest
  performance trap here: Metal *and* Vulkan both pegged the GPU at 100% while
  EE/GS/VU idled, giving 15 fps. The multithreaded software renderer with
  `extrathreads = 10` runs the same scene at **59.9 fps with GPU at 1%**.
- **`[SPU2/Output] OutputMuted = true`** to mute. `OutputVolume` is not a
  key; `StandardVolume` is right for modern PCSX2 but ARMSX2 keeps volume
  under `[SPU2/Output]`, and `Backend = Null` is silently ignored.
- **Leave `EECycleRate` alone.** Positive values are a 1.5x/2.0x *overclock*
  — i.e. slower emulation. Setting it to 1 as an "optimisation" made things
  worse and the log said so.

If a setting seems ignored, check whether the emulator **stripped it** when
it rewrote the ini — that is the quickest way to spot a wrong key name.

### Driving input

`g_pad_buf` is standard PS2 pad data:

```
+0  status (0x00 = ok)
+1  type   (0x79 = analog pad)
+2  button bits, ACTIVE LOW: 0=SELECT 3=START 4=UP 5=RIGHT 6=DOWN 7=LEFT
+3  button bits, ACTIVE LOW: 4=TRIANGLE 5=CIRCLE 6=CROSS 7=SQUARE
+4  analog axes, 0x7f centred
```

`padRead` refills it every frame, so a single write is lost. Writing in a
tight loop wins often enough to drive menus reliably — verified by leaving
attract mode and reaching `STAGE:P-01`. Reading the buffer back is *not* a
valid check for this reason: it always reads `ff ff`. Check the screen.

## Font

**The font already contains Latin glyphs** — the stress build renders full
Latin sentences in the dialogue box through the game's own sprite font, with
correct spacing and automatic word wrap. English needs no font hack, which
removes the biggest unknown for this project.

Text renders through a sprite-font atlas (`SPRFNT_SetFontTopCgNo*`,
`utl_cros_font_load`), loaded from the `CRS*` data.

## Debug symbols

`SLPM_654.05` has a full `.symtab`: **17,423 usable symbols with addresses**. This
is unusual and extremely useful — `g_pad_buf`, `g_telop`, `STR_GetIdx`,
`STR_Init`, `padRead` were all located directly rather than by searching.

## Patch chain (verified end to end)

1. `tools/cricmp dec` -> edit records -> `tools/cricmp enc`
2. `tools/isopatch.py` writes the result back through both container layers
3. Source ISO is copied first and verified unchanged by checksum

**Verified on screen**: all 2,739 Japanese strings replaced with indexed
placeholders, booted, and photographed rendering — briefing dialogue
(`R0179`, `R1513`) with correct order and speaker portraits, and the Global
Report narration (`R2274`), which is the space-id record class. See
`stress/README.md`.

**The game wraps on character count, not word boundaries** — a long line
breaks mid-word (`…U.N. Spacy Valkyri / e Corps.`). Translators should keep
lines short or place explicit `\n` breaks; there is no engine fix for it
short of patching the renderer.

### The container is full, and the fix is to rebuild it

`JPN.CVM` has **zero spare bytes**: the file is exactly its `0x1800` header
plus its declared 11,319 sectors, with no gaps between files. `BOOTDAT.CMP`
gets 97 sectors (198,656 bytes) and cannot grow in place.

`tools/cvmexpand.py` rebuilds the container instead. Two things about this
disc make it straightforward:

* Inside the CVM, the volume descriptor, both path tables and the root
  directory occupy sectors 16-21, **below** the first file at sector 22, and
  there are **no subdirectories**. So widening a file means inserting zeroed
  sectors and renumbering file extents -- no metadata moves.
* `ETC.CVM` is 199 MB of zeros, absent from `0FLIST.DIR`, and nothing opens
  it. The rebuilt container goes there and both outer directory records are
  repointed so nothing overlaps.

Also updated: the inner PVD volume size (`+80` LE, `+84` BE) and the CVMH's
own byte size (`+0x20`, big-endian). Everything ISO 9660 stores twice is
written in both orders -- missing one is a silent corruption.

Verified: all 70 files inside the rebuilt CVM read back byte-identical, the
outer image is the same size, and the game boots and renders at 59.9 fps from
the relocated container. `tools/build.py` does this automatically, and only
when the script actually outgrows its slot.

### Two different limits, and they fail in opposite directions

Every string is written **in place**, so each one must fit its own slot — and
at 2.12 ASCII characters per Japanese character, they comfortably do. That is
not the binding constraint.

The binding constraint is the **compressed** file. `BOOTDAT.CMP` has a
recorded length of 198,240 bytes but is allocated **97 whole sectors =
198,656 bytes**, and the next file begins immediately after. `tools/isopatch.py`
measures that allocation from where the next extent starts rather than
trusting the recorded length — which is worth 416 bytes, and 416 bytes is the
difference between a translation building and not.

What grows the file is not *how much* is translated but **which lines**.
Measured with `stress/sizesweep.py`:

| translated | compressed |
|---|---|
| 0% (original Japanese) | 198,128 |
| 50% | ~182,000 |
| 100% | ~151,000 |

Coverage helps monotonically. But the short, highly repetitive lines --
acknowledgements, the twelve clock bearings, the five turret names, all
differing by one character -- cost almost nothing compressed, while their
English replacements are novel text. Translate those first, as any sensible
person does, and the file **grows**: the 290-string UI-and-HUD translation
here comes out 262 bytes over the original slot.

Beware measuring this with generated filler. It reuses a small pool of words
and flatters the codec; the real translation is full of distinct domain
vocabulary. `sizesweep.py` reports the real `english.json` alongside its
sweep for exactly this reason.

### The recorded length must shrink with the data

The single worst trap in this container stack. A shorter file written into
its original extent, zero-padded, with the ISO directory record left alone,
**hangs the game at a black screen** — CRI's streaming reader feeds the
decompressor sector by sector and only reports the read finished once the
*recorded* length has been consumed, so it waits forever in `UTL_NwIsEnd`.

The failure is a pure function of compressed size, not of content, so it
looks nothing like a patching bug: identical edits pass or fail depending on
how well the file happened to compress. `tools/isopatch.py` now updates the
directory record's data length (both the little- and big-endian copies at
`+10`) whenever it writes.

## Reading the machine

PINE cannot report the program counter, so the emulator's own savestate is
the debugger. A `.p2s` is a zip — but zstd-compressed, which Python's
`zipfile` refuses, hence `tools/p2s.py`.

| Want | Tool | Note |
|---|---|---|
| Any savestate member | `tools/p2s.py state.p2s eeMemory.bin out` | 32 MB of EE RAM, `iopMemory.bin`, `GS.bin`, … |
| Registers / PC | `PCSX2 Internal Structures.dat` | `cpuRegs` tag, then a fixed 32-byte name field |
| Symbol for an address | `tools/symbols.py 0x1a1510` | 17,423 usable symbols |
| Disassembly | `tools/disasm.py STR_GetIdx` | capstone lacks R5900 MMI ops; those print as `.word` |
| Call stack | `tools/stack.py eeMemory.bin <sp>` | walks `sp` upward, labels text-range words |

`cpuRegs` layout, confirmed against known values (`Status = 0x70030c00`,
`PRId = 0x2e20`, `EPC` landing on a syscall): 32 GPRs x 16 bytes, `HI`/`LO`
16 each, `CP0regs` 32 words, then `sa`, `IsDelaySlot`, **`pc`**, `code`.

## Text coverage

`BOOTDAT` holds **two** text formats, and the record parser only sees one:

| Format | Count | What |
|---|---|---|
| records — `[6-char id][Shift-JIS]\x00` | 2,675 | dialogue, briefings, narration |
| pools — `[u32 offsets][NUL-terminated strings]` | 102 | stage names, menus, save/load prompts |

`tools/text.py` exposes both as one list of units: **2,777 strings, 2,739
containing Japanese, 64,092 characters, against 135,666 bytes of writable
slot** — 2.12 ASCII characters per Japanese character, so English fits
in place and nothing has to move.

### The id is not always six digits

A record id is three digits of category followed by three characters that are
either digits **or spaces** — `081   ` is as valid as `081009`. Matching only
`[0-9]{6}` finds 2,015 records and looks complete; it silently drops **660**,
the entire Global Report narration, and the loss is invisible until someone
watches the intro. That is a 50% undercount of the script.

The ELF says so plainly, which is why reading `STR_GetIdx` was worth more
than any amount of pattern-guessing: its first instruction is `lb $a1, 3($a0)`
followed by a compare against `0x20`, i.e. *if byte 3 is a space, the index is
zero*. The space form is a designed case, not corruption.

The pools are found by `tools/strtab.py`: the first table entry is also the
table's own length, which makes them unambiguous to locate.

### A slot must hold the text *and* its NUL terminator

`Unit.budget` is the whole slot: the original bytes plus the padding that
follows. The terminator lives in that padding, so a replacement may use at
most `budget - 1` bytes. `text.apply` and `build.check_budgets` originally
allowed `len(data) == budget`, which writes text over the last NUL and
leaves the string unterminated. The game then reads straight on into the
next record and draws its six-digit id glued to the end of the line --
on screen, `We're hit!021072Damage!`.

It is easy to miss because everything else looks right: the bytes are
correct, the read-back verification passes (it reads the same slot), and
only the *neighbouring* string is visibly wrong. 153 strings were affected,
38 of them in the hand-checked baseline that predates the script pass.

Rule: **a replacement must be strictly shorter than its budget.**

### Pool offset tables are **not** sorted

The obvious extra check on a candidate table — "the offsets should ascend" —
is wrong, and cost 88 live strings. A table may point several entries at the
same string, and may point back at a string it already used, so the list
dips. Requiring `offs == sorted(offs)` silently discarded the pool at
`0x0285fc` that holds **every mission objective**, which is why the pause
menu still rendered Japanese long after the script was translated.

What actually holds, and is what `strtab.py` checks now:

* `off0` is the table's own byte length, so the first string begins
  immediately after the table;
* no offset points back inside the table;
* **every offset lands on a string start** — the byte before it is the NUL
  that ended the previous string.

The last of these is the real invariant sortedness was standing in for, and
it is far stronger: random data almost never satisfies it.

Because entries may repeat, `tools/text.py` deduplicates pool units by
offset. Two entries pointing at one string are one string; exposing both
would let two different English texts be written to the same bytes, and the
second would silently win. There were 20 such collisions.

### A Shift-JIS byte scan is not a text census

Worth repeating inside a single file, not just across files. Scanning
`BOOTDAT` for byte pairs in the Shift-JIS lead-byte range suggests about
5,900 characters of text are unaccounted for. Nearly all of it is IEEE-754
floats and 16-bit coordinate pairs that happen to decode — the same trap
that makes a naive scan "find" text in 323 files. Screen by **hiragana
density** before believing any such number. Screened that way, the real
figure was 1,058 characters, and after the `strtab.py` fix no prose is
uncovered at all. Offsets point at
string *starts*, so in-place edits within budget need no fixups.

`STR_GetIdx` parses only the **last three digits** of a record's 6-digit id
into an index 0-999 (`d3*100 + d4*10 + d5`, or 0 if byte 3 is a space); the
first three are the category. Ids are not unique keys — many records share one.

### Unit ids are offsets, not indices

`tools/text.py` keys every string by its byte offset (`rec-01e594`), never by
its position in the list. Teaching the parser to see one more record shifts
every index after it, which would silently re-point an existing translation
at the wrong lines. This happened here — the fix arrived after the first
translations were written — and offsets made it a non-event.

### Captions: the engine already had them

In-mission radio dialogue is spoken but not shown. The whole caption system
exists and is simply switched off per line:

```
MIS_PlayVoice -> NAVI_PlayVoice          queues the line, asks
                                         SND_GetVoicePlayTime for its length
navi_Chrw     -> STR_GetDispAttr(id)     reads byte 2 of the record id
NAVI_DispNarrationExec                   draws the portrait unconditionally,
                                         the caption only if bit 0 is set
```

`STR_GetDispAttr` returns 1/2/3 for `'1'`/`'2'`/`'3'` and 0 otherwise, and the
caption is drawn when bit 0 of that is set. So **`'1'` in byte 2 means
captioned, `'0'` means voice only** — 864 records ship captioned, 1,811 do
not. Flipping that byte is all it takes; the timing is the engine's own.

Attribute `2` and `3` are unexplored. `3` also has bit 0 set and rendered
identically to `1` in testing, so it is not a second window style.

The caption window is a **fixed** preset in `navi_dispWinMsg`: text area
280x88 at (180, 287), drawn inside a 300x100 box. At the native 32px glyph
size that is four lines of 28 characters, and it does not shrink to fit —
a two-line caption leaves a visible empty band.

### What is text and what is art

Replacing all 2,739 Japanese strings leaves the **stage title card still
Japanese**. It is not text: `SBTTL_*.CMP` (one per stage, `TU00`, `TV01-12`,
`MV01-08`) are **TIM2 textures**, as are `MENU2D`, `LOGO` and `TTL`. The
27-entry pool of stage names is a separate list used elsewhere. Translating
the title cards, the logo and any 2D menu art is an **art job**, not a text
one, and is out of scope for this pipeline.

Caution on a tempting inference: `STAGE:P-01` rendering in Latin proves
nothing about the font, because that whole card is a texture. The font's
Latin coverage is proven properly by the stress build — the dialogue box
renders `R1513 sed do eiusmod tempor incididunt ut labor…` through the
sprite font itself.
