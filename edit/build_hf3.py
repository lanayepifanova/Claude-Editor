#!/usr/bin/env python3
"""
build_hf3.py — "Higgsfield Shorts Studio in Claude and Fable 5.2 - v3" reel.

Brief format: a media-kit video playing on TOP, her talking to camera on the
BOTTOM, word-by-word captions with the key numbers highlighted.

Three stages, each idempotent:
  master   cut the original footage with silence.json            -> graphics/hf3-master.mp4
  layout   kit montage (top 1080x1000) + her crop (bottom 1080x920) -> graphics/hf3-layout.mp4
  caps     word-by-word caption comp for HyperFrames             -> graphics/hf-shorts-v3-captions/

Beats are pinned to her words (cut-timeline seconds, from transcript.json) and
snapped to whole frames, so every join is one frame to the next with no overlap.
Captions then composite on the layout with edit/burn.py (--overlay), same as
every other video.

    python3 edit/build_hf3.py master|layout|caps|all
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "edit"))
import burn

AN = ROOT / "edit/analysis-hf-shorts-v3"
KIT = ROOT / "footage/Higgsfield Shorts Kit"
G = ROOT / "graphics"
MASTER = G / "hf3-master.mp4"
LAYOUT = G / "hf3-layout.mp4"
CAPS = G / "hf-shorts-v3-captions"
FPS = 30
W, H = 1080, 1920
TOP_H = 1000                 # kit plate height; she gets the other 920
HER_Y = 300                  # crop row in her frame: wall above, head from ~276, chest at the bottom

# (start second on the cut, kit file (glob stem), seek into clip, why)
BEATS = [
    (0.00,  "hypermotion/01.mp4", 1.0),                                  # "I didn't edit a single second"
    (2.12,  "commercial/hf_20261008_185749_905c365c", 1.5),              # "Claude did, no After Effects"
    (3.68,  "commercial/hf_20261007_190544_f638be57", 1.0),              # "no Premiere Pro"
    (4.72,  "hypermotion/03.mp4", 1.0),                                  # "one prompt"
    (6.28,  "motion/hf_20260610_200935_eb82df6c", 3.0),                         # "titles appear behind me"
    (8.24,  "motion/hf_20260610_190720_fdce4857", 3.0),                  # "images flow in, colours"
    (10.80, "motion/hf_20260902_180229_4fa23449", 3.0),                  # "I know nothing about editing"
    (12.41, "motion/hf_20261008_214233_cf634405", 1.0),                  # "Higgsfield's Shorts Studio inside Claude"
    (14.27, "hypermotion/hf_20260624_160502_263a0e61", 2.5),             # "Fable 5.2 and Anthropic's newest model"
    (16.60, "cinematic/hf_20261017_225957_d4f04816", 2.0),               # "upload a video that already did well"
    (19.08, "ugc/hf_20260925_160938_5b7edc0b", 1.0),                     # "add your script and materials"
    (21.22, "commercial/hf_20261008_202518_2f8bcdf1", 1.0),              # "photo, voice recording, video"
    (23.00, "cinematic/hf_20261017_194411_101c1509", 1.0),               # "builds a new video in the same format"
    (24.68, "ugc/hf_20260925_162704_e990569b", 1.5),                     # "a photo works too"
    (27.13, "cinematic/hf_20261012_092041_01a91c8f", 2.0),               # "connect Higgsfield's MCP to Claude"
    (29.30, "motion/POPTAPE sonnet 1", 2.0),                             # "type shorts"
    (30.40, "anime/hf_20260722_201043_c59b7f81", 2.5),                   # "add reference, script, materials, generate"
    (33.04, "anime/hf_20260709_104723_6bc09c31", 2.0),                   # "3 days"
    (35.20, "hypermotion/04.mp4", 1.0),                                  # "free, unlimited access"
    (37.32, "commercial/hf_20261019_190050_87125f31", 1.0),              # CTA
]


def kit_file(stem):
    hits = [p for p in KIT.glob("*/*.mp4") if f"{p.parent.name}/{p.name}".startswith(stem)]
    if len(hits) != 1:
        sys.exit(f"kit clip {stem!r}: {len(hits)} matches")
    return hits[0]


def master():
    sil = json.load(open(AN / "silence.json"))
    src = ROOT / sil["source"]
    burn.build_master(str(src), sil["segments"], str(MASTER), sil.get("fps", 30.0))
    print("master", MASTER, burn.probe(str(MASTER))["nb_read_packets"], "frames")


def layout():
    n = int(burn.probe(str(MASTER))["nb_read_packets"])
    starts = [round(b[0] * FPS) for b in BEATS] + [n]
    ins, parts, labels = ["-i", str(MASTER)], [], []
    for i, (b, a, z) in enumerate(zip(BEATS, starts, starts[1:]), start=1):
        frames = z - a
        path = kit_file(b[1])
        ins += ["-ss", str(b[2]), "-t", f"{frames/FPS+0.5:.3f}", "-i", str(path)]
        parts.append(
            f"[{i}:v]fps={FPS},scale={W}:{TOP_H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{TOP_H},setsar=1,trim=end_frame={frames},setpts=PTS-STARTPTS[k{i}]")
        labels.append(f"[k{i}]")
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(BEATS)}:v=1:a=0[top]"
    graph += f";[0:v]crop={W}:{H-TOP_H}:0:{HER_Y}[her];[top][her]vstack=inputs=2[v]"
    burn.run(["ffmpeg", "-y", *ins, "-filter_complex", graph, "-map", "[v]", "-map", "0:a",
              "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
              "-frames:v", str(n), "-c:a", "copy", "-movflags", "+faststart", str(LAYOUT)])
    print("layout", LAYOUT, burn.probe(str(LAYOUT))["nb_read_packets"], "frames of", n)


# ---- captions --------------------------------------------------------------------
FIXES = {"thropic's": "Anthropic's"}                 # whisper hears the "An" as a breath
KEY = {"5.2", "studio", "3", "days", "free", "unlimited", "shorts", "prompt"}
HOT = re.compile(r"Fable 5\.2|Shorts Studio|3 days|unlimited|free|SHORTS|prompt")


def clean(w):
    return re.sub(r'^["“”]+|["“”,.]+$', "", w.strip()).strip('"“”')


def chunks():
    words = json.load(open(AN / "transcript.json"))["words"]
    toks = []
    for w in words:
        raw = clean(w["w"])
        raw = FIXES.get(raw.lower(), raw)
        toks.append([raw, w["t0"], w["t1"], w["w"]])
    # fuse fixed phrases first
    out, i = [], 0
    while i < len(toks):
        a = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if nxt and a[0].lower() == "short" and nxt[0].lower() == "studio":
            out.append(["Shorts Studio", a[1], nxt[2], nxt[3]]); i += 2; continue
        if nxt and a[0].lower() == "fable" and nxt[0] == "5.2":
            out.append(["Fable 5.2", a[1], nxt[2], nxt[3]]); i += 2; continue
        if nxt and a[0] == "3" and nxt[0].lower() == "days":
            out.append(["3 days", a[1], nxt[2], nxt[3]]); i += 2; continue
        out.append(a); i += 1
    # a short function word rides with the word after it, so nothing flashes
    res, carry = [], None
    for t in out:
        if carry:
            t = [carry[0] + " " + t[0], carry[1], t[2], t[3]]; carry = None
        if re.fullmatch(r"[A-Za-z']{1,3}", t[0]) and t[0].lower() not in KEY and not re.search(r"[,.?!;:]", t[3]):
            carry = t; continue
        res.append(t)
    if carry:
        res.append(carry)
    # no flashes: a chunk shorter than MIN_HOLD takes the next one while the line still fits
    # (16 chars at 96px) and no comma or full stop sits between them
    merged, k = [], 0
    while k < len(res):
        cur = list(res[k]); k += 1
        while (k < len(res) and cur[2] - cur[1] < MIN_HOLD
               and len(cur[0]) + 1 + len(res[k][0]) <= MAX_CHARS
               and not re.search(r"[,.?!;:]", cur[3])):
            nx = res[k]; cur = [cur[0] + " " + nx[0], cur[1], nx[2], nx[3]]; k += 1
        merged.append(cur)
    # a tail under 0.30s ("Pro", "me") rides back onto the chunk before it
    back = []
    for c in merged:
        if (back and c[2] - c[1] < 0.30 and len(back[-1][0]) + 1 + len(c[0]) <= MAX_CHARS
                and not re.search(r"[,.?!;:]", back[-1][3])):
            back[-1] = [back[-1][0] + " " + c[0], back[-1][1], c[2], c[3]]
        else:
            back.append(c)
    res = back
    # the hold runs to the next chunk, never past 0.7s; a sentence end lets go sooner
    final = []
    for k, t in enumerate(res):
        end = res[k + 1][1] if k + 1 < len(res) else t[2] + 0.2
        end = min(end, t[1] + 0.7)
        txt = re.sub(r"\bshorts\b", "SHORTS", t[0])
        final.append((txt, round(t[1], 3), round(end, 3)))
    return final


def caps():
    ch = chunks()
    total = float(json.load(open(AN / "silence.json"))["cut_duration"])
    # the first chunk starts at the head of the cut; the last holds to the final frame
    ch[0] = (ch[0][0], 0.0, ch[0][2])
    ch[-1] = (ch[-1][0], ch[-1][1], total)
    CAPS.mkdir(exist_ok=True)
    shutil.copy(ROOT / "graphics/fonts/Figtree.ttf", CAPS / "Figtree.ttf")
    rows = []
    for k, (txt, a, b) in enumerate(ch):
        html_txt = HOT.sub(lambda m: f"<em>{m.group(0)}</em>", txt)
        rows.append(f'      <div id="c{k}" class="clip cue" data-start="{a:.3f}" data-duration="{b-a:.3f}" '
                    f'data-track-index="1"><span>{html_txt}</span></div>')
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>hf-shorts-v3-captions</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family:"HFCap"; src:url("Figtree.ttf") format("truetype"); font-weight:300 900; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:transparent; }}
      #root {{ position:relative; width:{W}px; height:{H}px; }}
      /* between the kit plate (ends y 1000) and her head (starts ~1276) */
      .cue {{ position:absolute; left:0; right:0; top:{CAP_Y}px; transform:translateY(-50%);
             display:flex; justify-content:center; text-align:center; }}
      .cue span {{ display:inline-block; max-width:1000px; white-space:nowrap;
        font-family:"HFCap", sans-serif; font-weight:850; font-size:96px; line-height:1.1;
        letter-spacing:-0.015em; color:#FFFFFF;
        /* hard edge, zero blur */
        text-shadow: 6px 0 0 #000, -6px 0 0 #000, 0 6px 0 #000, 0 -6px 0 #000,
          4px 4px 0 #000, -4px 4px 0 #000, 4px -4px 0 #000, -4px -4px 0 #000,
          6px 3px 0 #000, -6px 3px 0 #000, 6px -3px 0 #000, -6px -3px 0 #000,
          3px 6px 0 #000, -3px 6px 0 #000, 3px -6px 0 #000, -3px -6px 0 #000; }}
      .cue em {{ font-style:normal; color:#E8B33A; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}"
         data-width="{W}" data-height="{H}" data-fps="{FPS}" data-layout-allow-overflow="true">
{chr(10).join(rows)}
    </div>
    <script>
      // GENERATED by edit/build_hf3.py — captions cut in and out with the clip window, no tweens
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.set("#root", {{ opacity: 1 }}, 0);
      tl.set("#root", {{ opacity: 1 }}, {total:.3f});
      tl.seek(0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (CAPS / "index.html").write_text(html)
    print("captions:", len(ch), "chunks ->", CAPS / "index.html")
    print(" | ".join(f"{t}" for t, _, _ in ch))


CAP_Y = 1138
MIN_HOLD = 0.45
MAX_CHARS = 16

if __name__ == "__main__":
    for step in (sys.argv[1:] or ["all"]):
        if step in ("master", "all"): master()
        if step in ("layout", "all"): layout()
        if step in ("caps", "all"): caps()
