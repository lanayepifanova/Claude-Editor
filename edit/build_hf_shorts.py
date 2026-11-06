#!/usr/bin/env python3
"""Generate the two overlay compositions for the Higgsfield Shorts Studio video.

  graphics/hf-shorts-back   — sits UNDER her matte: big serif titles, colour washes
  graphics/hf-shorts-front  — sits OVER her: captions, cards, prompt bar, steps, CTA

Everything is pinned to the transcript (word timings on the cut timeline), never to
typed seconds, so a re-cut re-times it. Look follows the @justyn.ai reference
(dark green, cream serif, boxed captions) with none of its assets.

    python3 edit/build_hf_shorts.py
"""
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AN = ROOT / "edit/analysis-hf-shorts"
SRC = ROOT / "graphics/hf-shorts-src"
FONTS = ROOT / "graphics/fonts"
DUR = json.load(open(AN / "silence.json"))["cut_duration"]
WORDS = json.load(open(AN / "transcript.json"))
WORDS = WORDS if isinstance(WORDS, list) else WORDS["words"]

GREEN, GREEN2, CREAM, GOLD, INK = "#17372B", "#0F2A20", "#F3ECDD", "#D8B258", "#0E1A14"


def norm(s): return re.sub(r"[^a-z0-9/']", "", s.lower())


def W(word, after=0.0):
    """start time of the first spoken `word` at/after `after` (cut timeline)."""
    for w in WORDS:
        if w["t0"] >= after - 0.01 and norm(w["w"]) == norm(word):
            return w["t0"]
    sys.exit(f"cue not found: {word!r} after {after}")


def E(word, after=0.0):
    for w in WORDS:
        if w["t0"] >= after - 0.01 and norm(w["w"]) == norm(word):
            return w["t1"]
    sys.exit(f"cue not found: {word!r} after {after}")


