# Macross: English translation tooling

Tooling for an English fan translation of **Chou Jikuu Yousai Macross**
(超時空要塞マクロス, PS2, SLPM-65405, Sega AM2 / Bandai, 2003).

> **Disclaimer:** This repo was developed by a coding AI agent (Claude
> Opus/Sonnet 5). **This repository contains no game data and no game script.** It ships tools and
documentation for creating a translation patch for the game with minimal technical knowledge. You supply your own copy of the game; everything Japanese is extracted on your machine and never
committed.

## What works

- Every string in the game's text file is found, edited and written back —
  **2,777 strings, 2,739 of them Japanese, 64,092 characters**.
- The game's own font already has Latin glyphs, so **no font hack is needed**.
- English fits in place: **2.12 ASCII characters per Japanese character**, so
  nothing has to be moved and no pointers need rewriting.
- Proven by a full-coverage stress build — all 2,739 Japanese strings
  replaced with traceable placeholders, booted, and checked on screen.
- Line breaks are yours to place: the game wraps on character count, so an
  explicit newline is how you stop it splitting a word.
- **Spoken radio dialogue can be subtitled** with `--subtitles` — 1,811 lines
  the game says out loud but never shows.
- **No size ceiling.** `BOOTDAT.CMP` only gets 97 sectors on the disc and
  `JPN.CVM` is packed solid, which is not enough — translating the short,
  repetitive lines first actually makes the compressed file *grow*. When that
  happens `tools/build.py` rebuilds the container with room to spare, so you
  never have to shorten a sentence to make a build fit.

### Subtitles for the spoken radio dialogue

During missions the pilots talk over the radio, and the game speaks those
lines without showing them. It turns out the engine already has the whole
caption system — text, window and timing — and simply marks most in-mission
lines as voice only. `tools/build.py --subtitles` turns them on.

| Without `--subtitles` | With `--subtitles` |
|---|---|
| ![Radio line, spoken only](docs/shots/caption-before.png) | ![Radio line, subtitled](docs/shots/caption-after.png) |

It is a **one-byte edit per line**, not a code patch, and the timing is the
game's own: the caption is held for exactly the length of the voice clip,
measured by `SND_GetVoicePlayTime`. **1,811 lines** are affected.

### Before / after

Same scene, same input, unmodified disc on the left and a build from this
tooling on the right. (These frames predate the full script pass, so the
exact wording differs slightly from what ships today.)

| Before | After |
|---|---|
| ![Briefing, Japanese](docs/shots/dialogue-before.png) | ![Briefing, English](docs/shots/dialogue-after.png) |
| ![Global Report, Japanese](docs/shots/global-before.png) | ![Global Report, English](docs/shots/global-after.png) |

## Requirements

- Python 3.8+ (standard library only; `tkinter` for the editor)
- Your own copy of the game as an ISO — the supported image is verified by
  checksum before anything is written
