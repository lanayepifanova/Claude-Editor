#!/usr/bin/env python3
"""
build_slide_motion.py — generate the HyperFrames compositions that lay the
pre-designed PNG slide decks over the finished Firecrawl / Browser Use cuts.

The decks are full-frame 16:9 cards Lana designed, so a beat is a hard cut to
the card, a fast build across the layout grid, a slow hold, and a hard cut back
to her. Nothing is invented here: the plates are her PNGs, and every beat is
pinned to a phrase in the transcript (`cue`), so a retime is one number.

    python3 edit/build_slide_motion.py            # writes both index.html files

Never hand-edit graphics/*-motion/index.html — change BEATS and re-run.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── the build, in fractions of the frame ──────────────────────────────────
# Every slide in both decks uses the same template: eyebrow + headline at the
# top, content in the middle, a footer rule at the bottom. The reveal follows
# that structure instead of an arbitrary wipe.
HEAD_H = 0.22          # eyebrow + headline + subhead
FOOT_Y = 0.90          # footer rule
BANDS = 5              # content columns the build sweeps across

HEAD_DUR = 0.34        # headline wipes first
BAND_START = 0.18      # content starts before the headline lands
BAND_DUR = 0.26
BAND_STAGGER = 0.055
FOOT_AT = 0.52
FOOT_DUR = 0.22
PUSH = 1.022           # slow push-in so a held card is never a dead frame

PROJECTS = {
    "firecrawl-motion": {
        "source": "Firecrawl.mp4",
        "duration": 29.60,
        "ground": "#07080C",          # sampled from the deck's own edge
        "beats": [
            # slide, in, out, the words it lands on
            ("01-architecture.png",   4.40,  9.50, "This is great for anyone who's building an AI agent, an SEO tool"),
            ("03-firecrawl-run.png", 10.30, 14.30, "turn your website into this very clean, structured dataset"),
            ("08-watchlist.png",     15.40, 18.40, "track product launches ... from different startups"),
            ("02-pipeline.png",      20.70, 23.24, "handles all the complexities for you, and it's super fast"),
        ],
    },
    "browser-use-motion": {
        "source": "Browser Use.mp4",
        "duration": 36.80,
        "ground": "#08090C",
        "beats": [
            ("01-title.png",          0.25,  2.85, "So Claude can now read my Twitter feed"),
            ("02-architecture.png",   9.66, 15.60, "an open source Python framework called browser use"),
            ("03-scrape.png",        20.70, 25.00, "go through my X home feed, scroll through roughly a hundred posts"),
            ("04-prefilter.png",     25.00, 27.78, "ignore the memes, engagement bait, and repeated stories"),
            ("05-triage.png",        27.78, 32.72, "find 10 things most relevant to AI agents, developer tools"),
            ("06-output.png",        32.72, 36.80, "tell me what happened, why it matters, and give me the original post"),
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
      .card {{ position: absolute; inset: 0; overflow: hidden; }}
      .plate {{ position: absolute; inset: 0; z-index: 1; }}
      .plate img {{ width: 1920px; height: 1080px; object-fit: cover; display: block; }}
      /* Opaque strips in the deck's own edge colour. They start covering the
         whole frame and retract, so a beat cuts hard to the card's ground and
         the slide builds across it — never a flash of footage mid-build. */
      .cover {{ position: absolute; z-index: 2; transform-origin: right center; }}
      /* origin right: the strip shrinks rightward, so it uncovers left-to-right,
         matching reading order and the decks' own left-to-right pipeline arrows. */
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
{cards}
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
    """baked   -> index.html   : her cut + audio, cards burned on top
       overlay -> overlay.html : cards only on transparency, for V2 in Premiere.
                                 Same duration and same beat times, so it drops
                                 at 00:00 and lines up with the cut underneath."""
    cards, tweens = [], []
    for i, (slide, tin, tout, cue) in enumerate(spec["beats"], start=1):
        cid = f"c{i:02d}"
        dur = round(tout - tin, 3)
        covers = [
            f'        <div class="cover" id="{cid}-h" '
            f'style="left:0;top:0;width:100%;height:{HEAD_H*100:.4g}%;background:{spec["ground"]}"></div>'
        ]
        for b in range(BANDS):
            covers.append(
                f'        <div class="cover" id="{cid}-b{b}" '
                f'style="left:{b/BANDS*100:.4g}%;top:{HEAD_H*100:.4g}%;'
                f'width:{100/BANDS:.4g}%;height:{(FOOT_Y-HEAD_H)*100:.4g}%;'
                f'background:{spec["ground"]}"></div>'
            )
        covers.append(
            f'        <div class="cover" id="{cid}-f" '
            f'style="left:0;top:{FOOT_Y*100:.4g}%;width:100%;height:{(1-FOOT_Y)*100:.4g}%;'
            f'background:{spec["ground"]}"></div>'
        )
        cards.append(
            f'      <!-- {cid}  {tin:.2f}-{tout:.2f}s  "{cue}" -->\n'
            f'      <div class="clip card" id="{cid}" data-start="{tin}" '
            f'data-duration="{dur}" data-track-index="1">\n'
            f'        <div class="plate" id="{cid}-plate" data-layout-allow-overflow>'
            f'<img src="assets/slides/{slide}" alt="" /></div>\n'
            + "\n".join(covers) + "\n      </div>\n"
        )

        # every tween is positioned at GLOBAL time — the card's own start
        tweens.append(f'      // {cid} — {slide}')
        tweens.append(
            f'      tl.fromTo("#{cid}-plate", {{ scale: 1 }}, '
            f'{{ scale: {PUSH}, duration: {dur}, ease: "none" }}, {tin});'
        )
        tweens.append(
            f'      tl.to("#{cid}-h", {{ scaleX: 0, duration: {HEAD_DUR}, '
            f'ease: "power3.inOut" }}, {tin});'
        )
        for b in range(BANDS):
            at = round(tin + BAND_START + b * BAND_STAGGER, 3)
            tweens.append(
                f'      tl.to("#{cid}-b{b}", {{ scaleX: 0, duration: {BAND_DUR}, '
                f'ease: "power3.inOut" }}, {at});'
            )
        tweens.append(
            f'      tl.to("#{cid}-f", {{ opacity: 0, duration: {FOOT_DUR}, '
            f'ease: "power2.out" }}, {round(tin + FOOT_AT, 3)});'
        )

    overlay = variant == "overlay"
    out = ROOT / "graphics" / name / ("overlay.html" if overlay else "index.html")
    out.write_text(HTML.format(
        title=f"{name} ({variant})",
        duration=spec["duration"],
        page_bg="transparent" if overlay else "#000",
        media_open="" if overlay else VIDEO_BLOCK.format(duration=spec["duration"]),
        media_close="" if overlay else AUDIO_BLOCK.format(duration=spec["duration"]),
        cards="\n".join(cards),
        tweens="\n".join(tweens),
    ))
    covered = sum(b[2] - b[1] for b in spec["beats"])
    print(f"{name}: {len(spec['beats'])} beats, "
          f"{covered:.1f}s of {spec['duration']:.1f}s "
          f"({covered/spec['duration']*100:.0f}% covered) -> {out}")


if __name__ == "__main__":
    for name, spec in PROJECTS.items():
        # a beat must not run past the media, and must not overlap the previous
        prev_out = 0.0
        for slide, tin, tout, _ in spec["beats"]:
            assert tout > tin, f"{name}/{slide}: zero-length beat"
            assert tin >= prev_out - 1e-9, f"{name}/{slide}: overlaps previous beat"
            assert tout <= spec["duration"] + 1e-9, f"{name}/{slide}: runs past media"
            prev_out = tout
        build(name, spec, "baked")
        build(name, spec, "overlay")
