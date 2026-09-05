#!/usr/bin/env python3
"""Measure the recompressed script size against how much is translated.

This exists because the obvious intuition is wrong in a way that costs a day.
Two things had to be learned the hard way:

* A *full* English translation compresses far smaller than the Japanese
  original, so "will it fit" looks like a non-question.
* Translating the **short, repetitive** lines first makes the file **grow**.
  Lines like the acknowledgements and the twelve clock bearings differ by one
  character and cost almost nothing compressed; their English replacements are
  novel text. Do the menus and HUD callouts first -- which is exactly what a
  sensible person does -- and the file gets bigger, not smaller.

So the honest way to know is to measure. This sweeps coverage from 0% to 100%
and reports the peak against the space actually allocated.

    python3 stress/sizesweep.py "Macross (Japan).iso"
"""
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import cvmexpand                                            # noqa: E402
import text as gametext                                     # noqa: E402
from gamedata import CRICMP, need_cricmp, script_blob       # noqa: E402

# A deliberately wide vocabulary drawn with a Zipf-ish bias, so the generated
# text repeats common words the way real prose does instead of cycling a
# handful of them. Narrow filler (lorem ipsum) flatters the codec.
WORDS = ("the of and to a in is it you that he was for on are with as his they "
         "be at one have this from or had by hot but some what there we can out "
         "other were all your when up use word how said an each she which do "
         "their time if will way about many then them would write like so these "
         "her long make thing see him two has look more day could go come did "
         "my sound no most number who over know water than call first people may "
         "down side been now find any new work part take get place made live "
         "where after back little only round man year came show every good me "
         "give our under name very through just form much great think say help "
         "low line before turn cause same mean differ move right boy old too "
         "does tell sentence set three want air well also play small end put "
         "home read hand port large spell add even land here must big high such "
         "follow act why ask men change went light kind off need house picture "
         "try us again animal point mother world near build self earth father "
         "head stand own page should country found answer school grow study "
         "still learn plant cover food sun four thought let keep eye never last "
         "door between city tree cross since hard start might story saw far sea "
         "draw left late run don't while press close night real life few north "
         "book carry took science eat room friend began idea fish mountain stop "
         "once base hear horse cut sure watch colour face wood main enough plain "
         "girl usual young ready above ever red list though feel talk bird soon "
         "body dog family direct pose leave song measure state product black "
         "short numeral class wind question happen complete ship area half rock "
         "order fire south problem piece told knew pass since top whole king "
         "street inch multiply nothing course stay wheel full force blue object "
         "decide surface deep moon island foot system busy test record boat "
         "common gold possible plane stead dry wonder laugh thousand ago ran "
         "check game shape equate miss brought heat snow tire bring yes distant "
         "fill east paint language among").split()


def sentence(rng, budget, tag):
    out = f"{tag} " if tag else ""
    while len(out) < budget:
        w = WORDS[min(int(rng.paretovariate(1.1)) - 1, len(WORDS) - 1)]
        if len(out) + len(w) + 1 > budget:
            break
        out += w + " "
    return (out.strip() or "ok")[:budget]


def payload(units, fraction, rng, order="spread", fill=False):
    """`order` decides *which* lines get translated first.

    It matters more than how many. "spread" takes an even slice; "short-first"
    does the menus and one-word callouts before the prose, which is both what
    a translator naturally does and the order that makes the file grow."""
    if order == "short-first":
        ranked = sorted(units, key=lambda u: len(u.text))
    else:
        ranked = [u for i, u in enumerate(units) if i % 100 < fraction]
    chosen = ranked[:len(units) * fraction // 100] if order == "short-first" else ranked
    out = {}
    for u in chosen:
        want = u.budget if fill else min(u.budget, max(4, int(len(u.text) * 1.9)))
        out[u.uid] = sentence(rng, want, "")
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: sizesweep.py "Macross (Japan).iso"')
    need_cricmp()
    iso = sys.argv[1]
    blob = script_blob(iso)
    units = [u for u in gametext.units(blob) if u.needs_translation]
    cap = cvmexpand.allocation(iso, "JPN.CVM", "BOOTDAT.CMP")[0]

    def size(p):
        out, _ = gametext.apply(blob, p)
        tmp = os.path.join(ROOT, "work", "_sweep")
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        open(tmp + ".bin", "wb").write(out)
        subprocess.run([CRICMP, "enc", tmp + ".bin", tmp + ".cmp"],
                       check=True, stdout=subprocess.DEVNULL)
        return os.path.getsize(tmp + ".cmp")

    rng = random.Random(7)
    print(f"  {len(units)} translatable strings; {cap} bytes allocated\n")
    print("   translated      spread   short-first")
    peak = 0
    for pct in range(0, 101, 10):
        a = size(payload(units, pct, rng, "spread"))
        b = size(payload(units, pct, rng, "short-first"))
        peak = max(peak, a, b)
        flag = "   <-- over" if b > cap or a > cap else ""
        print(f"      {pct:>3}%      {a:>7}       {b:>7}{flag}")
    real = os.path.join(ROOT, "translation", "english.json")
    if os.path.exists(real):
        import json
        got = json.load(open(real, encoding="utf-8"))
        by = {u.uid for u in units}
        p = {k: v["en"] for k, v in got.items() if k in by}
        n = size(p)
        peak = max(peak, n)
        print(f"\n  the real translation/english.json ({len(p)} strings): {n}"
              f"   {'fits' if n <= cap else f'OVER by {n - cap}'}")
        print("  Generated text understates this: it reuses a small pool of "
              "common words, while a real translation is full of distinct "
              "domain vocabulary the codec has never seen. Trust this line "
              "over the sweep.")

    worst = size(payload(units, 100, rng, "spread", fill=True))
    peak = max(peak, worst)
    print(f"\n  every slot filled to the brim: {worst}")
    print(f"  peak {peak} against {cap} allocated -- "
          f"{'fits' if peak <= cap else f'SHORT BY {peak - cap}'}")
    if peak > cap:
        print("  tools/build.py rebuilds the container when this happens; see "
              "tools/cvmexpand.py")


if __name__ == "__main__":
    main()
