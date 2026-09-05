# Task specification

What this project is held to. Inherited from the Jan Jaka Jan (FM Towns)
project and adapted for a PS2 title; the constraints are the transferable
part, the game specifics are not.

## Goal

Produce tooling that lets a **human** translate *Chou Jikuu Yousai Macross*
(PS2, SLPM-65405) into English, and produce a patched disc image from that
translation, without distributing anything belonging to the publisher.

## Constraints

**C1 — The emulator is driven entirely from the command line.** No OS-level
screen capture, no window capture, no synthetic keystrokes into the desktop.
Screenshots come from the emulator's own save states; input is written into
the game's pad buffer over PINE. Anything else is not reproducible and not
scriptable.

**C2 — Search before reverse-engineering.** Someone has usually been here.
The single hardest problem in this project (CRICMP compression) was solved by
one GitHub search that found a tool naming this exact game. Reverse-engineer
what the search does not answer, not what it does.

**C3 — The original image is never modified.** It is opened read-only, the
output is a copy, and the source's size and checksum are re-verified after
every build. `tools/build.py` refuses to write to its own input.

**C4 — Translators get a workbook and an editor.** A CSV that opens in any
spreadsheet, and a GUI (`tools/editor.py`) for people who would rather not.
The byte budget is shown live, because an over-long line is the failure mode
that silently truncates a sentence in-game.

**C5 — Reverse-engineer in the emulator; ship from the file.** Live memory is
for *understanding*. The patch is always produced by transforming the file on
disc, never by replaying pokes. A patch that only exists as emulator state is
not a patch.

**C6 — Nothing ships untested, and testing means playing it.** Every claim
about what works is backed by a screenshot of the game running. "The bytes
are correct" is not the same as "it renders", and this project has already
produced a build where the bytes were provably perfect and the game hung.

**C7 — The distribution contains nothing derived from the game: no game data,
no artwork, and no script.** Users supply their own copy. The Japanese is
extracted on the translator's machine by `tools/make_workbook.py` and lands
in gitignored `work/`. The repository ships only `translation/english.json` —
English and notes keyed by string id, with no Japanese in it — and the
workbook generator seeds from it so existing work is visible. **Check this
before publishing:** the shipped translation file must contain zero CJK
characters. Screenshots are exempt: a couple of frames showing the
before/after is fair use and is the point of having a README.

**C8 — Coverage is proven, not assumed.** A full-coverage stress build
replaces *every* string with a placeholder carrying its own row number, and
is then played. A row number proves the right text reached the right place; a
generic filler proves only that something rendered. This is what caught both
a 50% undercount of the script and a boot hang.

**C9 — Ship the UI, not the script.** Functional strings — menus, prompts,
stage names, difficulty labels, and the HUD/radio vocabulary — are translated
properly and stay, so the game is navigable and playable in English out of
the box. The story script is a human translator's job and is deliberately
left undone. Screenshots may show demonstration lines that are not shipped;
say so where they appear.

**C10 — Identify the image before touching it.** A version check runs before
extraction and before patching, and hashes the files the patch depends on
rather than the whole disc, so a wrong region or a bad dump is distinguishable
from a re-release.

**C11 — Ids are properties of the game, not of the tool.** Strings are keyed
by byte offset, never by index. A parser that learns to see one more string
must not silently re-point an existing translation. This is not hypothetical:
the parser here was corrected mid-project and gained 660 records.

## Accomplished

- Disc, CVM container and CRICMP compression all read and written
- Both text formats found and unified: 2,777 strings, 64,092 Japanese characters
- Byte budget measured at 2.12 ASCII characters per Japanese character
- Full-coverage stress build boots and renders, verified on screen
- Font confirmed to carry Latin glyphs — no font hack needed
- Emulator fully scriptable: boot, memory, input, screenshots, savestate
  disassembly and call stacks
- End-to-end patcher with verification, and a translation editor

## Not done

- The script itself. That is deliberate (C9).
- Textures: stage title cards, logo, 2D menu art (TIM2). Art job, out of scope.
- Growing a string beyond its slot. Not needed at 2.12x, and would require
  rewriting the pool offset tables.
- Removing the compressed-size ceiling. `BOOTDAT.CMP` must fit 198,656 bytes
  and a partial translation compresses worse than a complete one, so the
  limit binds during the middle of the work. The fix is to rebuild `JPN.CVM`
  with a larger extent inside the 199 MB `ETC.CVM` occupies (a dummy of all
  zeros, absent from `0FLIST.DIR`; the outer directory record and the CVMH
  size field at `+0x20` would both need updating). Identified and measured,
  not built.
