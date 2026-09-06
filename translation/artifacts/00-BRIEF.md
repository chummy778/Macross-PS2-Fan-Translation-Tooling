# The Brief

> **This is a machine translation.** Everything below is the method it was
> produced against, not a claim that a human checked the result. No
> Japanese-reading human has reviewed any line of the output. The
> escalation channel in `04-QUERIES.md` and the deferred register in
> `05-DEFERRED.md` exist precisely because a fluent, confident,
> wrong sentence is invisible to everyone downstream of it.


*Chou Jikuu Yousai Macross* (PS2, SLPM-65405, Sega AM2 / Bandai, 2003) --
English fan translation. Written before the first line was drafted; amended
only with a dated note.

Contains no Japanese source text (see `docs/TASK_SPEC.md`, C7). Source forms
are named in romaji where naming them is unavoidable.

---

## 1. What is this game?

An arcade-style 3D Valkyrie combat game that retells the 1982 TV series
*Super Dimension Fortress Macross* from a seat the series never had: an
original-character rookie pilot who joins the Skull squadron on the day of
the Macross launch ceremony and ends the game inside Bodolza's flagship.

Three text surfaces, three tempos:

| Surface | Rows | Tempo |
|---|---|---|
| **Pre-mission briefing** | wide box, 3 lines | Slow. Read at leisure. Formal, procedural. |
| **In-mission radio** | 4x28 caption, timed to a voice clip | Fast. Heard while dodging. Must land in one pass. |
| **Global Report** | wide box, 3 lines | Slow. Retrospective narration between chapters. |

Era: 2009 in-fiction, 1982 in sensibility, 2003 in production. Comparable
English titles: *Ace Combat 04/5*, *Zone of the Enders*, the English dubs of
*Macross Plus* and *Do You Remember Love?*.

## 2. Who plays it?

People who sought out and applied a fan patch for a 2003 Japan-only Macross
game. They know the series, they know the mecha vocabulary, and they will
notice a Robotech name instantly and badly. High tolerance for foreignness,
zero tolerance for terminology drift. They are also playing an action game:
a radio caption they cannot read in two seconds is a failed caption.

## 3. What should the English feel like?

Three published targets, one per surface:

1. **Radio and HUD** -- the mission chatter of *Ace Combat 04: Shattered
   Skies*. Clipped, procedural, real-sounding traffic; controllers who nag
   without nagging; wingmen who talk like enlisted men, not like anime.
2. **Briefings and story dialogue** -- the English subtitle track of
   *Do You Remember Love?* / the *Macross Plus* dub. Plain, unfussy,
   period-neutral. Earnest without being florid.
3. **The Global Report** -- a captain's retrospective log. Measured,
   first-person, past tense, faintly rueful; the register of a naval memoir
   (O'Brian's Aubrey writing a despatch, not narrating an adventure).

## 4. Domestication axis

**Position: low domestication of names, high domestication of speech.**

| Decision | Choice | Reason |
|---|---|---|
| Character names | **Japanese canon**, in the romanizations Big West uses in English materials -- Hikaru Ichijo, Misa Hayase, Roy Focker, Claudia LaSalle, Lynn Minmay, Maximilian Jenius, Milia Fallyna, Hayao Kakizaki, Britai, Exsedol, Kamjin, Bodolza. | The audience is Macross fans. Robotech names (Rick Hunter, Lisa Hayes, Khyron, Breetai) would read as a different franchise. |
| Name order | **Given name first** ("Hikaru Ichijo"), surname alone with rank ("Lt. Hayase", "Major Focker"). | Matches the canon English materials and matches how the source actually uses them: rank+surname in the mouth, full name in narration. |
| Honorifics | **Dropped entirely.** | English military speech has its own deference system -- rank titles, "sir", and directness -- and it is richer here than transliterated suffixes would be. Every dropped suffix is repaid in the Address Matrix. |
| Terminology | **Preserved** -- Valkyrie, Battroid, GERWALK, Fighter, Destroid, gunpod, Fold, Pin Point Barrier, Daedalus Attack, Zentradi, Meltrandi, Protoculture, Micronian, reaction warhead, Grand Cannon. | These are the franchise's English terms already. Inventing new ones is the single fastest way to look wrong. |
| Cultural references | **Preserved.** The trading-card subplot, the shipboard TV station, Minmay's idol career all stay as they are. | Nothing here is opaque to the target audience. |
| Numbers/dates | Date stamps kept in the source's own YYYYMMDD-plus-time form; distances metric. | It is a log format, not prose. |

## 5. Untouchable

- Every canon proper noun in the Glossary marked **LOCKED**.
- Player callsigns: **Skull 7**, **Purple Leader**, **Apollo Leader**, and
  the Purple/Apollo 1-2-3 numbering. The game addresses the player by these
  constantly and a variant reads as a different unit.
- The rank ladder: Second Lieutenant -> First Lieutenant -> Captain ->
  Major -> Lieutenant Colonel -> Colonel. Six promotion scenes and roughly
  forty rank-vocative lines inherit it.
- The Minmay song fragment. One record carries a snatch of a copyrighted
  song as diegetic broadcast. It ships as **romanized sung Japanese**, the
  ordinary fansub convention for on-screen singing, rather than as an
  invented English lyric. See `04-QUERIES.md`, Q-11.
- One record contains a **stage direction left in the shipped data** by the
  developers (a note on how a line is to be performed). It is preserved as a
  parenthetical, not deleted and not translated into dialogue. See Q-03.

## 6. Hard constraints

1. **Per-string byte budget.** Shift-JIS bytes; ASCII is 1 byte. Roughly two
   ASCII characters per source character, and *only* that. Short strings are
   brutal: a five-character source string gets fourteen bytes.
2. **ASCII only.** Anything outside ASCII costs two bytes and risks the
   encoder. No curly quotes, no en/em dashes, no ellipsis character.
3. **The game wraps on character count, not word boundaries.** A line that
   overruns breaks mid-word. Every break is therefore explicit.
4. **Line geometry**, by surface:
   - in-mission caption: **4 lines x 28 characters**, and the window is that
     size whether or not it is filled;
   - briefing / promotion / Global Report box: **3 lines x 44 characters**
     (measured at ~52; 44 is the safety margin).
5. **House ellipsis:** three ASCII periods, no space before. Used for a
   trailing-off line and for a fragment seam. Not used for a pause inside a
   sentence -- that is a comma or a dash-pair.
6. **No-go words:** no profanity above "damn" / "hell" (the source's ceiling
   is exactly there); no anachronism after 2003; no "mech", "mecha", "robot"
   for a Valkyrie (the source distinguishes -- see Glossary).
7. Reading age: about 13. Radio captions lower.

## 7. Who decides?

Anything the text cannot answer goes to `04-QUERIES.md` and is sorted into
Internal / Editor / Source. Editor cards are capped at **10** for this pass
(2,448 strings; the protocol's 1% would allow 24, the ten-per-thousand rule
allows 24 -- the lower cap is chosen deliberately because most of this script
is procedural radio with no interpretive room, and a large card count here
would be noise). Unresolved queries ship on their default and are listed in
`05-DEFERRED.md`.

## 8. Opened at Brief time (first Query Log entries)

- Q-01 Which English name set? -> **resolved: Japanese canon.** (S4)
- Q-02 Are the player's two wingmen fixed characters or per-mission extras?
- Q-11 How to render the diegetic song fragment.
- Q-12 How the runtime assembles the sentence-fragment radio pool.
