#!/usr/bin/env python3
"""
brand_overlay.py — add Sky key-word highlights and the brand logo to a caption
overlay that has already been generated and approved.

captions_overlay.py does both on a fresh build (--highlight / --logo). This is
for overlays that already shipped: re-grouping from the transcript could move a
cue or lose a hand fix in the .srt, so the cues are read straight out of the
existing index.html and only the markup changes. Timing and wording stay
byte-identical.

    python3 edit/brand_overlay.py --src graphics/ignite-11-short2-captions \\
        --out graphics/ignite-11-short2-brand-captions \\
        --highlight edit/highlights-ignite-11-short2.json \\
        --logo graphics/brand/silicon-data-white.png

--restyle rewrites only the style of an already-branded overlay in place (the
cue <div>s are not touched) and is how a brand change reaches shipped overlays:

    python3 edit/brand_overlay.py --restyle graphics/ignite-11-short2-brand-captions
    # and --y moves the captions, e.g. under a title card
    python3 edit/brand_overlay.py --restyle graphics/kc-short1-title-captions --y 0.80
"""
import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from captions_overlay import (mark_highlights, cue_html, logo_markup, logo_spec,
                              font_face_css, HL_CSS)

LOGO = Path(__file__).resolve().parent.parent/"graphics"/"brand"/"silicon-data-white.png"


def restyle(project, font="Inter", weight=500, y=None):
    """Current brand style on an existing overlay; every cue line stays byte-identical."""
    out = Path(project)
    html = (out/"index.html").read_text()
    cues = re.findall(r'^.*class="clip cue".*$', html, re.M)
    w = int(re.search(r'data-width="(\d+)"', html).group(1))
    dur = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', html, re.S).group(1)
    html = re.sub(r'\n\s*@font-face \{[^}]*\}', '', html)
    html = re.sub(r"font-family:[^;]*;", f"font-family:'{font}', sans-serif;", html, count=1)
    html = re.sub(r"font-weight:\d+;", f"font-weight:{weight};", html, count=1)
    html = html.replace("<style>", "<style>" + font_face_css(font, weight, out), 1)
    html = re.sub(r"#000\b(?!\w)", "#09090B", html)
    html = re.sub(r"\n\s*/\* key words.*?\*/\n\s*\.cue em \{[^}]*\}", HL_CSS, html, flags=re.S)
    shutil.copy(LOGO, out/LOGO.name)
    logo = logo_spec(LOGO, 300, "left", 110, w)
    css, tag = logo_markup(logo, dur)
    html = re.sub(r"\n\s*#logo \{.*?\n\s*\}", lambda _: css, html, count=1, flags=re.S)
    html = re.sub(r'^\s*<img id="logo".*$', lambda _: tag, html, count=1, flags=re.M)
    if y is not None:                  # caption centre, from the top, like captions_overlay --y
        html, n = re.subn(r"(\.cue \{\s*position:absolute; left:0; right:0; top:)[\d.]+%",
                          lambda m: f"{m.group(1)}{y * 100:.1f}%", html, count=1)
        if not n:
            sys.exit(f"{project}: no .cue top to move")
    if re.findall(r'^.*class="clip cue".*$', html, re.M) != cues:
        sys.exit(f"{project}: cue lines changed, refusing to write")
    (out/"index.html").write_text(html)
    print(f"{out}/index.html restyled · {font} {weight} · {len(cues)} cues untouched")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restyle", help="branded project dir to restyle in place")
    ap.add_argument("--font", default="Inter")
    ap.add_argument("--weight", type=int, default=500)
    ap.add_argument("--y", type=float, help="with --restyle: move the captions (centre, from the top)")
    ap.add_argument("--src", help="existing caption project dir")
    ap.add_argument("--out", help="new project dir")
    ap.add_argument("--highlight", default="", help="JSON list of phrases")
    ap.add_argument("--logo", default="")
    ap.add_argument("--logo-corner", choices=["left", "right"], default="left")
    ap.add_argument("--logo-w", type=int, default=300)
    ap.add_argument("--logo-top", type=int, default=110)
    a = ap.parse_args()
    if a.restyle:
        return restyle(a.restyle, a.font, a.weight, a.y)
    if not (a.src and a.out):
        ap.error("--src and --out are required unless --restyle is given")

    html = (Path(a.src)/"index.html").read_text()
    if "<em>" in html or 'id="logo"' in html:
        sys.exit(f"{a.src} is already branded — point --src at the plain overlay")
    w = int(re.search(r'data-width="(\d+)"', html).group(1))
    dur = re.search(r'id="root"[^>]*data-duration="([\d.]+)"', html, re.S).group(1)

    phrases = json.load(open(a.highlight)) if a.highlight else []
    spans = list(re.finditer(r'(class="clip cue"[^>]*><span>)(.*?)(</span>)', html))
    # one word list across every cue so mark_highlights runs once, then cut it
    # back into cues — but matching must not span a cue boundary, so do it per cue
    total, found = 0, set()
    pieces, last = [], 0
    for m in spans:
        words = [{"w": t} for t in m.group(2).split(" ")]
        n, missed = mark_highlights(words, phrases)
        total += n
        found |= set(phrases) - set(missed)
        pieces += [html[last:m.start(2)], cue_html({"words": words})]
        last = m.end(2)
    html = "".join(pieces) + html[last:]
    for ph in phrases:
        if ph not in found:
            print(f"  WARNING highlight not found in any cue: {ph!r}")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    logo = None
    if a.logo:
        src = Path(a.logo)
        shutil.copy(src, out/src.name)
        logo = logo_spec(src, a.logo_w, a.logo_corner, a.logo_top, w)
    css, tag = logo_markup(logo, dur)
    html = html.replace("    </style>", f"{HL_CSS}{css}\n    </style>", 1)
    if tag:
        i = html.rindex("\n    </div>\n    <script>")
        html = html[:i] + "\n" + tag + html[i:]
    (out/"index.html").write_text(html)
    lit = len(re.findall(r'<span>[^\n]*<em>', html))
    print(f"{out}/index.html · {lit}/{len(spans)} cues highlighted ({total} hits)"
          f"{' · logo ' + a.logo_corner if logo else ''}")


if __name__ == "__main__":
    main()
