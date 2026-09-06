# Review record

Four passes, deliberately separated. What each one found, and what changed
in the artifacts as a result.

**State:** 2,732 of 2,739 translatable strings translated. The remaining
seven are the memory-card save titles, deliberately untouched and logged.

---

## Pass 1 -- bilingual accuracy (source beside target)

Run scene by scene during drafting, then again on the assembled file.

| Finding | Type | Severity | Fix |
|---|---|---|---|
| Misa Hayase's rank changes mid-script; early drafts used "Captain" before her promotion | accuracy | major | Rank checked per row against position. Glossary now carries the trap explicitly. |
| Two voice indices both say "Skull Leader"; briefly translated as two officers | accuracy | major | Both are Focker. The developer stage direction at row 779 names him. Cast map added to the Voice Cards. |
| "B mode" rendered literally in first draft | terminology | minor | Expanded to "Battroid mode". Glossary rule added. |
| Transformation (the ship) vs transformation (a Valkyrie) collapsed in three lines | terminology | major | Capitalisation rule locked in the Glossary. Row 359 -- a rookie asking what the word means -- is the load-bearing case. |
| Six developer stage directions found inside shipped records | accuracy | major | Preserved as parentheticals, not deleted. Q-06. |

## Pass 2 -- monolingual read (source hidden)

Read as an English reader, mechanically assisted.

| Finding | Type | Severity | Fix |
|---|---|---|---|
| "Barrier failing" / "Barrier falling" / "Barrier output falling" across five adjacent callouts | fluency | minor | Locked to "Barrier failing!" for rows 862-866. |
| "Macross main gun hit" vs "...damaged" for one source string | terminology | minor | Unified. |
| `Apollo Leader...! No....` -- four dots | style | minor | Fixed. House ellipsis rule now mechanically checked. |
| `Gunpod` capitalised in three lines | terminology | minor | All three are sentence-initial. No change; rule confirmed. |
| Callsign density | style | -- | 6% of translated lines carry a callsign. The failure mode this guards against -- every radio line opening with a unit name -- did not occur. |

## Pass 3 -- voice audit (vertical, out of story order)

Every line by one speaker read consecutively, per the cast map.

| Finding | Type | Severity | Fix |
|---|---|---|---|
| The junior operator's over-polite address marker was carried in three lines and dropped in four | style/voice | minor | Restored at rows 685 and 1335. Rows 1664/1670 have no byte room; the Quirk Register's frequency policy covers this -- a quirk is not every line. |
| Emma reads as three different people across the tutorial, the mission control and the final sortie | style/voice | -- | **Correct.** This is her documented Phase Table, not drift. |
| "Meltran" in Captain Global's own narration (row 2543) | terminology | minor | Changed to "Meltrandi". The clipped form belongs only in Zentradi mouths. |
| Zentradi no-contraction rule | style/voice | -- | Held across all 109 bracketed transmissions and Britai's Global Report track. |

**Blind assignment test.** Twenty unattributed lines, shuffled, assigned by
voice alone. Focker, Eddie, Bruce, the junior operator and the Zentradi were
each identifiable from a single line. Emma's procedural lines are not
distinguishable from a generic bridge voice -- which is correct, because the
source gives them the same voice index. **Pass.**

## Pass 4 -- in-context

**Not run.** Nothing in this pass has been seen rendered in the game. Every
line is within its byte budget and its measured line geometry, verified
mechanically on every build of the file, but geometry measured off two
screenshots is not the same as geometry seen. See `05-DEFERRED.md` items 1
and 4 for exactly what a playtester should look at first.

---

## Mechanical checks (run on the finished file)

| Check | Result |
|---|---|
| Shift-JIS byte budget, every string | pass -- 0 over |
| ASCII-only (C7: zero CJK in the shipped file) | pass -- 0 non-ASCII characters |
| Line width and line count per surface | pass -- 0 over |
| Forbidden renderings (Robotech names, banned carriers) | pass -- 0 |
| Glossary term spelling consistency | pass |
| Enemy-transmission bracket convention | pass -- 109 of 109 |
| Player's gender left unmarked | pass -- no "sir", no pronoun, in any line addressed to the player |
| Same source string, differing English | 4 remaining, each deliberate and speaker-motivated |
| Rank ladder | consistent; abbreviations only where the byte slot forbids the spoken form |

## Definition of done

- [x] Every string translated in scene context, or explicitly logged (7 logged).
- [x] Query Log triaged into lanes; no unlogged guesses.
- [x] Escalation cards within budget: 4 of 10 spent, all closed or defaulted.
- [x] Deferred register handed over.
- [x] Glossary locked; zero unresolved variants.
- [x] Voice ledgers complete: address matrix, quirks with frequency and
      suspension, idiolect inventories, phase boundaries mapped to row ranges.
- [x] Blind assignment test passed.
- [ ] **In-context pass -- not run.** The one line item outstanding.
- [x] Artifacts in a state a stranger could continue from tomorrow.
