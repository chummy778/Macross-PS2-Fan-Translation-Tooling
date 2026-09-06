# Deferred register

The known unknowns, stated plainly, handed over so that a later bilingual
pass, a dev answer, or player feedback can settle them cheaply instead of
rediscovering them.

Nothing here blocks the build. Everything here shipped on a stated default.

---

## Needs a playtester, not a translator

1. **The sentence-fragment radio pool (rows 1961-2144, ~180 strings).**
   These are assembled at runtime from pieces -- caller, squadron, bearing,
   order. It is not known whether the engine concatenates them into one
   caption or plays them as a queue, nor whether it inserts a separator.
   The English mirrors the source's own seam marks (a piece that begins
   with an ellipsis in Japanese begins with `...` in English), so it reads
   no worse than the original under either behaviour. **Watch one scramble
   call with `--subtitles` on and the answer is immediate.** If the engine
   concatenates without a space, the fragments want a leading space instead
   of a leading ellipsis -- a mechanical change to about 40 strings.

2. **The six developer stage directions** (rows 779, 1453, 1454, 1470,
   2237, 2245). Shipped as parentheticals. If they turn out never to be
   drawn, nothing happens. If they are drawn and read badly, deleting the
   parenthetical is a one-line edit each. See Q-06.

3. **The "x"-marked records** (~40 strings, listed in Q-07). Believed to be
   cut or duplicate content. The marker is dropped and the line translated,
   so they are correct either way -- but if any of them *is* live, its
   English has never been seen on screen.

4. **Caption geometry.** In-mission lines are written to 4 lines x 28
   characters; briefing, promotion and Global Report lines to 3 x 44,
   measured off the screenshots in `docs/shots/` with a safety margin. The
   Global Report box measured nearer 52 columns, so those lines have room
   to spare. **Nothing in this pass has been seen rendered.** A pass with
   `--subtitles` over one mission of each type would confirm all three.

5. **Rows 478, 481, 505, 506, 511, 550-556, 562-569, 679, 688-691, 715-719,
   735-737, 770, 788, 791, 798, 818-823, 828-829, 834, 838-839, 849, 896-897,
   907, 992-993, 1046, 1055, 1188-1193, 1296, 1305-1306, 1311, 1322-1323,
   1378, 1380, 1391-1394, 1418-1420, 1447-1451, 1458, 1627-1629, 2170-2187.**
   These carry the `081`/`021` captioned attribute but occur *during
   missions*, so they were written to the 28-column in-mission geometry
   rather than the wide briefing box. If they in fact use the wide box they
   will simply look narrow -- never clipped.

## Needs the source language or the developer

6. **"Makdomilla"** (rows 821-822) -- person, ship, or unit? Rendered as a
   unit callsign.
7. **"Bernal class"** (rows 91, 93) -- no canon English spelling located
   for the Zentradi branch-fleet flagship class.
8. **"kaarchuun"** (row 1448) -- a Zentradi word for inherited cultural
   memory, transliterated and left unglossed, as the source leaves it.
9. **Voice-index attributions.** The cast map in `03-VOICES.md` rests on
   characters naming themselves or being named by whoever answers them.
   Roughly a dozen minor bridge indices (072, 073, 129, 159, 169, 175, 183,
   191) are assigned to the Bridge Control *band* rather than to a named
   officer. The English does not depend on getting these right -- they all
   speak the same procedural register -- but a bilingual reviewer with the
   voice files could pin them.

## Known translator's judgement calls, open to revision

10. **Row 2618 / the diary track.** See Q-13. The narrator says "I entered
    the contest" and then names Minmay in the third person. Both persons
    are preserved as written.
11. **"Booby Duck"** (row 2569) -- the source's own nickname for the
    fast-pack Valkyrie, kept as written rather than smoothed.
12. **British spellings** (*authorised, metres, defence, agonised,
    realise*) are used throughout, matching the U.N. Spacy's
    internationalist register and the existing 290 UI strings. If a US-
    English house style is wanted later, it is a mechanical sweep of about
    30 strings.
13. **The seven memory-card save titles** (`str-027a9c-017`..`023`) are
    deliberately untouched. Renaming them orphans existing save data, and
    they are already readable English in full-width characters.

---

