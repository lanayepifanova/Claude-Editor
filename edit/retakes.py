#!/usr/bin/env python3
"""
retakes.py — find repeated takes in a cut and keep only the LAST one.

Her rule (2026-09-21): "if a sentence repeats twice, that means it's a retake,
so cut out all repeats of that sentence or line besides the last one, since the
last one is the usable take."

The silence pass removes dead air; this removes the *content* that was said
more than once. It runs AFTER preprocess.py, reads the word timings off the cut
timeline, maps the doomed spans back into SOURCE time, and writes them as a
`remove` list in an overrides file. preprocess.py then re-runs with
--overrides and excises them, so the proof, the transcript and the captions are
all regenerated consistently. The locked silence recipe is never touched.

    python3 edit/preprocess.py footage/clip.MOV --out edit/analysis-<name>
    python3 edit/retakes.py edit/analysis-<name>          # review the report
    python3 edit/preprocess.py footage/clip.MOV --out edit/analysis-<name> \
        --overrides edit/overrides-<name>.json

Two shapes count as a superseded take:
  * a near-duplicate line  — same words, said again (difflib ratio >= --sim)
  * a false start          — an abandoned run that the next attempt restates
                             from the top (prefix of a later line)
Only nearby lines are compared (--window), because a phrase legitimately
repeated a minute later is rhetoric, not a retake.
"""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

# a pause this long on the CUT timeline ends a line even without punctuation
GAP_SPLIT = 0.60
PUNCT_END = ".?!"


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def lines(words):
    """Group word tokens into spoken lines: sentence punctuation, or a pause."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        text = w["w"].strip()
        gap = (words[i+1]["t0"] - w["t1"]) if i + 1 < len(words) else 99.0
        if (text and text[-1] in PUNCT_END) or gap >= GAP_SPLIT:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def tokens(words, idx):
    return [t for t in (norm(words[i]["w"]) for i in idx) if t]


def is_prefix_restart(a, b, min_words):
    """a is an abandoned run that b restarts from the top."""
    if len(a) < min_words or len(b) <= len(a):
        return False
    n = min(len(a), len(b))
    same = sum(1 for k in range(n) if a[k] == b[k])
    return same >= min_words and same / len(a) >= 0.8


def cut_to_source(segments):
    """Return f(cut_time) -> source_time plus the segment's cut-time bounds."""
    marks, acc = [], 0.0
    for s, e in segments:
        marks.append((acc, acc + (e - s), s))
        acc += e - s
    def f(t):
        for c0, c1, s0 in marks:
            if t < c1 or (c0, c1, s0) == marks[-1]:
                return s0 + max(0.0, t - c0), (c0, c1, s0)
        return marks[-1][2], marks[-1]
    return f, marks


# a leftover shorter than this is not a word, it is the stub of the take we
# just removed — snap the span out to the segment edge and take it with us
RESIDUE = 0.30


