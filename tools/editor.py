#!/usr/bin/env python3
"""A small editor for the translation workbook.

    python3 tools/editor.py [work/workbook.csv]

A spreadsheet works too, but it will not tell you that a line is three bytes
too long for its slot -- and in this game that is the difference between a
finished sentence and a truncated one. So the byte budget is the centre of
this window: it updates as you type and turns red before you commit.

Saves to the CSV, and to `translation/english.json` (English and notes only,
never the Japanese) which is the file the repository actually ships.
"""
import csv
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ENGLISH = os.path.join(ROOT, "translation", "english.json")
FIELDS = ["id", "kind", "speaker", "budget_bytes", "caption",
          "japanese", "english", "notes"]


def sjis_len(s):
    try:
        return len(s.encode("shift_jis"))
    except UnicodeEncodeError:
        return -1


class Editor(tk.Tk):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.rows = list(csv.DictReader(open(path, encoding="utf-8")))
        self.title(f"Macross translation — {os.path.basename(path)}")
        self.geometry("1100x650")
        self._build()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._close)

    # --- layout ---------------------------------------------------------
    def _build(self):
        bar = ttk.Frame(self, padding=6)
        bar.pack(fill="x")
        self.only_todo = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="untranslated only", variable=self.only_todo,
                        command=self._refresh).pack(side="left")
        ttk.Label(bar, text="   filter:").pack(side="left")
        self.filter = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.filter, width=28)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _: self._refresh())
        self.progress = ttk.Label(bar, text="")
        self.progress.pack(side="right")
        ttk.Button(bar, text="Save", command=self._save).pack(side="right", padx=8)

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.Frame(pane)
        cols = ("id", "speaker", "japanese", "english")
        self.tree = ttk.Treeview(left, columns=cols, show="headings",
                                 selectmode="browse")
        for c, w in zip(cols, (110, 80, 320, 320)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._select)
        pane.add(left, weight=3)

        right = ttk.Frame(pane, padding=8)
        self.jp = tk.Text(right, height=6, wrap="word", state="disabled",
                          background="#f2f2f2")
        ttk.Label(right, text="Japanese").pack(anchor="w")
        self.jp.pack(fill="x")
        ttk.Label(right, text="English").pack(anchor="w", pady=(10, 0))
        self.en = tk.Text(right, height=6, wrap="word", undo=True)
        self.en.pack(fill="x")
        self.en.bind("<KeyRelease>", lambda _: self._count())
        self.budget = ttk.Label(right, text="")
        self.budget.pack(anchor="w", pady=4)
        self.caption = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, variable=self.caption,
                        text="show this line on screen (subtitle)",
                        command=self._apply).pack(anchor="w", pady=(6, 0))
        ttk.Label(right, wraplength=320, foreground="#555",
                  text="Most in-mission radio dialogue is spoken but not "
                       "displayed. Ticking this subtitles it. Captions get "
                       "four lines of 28 characters."
                  ).pack(anchor="w")
        ttk.Label(right, text="Notes").pack(anchor="w", pady=(10, 0))
        self.note = tk.Text(right, height=4, wrap="word")
        self.note.pack(fill="x")
        ttk.Button(right, text="Apply to this line",
                   command=self._apply).pack(anchor="e", pady=8)
        ttk.Label(right, wraplength=320, foreground="#555",
                  text="The game wraps on character count, not words, so a "
                       "long line can break mid-word. Keep lines short, or "
                       "put an explicit newline where the break belongs."
                  ).pack(anchor="w")
        pane.add(right, weight=2)
        self.current = None

    # --- behaviour ------------------------------------------------------
    def _visible(self):
        f = self.filter.get().lower()
        for r in self.rows:
            if self.only_todo.get() and r["english"].strip():
                continue
            if f and f not in (r["japanese"] + r["english"] + r["id"]).lower():
                continue
            yield r

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in self._visible():
            self.tree.insert("", "end", iid=r["id"],
                             values=(r["id"], r["speaker"],
                                     r["japanese"].replace("\n", "⏎"),
                                     r["english"].replace("\n", "⏎")))
        done = sum(1 for r in self.rows if r["english"].strip())
        self.progress.config(
            text=f"{done} / {len(self.rows)} translated "
                 f"({done / max(1, len(self.rows)):.0%})")

    def _select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        r = next(x for x in self.rows if x["id"] == sel[0])
        self.current = r
        self.jp.config(state="normal")
        self.jp.delete("1.0", "end")
        self.jp.insert("1.0", r["japanese"])
        self.jp.config(state="disabled")
        self.en.delete("1.0", "end")
        self.en.insert("1.0", r["english"])
        self.note.delete("1.0", "end")
        self.note.insert("1.0", r["notes"])
        self.caption.set((r.get("caption") or "on").lower() != "off")
        self._count()

    def _count(self):
        if not self.current:
            return
        s = self.en.get("1.0", "end-1c")
        n, cap = sjis_len(s), int(self.current["budget_bytes"])
        if n < 0:
            self.budget.config(text="cannot be encoded (Shift-JIS only)",
                               foreground="#b00")
        else:
            over = n - cap
            self.budget.config(
                text=f"{n} / {cap} bytes" + (f"  — {over} OVER" if over > 0 else ""),
                foreground="#b00" if over > 0 else "#070")

    def _apply(self):
        if not self.current:
            return
        self.current["english"] = self.en.get("1.0", "end-1c")
        self.current["notes"] = self.note.get("1.0", "end-1c")
        self.current["caption"] = "on" if self.caption.get() else "off"
        self._refresh()

    def _save(self):
        self._apply()
        over = [r["id"] for r in self.rows
                if r["english"].strip()
                and not 0 <= sjis_len(r["english"]) <= int(r["budget_bytes"])]
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, FIELDS)
            w.writeheader()
            w.writerows(self.rows)
        en = {}
        if os.path.exists(ENGLISH):
            en = json.load(open(ENGLISH, encoding="utf-8"))
        for r in self.rows:
            if not r["english"].strip():
                continue
            # The caption preference travels with the translated line. Turning
            # captions on wholesale is `tools/build.py --subtitles`, so there
            # is no need to record 2,675 defaults here.
            en[r["id"]] = {"en": r["english"], "note": r["notes"],
                           "caption": (r.get("caption") or "on").lower() != "off"}
        json.dump(en, open(ENGLISH, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        msg = f"Saved {self.path}\nand {len(en)} strings to translation/english.json"
        if over:
            msg += (f"\n\n{len(over)} line(s) are over their byte budget and "
                    f"will fail the build:\n" + ", ".join(over[:10]))
        messagebox.showwarning("Saved with problems", msg) if over else \
            messagebox.showinfo("Saved", msg)

    def _close(self):
        if messagebox.askyesno("Quit", "Save before closing?"):
            self._save()
        self.destroy()


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "work/workbook.csv")
    if not os.path.exists(p):
        sys.exit(f"{p} not found — run tools/make_workbook.py first")
    Editor(p).mainloop()
