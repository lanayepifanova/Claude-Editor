#!/usr/bin/env python3
"""
brand_overlay.py — add gold key-word highlights and the brand logo to a caption
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
"""
import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from captions_overlay import mark_highlights, cue_html, logo_markup, HL_CSS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="existing caption project dir")
    ap.add_argument("--out", required=True, help="new project dir")
    ap.add_argument("--highlight", default="", help="JSON list of phrases")
    ap.add_argument("--logo", default="")
    ap.add_argument("--logo-corner", choices=["left", "right"], default="left")
    ap.add_argument("--logo-w", type=int, default=300)
    ap.add_argument("--logo-top", type=int, default=110)
    a = ap.parse_args()

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
        logo = {"src": src.name, "side": a.logo_corner, "inset": round(w * 0.055),
                "top": a.logo_top, "w": a.logo_w, "opacity": 0.92}
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
