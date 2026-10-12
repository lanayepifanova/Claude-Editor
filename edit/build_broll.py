#!/usr/bin/env python3
"""
build_broll.py — full-screen 9:16 picture takeovers, one per beat, pinned to words.

The plate pipeline (prep_photos.py -> build_photos.py) floats a picture in a band
below the caption. This is the other look: the picture IS the frame. She asked for
"a picture change every 3-4 seconds ... portrait and just takes over the entire
screen", with her raw footage left showing on the storytelling beats ("That is,
until now", "So what have they found?", ...). A RAW beat is simply a gap in the
overlay, so the cut underneath shows through.

Every beat starts on a phrase from the CUT transcript (`cue`), never a typed
timestamp, so re-cutting the video moves the pictures with the words. A beat runs
until the next beat starts — there are no holes except the RAW ones.

Two ways to fill the frame:
  cover (cx, cy, h)       crop a 9:16 window centred on (cx, cy), h = window
                          height as a fraction of the source. For photos.
  fit   (x0, y0, x1, y1)  crop that box, then fit it whole inside the band below
                          the caption on a flat `bg`. For maps, charts and slides,
                          where cropping would cut off the labels that carry the
                          meaning and a caption must not sit on the graphic.
  panel (x0, y0, x1, y1)  crop that box, then fit it whole inside the project's
                          `panel` rectangle and leave the rest of the frame
                          transparent. For landscape talking-heads with empty
                          wall beside her — the picture sits in the space, she
                          stays visible ("make it to the left in the empty space
                          ... don't have the picture on me").

Cuts are hard (CLAUDE.md: hard cut is the default); each picture gets a slow push
so nothing holds still.

    python3 edit/build_broll.py gladiator
    (cd graphics/gladiator-broll && npx hyperframes render . --format mov ...)

Never hand-edit the generated HTML — change BEATS and re-run.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW, FH = 1080, 1920
FIT_BAND = (600, 1640)     # default: below a y=0.25 caption, above the TikTok UI floor
PUSH = 1.06                # scale a picture eases up to over its beat

FULL = (0.0, 0.0, 1.0, 1.0)

PROJECTS = {
    # Landscape talking-head: she sits right of centre with bare yellow wall to
    # her left. Her leftmost extent over the whole cut is x~940 in 99% of frames
    # (hands included), so pictures fit inside 70..900 x 70..800, above the
    # y=0.82 caption. "make it to the left in the empty space ... don't have the
    # picture on me". Sources: Wikimedia Commons, see gliders-broll-credits.txt.
    "gliders": {
        "analysis": "edit/analysis-gliders",
        "src": "graphics/gliders-broll-src",
        "frame": (1920, 1080),
        "panel": (70, 70, 900, 800),
        "beats": [
            ("loc glide 1",                 "i'm going to run",        "panel", (0.04, 0.10, 0.96, 0.90)),
            ("unruhiger gleitflug",         "so let's go through",     "panel", FULL),
            ("munich museum glider",        "starting off",            "panel", FULL),
            ("gartenlaube glide over hill", "someone had to prove",    "panel", FULL),
            ("lilienthal portrait",         "and that person was",     "panel", FULL),
            ("workshop drawing",            "he built his own",        "panel", FULL),
            ("gartenlaube bat wings",       "kind of like bat",        "panel", FULL),
            ("gartenlaube top of hill",     "run off the top",         "panel", FULL),
            ("fliegeberg today",            "he even had a",           "panel", FULL),
            ("going to fly",                "just so he could",        "panel", FULL),
            ("sepia long glide",            "his longest glides",      "panel", FULL),
            ("us patent",                   "so his gliders had",      "panel", FULL),
            ("legs from below",             "besides when he",         "panel", FULL),
            ("museum glider pilot",         "that shifted the",        "panel", FULL),
            ("hang glider brazil",          "and it's basically how",  "panel", FULL),
            ("fliegekunst plates",          "he also wrote down",      "panel", FULL),
            ("curved plate streamlines",    "and one of his",          "panel", FULL),
            ("camber diagram",              "and that curve is",       "panel", FULL),
            ("lift measurements",           "he published tables",     "panel", FULL),
            ("de patent",                   "and that gave the",       "panel", FULL),
            ("lichterfelde 1895",           "but obviously steering",  "panel", FULL),
            ("doppeldecker 1895",           "the design problem is",   "panel", FULL),
            ("replica hangar",              "the forces on it",        "panel", FULL),
            ("big biplane reconstruction",  "so a bigger glider",      "panel", FULL),
            ("todesflug wreck",             "in 1896",                 "panel", FULL),
            ("gollenberg memorial",         "he broke his",            "panel", FULL),
            ("loc glide 1",                 "so gliders basically",    "panel", (0.04, 0.10, 0.96, 0.90)),
            ("normalsegelapparat 1895",     "but they had two",        "panel", FULL),
        ],
    },
    # Landscape talking-head, MIRRORED at the burn (`burn.py --mirror`, her ask:
    # "invert left to right, so that im on the right side"). After the flip she
    # sits right of x~1000 in 95% of frames and the bare red wall is on the left,
    # so the gliders panel fits unchanged. Only Wright-specific pictures (her
    # ask): the roll/pitch/yaw/canard/droop cards are crops of the Commons
    # Wright Flyer three-view with a serif title, not a generic airliner diagram.
    # Sources: Wikimedia Commons, see wright-flyer-broll-credits.txt.
    "wright-flyer": {
        "analysis": "edit/analysis-wright-flyer",
        "src": "graphics/wright-flyer-broll-src",
        "frame": (1920, 1080),
        "panel": (70, 70, 900, 800),
        "beats": [
            ("first flight",          "this is the famous",       "panel", FULL),
            ("cycle shop",            "two famous brothers",      "panel", FULL),
            ("lilienthal glide",      "they read everything",     "panel", FULL),
            ("1900 glider kite",      "using his tables",         "panel", FULL),
            ("1901 glider wilbur",    "but in 1901",              "panel", FULL),
            ("wind tunnel replica",   "so they built a",          "panel", FULL),
            ("balance schema",        "200 different",            "panel", FULL),
            ("1902 glider turns",     "their biggest idea",       "panel", FULL),
            ("three view white",      "can rotate three",         "panel", FULL),
            ("patent fig1",           "this is called the",       "panel", FULL),
            ("roll card",             "the first control is",     "panel", FULL),
            ("lilienthal legs",       "rolled his glider",        "panel", FULL),
            ("1899 kite",             "to twist the",             "panel", FULL),
            ("right turn rear",       "wing warping",             "panel", FULL),
            ("pitch card",            "the second control is",    "panel", FULL),
            ("flyer side view",       "and for that they put",    "panel", FULL),
            ("yaw card",              "the third control is",     "panel", FULL),
            ("1902 glider tests",     "and for that they added",  "panel", FULL),
            ("1904 circling",         "for each of",              "panel", FULL),
            ("engine left front",     "they also needed an",      "panel", FULL),
            ("charlie taylor",        "so their mechanic",        "panel", FULL),
            ("engine smithsonian",    "it made around",           "panel", FULL),
            ("engine underside",      "partly because he cast",   "panel", FULL),
            ("propeller",             "they had to also",         "panel", FULL),
            ("pilot seat engine",     "what shape a propeller",   "panel", FULL),
            ("1901 glider kite",      "and the",                  "panel", FULL),
            ("wind tunnel 2",         "so they could design",     "panel", FULL),
            ("flyer front view",      "they put two propellers",  "panel", FULL),
            ("three view white",      "so that their twisting",   "panel", (0.02, 0.02, 0.65, 0.61)),
            ("first flight restored", "and on december 17",       "panel", FULL),
            ("flight path diagram",   "the first flight lasted",  "panel", (0.0, 0.0, 0.62, 1.0)),
            ("four markers",          "37 meters",                "panel", FULL),
            ("launch track dec 14",   "but it was the",           "panel", FULL),
            ("telegram",              "they flew three more",     "panel", FULL),
            ("damaged after final",   "they stayed up",           "panel", FULL),
            ("canard card",           "the layout",               "panel", FULL),
            ("droop card",            "and the wings drooped",    "panel", FULL),
            ("wilbur after trial",    "made the plane pretty",    "panel", FULL),
            ("1904 flyer",            "it wobbled a lot",         "panel", FULL),
            ("brothers porch",        "the whole time",           "panel", FULL),
        ],
    },
    # Landscape talking-head, MIRRORED at the burn (`burn.py --mirror`, her ask:
    # "invert so that i go from left to right"). She sits on the left in the
    # footage; flipped she is right of x~1000 with bare yellow wall on the left,
    # so the gliders panel fits unchanged. Sources: Wikimedia Commons, see
    # sopwith-camel-broll-credits.txt.
    "sopwith-camel": {
        "analysis": "edit/analysis-sopwith-camel",
        "src": "graphics/sopwith-camel-broll-src",
        "frame": (1920, 1080),
        "panel": (70, 70, 900, 800),
        "beats": [
            ("camel usaf",        "this is the sopwith",     "panel", FULL),
            ("rfc q12011",        "because it shot down",    "panel", FULL),
            ("aerodrome attack",  "which is more than",      "panel", FULL),
            ("roy brown",         "there's a story",         "panel", FULL),
            ("red baron",         "who was officially",      "panel", FULL),
            ("dpla 8",            "it was a british",        "panel", FULL),
            ("pup side",          "to replace their",        "panel", FULL),
            ("camel front",       "and it reached the",      "panel", FULL),
            ("replica a",         "so what made it",         "panel", FULL),
            ("dogfight turnbull", "a dogfight is won",       "panel", FULL),
            ("rfc q12121",        "it was also very",        "panel", FULL),
            ("flying school",     "so more than",            "panel", FULL),
            ("wreck nara",        "while learning to" ,      "panel", FULL),
            ("camel iwm",         "it got its name",         "panel", FULL),
            ("dpla 4",            "which covered its",       "panel", FULL),
            ("dpla 5",            "so the guns fired",       "panel", FULL),
            ("sync lever",        "and they were timed",     "panel", FULL),
            ("clerget faam",      "the tight turning",       "panel", FULL),
            ("rotary anim",       "which means the whole",   "panel", FULL),
            ("gyroscope toy",     "a heavy spinning",        "panel", FULL),
            ("camel 1917",        "and that let the",        "panel", FULL),
            ("camel drawing",     "it also made the",        "panel", FULL),
            ("iwm museum 3",      "with the engine",         "panel", FULL),
            ("camel b7280",       "the plane was twitchy",   "panel", FULL),
            ("barker",            "so good pilots",          "panel", FULL),
            ("camel rear",        "the camel had one"    ,   "panel", FULL),
            ("replica c",         "and its two wings",       "panel", FULL),
            ("replica b",         "they held its top",       "panel", FULL),
            ("started up",        "kilometers per hour",     "panel", FULL),
            ("three camels",      "so the camel could"    ,  "panel", (0.25, 0.10, 0.98, 0.80)),
            ("vimy museum",       "and after the war",       "panel", FULL),
        ],
    },
    "gladiator": {
        "analysis": "edit/analysis-gladiator",
        "src": "graphics/gladiator-broll-src",
        # captions moved to y=0.75 and a disclosure line sits at y=0.25 for the
        # whole video (her ask, 2026-10-06), so maps and charts fit BETWEEN them
        "fit_band": (560, 1340),
        "banner": ("Disseminated on behalf of\nGladiator Metals Corp", 0.25),   # two rows, her ask
        # (asset or "RAW", cue phrase in the cut transcript, mode, args, bg)
        "beats": [
            ("RAW",                       "imagine this"),
            ("yukon",                     "the yukon",               "cover", (0.50, 0.50, 1.00)),
            ("hudbay pit",                "hudbay has spent",        "cover", (0.60, 0.50, 0.84)),
            ("belt map light",            "out of a 35",             "fit",   (0.0, 0.0, 1.0, 1.0), "#ffffff"),
            ("walk away aerial",          "now the economics",       "cover", (0.55, 0.50, 0.84)),
            ("forty years outcrop",       "for 40 years",            "cover", (0.50, 0.50, 1.00)),
            ("RAW",                       "that is until now"),
            ("gladiator cover",           "gladiator metals trades", "fit",   (0.0, 0.0, 0.56, 1.0), "#739bc4"),
            ("phone call",                "in the us and",           "cover", (0.50, 0.50, 1.00)),
            ("jason bontempo",            "in 2021 ceo",             "cover", (0.73, 0.44, 0.84)),
            ("drilling family geologist", "a yukon drilling",        "cover", (0.62, 0.50, 1.00)),
            ("marcus harden",             "geologist marcus",        "cover", (0.80, 0.50, 1.00)),
            ("whole belt dark",           "and together they",       "fit",   (0.0, 0.0, 1.0, 1.0), "#000000"),
            ("RAW",                       "so what have they"),
            ("cowley park",               "cali park",               "cover", (0.56, 0.52, 0.84)),
            ("cub east map",              "cub east is",             "fit",   (0.0, 0.0, 1.0, 1.0), "#ffffff"),
            ("cub east core",             "and one hole there",      "cover", (0.50, 0.50, 1.00)),
            ("chiefs trend map",          "on the chief's trend",    "fit",   (0.0, 0.0, 1.0, 1.0), "#ffffff"),
            ("chiefs core",               "they hit 49.8",           "cover", (0.50, 0.50, 1.00)),
            ("RAW",                       "here's where it gets"),
            ("blackrock",                 "in july blackrock",       "cover", (0.50, 0.50, 1.00)),
            ("cash",                      "gladiator now has",       "cover", (0.50, 0.50, 1.00)),
            ("drill core racks",          "to five drill",           "cover", (0.55, 0.50, 1.00)),
            ("RAW",                       "now i want to"),
            ("exploration outcrop",       "gladiator is a",          "cover", (0.40, 0.50, 1.00)),
            ("riskiest prospectors",      "and exploration is one",  "cover", (0.62, 0.50, 0.84)),
            ("market cap chart",          "the company's market cap", "fit",  (0.16, 0.08, 0.84, 0.92), "#1c1f26"),
            ("foran arizona sonoran",     "more advanced copper",    "fit",   (0.04, 0.30, 0.43, 0.86), "#ffffff"),
            ("drilling cross section",    "but those companies",     "fit",   (0.0, 0.0, 1.0, 1.0), "#ffffff"),
            ("website",                   "this is an investment",   "fit",   (0.0, 0.0, 1.0, 0.73), "#3d3d3d"),
            ("RAW",                       "do your own research"),
        ],
    },
}


def norm(s):
    return re.sub(r"[^a-z0-9.']", "", s.lower().replace("’", "'")).strip(".")


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(path)], text=True)
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


def resolve(words, beats, fps):
    toks = [norm(w["w"]) for w in words]
    at, i0 = [], 0
    for b in beats:
        cue = [norm(t) for t in b[1].split()]
        for i in range(i0, len(toks) - len(cue) + 1):
            if toks[i:i + len(cue)] == cue:
                at.append(round(words[i]["t0"] * fps) / fps)
                i0 = i + 1
                break
        else:
            sys.exit(f"cue not found after word {i0}: {b[1]!r}")
    return at


def prep(src, dst, mode, args, bg, band=FIT_BAND, panel=None):
    w, h = probe(src)
    if mode == "panel":
        x0, y0, x1, y1 = args
        px0, py0, px1, py1 = panel
        cw, ch = (x1 - x0) * w, (y1 - y0) * h
        s = min((px1 - px0) / cw, (py1 - py0) / ch)
        sw, sh = int(cw * s) // 2 * 2, int(ch * s) // 2 * 2
        left = px0 + (px1 - px0 - sw) // 2
        top = py0 + (py1 - py0 - sh) // 2
        vf = (f"crop={int(cw)}:{int(ch)}:{int(x0 * w)}:{int(y0 * h)},"
              f"scale={sw}:{sh}:flags=lanczos,format=rgba,"
              f"pad={FW}:{FH}:{left}:{top}:color=0x00000000")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf,
                        "-frames:v", "1", str(dst)], check=True)
        return
    if mode == "cover":
        cx, cy, hf = args
        ch = hf * h
        cw = ch * FW / FH
        if cw > w:
            cw, ch = w, w * FH / FW
        x = min(max(cx * w - cw / 2, 0), w - cw)
        y = min(max(cy * h - ch / 2, 0), h - ch)
        vf = f"crop={int(cw)}:{int(ch)}:{int(x)}:{int(y)},scale={FW}:{FH}:flags=lanczos"
    else:
        x0, y0, x1, y1 = args
        cw, ch = (x1 - x0) * w, (y1 - y0) * h
        bh = band[1] - band[0]
        s = min(FW / cw, bh / ch)
        sw, sh = int(cw * s) // 2 * 2, int(ch * s) // 2 * 2
        top = band[0] + (bh - sh) // 2
        vf = (f"crop={int(cw)}:{int(ch)}:{int(x0 * w)}:{int(y0 * h)},"
              f"scale={sw}:{sh}:flags=lanczos,"
              f"pad={FW}:{FH}:{(FW - sw) // 2}:{top}:color={bg}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf,
                    "-frames:v", "1", "-q:v", "2", str(dst)], check=True)


HTML = """<!doctype html>
<html lang="en" data-resolution="{orient}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={fw}, height={fh}" />
    <title>{name} b-roll</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {fw}px; height: {fh}px; overflow: hidden; background: transparent; }}
      .beat {{ position: absolute; inset: 0; overflow: hidden; }}
      .beat img {{ position: absolute; inset: 0; width: {fw}px; height: {fh}px; display: block; }}
      /* the disclosure line: same hard-edged ink as the captions, smaller and lighter */
      #banner {{ position: absolute; left: 0; width: {fw}px; z-index: 1000;
        display: flex; justify-content: center; transform: translateY(-50%); }}
      #banner span {{ max-width: 960px; text-align: center;
        font-family: 'Montserrat', 'Avenir Next', 'Helvetica Neue', Arial, sans-serif;
        font-weight: 700; font-size: 36px; line-height: 1.2; color: #FFFFFF;
        text-shadow: 3px 0 0 #000, -3px 0 0 #000, 0 3px 0 #000, 0 -3px 0 #000,
          2px 2px 0 #000, -2px 2px 0 #000, 2px -2px 0 #000, -2px -2px 0 #000; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration}"
         data-width="{fw}" data-height="{fh}">
{beats}
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


