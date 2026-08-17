#!/usr/bin/env python3
"""
build_bubbles.py — generate the "bubbles" compositions: individual panels lifted
out of the slide decks, treated black-and-white with one accent, floating over
the footage instead of replacing it.

This supersedes the full-frame approach in build_slide_motion.py. Lana's call,
2026-08-17: "i want it to overlay on top of my video instead of the whole
screen, or maybe take certain bubbles and sections". Because the video stays
visible, her burned-in captions stay visible too — so nothing has to be redrawn
and no card may cross CAPTION_TOP.

Panels come from edit/extract_panels.py (graphics/<deck>-bubbles/). Beats are
pinned to transcript phrases, same as before, so a retime is one number.

    python3 edit/build_bubbles.py

Never hand-edit the generated index.html / overlay.html — change BEATS and re-run.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRAME_W, FRAME_H = 1920, 1080
CAPTION_TOP = 845     # her burned-in caption starts here; nothing may cross it
SAFE_TOP = 120

# entrance: fast and tight, nothing floats or bounces
IN_DUR = 0.28
IN_RISE = 18          # px
IN_STAGGER = 0.09

PROJECTS = {
    "firecrawl-bubbles-motion": {
        "source": "Firecrawl.mp4",
        "deck": "firecrawl",
        "duration": 29.60,
        "beats": [
            {
                "cue": "great for anyone building an AI agent, an SEO tool",
                "in": 4.40, "out": 9.50,
                "layout": "row",
                # two columns, not three: at 250px the column text was too
                # small to read. Sources and output bookend the pipeline.
                "x": 1180, "y": 210, "size": 330, "gap": 18,
                "panels": ["01-architecture--01.png",   # the whole surface
                           "01-architecture--05.png"],  # 8:00 AM digest
            },
            {
                "cue": "turn your website into this very clean, structured dataset",
                "in": 10.30, "out": 14.30,
                "layout": "stack",
                "x": 1100, "y": 200, "size": 780, "gap": 20,
                "panels": ["03-firecrawl-run--01.png"],  # the live run terminal
            },
            {
                "cue": "track product launches ... from different startups",
                "in": 15.40, "out": 18.40,
                "layout": "stack",
                "x": 1400, "y": 140, "size": 440, "gap": 18,
                "panels": ["08-watchlist--01.png",       # Cursor
                           "08-watchlist--02.png",       # Replicate
                           "08-watchlist--05.png"],      # Anthropic
            },
            {
                "cue": "handles all the complexities for you, and it's super fast",
                "in": 20.70, "out": 23.24,
                "layout": "stack",
                "x": 1330, "y": 200, "size": 520, "gap": 20,
                "panels": ["02-pipeline--02.png",        # ~120 credits / run
                           "02-pipeline--03.png",        # 4m 55s wall clock
                           "02-pipeline--04.png"],       # 2 pages you read
            },
        ],
    },
}

HTML = """<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{
        margin: 0; width: 1920px; height: 1080px;
        overflow: hidden; background: {page_bg};
      }}
      #src-video {{ width: 1920px; height: 1080px; object-fit: cover; }}
      .beat {{ position: absolute; inset: 0; }}
      .bubble {{ position: absolute; display: block; }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{duration}"
      data-width="1920"
      data-height="1080"
    >
{media_open}
{beats}
{media_close}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{tweens}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

VIDEO_BLOCK = """      <video
        id="src-video"
        class="clip"
        src="assets/source.mp4"
        data-start="0"
        data-duration="{duration}"
        data-track-index="0"
        muted
        playsinline
      ></video>
"""

AUDIO_BLOCK = """      <audio
        id="src-audio"
        src="assets/source.mp4"
        data-start="0"
        data-duration="{duration}"
        data-track-index="10"
        data-volume="1"
      ></audio>"""


def layout(beat, sizes):
    """Place each panel, returning (left, top, width, height) per bubble."""
    out, x, y = [], beat["x"], beat["y"]
    for name in beat["panels"]:
        w0, h0 = sizes[name]
        if beat["layout"] == "row":
            w = beat["size"]
            h = round(h0 * w / w0)
            out.append((x, y, w, h))
            x += w + beat["gap"]
        else:
            w = beat["size"]
            h = round(h0 * w / w0)
            out.append((x, y, w, h))
            y += h + beat["gap"]
    return out


def build(name, spec, variant="baked"):
    sizes = {}
    index = json.loads((ROOT / "graphics" / f"{spec['deck']}-bubbles" / "panels.json").read_text())
    for slide, panels in index.items():
        for p in panels:
            sizes[p["file"]] = (p["w"], p["h"])

    beats_html, tweens = [], []
    for bi, beat in enumerate(spec["beats"], start=1):
        bid = f"b{bi:02d}"
        dur = round(beat["out"] - beat["in"], 3)
        boxes = layout(beat, sizes)

        # a bubble that crosses the caption band would bury her burned-in text
        bottom = max(y + h for (_, y, _, h) in boxes)
        right = max(x + w for (x, _, w, _) in boxes)
        assert bottom <= CAPTION_TOP, (
            f"{name} beat {bi} ({beat['cue'][:30]}...) reaches y={bottom}, "
            f"crossing the caption band at {CAPTION_TOP}")
        assert right <= FRAME_W, f"{name} beat {bi} runs off frame at x={right}"
        assert min(y for (_, y, _, _) in boxes) >= SAFE_TOP, f"{name} beat {bi} too high"

        rows = [f'      <!-- {bid}  {beat["in"]:.2f}-{beat["out"]:.2f}s  "{beat["cue"]}" -->',
                f'      <div class="clip beat" id="{bid}" data-start="{beat["in"]}" '
                f'data-duration="{dur}" data-track-index="1">']
        for pi, (panel, (x, y, w, h)) in enumerate(zip(beat["panels"], boxes)):
            rows.append(
                f'        <img class="bubble" id="{bid}-p{pi}" src="assets/bubbles/{panel}" '
                f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" alt="" />')
            tweens.append(
                f'      tl.fromTo("#{bid}-p{pi}", {{ opacity: 0, y: {IN_RISE} }}, '
                f'{{ opacity: 1, y: 0, duration: {IN_DUR}, ease: "power3.out" }}, '
                f'{round(beat["in"] + pi * IN_STAGGER, 3)});')
        rows.append("      </div>")
        beats_html.append("\n".join(rows))

    overlay = variant == "overlay"
    # The overlay lives in variants/ so it is not a second ROOT-level
    # composition; two roots make the runtime discover both entry points and
    # double the audio (lint: multiple_root_compositions).
    if overlay:
        out = ROOT / "graphics" / name / "variants" / "overlay.html"
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        out = ROOT / "graphics" / name / "index.html"
    body = HTML.format(
        title=f"{name} ({variant})",
        duration=spec["duration"],
        page_bg="transparent" if overlay else "#000",
        media_open="" if overlay else VIDEO_BLOCK.format(duration=spec["duration"]),
        media_close="" if overlay else AUDIO_BLOCK.format(duration=spec["duration"]),
        beats="\n\n".join(beats_html),
        tweens="\n".join(tweens),
    )
    if overlay:
        body = body.replace('src="assets/', 'src="../assets/')
    out.write_text(body)
    n = sum(len(b["panels"]) for b in spec["beats"])
    print(f"{name} ({variant}): {len(spec['beats'])} beats, {n} bubbles -> {out}")


if __name__ == "__main__":
    for name, spec in PROJECTS.items():
        prev = 0.0
        for b in spec["beats"]:
            assert b["out"] > b["in"], f"{name}: zero-length beat"
            assert b["in"] >= prev - 1e-9, f"{name}: overlapping beats"
            assert b["out"] <= spec["duration"] + 1e-9, f"{name}: beat past media"
            prev = b["out"]
        build(name, spec, "baked")
        build(name, spec, "overlay")