## Found by the in-game test pass (2026-09-05) -- FIXED

14. **The pool detector required sorted offset tables, and threw away every
    pool that reused a string.** Confirmed on screen: the pause menu's
    MISSION objective rendered in Japanese, because the pool holding all 39
    mission objectives was invisible to `tools/text.py` and so never reached
    the workbook.

    `tools/strtab.py` rejected any table whose offsets were not in
    non-decreasing order. That reads like a cheap sanity check and is in
    fact a content assumption: a table may legitimately point several
    entries at one string, and may point back at a string it already used,
    so the list dips. Replaced with the invariant sortedness was standing in
    for -- **every offset must land on a string start**, i.e. the byte
    before it is the NUL that ended the previous string -- plus a check that
    no offset points back inside the table. That is strictly stronger and
    does not care about order.

    `tools/text.py` also now **deduplicates pool entries by offset**. Where a
    table points twice at one string, that is one string; exposing it twice
    would let a translator write two different English texts to the same
    bytes and let the second silently win. 20 such collisions existed.

    Recovered: **88 strings, 1,058 characters** -- 39 mission objectives, 39
    radio grid letters and numbers, 8 countdown fragments, and 2 markers
    left untranslated on purpose. Verified on screen after rebuilding.

    Existing ids are unaffected: all five previously-known pool bases are
    still found at the same base with the same entry order, so none of the
    already-translated strings moved (C11).

    **A correction to the first report of this.** The initial estimate of
    "1,368 runs, ~5,930 characters, about 9% of the game's text" was wrong.
    It came from a raw Shift-JIS byte-range scan, which counts any byte pair
    in the lead-byte range as text -- and the file is full of IEEE-754 floats
    and 16-bit coordinate pairs that decode. Screened by hiragana density,
    the honest figure is the 1,058 characters above, and **after the fix zero
    real prose remains uncovered**. `docs/FORMATS.md` warns about exactly
    this trap for whole files; it applies just as much inside one.

15. **`tools/shot.py` looked in the wrong place for save states** and
    reported "no save state appeared" while ARMSX2 was writing them
    normally. ARMSX2 and PCSX2 keep separate data roots
    (`~/Library/Application Support/ARMSX2/` vs `.../PCSX2/`). Fixed: it now
    searches both, newest wins.

16. **Two recovered strings ship untranslated, deliberately.**
    `str-003f24-592` is nothing but the developers' cut-line marker, with no
    text in it. `str-019764-394` is already English in the source and its
    leading marker glyph is non-ASCII, which C7 forbids in the shipped file,
    so it ships unchanged rather than losing the marker.

## Found by playtesting (2026-09-05, second pass)

18. **Unterminated strings -- FIXED.** A replacement that exactly filled its
    byte budget left no room for the NUL terminator, so the game read on
    into the next record and drew its six-digit voice id on the end of the
    line. 153 strings affected, 38 of them in the hand-checked baseline.
    Root cause fixed in `text.apply` and `build.check_budgets`; all 153
    shortened. Verified by reading the strings back out of EE RAM.

19. **The briefing box holds two lines, not three -- FIXED.** Briefing and
    promotion strings were written to three lines; the third was silently
    dropped on screen. 42 strings reflowed to two lines of 48. The Global
    Report box does take three lines; that surface was correct.

20. **Japanese remains in files this patcher does not touch -- NOT FIXED.**
    `RSLT.MRG`, `JISUCST.MRG`, `MENU_AUTH.CMP`, `MENU_AUTH_RSLT.CMP` and the
    `GLB_AUTH_*` / `BRF_AUTH_*` cutscene-authoring files together hold about
    1,100 characters of real prose. `docs/FORMATS.md` claims the `*_AUTH_*`
    files "hold no text"; that is wrong. The build pipeline only ever writes
    `BOOTDAT.CMP`, so reaching these needs a second patch path: decompress,
    edit, recompress and write back a different member of `JPN.CVM`. Ids
    would also need a file-qualified form. This is the mission-select and
    results-screen Japanese a player still sees.

## Still open

17. **The runtime-assembled radio fragments (item 1 above) remain
    unverified.** The in-game pass reached the briefings, the Global Report,
    the promotion scenes, the in-mission caption window and the pause menu,
    but never caught a scramble call on screen.
