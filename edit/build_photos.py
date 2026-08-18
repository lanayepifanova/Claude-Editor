#!/usr/bin/env python3
"""
build_photos.py — lay Lana's own labelled photos over the footage.

Each asset is named for the words it lands on, so `cue` here is the transcript
phrase and `at` is the measured word time. Plates come from edit/prep_photos.py.

Transitions are deliberately plain: a soft fade with a 1.5% settle, nothing
sliding or bouncing — "subtle classy transitions only". Where two graphics run
back to back in the same stage they overlap by DISSOLVE, so one cross-dissolves
into the next instead of cutting.

    python3 edit/prep_photos.py --deck firecrawl
    python3 edit/build_photos.py

Never hand-edit the generated HTML — change BEATS and re-run.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRAME_W, FRAME_H = 1920, 1080
CAPTION_TOP = 845      # her burned-in caption; nothing may cross it
SAFE_TOP = 120
EDGE = 40              # keep off the frame edge

FADE_IN = 0.35
FADE_OUT = 0.30
SETTLE = 0.985         # scale it eases up from
DISSOLVE = 0.30        # overlap between back-to-back graphics

PROJECTS = {
    "firecrawl-photos-motion": {
        "source": "Firecrawl.mp4",
        "deck": "firecrawl",
        "duration": 29.60,
        # asset, in, out, width, centre x/y, the words it lands on
        "beats": [
            ("website",            1.27,  3.20, 600, 1500, 440, "scrape any website for free"),
            ("firecrawl",          3.38,  5.85, 640, 1470, 430, "with AI using Firecrawl"),
            ("ai agent",           6.04,  7.32, 640, 1500, 440, "building an AI agent"),
            ("seo tool",           7.02,  8.73, 620, 1500, 450, "an SEO tool"),
            ("data extraction",    8.43,  9.70, 800, 1460, 440, "or just a data extraction"),
            ("structured dataset", 12.34, 15.70, 860, 1440, 440, "very clean, structured dataset"),
            ("product launches",   15.85, 19.30, 900, 1420, 430, "track product launches"),
            ("love firecrawl",     19.48, 23.80, 820, 1450, 440, "all my homies love Firecrawl"),
            ("student program",    23.98, 29.45, 380, 1560, 450, "they have a student program"),
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
      .plate {{ position: absolute; display: block; }}
      /* a screen recording cannot live inside a timed wrapper, so it carries
         its own timing and an untimed shell takes the fade */
      .shell {{ position: absolute; }}
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


def build(name, spec, variant="baked"):
    photos = json.loads((ROOT / "graphics" / f"{spec['deck']}-photos" / "photos.json").read_text())
    html, tweens = [], []

    for i, (asset, tin, tout, width, cx, cy, cue) in enumerate(spec["beats"], start=1):
        bid = f"p{i:02d}"
        meta = photos[asset]
        dur = round(tout - tin, 3)
        w0, h0 = meta.get("w"), meta.get("h")
        if w0 is None:                      # the screen recording
            w0, h0 = 2566, 1050
        h = round(h0 * width / w0)
        x, y = round(cx - width / 2), round(cy - h / 2)

        # a graphic that crossed the caption band would bury her burned-in text
        assert y + h <= CAPTION_TOP, (
            f"{name} '{asset}' reaches y={y + h}, crossing the caption band at {CAPTION_TOP}")
        assert y >= SAFE_TOP, f"{name} '{asset}' too high (y={y})"
        assert x >= EDGE and x + width <= FRAME_W - EDGE, (
            f"{name} '{asset}' spans x={x}..{x + width}, outside the {EDGE}px margin")

        track = 1 + (i % 2)                 # alternate so a dissolve can overlap
        html.append(f'      <!-- {bid}  {tin:.2f}-{tout:.2f}s  "{cue}" -->')

        if meta["mode"] == "raw-video":
            html.append(
                f'      <div class="shell" id="{bid}-shell" '
                f'style="left:{x}px;top:{y}px;width:{width}px;height:{h}px">\n'
                f'        <video class="clip" id="{bid}" src="assets/photos/{meta["file"]}" '
                f'data-start="{tin}" data-duration="{dur}" data-track-index="{track}" '
                f'style="width:{width}px;height:{h}px;object-fit:cover;display:block" '
                f'muted playsinline></video>\n'
                f'      </div>')
            target = f"#{bid}-shell"
        else:
            html.append(
                f'      <div class="clip beat" id="{bid}" data-start="{tin}" '
                f'data-duration="{dur}" data-track-index="{track}">\n'
                f'        <img class="plate" id="{bid}-img" src="assets/photos/{meta["file"]}" '
                f'style="left:{x}px;top:{y}px;width:{width}px;height:{h}px" alt="" />\n'
                f'      </div>')
            target = f"#{bid}-img"

        tweens.append(f'      // {bid} — {asset}  "{cue}"')
        tweens.append(
            f'      tl.fromTo("{target}", {{ opacity: 0, scale: {SETTLE} }}, '
            f'{{ opacity: 1, scale: 1, duration: {FADE_IN}, ease: "power2.out" }}, {tin});')
        tweens.append(
            f'      tl.to("{target}", {{ opacity: 0, duration: {FADE_OUT}, '
            f'ease: "power2.in" }}, {round(tout - FADE_OUT, 3)});')

    overlay = variant == "overlay"
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
        beats="\n\n".join(html),
        tweens="\n".join(tweens),
    )
    if overlay:
        body = body.replace('src="assets/', 'src="../assets/')
    out.write_text(body)
    print(f"{name} ({variant}): {len(spec['beats'])} graphics -> {out}")


if __name__ == "__main__":
    for name, spec in PROJECTS.items():
        prev_out, prev_name = 0.0, None
        for asset, tin, tout, *_ in spec["beats"]:
            assert tout > tin, f"{name}: '{asset}' zero length"
            assert tout <= spec["duration"] + 1e-9, f"{name}: '{asset}' past media"
            if tin < prev_out:
                gap = round(prev_out - tin, 3)
                assert gap <= DISSOLVE + 1e-6, (
                    f"{name}: '{asset}' overlaps '{prev_name}' by {gap}s, "
                    f"more than the {DISSOLVE}s dissolve")
            prev_out, prev_name = tout, asset
        build(name, spec, "baked")
        build(name, spec, "overlay")
