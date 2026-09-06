# Query Log

Every ambiguity resolved during the pass, sorted into a lane at the moment it
was written. **Internal** = resolved by the pipeline. **Editor** = needs a
monolingual English editor's ruling. **Source** = only the developer or the
Japanese source can answer; ships on a default meanwhile.

Editor budget for this pass: **10 cards**. Spent: **4**. The rest of the
script is procedural radio with no interpretive room, and flagging it would
have made the four cards that matter invisible.

---

## Editor lane -- cards raised

### CARD Q-05 . rows 1697/1698, and ~120 dependent strings . priority HIGH

```
SCENE:   The promotion cutscene. Focker hands the player their own flight.
         The game then addresses the player by that unit name for the rest
         of the campaign, on the mission caption window.
LITERAL: From today ⟨I⟩ entrust Purple Squadron to you.
         ⟨I⟩ count on ⟨you⟩, Purple Leader.
GLOSS:   Two parallel strings exist, one for each posting the player can
         choose at the start (Prometheus -> Purple, ARMD-1 -> Apollo).
QUESTION: Should the two branches keep visibly different unit names in
         English, or be unified?
OPTION A: Keep both -- "Purple Leader" and "Apollo Leader".
         implies: the posting choice is visible for the whole game
         commits us to: two variants of ~120 later strings, already written
         costs: nothing; the source already ships both sets
OPTION B: Unify to one name.
         implies: the branch is cosmetic
         commits us to: overwriting one branch's strings
         costs: erases a choice the game makes the player make in scene 1
WHY UNSURE: Nothing; A is obviously right.
DEFAULT: A. **Closed without escalation** -- fails the Novelty and
         Consequence tests once written out. Recorded here as an example
         of a card that was drafted and then correctly not sent.
```

### CARD Q-06 . row 779 . speaker: Roy Focker . priority HIGH

```
SCENE:   Mid-mission radio, the fight in which Focker is mortally wounded.
LITERAL: Ngh-- [and then, in parentheses, a note addressed to the voice
         actor: "he takes his fatal wound here; Focker does not let it
         show; it bleeds into the voice a little"]
GLOSS:   A stage direction the developers left inside the shipped data.
         It is not dialogue. It has a voice id and can be captioned.
QUESTION: Should the direction be shown to the player, or removed?
OPTION A: Keep it, as a parenthetical after the grunt.
         implies: the player sees a piece of the game's own making
         commits us to: one visibly odd caption
         costs: breaks the fiction for two seconds
OPTION B: Ship only "Ngh--" and drop the direction.
         implies: a tidy caption
         commits us to: deleting shipped source content
         costs: the line becomes a bare grunt with no weight, and the
         translation quietly destroys something the source contains
WHY UNSURE: Nothing in the data says whether this line is ever drawn.
WOULD SETTLE IT: Watching the mission with --subtitles on.
DEFAULT: **A.** Rule 8, nothing lost. A translator may delete nothing the
         publisher shipped. Flagged in the Deferred register for a
         playtester to confirm; if it renders badly, B is a one-line change.
PROPAGATION: rows 779, 1453, 1454, 1470, 2237, 2245 -- six directions in all.
```

### CARD Q-11 . row 893 . priority MEDIUM

```
SCENE:   Mid-mission. The ship's TV station bleeds into the military
         radio band, and a few seconds of a Lynn Minmay song come through.
LITERAL: Three music-note lines: an English word, one line of lyric, and
         the song's title. (Not quoted here -- see GLOSS.)
GLOSS:   A fragment of a real, copyrighted Lynn Minmay song, quoted
         diegetically. The line's job is "her song is on this channel",
         not "here are the words". The lyric is therefore not reproduced
         in this repository either.
QUESTION: How should a snatch of a real, copyrighted song be rendered?
OPTION A: A diegetic marker, no lyric: "~ (Minmay's song, bleeding /
         ~ across from the ship's / ~ broadcast)".
         implies: the player learns exactly what the line is for
         commits us to: not shipping an English lyric
         costs: the specific words are gone
OPTION B: An invented English lyric translation.
         implies: a singable line on screen
         commits us to: publishing a derivative of a copyrighted song
         costs: legal exposure for the patch, and a bad lyric
DEFAULT: **A, shipped.** The function survives; the copyrighted content
         does not travel. Logged so that nobody "restores" it later.
```

### CARD Q-13 . rows 2615-2618 . priority LOW