class Comp:
    def __init__(self, name):
        self.name, self.html, self.js, self.n = name, [], [], 0

    def add(self, inner, t0, t1, style="", cls="", tween=None, ):
        """one timed element on its own track. returns css id."""
        self.n += 1
        i = f"e{self.n}"
        t1 = min(t1, DUR)
        self.html.append(
            f'<div id="{i}" class="clip {cls}" data-start="{t0:.3f}" '
            f'data-duration="{t1 - t0:.3f}" data-track-index="{self.n}" style="{style}">{inner}</div>')
        return i, t0, t1

    def js_(self, s): self.js.append(s)

    # ---- shared motion: wipe in along the grid, wipe out; fast, tight, no bounce ----
    def wipe(self, el, direction="left", d=0.32):
        i, t0, t1 = el
        a = {"left": "inset(0 100% 0 0)", "up": "inset(100% 0 0 0)", "down": "inset(0 0 100% 0)",
             "right": "inset(0 0 0 100%)"}[direction]
        self.js_(f'tl.fromTo("#{i}",{{clipPath:"{a}"}},{{clipPath:"inset(0 0% 0 0)",duration:{d},ease:"power3.out"}},{t0:.3f});')
        self.js_(f'tl.to("#{i}",{{opacity:0,duration:0.14,ease:"power2.in"}},{max(t1 - 0.14, t0 + d):.3f});')

    def pop(self, el, d=0.3, y=36):
        i, t0, t1 = el
        self.js_(f'tl.fromTo("#{i}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:{d},ease:"power3.out"}},{t0:.3f});')
        self.js_(f'tl.to("#{i}",{{opacity:0,duration:0.14,ease:"power2.in"}},{max(t1 - 0.14, t0 + d):.3f});')

    def write(self):
        d = ROOT / "graphics" / self.name
        d.mkdir(parents=True, exist_ok=True)
        for f in ("InstrumentSerif-Regular.ttf", "InstrumentSerif-Italic.ttf", "Inter-Medium.ttf"):
            shutil.copy(FONTS / f, d / f)
        for f in ("presenter.jpg", "still1.jpg", "still2.jpg", "still3.jpg", "still4.jpg", "higgsfield-icon.png"):
            shutil.copy(SRC / f, d / f)
        import base64
        def uri(f): return "data:font/ttf;base64," + base64.b64encode((FONTS / f).read_bytes()).decode()
        fsrc = lambda f: f
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/><title>{self.name}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face{{font-family:"HFSerif";src:url("{fsrc("InstrumentSerif-Regular.ttf")}");font-style:normal}}
@font-face{{font-family:"HFSerif";src:url("{fsrc("InstrumentSerif-Italic.ttf")}");font-style:italic}}
@font-face{{font-family:"HFSans";src:url("{fsrc("Inter-Medium.ttf")}");font-weight:500}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:transparent}}
#root{{position:relative;width:1080px;height:1920px}}
.clip{{position:absolute}}
.serif{{font-family:"HFSerif",Georgia,serif;font-weight:400}}
.sans{{font-family:"HFSans",sans-serif;font-weight:500}}
em{{font-style:italic;color:{GOLD}}}
.card{{background:{CREAM};color:{GREEN2};border-radius:18px}}
.dark{{background:{GREEN};color:{CREAM};border-radius:18px}}
.cap{{left:0;right:0;top:25%;transform:translateY(-50%);display:flex;justify-content:center}}
.cap span{{background:{GREEN};color:{CREAM};font-family:"HFSerif",serif;font-size:56px;line-height:1;
  padding:10px 22px 14px;border-radius:6px;white-space:nowrap;box-shadow:0 0 0 2px rgba(243,236,221,.28)}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920"
  data-fps="30" data-layout-allow-overflow="true">
{chr(10).join(self.html)}
</div>
<script>
// GENERATED by edit/build_hf_shorts.py — do not hand-edit.
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
tl.seek(0);
window.__timelines["main"] = tl;
</script></body></html>"""
        (d / "index.html").write_text(page)
        print(f"{self.name}: {self.n} elements -> {d/'index.html'}")


# ============================================================ BACK (behind her)
B = Comp("hf-shorts-back")

# 1 hook — green plate with the title behind her: "Claude did."
t_cl, t_did = W("Claude", 1.5), W("did.", 2.0)
el = B.add(f'<div class="serif" style="position:absolute;left:0;right:0;top:150px;text-align:center;'
           f'font-size:250px;line-height:1;color:{CREAM};white-space:nowrap">Claude<span id="did" style="display:inline-block;'
           f'color:{GOLD};font-style:italic;opacity:0">&nbsp;did.</span></div>',
           0.0, W("No", 2.5), style=f"left:0;top:0;width:1080px;height:1920px;background:{GREEN}")
B.wipe(el, "left", 0.30)
B.js_(f'tl.fromTo("#did",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{t_did:.3f});')

# 2 titles appear behind me
t0 = W("titles", 8.0)
el = B.add(f'<div class="serif" style="font-size:430px;line-height:1;color:{GREEN};text-align:center;'
           f'">Titles</div>', t0, W("the", 9.6) + 0.25,
           style="left:0;top:560px;width:1080px")
B.wipe(el, "up", 0.35)

# 3 mood changes with the colours — plates cycle, her cutout stays
t_mood, t_col = W("mood", 10.5), W("colors.", 11.5)
t_end = W("All", 12.5)
cols = [(GREEN, CREAM), ("#C8552F", CREAM), ("#D9A21B", GREEN2), ("#14264A", CREAM), ("#4B2A4F", CREAM)]
step = (t_end - t_mood) / len(cols)
for k, (bg, fg) in enumerate(cols):
    a = t_mood + k * step
    b = t_end if k == len(cols) - 1 else a + step + 0.06
    el = B.add(f'<div class="serif" style="position:absolute;left:0;right:0;top:170px;text-align:center;'
               f'font-size:300px;line-height:1;color:{fg};font-style:italic">Colors</div>',
               a, b, style=f"left:0;top:0;width:1080px;height:1920px;background:{bg}")
    B.js_(f'tl.fromTo("#{el[0]}",{{clipPath:"inset(0 0 100% 0)"}},{{clipPath:"inset(0 0 0% 0)",duration:0.2,ease:"power3.out"}},{a:.3f});')

# 4 product line
a, b = W("I", 16.0), W("You", 19.2)
el = B.add(f'<img src="higgsfield-icon.png" style="position:absolute;left:465px;top:70px;width:150px;height:150px;border-radius:34px">'
           f'<div class="serif" style="position:absolute;left:0;right:0;top:250px;text-align:center;font-size:170px;'
           f'line-height:1;color:{CREAM};white-space:nowrap">Shorts <em>Studio</em></div>',
           a, b + 0.3, style=f"left:0;top:0;width:1080px;height:1920px;background:{GREEN}")
B.wipe(el, "right", 0.3)

# 5 CTA — REELS behind her
a = W("Comment", 46.0)
el = B.add('', a, DUR, style=f"left:0;top:0;width:1080px;height:1920px;background:{GREEN}")
B.wipe(el, "left", 0.3)
B.write()

# ============================================================ FRONT (over her)
F = Comp("hf-shorts-front")

# ---- captions: boxed serif pills, wording from the editable SRT --------------------
def ts(s):
    h, m, r = s.split(":"); sec, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000

cues = []
for blk in open(ROOT / "project/hf-shorts.srt").read().strip().split("\n\n"):
    l = blk.split("\n"); a, b = l[1].split(" --> ")
    cues.append([ts(a), ts(b), " ".join(l[2:])])
HI = ["Claude", "Higgsfield", "Shorts Studio", "/shorts-studio", "MCP", "Reels", "Premiere Pro"]
for a, b, txt in cues:
    h = txt
    for k in HI:
        h = h.replace(k, f"<em>{k}</em>")
    F.add(f"<span>{h}</span>", a, b, cls="cap")

# ---- 2: no After Effects / no Premiere Pro — chips struck through ------------------
def chip(label, w=410):
    return (f'<div class="card sans" style="width:{w}px;height:104px;display:flex;align-items:center;justify-content:center;'
            f'font-size:40px;position:relative">{label}<div class="strike" style="position:absolute;left:18px;right:18px;top:50%;'
            f'height:6px;background:#C8552F;transform-origin:left;transform:scaleX(0)"></div></div>')
a, b = W("After", 2.5), W("one", 4.4) + 1.0
c1 = F.add(chip("After Effects"), a, b, style="left:100px;top:1360px")
F.pop(c1, 0.28)
F.js_(f'tl.to("#{c1[0]} .strike",{{scaleX:1,duration:0.22,ease:"power3.out"}},{a + 0.45:.3f});')
a2 = W("Premiere", 3.5)
c2 = F.add(chip("Premiere Pro"), a2, b, style="left:570px;top:1360px")
F.pop(c2, 0.28)
F.js_(f'tl.to("#{c2[0]} .strike",{{scaleX:1,duration:0.22,ease:"power3.out"}},{a2 + 0.55:.3f});')

# ---- 3: the prompt bar on top ------------------------------------------------------
a, b = W("one", 4.4), W("know", 6.5) + 0.6
prompt = "I want you to take a pass at editing this."
chars = "".join(f'<span class="ch" style="opacity:0">{c if c != " " else "&nbsp;"}</span>' for c in prompt)
el = F.add(f'<div class="sans" style="font-size:20px;letter-spacing:.14em;color:#6B6A5F;margin:0 0 10px 6px">&#9679; CLAUDE</div>'
           f'<div class="sans" style="font-size:36px;color:{INK};display:flex;align-items:center;justify-content:space-between">'
           f'<div>{chars}</div><div class="spin" style="width:44px;height:44px;border-radius:50%;border:5px solid {GREEN};'
           f'border-top-color:transparent;flex:none;margin-left:16px"></div></div>',
           a - 0.3, b, cls="card", style="left:60px;top:110px;width:960px;padding:22px 30px 26px;border-radius:30px")
F.pop(el, 0.3, -30)
F.js_(f'tl.to("#{el[0]} .ch",{{opacity:1,duration:0.01,stagger:{(b - a - 1.1) / len(prompt):.4f}}},{a:.3f});')
F.js_(f'tl.to("#{el[0]} .spin",{{rotation:720,duration:{b - a + 0.3:.2f},ease:"none"}},{a - 0.3:.3f});')

# ---- 4: "I know nothing about video editing" -> 0 -----------------------------------
a, b = W("nothing", 6.5), W("Watch", 7.5) + 0.2
el = F.add('<div class="sans" style="font-size:24px;letter-spacing:.16em;opacity:.7">VIDEO EDITING EXPERIENCE</div>'
           f'<div class="serif" style="font-size:190px;line-height:1">0 <em style="font-size:80px">years</em></div>',
           a, b, cls="dark", style="left:210px;top:1280px;width:660px;padding:26px 0 18px;text-align:center")
F.wipe(el, "left", 0.3)

# ---- 5: photos flow into frame -----------------------------------------------------
a = W("photos", 9.0); b = W("and", 10.5) + 1.0
spots = [(70, 1090, -7), (560, 1150, 5), (150, 1420, 4), (640, 1450, -5)]
for k, (x, y, r) in enumerate(spots):
    el = F.add(f'<img src="still{k + 1}.jpg" style="width:330px;display:block;border-radius:4px">',
               a + k * 0.2, b, cls="card",
               style=f"left:{x}px;top:{y}px;width:360px;padding:15px 15px 44px;border-radius:6px;transform:rotate({r}deg)")
    F.js_(f'tl.fromTo("#{el[0]}",{{opacity:0,y:260,rotation:{r - 14}}},{{opacity:1,y:0,rotation:{r},duration:0.45,ease:"power3.out"}},{a + k * 0.2:.3f});')
    F.js_(f'tl.to("#{el[0]}",{{opacity:0,y:-40,duration:0.18,ease:"power2.in"}},{b - 0.18:.3f});')

# ---- 6: what I gave it: photo + script + reference ---------------------------------
a0, b0 = W("one", 13.4), W("I", 16.0) + 0.2
y = 1250
photo = F.add(f'<img src="presenter.jpg" style="width:280px;height:300px;object-fit:cover;object-position:50% 38%;border-radius:10px;display:block">'
              '<div class="sans" style="font-size:22px;letter-spacing:.14em;margin-top:12px;text-align:center">PHOTO</div>',
              W("photo,", 13.4), b0, cls="card", style=f"left:60px;top:{y}px;width:310px;padding:15px 15px 16px")
F.pop(photo, 0.3)
script = F.add('<div class="sans" style="font-size:22px;letter-spacing:.14em;margin-bottom:12px">SCRIPT</div>'
               '<div class="serif" style="font-size:31px;line-height:1.15">&ldquo;I didn&rsquo;t edit a single second of this video. <em style="color:#B5542C">Claude did.</em>&rdquo;</div>'
               '<div class="sans" style="font-size:19px;margin-top:14px;opacity:.6">No After Effects. No Premiere Pro.</div>',
               W("script,", 14.0), b0, cls="card", style=f"left:385px;top:{y}px;width:310px;height:352px;padding:20px")
F.pop(script, 0.3)
ref = F.add('<div style="width:280px;height:300px;border-radius:10px;background:#0F2A20;display:flex;align-items:center;justify-content:center">'
            f'<div style="width:0;height:0;border-left:56px solid {CREAM};border-top:34px solid transparent;border-bottom:34px solid transparent;margin-left:14px"></div></div>'
            '<div class="sans" style="font-size:22px;letter-spacing:.14em;margin-top:12px;text-align:center">REFERENCE VIDEO</div>',
            W("reference", 15.0), b0, cls="card", style=f"left:710px;top:{y}px;width:310px;padding:15px 15px 16px")
F.pop(ref, 0.3)

# ---- 7: months of Premiere -> struck --------------------------------------------------
a, b = W("months", 19.8), W("Just", 22.9) + 0.1
el = F.add('<div class="sans" style="font-size:24px;letter-spacing:.16em;opacity:.7">LEARNING PREMIERE PRO &amp; AFTER EFFECTS</div>'
           '<div class="serif" id="mo" style="font-size:200px;line-height:1;position:relative;display:inline-block">Months'
           '<div class="strike" style="position:absolute;left:0;right:0;top:54%;height:10px;background:#C8552F;transform-origin:left;transform:scaleX(0)"></div></div>',
           a, b, cls="dark", style="left:150px;top:1300px;width:780px;padding:26px 0 20px;text-align:center")
F.wipe(el, "left", 0.3)
F.js_(f'tl.to("#{el[0]} .strike",{{scaleX:1,duration:0.25,ease:"power3.out"}},{W("or", 21.0):.3f});')

# ---- 8: two ways in --------------------------------------------------------------------
a, b = W("pick", 23.2), W("Genjutsu", 27.5) + 0.3
rA = F.add('<div class="sans" style="font-size:22px;letter-spacing:.16em;opacity:.7">ROUTE A</div>'
           '<div class="serif" style="font-size:66px;line-height:1.02">Upload your own<br>reference video</div>',
           a, b, cls="card", style="left:70px;top:1130px;width:940px;padding:22px 34px 24px")
F.wipe(rA, "left", 0.3)
rB = F.add('<div class="sans" style="font-size:22px;letter-spacing:.16em;opacity:.7">ROUTE B</div>'
           '<div class="serif" style="font-size:66px;line-height:1.02">Pick a <em style="color:#B5542C">template</em><br>from the Higgsfield site</div>',
           W("one", 25.0), b, cls="card", style="left:70px;top:1420px;width:940px;padding:22px 34px 24px")
F.wipe(rB, "left", 0.3)

# ---- 9: a few clicks -----------------------------------------------------------------------
a, b = W("fully", 28.5), W("You", 31.3) + 0.1
el = F.add('<div class="sans" style="font-size:24px;letter-spacing:.16em;opacity:.7">FULLY EDITED VIDEO</div>'
           '<div class="serif" style="font-size:150px;line-height:1">in <em>a few</em><br>clicks.</div>',
           a, b, cls="dark", style="left:140px;top:1190px;width:800px;padding:26px 0 24px;text-align:center")
F.wipe(el, "up", 0.32)

# ---- 10: no filming — a photo works ---------------------------------------------------------
a, b = W("film", 31.8), W("Here's", 33.5) + 0.15
el = F.add(f'<img src="presenter.jpg" style="width:230px;height:250px;object-fit:cover;object-position:50% 38%;border-radius:10px;flex:none">'
           '<div><div class="sans" style="font-size:22px;letter-spacing:.16em;opacity:.7">NO FILMING</div>'
           '<div class="serif" style="font-size:78px;line-height:1">A <em style="color:#B5542C">photo</em><br>works.</div></div>',
           a, b, cls="card", style="left:90px;top:1260px;width:900px;padding:22px 30px;display:flex;gap:30px;align-items:center")
F.wipe(el, "left", 0.3)

# ---- 11: step 1 — connect Higgsfield MCP to Claude --------------------------------------------
a, b = W("First,", 34.0), W("Then", 38.2) + 0.25
el = F.add('<div class="sans" style="font-size:24px;letter-spacing:.16em;color:%s">STEP 01</div>' % GOLD +
           '<div class="serif" style="font-size:84px;line-height:1;margin:6px 0 24px">Connect Higgsfield MCP<br>to Claude</div>'
           '<div style="display:flex;align-items:center;gap:22px">'
           '<img src="higgsfield-icon.png" style="width:120px;height:120px;border-radius:28px">'
           f'<div style="flex:1;height:6px;background:{GOLD};transform-origin:left;transform:scaleX(0)" class="link"></div>'
           f'<div class="serif" style="font-size:78px;line-height:1;background:{CREAM};color:{GREEN};padding:16px 28px 22px;border-radius:24px">Claude</div></div>'
           '<div class="sans" style="font-size:24px;margin-top:20px;opacity:.75">setup page on higgsfield.ai</div>',
           a, b, cls="dark", style="left:60px;top:1180px;width:960px;padding:30px 38px 32px")
F.wipe(el, "up", 0.34)
F.js_(f'tl.to("#{el[0]} .link",{{scaleX:1,duration:0.4,ease:"power3.out"}},{W("connect", 34.5) + 0.8:.3f});')

# ---- 12: step 2 — type /shorts-studio, then the three inputs ----------------------------------
a, b = W("Then", 38.2), W("And", 42.3) + 0.2
cmd = "/shorts-studio"
cc = "".join(f'<span class="ch" style="opacity:0">{c}</span>' for c in cmd)
el = F.add('<div class="sans" style="font-size:24px;letter-spacing:.16em;color:%s">STEP 02</div>' % GOLD +
           f'<div class="sans" style="margin:14px 0 22px;background:{CREAM};color:{INK};border-radius:22px;padding:20px 28px;font-size:52px">'
           f'<span style="opacity:.45">&rsaquo;&nbsp;</span>{cc}<span class="caret" style="display:inline-block;width:4px;height:48px;background:{INK};vertical-align:-8px;margin-left:4px"></span></div>'
           '<div style="display:flex;gap:16px">'
           + "".join(f'<div class="serif chip2" style="opacity:0;flex:1;text-align:center;font-size:48px;line-height:1;padding:16px 0 20px;'
                     f'border:3px solid {CREAM};border-radius:16px">{t}</div>' for t in ("Reference", "Script", "Materials")) +
           f'</div><div class="serif gen" style="opacity:0;margin-top:18px;text-align:center;font-size:64px;line-height:1;background:{GOLD};'
           f'color:{GREEN2};padding:16px 0 22px;border-radius:18px">Generate</div>',
           a, b, cls="dark", style="left:60px;top:1130px;width:960px;padding:30px 38px 34px")
F.wipe(el, "up", 0.32)
ta, tb = W("type", 38.5) + 0.35, W("add", 39.5)
F.js_(f'tl.to("#{el[0]} .ch",{{opacity:1,duration:0.01,stagger:{(tb - ta) / len(cmd):.4f}}},{ta:.3f});')
for k, wd in enumerate(("reference,", "script,", "materials,")):
    F.js_(f'tl.fromTo("#{el[0]} .chip2:nth-child({k + 1})",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25,ease:"power3.out"}},{W(wd, 39.8):.3f});')
F.js_(f'tl.fromTo("#{el[0]} .gen",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25,ease:"power3.out"}},{W("generate.", 41.5):.3f});')

# ---- 13: 3-day free trial stamp ----------------------------------------------------------------------
a, b = W("three-day", 44.0), W("Comment", 46.5) - 0.05
el = F.add('<div class="sans" style="font-size:26px;letter-spacing:.18em">NEW USERS</div>'
           '<div class="serif" style="font-size:150px;line-height:.95">3-day<br><em style="color:#B5542C">free trial</em></div>'
           '<div class="sans" style="font-size:26px;letter-spacing:.18em;margin-top:6px">HIGGSFIELD MCP</div>',
           a - 0.3, b, cls="card", style="left:190px;top:1240px;width:700px;padding:26px 0 28px;text-align:center;border:6px solid %s" % GREEN2)
F.js_(f'tl.fromTo("#{el[0]}",{{opacity:0,scale:1.25,rotation:-10}},{{opacity:1,scale:1,rotation:-3,duration:0.28,ease:"power3.out"}},{a - 0.3:.3f});')
F.js_(f'tl.to("#{el[0]}",{{opacity:0,duration:0.14}},{b - 0.14:.3f});')

# ---- 14: CTA ---------------------------------------------------------------------------------------------
a = W("Comment", 46.0)
el = F.add('<div class="serif" style="font-size:110px;line-height:1">Comment <em>&ldquo;REELS&rdquo;</em></div>'
           f'<div class="sans" style="font-size:28px;margin-top:10px;color:{CREAM};opacity:.85">and I&rsquo;ll send you the command &amp; setup link</div>',
           a, DUR, style=f"left:0;top:70px;width:1080px;text-align:center;color:{CREAM}")
F.pop(el, 0.3, -30)
rl = "REELS"
rc = "".join(f'<span class="ch" style="opacity:0">{c}</span>' for c in rl)
el = F.add(f'<div style="width:56px;height:56px;border-radius:50%;background:{GREEN};flex:none"></div>'
           f'<div class="sans" style="font-size:40px;flex:1;margin-left:18px;color:{INK}"><span class="ph" style="opacity:.4">Add a comment&hellip;</span>{rc}</div>'
           f'<div style="width:56px;height:56px;border-radius:50%;background:{GREEN};flex:none"></div>',
           a + 0.2, DUR, cls="card", style="left:60px;top:1560px;width:960px;height:96px;padding:0 20px;display:flex;align-items:center;border-radius:48px")
F.pop(el, 0.3)
F.js_(f'tl.set("#{el[0]} .ph",{{opacity:0}},{a + 0.9:.3f});')
F.js_(f'tl.to("#{el[0]} .ch",{{opacity:1,duration:0.01,stagger:0.12}},{a + 0.9:.3f});')
F.write()