def source_spans(c0, c1, marks):
    """Map a cut-time span onto the source intervals it covers."""
    out = []
    for m0, m1, s0 in marks:
        lo, hi = max(c0, m0), min(c1, m1)
        if hi > lo:
            a, b = s0 + (lo - m0), s0 + (hi - m0)
            seg_end = s0 + (m1 - m0)
            if a - s0 < RESIDUE:       # nothing usable before the span
                a = s0
            if seg_end - b < RESIDUE:  # nothing usable after it
                b = seg_end
            out.append([round(a, 3), round(b, 3)])
    merged = []
    for s, e in out:
        if merged and s - merged[-1][1] < 1e-6:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis")
    ap.add_argument("--out", default="",
                    help="overrides file to write (default edit/overrides-<name>.json)")
    ap.add_argument("--sim", type=float, default=0.72,
                    help="difflib ratio above which two lines are the same take")
    ap.add_argument("--window", type=int, default=6,
                    help="how many lines ahead to look for the next attempt")
    ap.add_argument("--min-words", type=int, default=3,
                    help="ignore repeats shorter than this — they are just phrasing")
    ap.add_argument("--apply", action="store_true",
                    help="write the overrides file (default is report only)")
    a = ap.parse_args()

    an = Path(a.analysis)
    words = json.load(open(an / "transcript.json"))["words"]
    sil = json.load(open(an / "silence.json"))
    segs = sil["segments"]
    if not words:
        sys.exit("no transcript — run preprocess.py first")

    ls = lines(words)
    toks = [tokens(words, idx) for idx in ls]

    # group[i] = index of the line that supersedes i (transitively resolved)
    superseded_by = {}
    for i in range(len(ls)):
        if len(toks[i]) < a.min_words:
            continue
        for j in range(i + 1, min(i + 1 + a.window, len(ls))):
            if len(toks[j]) < a.min_words:
                continue
            ratio = SequenceMatcher(None, toks[i], toks[j]).ratio()
            why = None
            if ratio >= a.sim:
                why = f"repeat (ratio {ratio:.2f})"
            elif is_prefix_restart(toks[i], toks[j], a.min_words):
                why = "false start"
            if why:
                superseded_by[i] = (j, why)
                break

    # resolve chains so only the LAST take of a run survives
    doomed = {}
    for i, (j, why) in superseded_by.items():
        k, seen = j, {i}
        while k in superseded_by and k not in seen:
            seen.add(k)
            k = superseded_by[k][0]
        doomed[i] = (k, why)

    removals, report = [], []
    for i in sorted(doomed):
        k, why = doomed[i]
        idx = ls[i]
        w0, w1 = words[idx[0]], words[idx[-1]]
        # take the whole line plus the air the cut left around it, but never
        # reach into a neighbouring word
        prev_end = words[idx[0] - 1]["t1"] if idx[0] > 0 else 0.0
        nxt_start = (words[idx[-1] + 1]["t0"] if idx[-1] + 1 < len(words)
                     else w1["t1"] + 1.0)
        c0 = max(prev_end, w0["t0"] - 0.08)
        c1 = min(nxt_start, w1["t1"] + 0.08)
        # ...but never let the pad reach into the segment holding a NEIGHBOURING
        # word. Whisper ends each word exactly where the next one starts, so the
        # doomed line's last word appears to run a beat past the join it sits
        # on; padding from there eats the first word of the take that replaces
        # it. Anchor on the neighbours' segments, not on the line's own.
        marks = cut_to_source(segs)[1]
        def hold(t):
            for m0, m1, _ in marks:
                if m0 <= t < m1:
                    return m0, m1
            return marks[-1][0], marks[-1][1]
        nxt_seg_start = hold(nxt_start)[0]
        if nxt_seg_start > w1["t0"]:          # the next word lives further on
            c1 = min(c1, nxt_seg_start)
        if idx[0] > 0:
            prev_seg_end = hold(words[idx[0] - 1]["t0"])[1]
            if prev_seg_end < w1["t1"]:       # the previous word ended earlier
                c0 = max(c0, prev_seg_end)
        spans = source_spans(c0, c1, marks)
        removals += spans
        report.append({
            "line": " ".join(words[n]["w"] for n in idx),
            "kept_instead": " ".join(words[n]["w"] for n in ls[k]),
            "why": why, "cut": [round(c0, 3), round(c1, 3)], "source": spans,
        })

    removals.sort()
    merged = []
    for s, e in removals:
        if merged and s - merged[-1][1] < 0.02:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

    total = sum(e - s for s, e in merged)
    for r in report:
        print(f"  DROP  {r['cut'][0]:7.2f}-{r['cut'][1]:7.2f}  [{r['why']}]")
        print(f"        {r['line']}")
        print(f"     -> keeping: {r['kept_instead']}")
    print(f"\n  {len(report)} superseded take(s) · {total:.2f}s of source removed")

    if not a.apply:
        print("  (report only — re-run with --apply to write the overrides)")
        return

    name = an.name.replace("analysis-", "")
    dest = Path(a.out) if a.out else Path("edit") / f"overrides-{name}.json"
    data = json.load(open(dest)) if dest.exists() else {}
    data["remove"] = merged
    json.dump(data, open(dest, "w"), indent=1)
    print(f"  -> {dest}")


if __name__ == "__main__":
    main()
