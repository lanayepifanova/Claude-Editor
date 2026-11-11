#!/usr/bin/env python3
"""Speaker name cards for the opening of an interview — a white plate with a
gradient bar and a black/blue corner tab in Silicon Data Index Blue #2151D1:
the YC-style references in footage/Editing Examples/ with the orange swapped for
the brand blue (her call, 2026-11-05). Index Blue is the deck's blue for white
grounds, which is what the plate is. Each card swipes in, holds,
swipes out. Bring each card in as early as possible, on the person's first shot.

Config is a JSON list, one card per person:

    {"res": "1920x1080", "fps": "24000/1001", "safe": [34, 1046],
     "cards": [{"name": "Keith Newman", "role": "Host, Ignite Studio",
                "side": "left", "in": 0.3, "out": 7.3}, ...]}

`safe` is the picture area inside any baked-in letterbox (ffmpeg cropdetect);
cards sit on its bottom edge. Writes a HyperFrames project; render it with
    (cd graphics/<name>-cards && npx hyperframes render . --format mov -q high -f <fps> -o ../<name>-cards.mov)
fps must be rational for 23.976 footage ("24000/1001"); hyperframes rejects decimals.
"""
import argparse, html, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "graphics", "fonts", "Figtree.ttf")

SWIPE = 0.55          # seconds for the wipe in / out


def card_html(i, c):
    side = c.get("side", "left")
    return (f'      <div id="card{i}" class="card {side}">\n'
            f'        <div class="bar"></div><div class="tab"></div>\n'
            f'        <div class="plate"><div class="name">{html.escape(c["name"])}</div>'
            f'<div class="role">{html.escape(c["role"])}</div></div>\n'
            f'      </div>')


def tweens(i, c):
    # Reveal: the bar and tab snap in from the outer edge first, then the plate
    # wipes open behind them and the type slides a short way into place.
    # Exit runs the same wipe back toward the outer edge.
    left = c.get("side", "left") == "left"
    shut = "inset(0% 100% 0% 0%)" if left else "inset(0% 0% 0% 100%)"
    dx = -40 if left else 40
    t0, t1 = c["in"], c["out"] - SWIPE
    s = f"#card{i}"
    return f"""
      tl.set("{s}", {{ autoAlpha: 1 }}, {t0});
      tl.fromTo("{s} .bar", {{ clipPath: "{shut}" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: {SWIPE}, ease: "expo.out" }}, {t0});
      tl.fromTo("{s} .tab", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.25, ease: "power3.out" }}, {t0});
      tl.fromTo("{s} .plate", {{ clipPath: "{shut}" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: {SWIPE}, ease: "expo.out" }}, {t0 + 0.08});
      tl.fromTo("{s} .name, {s} .role", {{ x: {dx}, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.5, ease: "power3.out", stagger: 0.06 }}, {t0 + 0.16});
      tl.to("{s} .name, {s} .role", {{ x: {dx}, opacity: 0, duration: 0.3, ease: "power3.in" }}, {t1});
      tl.to("{s} .plate", {{ clipPath: "{shut}", duration: {SWIPE}, ease: "expo.in" }}, {t1 + 0.05});
      tl.to("{s} .bar", {{ clipPath: "{shut}", duration: {SWIPE}, ease: "expo.in" }}, {t1 + 0.12});
      tl.to("{s} .tab", {{ scaleY: 0, duration: 0.2, ease: "power3.in" }}, {t1 + 0.45});
      tl.set("{s}", {{ autoAlpha: 0 }}, {c["out"]});"""


def build(cfg):
    w, h = map(int, cfg["res"].split("x"))
    fps = cfg["fps"]
    top, bottom = cfg.get("safe", [0, h])
    k = w / 1920 * 1.15                # laid out at 1920, then sized up to the references
    margin = round(cfg.get("margin", 26) * k)
    lift = round(cfg.get("lift", 14) * k)         # gap above the picture's bottom edge
    cards = cfg["cards"]
    dur = round(max(c["out"] for c in cards) + 0.5, 3)
    secs = "\n".join(card_html(i, c) for i, c in enumerate(cards))
    tws = "".join(tweens(i, c) for i, c in enumerate(cards))
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>speaker cards</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Figtree"; src: url("Figtree.ttf") format("truetype"); font-weight: 300 900; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{w}px; height:{h}px; overflow:hidden; background:transparent; }}
      #root {{ position:relative; width:{w}px; height:{h}px; }}
      .card {{ position:absolute; bottom:{h - bottom + lift}px; visibility:hidden;
               font-family:"Figtree", "Avenir Next", sans-serif; }}
      .card.left {{ left:{margin}px; }}
      .card.right {{ right:{margin}px; }}
      .bar {{ height:{round(22*k)}px; margin-left:{round(22*k)}px;
              background:linear-gradient(90deg, #EEF2FC 0%, #7D9BE6 22%, #3A66D8 50%, #2151D1 100%); }}
      .tab {{ position:absolute; left:0; top:0; width:{round(22*k)}px; height:{round(44*k)}px;
              background:linear-gradient(#000 0 50%, #2151D1 50% 100%); transform-origin:top; z-index:2; }}
      .plate {{ background:#fff; padding:{round(16*k)}px {round(41*k)}px {round(29*k)}px {round(33*k)}px;
                margin-left:0; min-width:{round(600*k)}px; }}
      .name {{ font-weight:700; font-size:{round(72*k)}px; line-height:1.05; letter-spacing:-0.01em; color:#000; }}
      .role {{ font-weight:400; font-size:{round(45*k)}px; line-height:1.2; margin-top:{round(3*k)}px; color:#111; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}"
         data-width="{w}" data-height="{h}" data-fps="{fps}"
         data-layout-allow-overflow="true">
{secs}
    </div>
    <script>
      // GENERATED by edit/speaker_cards.py — do not hand-edit.
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});{tws}
      tl.set("#root", {{ opacity: 1 }}, {dur});
      tl.seek(0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", help="edit/cards-<name>.json")
    ap.add_argument("--out", required=True, help="graphics/<name>-cards (project dir)")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "index.html"), "w").write(build(cfg))
    shutil.copy(FONT, os.path.join(a.out, "Figtree.ttf"))
    print(f"wrote {a.out}/index.html")


if __name__ == "__main__":
    main()