```
SCENE:   The Global Report's civilian-diary commentary track.
LITERAL: [2616] ...the head of the town association entered ⟨me⟩ without
         asking, so ⟨I⟩ ended up going in too.
         [2618] The contest was a great success, and Minmay-chan was
         splendidly chosen Miss Macross.
GLOSS:   2616 says the speaker entered the contest; 2618 names Minmay in
         the third person with a familiar suffix. Either the narrator is a
         friend of Minmay's who also entered, or the writer slipped.
QUESTION: Is this track Minmay's own diary, or a classmate's?
OPTION A: Keep both persons exactly as written -- "entered me", "Minmay
         was chosen". Reads as a friend's diary.
OPTION B: Regularise to Minmay's own voice -- "somehow I was chosen".
DEFAULT: **A, shipped.** Rule 5: do not resolve what the source leaves
         open. Row 2651 in the same track is unmistakably Minmay, which
         makes B tempting and A honest.
```

---

## Source lane -- would need the developer

| # | Question | Ships on |
|---|---|---|
| Q-07 | Are the "x"-prefixed records (rows 233-248, 317, 367-368, 427, 465, 492, 495, 560, 623-641, 647-649, 699-702, 705, 787, 1080-1081, 1084-1085, 1141, 1166-1169, 1173-1174) cut content, or live lines with a visible marker? | Marker dropped, line translated. If they are cut, nothing is lost; if they are live, the English is correct and the marker would only have looked like corruption. |
| Q-08 | Is "Makdomilla" (rows 821-822) a person, a ship, or a unit? Kamjin hails it by name and it answers. | Treated as a unit callsign and transliterated. |
| Q-09 | "Bernal class" (rows 91, 93) -- the Zentradi branch-fleet flagship class. No canon English spelling found. | Transliterated "Bernal". |
| Q-10 | "kaarchuun" (row 1448) -- a Zentradi word for inherited cultural memory. | Transliterated, unglossed, as the source leaves it. |
| Q-12 | How does the runtime assemble the sentence-fragment radio pool (rows 1961-2144)? Concatenated into one caption, or played as a queue of separate ones? Is a separator inserted? | Fragments mirror the source's own seam marks: a piece that begins with an ellipsis in Japanese begins with "..." in English. Reads correctly under either assembly. See the Deferred register. |

---

## Internal lane -- resolved, recorded, not escalated

| # | Question | Resolution |
|---|---|---|
| Q-01 | Which English name set -- canon Japanese or Robotech? | Japanese canon. Brief S4. |
| Q-02 | Are the player's two wingmen fixed characters or per-mission extras? | Fixed. Eddie Juutilainen is always 2, Bruce Rudel always 3; they self-identify by callsign in six separate missions and die under those numbers. Seven voice indices resolve onto the two of them. |
| Q-03 | The developers' stage directions inside the data. | Preserved as parentheticals. See Q-06. |
| Q-04 | What is the "x" prefix on ~40 records? | A cut/duplicate marker. Every "x" line duplicates a nearby line or belongs to a block of alternate banter. Dropped from the English because an ASCII "x" on screen would read as corruption. |
| Q-14 | Two speakers say "Skull Leader" -- Focker, and someone else? | Both are Focker; two recording sessions, two voice indices (038, 042). Confirmed by the stage direction at row 779, which names him. |
| Q-15 | Is Misa Hayase a First Lieutenant or a Captain? | Both. She is promoted between rows 63 and 73; the script marks it explicitly at row 697. Rank checked per row against position. |
| Q-16 | "B mode" -- keep the source's single-letter shorthand? | No. Expanded to "Battroid mode". A bare letter is unreadable at radio speed, and the game's own briefings spell it out elsewhere. |
| Q-17 | Player's gender. | Never marked in the source. Never marked in the English: no "sir", no pronoun, in any of the ~600 lines addressed to the player. Checked mechanically. |
| Q-18 | Zentradi transmissions are wrapped in corner brackets in the source. | Rendered as [square brackets], on all 109 of them. |
| Q-19 | Do the rank-vocative line sets need all six ranks? | Yes; six parallel strings exist for each. Second Lieutenant and Lieutenant Colonel are abbreviated only where the byte slot refuses the spoken form (rows 670, 674, 1751, 1756, 1762, 1771, 1786, 1804). |
| Q-20 | "Meltran" vs "Meltrandi". | "Meltrandi" everywhere except inside Zentradi speech, where their own clipped form is kept (rows 1393, 1394, 2669). |
