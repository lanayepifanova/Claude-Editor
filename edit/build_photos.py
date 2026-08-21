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

# Landscape defaults. A project may override with "frame" and "band" — vertical
# puts the burned-in caption at the TOP, so the legal area is below it, not above.
FRAME_W, FRAME_H = 1920, 1080
CAPTION_TOP = 845      # her burned-in caption; nothing may cross it
SAFE_TOP = 120
EDGE = 40              # keep off the frame edge

FADE_IN = 0.35
FADE_OUT = 0.30
SETTLE = 0.985         # scale it eases up from
DISSOLVE = 0.30        # overlap between back-to-back graphics

PROJECTS = {
    "neurons-photos-motion": {
        "source": "neurons.mp4",
        "deck": "neurons",
        "duration": 49.71,
        "frame": (1080, 1920),
        # Her framing in this clip is much closer than Sony TSMC's: her chin sits
        # at ~1150, not ~950, so the locked centre y=1260 would have put every
        # plate across her mouth. Measured off the export with a ruler overlay and
        # moved the band down — plates run 1180..1616, clearing her chin and still
        # landing inside the 1620 TikTok floor. Height is fixed at 436 and the
        # width falls out of each plate's aspect, which is why the numbers below
        # are 786 (1436x796 sources) and 752 (1436x832 sources).
        "band": (580, 1620),
        # 27.9-31.3 and 42.8-45.8 are deliberately empty: she gestures into the
        # plate area on "the more electricity" and on "behave more like brains",
        # and a gesture gets left alone.
        "beats": [
            ("neuron label",   0.15,   2.88, 786, 540, 1398, "you can now rent living human brain cells"),
            ("cortical pong",   2.95,   6.02, 752, 540, 1398, "A company called Cortical Labs"),
            ("cl1 device",   6.10,   8.93, 752, 540, 1398, "through a platform called Cortical Cloud"),
            ("lab hands",   9.00,  11.53, 752, 540, 1398, "at around $300 a week"),
            ("stem cells",  11.60,  14.33, 786, 540, 1398, "human neurons grown from stem cells"),
            ("mea chip",  14.40,  17.00, 752, 540, 1398, "and placed onto silicon hardware"),
            ("cloud compute",  18.15,  21.02, 786, 540, 1398, "from a traditional cloud provider"),
            ("living network",  21.10,  24.17, 786, 540, 1398, "access to a living neural network"),
            ("hidden layers",  25.05,  27.88, 786, 540, 1398, "modern AI has a huge scaling problem"),
            ("why layers",  31.30,  33.90, 786, 540, 1398, "and that cost just keeps increasing"),
            ("neurons firing",  33.95,  36.88, 786, 540, 1398, "efficient compared with conventional computer hardware"),
            ("dual smad",  36.95,  39.78, 786, 540, 1398, "which is why researchers are interested"),
            ("net layers",  39.85,  42.78, 786, 540, 1398, "complement or even replace parts of today's AI infrastructure"),
            ("culture dish",  45.75,  48.62, 752, 540, 1398, "starting to experiment with using actual brain cells"),
        ],
    },
    "sonytsmc-photos-motion": {
        "source": "sonytsmc.mov",
        "deck": "sonytsmc",
        "duration": 47.70,
        "frame": (1080, 1920),
        # captions are burned at y=25% (~440-525px), so the legal band starts
        # well below them; the floor keeps graphics clear of TikTok's bottom UI.
        # Centre y is 1260, not the 1090 first tried — at 1090 the taller plates
        # topped out around y=784, which is mid-face on her framing. She asked
        # for them lower; 1260 puts the tallest plate's top edge below her chin
        # and still lands its bottom at 1566, inside the 1620 floor.
        "band": (580, 1620),
        # asset, in, out, width, centre x/y, the words it lands on
        "beats": [
            ("news piece",                 0.15,  2.45, 960, 540, 1260, "Sony and TSMC have signed a binding agreement"),
            ("chip factory",               2.45,  4.25, 920, 540, 1260, "to build a chip factory"),
            ("kumamoto",                   4.25,  6.05, 920, 540, 1260, "in Koshi City, which is in the Kumamoto prefecture"),
            ("japan",                      6.05,  8.00, 920, 540, 1260, "in Japan."),
            ("largest contract chipmaker", 8.00, 10.30, 980, 540, 1260, "the largest contract chip maker in the world"),
            ("mobile processors",         10.30, 12.30, 960, 540, 1260, "fabricates every processor on your phone"),
            ("chip maker",                12.30, 14.40, 920, 540, 1260, "every serious AI accelerator on the market"),
            ("minority partners",         14.60, 17.20, 900, 540, 1260, "they're actually a minority partner"),
            ("sony",                      17.20, 19.00, 760, 540, 1260, "in a company that Sony controls."),
            ("image sensor 2",            19.00, 21.00, 980, 540, 1260, "What it will build is image sensors"),
            ("image sensor 3",            21.00, 23.20, 980, 540, 1260, "turn light into an electrical signal inside a camera"),
            ("image sensors",             23.40, 25.60, 800, 540, 1260, "the benchmark supplier of these to the phone industry"),
            # 283x178 native — the smallest asset by far, so it is held back to
            # 560 wide; anything larger shows the upscale
            ("chip stacking",             25.90, 28.10, 560, 540, 1260, "a design approach called stacking"),
            ("chipstaking 2",             28.10, 30.30, 880, 540, 1260, "the layer of pixels that catches the light"),
            ("high rise 3d chips",        30.30, 32.35, 880, 540, 1260, "bonded to a separate logic layer underneath it"),
            ("copper connections",        32.35, 34.40, 900, 540, 1260, "using copper to copper connections."),
            # 34.40-36.90 deliberately clear — she mimes "side by side" with both
            # hands there, and a graphic over it would bury the gesture
            ("chipmaking",                36.90, 39.90, 900, 540, 1260, "So volume production is actually not expected until 2029."),
            ("semiconductor",             40.10, 43.30, 920, 540, 1260, "before the plant's able to ship a single sensor"),
            ("news piece 2",              43.50, 45.55, 980, 540, 1260, "For Sony, this is definitely a defining commitment."),
            ("tsmc",                      45.65, 47.60, 720, 540, 1260, "And for TSMC, it's probably like a line item."),
        ],
    },
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
<html lang="en" data-resolution="{resolution}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={fw}, height={fh}" />
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{
        margin: 0; width: {fw}px; height: {fh}px;
        overflow: hidden; background: {page_bg};
      }}
      #src-video {{ width: {fw}px; height: {fh}px; object-fit: cover; }}
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
      data-width="{fw}"
      data-height="{fh}"
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
    fw, fh = spec.get("frame", (FRAME_W, FRAME_H))
    band_top, band_bottom = spec.get("band", (SAFE_TOP, CAPTION_TOP))

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
        assert y + h <= band_bottom, (
            f"{name} '{asset}' reaches y={y + h}, past the legal band at {band_bottom}")
        assert y >= band_top, f"{name} '{asset}' starts at y={y}, above the band at {band_top}"
        assert x >= EDGE and x + width <= fw - EDGE, (
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
        out.parent.mkdir(parents=True, exist_ok=True)
    body = HTML.format(
        title=f"{name} ({variant})",
        duration=spec["duration"],
        fw=fw, fh=fh,
        resolution="portrait" if fh > fw else "landscape",
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
        # a deck whose plates have been cleaned off disk (its video is finished
        # and its assets removed) is skipped rather than crashing the whole run
        if not (ROOT / "graphics" / f"{spec['deck']}-photos" / "photos.json").exists():
            print(f"{name}: no {spec['deck']}-photos/photos.json on disk, skipping")
            continue
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
