#!/usr/bin/env python3
"""
captions_overlay.py — transcript.json -> a HyperFrames caption overlay.

Premiere exposes no caption-positioning API, so social-style captions are burned
as a transparent overlay instead. Everything is driven by the analysis, so this
never needs a screenshot to place.

    python3 edit/captions_overlay.py --analysis edit/analysis-Reddit \
        --out graphics/reddit-captions --res 1080x1920 --y 0.25
"""
import argparse, json, re, sys
from pathlib import Path

# TikTok-style: short punchy chunks, not broadcast single-lines
MAX_CHARS = 26          # overwritten in main() from width / font size
# never strand these at the end of a cue — they read as a dangling fragment
ORPHAN = {"a","an","the","of","in","to","and","or","for","on","at","is","it",
          "my","your","that","this","with","but","so","if","as","be","was",
          # interrogatives / relatives — a cue ending on one dangles hard
          "which","who","what","when","where","why","how",
          # modals and auxiliaries, always followed by their verb
          "would","could","should","will","can","do","does","did","have","has",
          # prepositions and determiners that bind forward to a noun
          "into","onto","from","through","any","some","each","other","more",
          "most","new","very","our","their","its","you","we","they",
          # hedges that modify the word after them
          "roughly","sometimes","just","like","really","also",
          # noun-modifiers common in this footage ("AI agents", "SEO tool")
          "ai","seo"}
MAX_DUR   = 2.2
MIN_DUR   = 0.55
GAP_SPLIT = 0.45          # a pause this long starts a new cue


def apply_fixes(words, fixes):
    """Replace mis-heard word SEQUENCES, keeping the original timing span."""
    n = 0
    for wrong, right in fixes.items():
        wt = wrong.split()
        rt = right.split()
        i = 0
        while i <= len(words) - len(wt):
            window = [words[i+k]["w"].lower().strip(".,!?'\"") for k in range(len(wt))]
            if window == [x.lower().strip(".,!?'\"") for x in wt]:
                t0, t1 = words[i]["t0"], words[i+len(wt)-1]["t1"]
                tail = words[i+len(wt)-1]["w"]
                punct = tail[-1] if tail and tail[-1] in ".,!?" else ""
                step = (t1 - t0) / max(len(rt), 1)
                repl = [{"w": rt[k] + (punct if k == len(rt)-1 else ""),
                         "t0": round(t0 + k*step, 3),
                         "t1": round(t0 + (k+1)*step, 3)} for k in range(len(rt))]
                words[i:i+len(wt)] = repl
                n += 1
                i += len(rt)
            else:
                i += 1
    return words, n


def group(words):
    cues, cur, carry = [], [], []
    def flush():
        nonlocal cur
        if cur:
            txt = re.sub(r"\s+", " ", " ".join(w["w"] for w in cur)).strip()
            if txt:
                cues.append({"start": cur[0]["t0"], "end": cur[-1]["t1"], "text": txt,
                             "words": list(cur)})
        cur = []
    for w in words:
        if cur:
            prospective = " ".join(x["w"] for x in cur + [w]).strip()
            gap = w["t0"] - cur[-1]["t1"]
            if len(prospective) > MAX_CHARS or gap >= GAP_SPLIT or \
               w["t1"] - cur[0]["t0"] > MAX_DUR:
                # pull a trailing function word forward rather than stranding it
                while len(cur) > 1 and \
                        cur[-1]["w"].lower().strip(".,!?'\"") in ORPHAN:
                    w2 = cur.pop()
                    carry.append(w2)
                flush()
                while carry:
                    cur.append(carry.pop())
        cur.append(w)
        if re.search(r"[.!?]$", w["w"]):
            flush()
    flush()
    # A cue can end up too short to read — usually a sentence tail like "post."
    # left behind by the overflow split. Stretching its end (below) can't help
    # when the next cue starts immediately, or when it is the last cue and the
    # clip ends. So first move words BACKWARD across the boundary: the cue
    # inherits the earlier word's t0 and gains real time on screen. Only borrow
    # while both cues stay legal, and never empty the donor.
    def txt_of(ws):
        return re.sub(r"\s+", " ", " ".join(x["w"] for x in ws)).strip()
    for i in range(len(cues) - 1, 0, -1):
        c, prev = cues[i], cues[i-1]
        while c["end"] - c["start"] < MIN_DUR and len(prev["words"]) > 1:
            cand = prev["words"][-1]
            if len(txt_of([cand] + c["words"])) > MAX_CHARS:
                break
            if c["end"] - cand["t0"] > MAX_DUR:
                break
            if re.search(r"[.!?]$", cand["w"]):
                break                      # a sentence must end where its cue does
            # Some sentences are spoken too fast for BOTH halves to clear
            # MIN_DUR — 50 chars in 1.28s cannot split into two 0.7s cues. Taking
            # every word we're allowed just moves the flash onto the donor, so
            # stop at the balance point and leave two short cues rather than one
            # unreadable one.
            if cand["t0"] - prev["start"] < c["end"] - cand["t0"]:
                break
            moved = [prev["words"].pop()]
            # borrowing must not leave the donor dangling on a function word —
            # take those with it, so long as the receiver stays legal
            while len(prev["words"]) > 1 and \
                    prev["words"][-1]["w"].lower().strip(".,!?'\"") in ORPHAN and \
                    not re.search(r"[.!?]$", prev["words"][-1]["w"]) and \
                    len(txt_of([prev["words"][-1]] + moved + c["words"])) <= MAX_CHARS and \
                    c["end"] - prev["words"][-1]["t0"] <= MAX_DUR and \
                    prev["words"][-1]["t0"] - prev["start"] >= \
                        c["end"] - prev["words"][-1]["t0"]:
                moved.insert(0, prev["words"].pop())
            c["words"][:0] = moved
            for x in (c, prev):
                x["start"], x["end"] = x["words"][0]["t0"], x["words"][-1]["t1"]
                x["text"] = txt_of(x["words"])
    # enforce a readable minimum without colliding with the next cue
    for i, c in enumerate(cues):
        if c["end"] - c["start"] < MIN_DUR:
            nxt = cues[i+1]["start"] if i+1 < len(cues) else c["end"] + MIN_DUR
            c["end"] = min(c["start"] + MIN_DUR, nxt - 0.02)
    return [c for c in cues if c["end"] > c["start"]]


