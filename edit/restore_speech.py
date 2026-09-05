#!/usr/bin/env python3
"""Find speech the silence pass deleted, and write the overrides that keep it.

The locked recipe triggers on -35 dB and holds down to -37. Speech quieter than
that — a trailing word, the end of a sentence she drops her voice on — never
trips the trigger and is removed as room tone. On "instinct" that ate "weeks"
out of "in just the last few weeks" (peak -39 dB) and punched a 0.16s hole
inside "public yet", so both phrases sounded cut out.

This does NOT touch the recipe. It reads the envelope, finds runs inside the
REMOVED regions that are clearly above room tone (>-45 dB for >=0.06s), and
emits `edit/overrides-<name>.json` extending the neighbouring kept segment over
them — the mechanism preprocess.py already has for manual adjustment.

    python3 edit/restore_speech.py edit/analysis-instinct
    python3 edit/preprocess.py footage/instinct.mov --out edit/analysis-instinct \
        --overrides edit/overrides-instinct.json
"""
import argparse, json, sys
from pathlib import Path

QUIET   = -45.0   # above this is not room tone (which sits below -50 on these clips)
MIN_RUN = 0.06    # shorter than this is a click, not a syllable
TAIL    = 0.04    # the recipe's own tail padding, reused for the restored edge
HOLE    = 0.10    # a gap this short inside continuous speech is a chopped word
ADJ     = 0.12    # how far speech may sit from the cut and still be its tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis")
    ap.add_argument("--out", help="default: edit/overrides-<name>.json")
    ap.add_argument("--quiet-db", type=float, default=QUIET)
    args = ap.parse_args()

    adir = Path(args.analysis)
    sil = json.load(open(adir / "silence.json"))
    env = json.load(open(adir / "envelope.json"))
    v, win = env["values"], env["window"]
    segs = [list(s) for s in sil["segments"]]
    dur = sil["source_duration"]

    gaps = []
    for i in range(len(segs) - 1):
        if segs[i+1][0] - segs[i][1] > 0.02:
            gaps.append((segs[i][1], segs[i+1][0], i))
    if dur - segs[-1][1] > 0.02:
        gaps.append((segs[-1][1], dur, len(segs) - 1))

    new = [list(s) for s in segs]
    found = []
    for a, b, prev in gaps:
        i0, i1 = int(a / win), int(b / win)
        runs, st = [], None
        for i in range(i0, i1):
            if v[i] > args.quiet_db and st is None:
                st = i
            elif v[i] <= args.quiet_db and st is not None:
                if (i - st) * win >= MIN_RUN:
                    runs.append((st * win, i * win, max(v[st:i])))
                st = None
        if st is not None and (i1 - st) * win >= MIN_RUN:
            runs.append((st * win, i1 * win, max(v[st:i1])))
        if not runs:
            continue
        # Only speech that CONTINUES from the cut is a clipped word. A blip
        # sitting alone in the middle of a long pause is a breath or a lip
        # noise, and reaching out to it would restore the whole pause with it
        # — on "polymarket" that turned a 35s cut into 46s.
        lead, tail_runs = [], []
        edge = a
        for s0, e0, pk in runs:                   # forward from the cut we just made
            if s0 - edge <= ADJ:
                tail_runs.append((s0, e0, pk)); edge = e0
            else:
                break
        edge = b
        for s0, e0, pk in reversed(runs):         # backward from where speech resumes
            if (s0, e0, pk) in tail_runs:
                break
            if edge - e0 <= ADJ:
                lead.append((s0, e0, pk)); edge = s0
            else:
                break
        if tail_runs:
            new[prev][1] = max(new[prev][1], tail_runs[-1][1] + TAIL)
        if lead and prev + 1 < len(new):
            new[prev+1][0] = min(new[prev+1][0], lead[-1][0] - 0.02)
        if tail_runs or lead:
            found.append((a, b, prev, tail_runs + list(reversed(lead))))

    # A restored tail can now reach into the next segment, and a sub-0.10s hole
    # left inside continuous speech is a chopped word either way — merge both.
    dropped = set()
    for i in range(len(new)):
        if i in dropped:
            continue
        j = i + 1
        while j < len(new) and new[j][0] - new[i][1] <= HOLE:
            new[i][1] = max(new[i][1], new[j][1])
            dropped.add(j)
            j += 1

    changed = {}
    for i in range(len(segs)):
        if i in dropped:
            continue
        adj = {}
        if round(new[i][0], 3) != round(segs[i][0], 3): adj["in"] = round(new[i][0], 3)
        if round(new[i][1], 3) != round(segs[i][1], 3): adj["out"] = round(new[i][1], 3)
        if adj: changed[str(i)] = adj

    # every dropped segment must be swallowed by a kept one, or its audio is lost
    for d in sorted(dropped):
        if not any(new[i][0] <= segs[d][0] and new[i][1] >= segs[d][1]
                   for i in range(len(new)) if i not in dropped):
            sys.exit(f"refusing: seg {d} ({segs[d][0]:.2f}-{segs[d][1]:.2f}) "
                     "would be dropped without a neighbour covering it")

    ov = {"segments": changed, "drop": sorted(dropped)}
    name = adir.name.replace("analysis-", "")
    out = Path(args.out or f"edit/overrides-{name}.json")
    json.dump(ov, open(out, "w"), indent=2)

    for a, b, prev, runs in found:
        print(f"  removed {a:6.2f}-{b:<6.2f} held speech: " +
              "  ".join(f"{s:.2f}-{e:.2f} peak {p:.0f}dB" for s, e, p in runs))
    kept_old = sum(e - s for s, e in segs)
    kept_new = sum(e - s for i, (s, e) in enumerate(new) if i not in dropped)
    print(f"\n  {len(found)} spot(s) · {len(changed)} extension(s) · "
          f"{len(dropped)} merge(s)")
    print(f"  cut {kept_old:.2f}s -> {kept_new:.2f}s  (+{kept_new-kept_old:.2f}s restored)")
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
