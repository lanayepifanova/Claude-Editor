#!/usr/bin/env python3
"""
verify.py — check the edit as DATA and report in text.

Replaces "render it and look at a screenshot" for everything except final taste.
Each finding is a line an agent can act on without an image entering context.

    python3 edit/verify.py
"""
import argparse, json, sys
from pathlib import Path

# card content roughly occupies the middle 68% of the frame width, and a band
# whose height depends on how much is in it. Approximated per block type.
BLOCK_H = {"headline": 200, "eyebrow": 100, "screenshot": 1150, "briefRow": 150,
           "waveform": 340, "handoff": 400, "split": 900, "checklist": 620, "rec": 60}


def card_box(card, res):
    """Approximate the card's bounding box in frame pixels."""
    h = sum(BLOCK_H.get(b["type"], 150) for b in card["blocks"])
    cy = res[1] / 2 + card.get("offsetY", 0)
    if card.get("anchor") == "top-right":
        return (res[0]*0.72, 150, res[0]*0.98, 260)
    return (res[0]*0.16, cy - h/2, res[0]*0.84, cy + h/2)


def cells_for(box, res, grid):
    gw, gh = grid
    x0, y0, x1, y1 = box
    return [(gx, gy)
            for gy in range(gh) for gx in range(gw)
            if not (x1 < gx*res[0]/gw or x0 > (gx+1)*res[0]/gw or
                    y1 < gy*res[1]/gh or y0 > (gy+1)*res[1]/gh)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="edit/manifest.json")
    ap.add_argument("--analysis", default="edit/analysis")
    a = ap.parse_args()

    m = json.load(open(a.manifest))
    an = Path(a.analysis)
    res, fps, dur = m["resolution"], m["fps"], m["duration"]
    cards = m["cards"]
    findings, notes = [], []

    # 1 ── same-track overlap
    by_track = {}
    for c in cards:
        by_track.setdefault(c["track"], []).append(c)
    for tr, cs in by_track.items():
        cs.sort(key=lambda c: c["start"])
        for x, y in zip(cs, cs[1:]):
            xe = x["start"] + x["duration"]
            if xe > y["start"] + 1e-6:
                findings.append(f"OVERLAP  track {tr}: {x['id']} ends {xe:.2f}s but "
                                f"{y['id']} starts {y['start']:.2f}s")

    # 2 ── off the end of the video
    for c in cards:
        e = c["start"] + c["duration"]
        if e > dur + 1e-6:
            findings.append(f"OVERRUN  {c['id']} ends {e:.2f}s, video is {dur:.2f}s")

    # 3 ── too fast to read
    for c in cards:
        if c["duration"] < 1.8:
            findings.append(f"TOO FAST {c['id']} is {c['duration']:.2f}s (min 1.8s)")

    # 4 ── beats outside their own card
    for c in cards:
        s, e = c["start"], c["start"] + c["duration"]
        for b in c.get("beats", []):
            if not (s - 1e-6 <= b["at"] <= e + 1e-6):
                findings.append(f"STRAY    {c['id']}.{b['target']} fires {b['at']:.2f}s, "
                                f"card is {s:.2f}-{e:.2f}s")

    # 5 ── frame-alignment
    for c in cards:
        for v, what in ((c["start"], "start"), (c["duration"], "duration")):
            if abs(round(v*fps) - v*fps) / fps > 1e-4:
                findings.append(f"OFF-GRID {c['id']} {what}={v} not on a {fps:g}fps frame")

    # 6 ── does the card sit on the subject? (uses framing.json, no images)
    fpath = an/"framing.json"
    if fpath.exists():
        fr = json.load(open(fpath))
        grid = fr["grid"]
        for c in cards:
            box = card_box(c, res)
            cells = cells_for(box, res, grid)
            if not cells: continue
            worst_t, worst = None, 1.0
            for s in fr["samples"]:
                if not (c["start"] <= s["t"] <= c["start"] + c["duration"]): continue
                safe = sum(1 for gx, gy in cells if s["cells"][gy][gx]["safe"])
                frac = safe/len(cells)
                if frac < worst: worst, worst_t = frac, s["t"]
            if worst_t is not None:
                pct = int(worst*100)
                if worst < 0.25:
                    notes.append(f"{c['id']:<6} sits over the subject at {worst_t:.1f}s "
                                 f"({pct}% clear) — knockout edge doing the work")
                else:
                    notes.append(f"{c['id']:<6} clear background {pct}% at its worst "
                                 f"({worst_t:.1f}s)")
    else:
        notes.append("framing.json missing — run preprocess.py for placement checks")

    # 7 ── cue-pinned beats still land on the word they were pinned to
    tpath = an/"transcript.json"
    if tpath.exists():
        words = json.load(open(tpath))["words"]
        for c in cards:
            for b in c.get("beats", []):
                cue = b.get("cue")
                if not cue: continue
                toks = cue.lower().split()
                hit = None
                for i in range(len(words) - len(toks) + 1):
                    if [words[i+k]["w"].lower().strip(".,!?") for k in range(len(toks))] == toks:
                        hit = words[i]["t0"]; break
                if hit is None:
                    findings.append(f"CUE?     {c['id']}.{b['target']} pinned to \"{cue}\" — "
                                    f"not found in transcript")
                elif abs(hit - b["at"]) > 0.15:
                    findings.append(f"CUE DRIFT {c['id']}.{b['target']} fires {b['at']:.2f}s but "
                                    f"\"{cue}\" is at {hit:.2f}s")
                else:
                    notes.append(f"{c['id']}.{b['target']:<6} on cue \"{cue}\" ({hit:.2f}s)")

    # 8 ── dead air with nothing on screen
    spans = sorted(
        [(c["start"], c["start"]+c["duration"]) for c in cards if c["track"] == 1] +
        [(c["start"], c["start"]+c["duration"]) for c in m.get("externalCards", [])])
    merged = []
    for s_, e_ in spans:
        if merged and s_ <= merged[-1][1] + 1e-6:
            merged[-1][1] = max(merged[-1][1], e_)
        else:
            merged.append([s_, e_])
    spans = merged
    t = 0.0
    for s, e in spans:
        if s - t > 1.5:
            notes.append(f"gap    {t:.2f}-{s:.2f}s ({s-t:.1f}s with no graphic)")
        t = max(t, e)
    if dur - t > 1.5:
        notes.append(f"gap    {t:.2f}-{dur:.2f}s ({dur-t:.1f}s with no graphic)")

    print(f"cards {len(cards)} · beats {sum(len(c.get('beats',[])) for c in cards)} · {dur:.2f}s\n")
    for n in notes: print("  ·", n)
    print()
    if findings:
        for f in findings: print("  ✗", f)
        print(f"\n{len(findings)} problem(s)")
        sys.exit(1)
    print("  ✓ no problems")


if __name__ == "__main__":
    main()