def build(cues, w, h, ypct, dur, fps, font, size, weight, maxw):
    edge = max(3, round(size * 0.075))          # hard dark edge, no blur
    e2 = round(edge * 0.7)
    secs, tl = [], []
    for i, c in enumerate(cues):
        d = round(c["end"] - c["start"], 3)
        secs.append(
            f'      <div id="cue{i}" class="clip cue" data-start="{round(c["start"],3)}" '
            f'data-duration="{d}" data-track-index="1"><span>{c["text"]}</span></div>')
        # deliberately no tween — the framework's clip window switches it on and
        # off instantly. Any fade here would read as a transition.
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>captions</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{w}px; height:{h}px; overflow:hidden; background:transparent; }}
      #root {{ position:relative; width:{w}px; height:{h}px; }}
      .cue {{
        position:absolute; left:0; right:0; top:{ypct*100:.1f}%;
        transform:translateY(-50%);
        display:flex; align-items:center; justify-content:center;
        text-align:center;
      }}
      .cue span {{
        display:inline-block; max-width:{round(w*maxw)}px; white-space:nowrap;
        font-family:'{font}', 'Avenir Next', 'Helvetica Neue', Arial, sans-serif;
        font-weight:{weight}; font-size:{size}px; line-height:1.18;
        letter-spacing:-0.01em; color:#FFFFFF;
        /* hard edge, zero blur — reads on any background, never looks glowy */
        text-shadow:
          {edge}px 0 0 #000, -{edge}px 0 0 #000, 0 {edge}px 0 #000, 0 -{edge}px 0 #000,
          {e2}px {e2}px 0 #000, -{e2}px {e2}px 0 #000,
          {e2}px -{e2}px 0 #000, -{e2}px -{e2}px 0 #000;
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}"
         data-width="{w}" data-height="{h}" data-fps="{fps}"
         data-layout-allow-overflow="true">
{chr(10).join(secs)}
    </div>
    <script>
      // GENERATED by edit/captions_overlay.py — do not hand-edit.
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // captions cut in and out with the clip window — no tweens by design
      tl.set("#root", {{ opacity: 1 }}, 0);
      tl.set("#root", {{ opacity: 1 }}, {dur});
      tl.seek(0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    global MAX_DUR, MIN_DUR
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True, help="hyperframes project dir")
    ap.add_argument("--res", required=True, help="WxH")
    ap.add_argument("--y", type=float, default=0.25, help="vertical centre, 0-1")
    ap.add_argument("--fps", type=float, default=None,
                    help="defaults to the fps preprocess.py detected and recorded "
                         "in silence.json — pass this only to override")
    ap.add_argument("--font", default="Montserrat")
    ap.add_argument("--weight", type=int, default=800)
    ap.add_argument("--size", type=int, default=0, help="0 = scale from height")
    ap.add_argument("--maxw", type=float, default=0.72,
                    help="max text width as a fraction of frame width")
    ap.add_argument("--srt", default="")
    ap.add_argument("--fixes", default="", help="JSON {wrong: right} applied to cue text")
    ap.add_argument("--maxdur", type=float, default=MAX_DUR,
                    help="longest a cue stays up. Default 2.2 is the vertical/social "
                         "value; CLAUDE.md's broadcast spec is 3.5 for 16:9")
    ap.add_argument("--mindur", type=float, default=MIN_DUR,
                    help="shortest a cue stays up. Default 0.55 vertical/social; "
                         "broadcast spec is 0.7")
    ap.add_argument("--timeline", default="",
                    help="premiere-clips.json — retime words onto Premiere's ACTUAL "
                         "clip boundaries, which differ from the ffmpeg cut by frame rounding")
    a = ap.parse_args()

    MAX_DUR, MIN_DUR = a.maxdur, a.mindur

    an = Path(a.analysis)
    words = json.load(open(an/"transcript.json"))["words"]
    sil = json.load(open(an/"silence.json"))
    dur = sil["cut_duration"]
    # The overlay must sit on the same frame grid the cut was snapped to. Take it
    # from the analysis rather than defaulting here — two defaults drift apart, and
    # an overlay on a different grid than the cut list is a desync nobody sees
    # until the render.
    if a.fps is None:
        a.fps = sil.get("fps")
        if a.fps is None:
            sys.exit(f"{an}/silence.json has no fps (analysed before fps was "
                     f"recorded) — re-run preprocess.py or pass --fps")
    w, h = (int(x) for x in a.res.lower().split("x"))
    size = a.size or round(h * 0.028)          # ~2.8% of height

    if a.timeline and Path(a.timeline).exists():
        prem = json.load(open(a.timeline))
        segs = json.load(open(an/"silence.json"))["segments"]
        # my cut timeline: cumulative segment starts
        mine, t = [], 0.0
        for s_, e_ in segs:
            mine.append((t, e_ - s_)); t += e_ - s_
        n = min(len(mine), len(prem))
        def remap(x):
            for i in range(n):
                m0, md = mine[i]
                if m0 <= x < m0 + md or (i == n-1 and x >= m0):
                    p0, p1 = prem[i]
                    scale = (p1 - p0) / md if md > 0 else 1.0
                    return round(p0 + (x - m0) * scale, 4)
            return round(x, 4)
        drift = max(abs(remap(m0) - m0) for m0, _ in mine)
        for wd in words:                 # not `w` — that is the frame width
            wd["t0"], wd["t1"] = remap(wd["t0"]), remap(wd["t1"])
        dur = prem[n-1][1]
        print(f"  retimed to Premiere's timeline (corrected up to {drift*1000:.0f}ms)")

    if a.fixes and Path(a.fixes).exists():
        words, n = apply_fixes(words, json.load(open(a.fixes)))
        print(f"  applied {n} correction(s)")
    # Whisper routinely stretches the FINAL token past the end of the audio
    # (Firecrawl: "good." ended at 32.90s on a 30.87s cut). Uncapped, the last
    # cue overruns the composition window, gets clipped at render, and flashes
    # for a fraction of its intended time instead of holding.
    #
    # The drift can push a word's START past the end too, and dropping those
    # outright loses a word that is genuinely audible: on "instinct" the closing
    # "beta." was timed at 34.14s on a 33.97s cut and vanished, leaving the last
    # cue reading "still in private". So only discard a token that lands clearly
    # outside the cut; pull a drifted one back onto the final frames instead.
    slack = 0.75
    words = [wd for wd in words if wd["t0"] < dur + slack]
    for wd in words:
        if wd["t0"] >= dur:
            wd["t0"] = max(0.0, dur - 1.0 / a.fps)
        wd["t1"] = min(wd["t1"], dur)
    global MAX_CHARS
    # Montserrat 800 averages ~0.58em per character; keep every cue on one line
    MAX_CHARS = max(12, int((w * a.maxw) / (size * 0.58)))
    cues = group(words)
    for c in cues:                        # MIN_DUR padding can also overrun
        c["end"] = min(c["end"], dur)
    html = build(cues, w, h, a.y, dur, a.fps, a.font, size, a.weight, a.maxw)
    out = Path(a.out); (out).mkdir(parents=True, exist_ok=True)
    (out/"index.html").write_text(html)

    if a.srt:
        def ts(s):
            return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{s%60:06.3f}".replace(".", ",")
        Path(a.srt).write_text("".join(
            f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n"
            for i, c in enumerate(cues, 1)))

    over = [c for c in cues if len(c["text"]) > MAX_CHARS]
    print(f"{out}/index.html")
    print(f"  {len(cues)} cues · {w}x{h} · {size}px {a.font} {a.weight} · "
          f"y={a.y*100:.0f}% · one line, max {MAX_CHARS} chars")
    print(f"  longest cue: {max(len(c['text']) for c in cues)} chars"
          f"{' (' + str(len(over)) + ' over limit)' if over else ''}")
    print(f"  avg on screen: {sum(c['end']-c['start'] for c in cues)/len(cues):.2f}s")


if __name__ == "__main__":
    main()
