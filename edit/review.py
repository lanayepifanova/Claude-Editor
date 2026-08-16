#!/usr/bin/env python3
"""
review.py — print captions in the terminal for approval BEFORE rendering.

Rendering to check wording costs ~1 minute of GPU and a 45-100 MB file. Reading
them takes seconds. Run this, fix the wording, and only then render.

    python3 edit/review.py "project/Reddit.srt"
    python3 edit/review.py "project/Reddit.srt" --cues     # with timings
"""
import argparse, re, textwrap
from pathlib import Path

# things worth a second look: transcription tends to fail on these
SUSPECT = re.compile(
    r"\b(?:"
    r"[A-Z]{2,}\d+|"                       # AI8, 9S — letters glued to digits
    r"\d+[A-Za-z]{2,}|"
    r"[A-Z][a-z]+[A-Z][a-z]+"              # NeoCloud, HyperScale
    r")\b")
ODD_ENDINGS = {"a", "an", "the", "of", "in", "to", "and", "or", "for", "on", "at"}


def read(p):
    cues = []
    for b in Path(p).read_text().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3:
            continue
        a, z = L[1].split(" --> ")
        def s(ts):
            h, m, rest = ts.split(":")
            sec, ms = rest.split(",")
            return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000
        cues.append({"i": L[0], "start": s(a), "end": s(z), "text": " ".join(L[2:])})
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("srt")
    ap.add_argument("--cues", action="store_true", help="list each cue with timing")
    a = ap.parse_args()
    cues = read(a.srt)
    if not cues:
        raise SystemExit("no cues found")

    full = " ".join(c["text"] for c in cues)
    print("\n" + "="*78)
    print(f"  {Path(a.srt).name}  —  read this before rendering")
    print("="*78 + "\n")
    print(textwrap.fill(full, 76, initial_indent="  ", subsequent_indent="  "))
    print()

    if a.cues:
        print("-"*78)
        for c in cues:
            print(f"  {c['i']:>3}  {c['start']:6.2f}-{c['end']:5.2f}  {c['text']}")
        print()

    # flags
    flags = []
    for c in cues:
        for m in SUSPECT.findall(c["text"]):
            flags.append(f"{c['start']:6.2f}s  odd token \"{m}\"  in \"{c['text']}\"")
        last = c["text"].rstrip(".,!?").split()[-1].lower() if c["text"].split() else ""
        if last in ODD_ENDINGS:
            flags.append(f"{c['start']:6.2f}s  ends on \"{last}\"  \"{c['text']}\"")
    over = [c for c in cues if len(c["text"]) > 26]
    multi = [c for c in cues if "\n" in c["text"]]

    print("-"*78)
    print(f"  {len(cues)} cues · avg {sum(c['end']-c['start'] for c in cues)/len(cues):.2f}s "
          f"on screen · longest {max(len(c['text']) for c in cues)} chars")
    if over:  print(f"  ! {len(over)} cue(s) over 26 chars")
    if multi: print(f"  ! {len(multi)} multi-line cue(s)")
    if flags:
        print(f"\n  worth checking ({len(flags)}):")
        for f in flags[:12]:
            print(f"    {f}")
    else:
        print("  nothing obviously suspect")
    print()


if __name__ == "__main__":
    main()