def build(name, spec):
    global FW, FH
    FW, FH = spec.get("frame", (1080, 1920))
    an = ROOT / spec["analysis"]
    sil = json.loads((an / "silence.json").read_text())
    fps, dur = sil["fps"], round(sil["cut_duration"], 3)
    words = json.loads((an / "transcript.json").read_text())
    words = words["words"] if isinstance(words, dict) else words
    beats = spec["beats"]
    at = resolve(words, beats, fps) + [dur]
    frames = [round(t * fps) for t in at]  # integer frames, so joins cannot drift

    out = ROOT / "graphics" / f"{name}-broll"
    img = out / "assets"
    if img.exists():
        shutil.rmtree(img)                 # mirror BEATS exactly, no stale plates
    img.mkdir(parents=True)
    src_dir = ROOT / spec["src"]
    html, tweens, n = [], [], 0
    for k, b in enumerate(beats):
        tin, tout = frames[k] / fps, frames[k + 1] / fps
        length = tout - tin
        if b[0] == "RAW":
            print(f"  {tin:6.2f}-{tout:6.2f}  {length:4.2f}s  (her)   \"{b[1]}\"")
            continue
        n += 1
        asset, cue, mode, args = b[:4]
        bg = b[4] if len(b) > 4 else "#000"
        srcs = [p for p in src_dir.iterdir() if p.stem == asset]
        assert len(srcs) == 1, f"{asset}: expected one source, found {srcs}"
        fn = f"b{n:02d}.{'png' if mode == 'panel' else 'jpg'}"
        prep(srcs[0], img / fn, mode, args, bg, spec.get("fit_band", FIT_BAND),
             spec.get("panel"))
        bid = f"b{n:02d}"
        flag = "" if 2.4 <= length <= 4.6 else "   <- check length"
        print(f"  {tin:6.2f}-{tout:6.2f}  {length:4.2f}s  {asset:26s} \"{cue}\"{flag}")
        # Each picture runs one frame into the next and the later one is stacked
        # above it. Rounding start and duration separately used to leave a single
        # frame at three joins where neither was up, and her face flashed through
        # (she caught it right after "267 million pounds of copper").
        nxt_raw = k + 1 < len(beats) and beats[k + 1][0] == "RAW"
        held = length + (0 if nxt_raw or k + 1 == len(beats) else 1 / fps)
        html.append(f'      <!-- {bid} {tin:.2f}-{tout:.2f}  "{cue}" -->\n'
                    f'      <div class="clip beat" id="{bid}" data-start="{tin:.4f}" '
                    f'data-duration="{held:.4f}" data-track-index="{1 + n % 2}" '
                    f'style="z-index:{n}">'
                    f'<img id="{bid}-img" src="assets/{fn}" alt="" /></div>')
        # transform-origin follows the crop centre, so the push leans into the subject;
        # a panel is a small picture on a full-frame canvas, so it pushes from the
        # panel's own centre or it would drift across the frame
        if mode == "panel":
            px0, py0, px1, py1 = spec["panel"]
            tweens.append(f'      gsap.set("#{bid}-img", {{ transformOrigin: '
                          f'"{(px0 + px1) / 2}px {(py0 + py1) / 2}px" }});')
        tweens.append(f'      tl.fromTo("#{bid}-img", {{ scale: 1 }}, {{ scale: {PUSH}, '
                      f'duration: {length:.4f}, ease: "power1.out" }}, {tin:.4f});')
    if spec.get("banner"):
        text, y = spec["banner"]
        html.append(f'      <div class="clip" id="banner" data-start="0" data-duration="{dur}" '
                    f'data-track-index="9" style="top:{round(y * FH)}px"><span>{text.replace(chr(10), "<br>")}</span></div>')
    (out / "index.html").write_text(HTML.format(
        fw=FW, fh=FH, name=name, duration=dur,
        orient="portrait" if FH > FW else "landscape",
        beats="\n".join(html), tweens="\n".join(tweens)))
    print(f"{name}: {n} pictures -> {out / 'index.html'}")


if __name__ == "__main__":
    names = sys.argv[1:] or list(PROJECTS)
    for nm in names:
        build(nm, PROJECTS[nm])