- A PS2 emulator to play the result. Development used
  [ARMSX2](https://github.com/ARMSX2/ARMSX2), the native arm64 macOS build;
  official PCSX2 works too.

## Setup

The CRICMP codec is a third-party tool and is not committed here. Build it
once and drop the binary in `tools/`:

```sh
git clone https://github.com/zeesworth/cricmp
cd cricmp && make
cp cricmp ../macross-en/tools/cricmp
```

## Use

```sh
python3 tools/verify.py "Macross (Japan).iso"          # is this the right image?
python3 tools/make_workbook.py "Macross (Japan).iso"   # -> work/workbook.csv
python3 tools/editor.py                                # translate (or use a spreadsheet)
python3 tools/build.py "Macross (Japan).iso" "Macross (EN).iso"
python3 tools/build.py "Macross (Japan).iso" "Macross (EN).iso" --subtitles
```

`make_workbook.py` extracts the Japanese from *your* disc and seeds the
English column from `translation/english.json`, so existing work shows up
next to what is still to do. `work/` is gitignored — **do not commit the
workbook**, it contains the publisher's script.

`build.py` refuses to touch the source image, checks every line against its
byte budget before writing anything, and reads the finished ISO back to
confirm each string really arrived.

## What is translated here

Two files, kept deliberately apart.

### `translation/english.json` — 290 strings, hand-checked

The minimal playability translation that has always shipped here: menus,
stage and track names, difficulty labels, save/load prompts, controller
warnings, and the HUD and radio vocabulary. Enough to navigate and play the
game in English. This is what a plain `build.py` uses, and it is unchanged.

### `translation/english-mtl.json` — 2,538 strings, **machine translation**

> ⚠️ **This is a machine translation (MTL).** It was produced by an AI
> (Claude Opus 5), not by a human translator, and **no human who reads
> Japanese has checked a single line of it.** It is fluent, it is
> internally consistent, and it may still be confidently wrong in ways
> nothing in this repository can detect. Treat it as a playable draft and a
> starting point for a human pass — not as a finished localisation.

It covers the whole story script: mission briefings, in-mission radio
dialogue, the training course, promotion and trading-card scenes, the
Zentradi transmissions, the Global Report narration, and the mission
objectives in the pause menu.

It is a **layer**, not a replacement — it contains only what it adds to the
baseline, plus two vocabulary-consistency overrides. Opt in:

```sh
python3 tools/build.py "Macross (Japan).iso" "Macross (EN).iso" --mtl
python3 tools/build.py "Macross (Japan).iso" "Macross (EN).iso" --mtl --subtitles
python3 tools/make_workbook.py "Macross (Japan).iso" --mtl   # seed a workbook from it
```

Nine strings are left untranslated on purpose: the seven memory-card save
titles (`str-027a9c-017`..`023`), whose renaming would orphan existing save
data, and two developer markers with no translatable text.

### How the MTL was produced

Against a written method rather than line by line, and the method ships with
it in [`translation/artifacts/`](translation/artifacts/): a brief, a story
bible, a locked glossary, voice cards with an address matrix and quirk
register, a query log sorted into internal/editor/developer lanes, a
deferred register of known unknowns, and a record of what each review pass
changed. A human translator picking this up should start there.

**What was verified on screen**, in ARMSX2: the Global Report narration, the
mission briefings, the promotion scenes, the in-mission subtitle window and
the pause-menu objectives all render correctly, within their boxes, with the
line breaks as written. **Not verified:** the runtime-assembled scramble
calls — see `05-DEFERRED.md` item 17.

## Known limitations

- **The game wraps text on character count, not word boundaries**, so a long
  line can break mid-word. Keep lines short or place explicit newlines.
- **Radio captions get four lines of 28 characters.** The window is that size
  whether or not you fill it, so a two-line caption leaves a visible gap.
  Write to fill it.
- Subtitles are only lightly playtested — the tutorial mission. Enabling all
  1,811 lines is the blunt setting; some may be silent by design, and the
  caption window clips the lower HUD slightly.
- **Stage title cards, the logo and 2D menu art are textures** (`SBTTL_*`,
  `MENU2D`, `TTL`, `LOGO` — TIM2 format), not text. Translating them is an
  art job this tooling does not cover.
- Memory-card save titles (`str-027a9c-017`..`023`) are deliberately left
  alone; renaming them would orphan existing save data. They are already
  readable English words, just in full-width characters.
- Only SLPM-65405 (Japan) is supported.
  Another release needs its own hashes in `tools/verify.py`.

## Documentation

- [`docs/FORMATS.md`](docs/FORMATS.md) — disc layout, containers, text
  formats, emulator control, and the traps
- [`docs/TASK_SPEC.md`](docs/TASK_SPEC.md) — the constraints this work is held to
- [`docs/JOURNAL.md`](docs/JOURNAL.md) — how it went, including the dead ends
- [`stress/README.md`](stress/README.md) — the full-coverage harness

## Credits

CRICMP compression is handled by [`zeesworth/cricmp`](https://github.com/zeesworth/cricmp),
which names this game in its README and supplies both a decompressor and a
recompressor.
