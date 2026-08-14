#!/usr/bin/env python3
"""
build.py — manifest.json -> HyperFrames composition HTML.

The manifest is the edit. This file owns the *vocabulary* (CSS + motion); the
manifest owns the *decisions* (what, where, when). Changing a card is a small
JSON patch, not an HTML rewrite.

    python3 edit/build.py --manifest edit/manifest.json \
                          --analysis edit/analysis \
                          --out graphics/intro-overlays/index.html
"""
import argparse, json
from pathlib import Path

# ── style vocabulary ──────────────────────────────────────────────────────
def css(st):
    e = st["edge"]; c = st["cream"]; s = st["sizes"]
    return f"""
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:3840px; height:2160px; overflow:hidden; background:transparent; }}
      :root {{
        --ink:{st['ink']}; --cream:{c}; --gold:{st['gold']};
        --red:{st['red']}; --orange:{st['orange']};
        --serif:{st['serif']}; --sans:{st['sans']}; --mono:{st['mono']};
      }}
      #root {{ position:relative; width:3840px; height:2160px; }}
      .clip {{ position:absolute; inset:0; display:grid; place-items:center; }}
      .anchor-top-right {{ place-items:start end; padding:190px 200px 0 0; }}
      .card {{ position:relative; width:3200px; text-align:center; }}

      /* flat cream knockout — a hard edge, never a glow */
      .lift {{ text-shadow:
        {e}px 0 0 {c}, -{e}px 0 0 {c}, 0 {e}px 0 {c}, 0 -{e}px 0 {c},
        {e-2}px {e-2}px 0 {c}, -{e-2}px {e-2}px 0 {c},
        {e-2}px -{e-2}px 0 {c}, -{e-2}px -{e-2}px 0 {c}; }}
      .liftimg {{ filter:
        drop-shadow(5px 0 0 {c}) drop-shadow(-5px 0 0 {c})
        drop-shadow(0 5px 0 {c}) drop-shadow(0 -5px 0 {c}); }}

      .eyebrow {{ font-family:var(--sans); font-size:{s['eyebrow']}px; font-weight:900;
                 letter-spacing:.34em; text-transform:uppercase; color:var(--ink);
                 margin-bottom:44px; }}
      .headline {{ font-family:var(--serif); font-size:{s['headline']}px; font-weight:700;
                  line-height:1.02; color:var(--ink); }}

      .shot-wrap {{ position:relative; display:inline-block; margin-top:54px; }}
      .shot {{ display:block; height:auto; border:10px solid #000; }}
      .shot-stamp {{ position:absolute; right:-90px; top:-90px; display:block; }}

      .rec-row {{ display:flex; align-items:center; gap:24px; }}
      .dot {{ display:block; width:40px; height:40px; border-radius:50%; background:var(--red); }}
      .rec-label {{ font-family:var(--sans); font-size:44px; font-weight:900;
                   letter-spacing:.22em; color:var(--ink); }}
      .tc {{ font-family:var(--mono); font-size:44px; font-weight:800;
            color:var(--ink); margin-left:22px; }}

      .brief-row {{ display:flex; justify-content:space-between; width:2600px;
                   margin:0 auto; align-items:flex-start; }}
      .items {{ display:inline-block; text-align:left; }}
      .item {{ display:flex; align-items:baseline; gap:44px; }}
      .num {{ font-family:var(--sans); font-size:{s['num']}px; font-weight:900;
             letter-spacing:.12em; color:var(--red); min-width:100px; }}
      .item-text {{ font-family:var(--serif); font-size:{s['item']}px; font-weight:700;
                   line-height:1.06; color:var(--ink); }}

      .wave-wrap {{ position:relative; width:2600px; height:340px; margin:46px auto 40px; }}
      .wave {{ position:absolute; left:50%; top:0; display:flex; align-items:flex-end;
              gap:5px; height:240px; transform:translateX(-50%); }}
      .bar {{ display:block; flex:1 1 0; background:var(--ink);
             transform-origin:bottom center; min-height:12px; }}
      .bar.rm {{ background:var(--gold); }}
      .strike {{ position:absolute; display:block; height:13px; background:var(--red);
                transform-origin:left center; }}
      .wave-meta {{ position:absolute; left:0; right:0; top:262px; font-family:var(--mono);
                   font-size:52px; font-weight:800; color:var(--ink); text-align:center; }}
      .meta-after {{ color:var(--red); }}

      .handoff {{ display:flex; align-items:center; justify-content:center; gap:130px; }}
      .fig-wrap {{ position:relative; display:inline-block; width:380px; height:380px; }}
      .fig {{ display:block; width:380px; height:380px; }}
      .xbar {{ position:absolute; display:block; width:440px; height:20px;
              background:var(--red); border-radius:3px; }}
      .arrow {{ display:block; width:240px; height:18px; background:var(--red);
               transform-origin:left center; }}
      .glyph {{ display:block; width:340px; height:340px; }}

      .split {{ position:relative; width:2600px; height:900px; margin:0 auto; }}
      .gh {{ position:absolute; left:50%; top:0; width:340px; height:340px;
            margin-left:-170px; display:block; }}
      .conn {{ position:absolute; left:0; top:0; width:2600px; height:700px; display:block; }}
      .tool {{ position:absolute; top:600px; width:1000px; text-align:center; }}
      .tool img {{ display:block; width:250px; height:250px; margin:0 auto 34px; }}
      .tool .name {{ font-family:var(--serif); font-size:{s['toolName']}px; font-weight:700;
                    color:var(--ink); white-space:nowrap; }}

      .check-list {{ display:inline-block; text-align:left; }}
      .crow {{ position:relative; display:flex; align-items:center; gap:70px; }}
      .crow + .crow {{ margin-top:38px; }}
      .clabel {{ font-family:var(--serif); font-size:118px; font-weight:700;
                color:var(--ink); width:1320px; }}
      .cmark {{ font-family:var(--sans); font-size:112px; font-weight:900;
               color:var(--red); width:120px; text-align:center; }}
      .cstrike {{ position:absolute; left:0; top:54%; display:block; width:1320px;
                 height:14px; background:var(--red); transform-origin:left center; }}
      .cblank {{ width:1320px; height:14px; background:var(--ink); display:block; }}
"""


# ── block renderers ───────────────────────────────────────────────────────
def block_html(cid, b):
    t = b["type"]
    if t == "headline":
        return f'<h2 class="headline lift">{b["text"]}</h2>'
    if t == "eyebrow":
        return f'<div class="eyebrow lift">{b["text"]}</div>'
    if t == "screenshot":
        return (f'<div class="shot-wrap" id="{cid}-shot">'
                f'<img class="shot liftimg" src="{b["src"]}" style="width:{b["width"]}px" alt="">'
                f'<img class="shot-stamp liftimg" id="{cid}-stamp" src="{b["stamp"]}" '
                f'style="width:{b["stampSize"]}px;height:{b["stampSize"]}px" alt=""></div>')
    if t == "rec":
        return (f'<div class="rec-row lift" id="{cid}-row"><span class="dot" id="{cid}-dot"></span>'
                f'<span class="rec-label">REC</span>'
                f'<span class="tc" id="{cid}-tc">00:00:00:00</span></div>')
    if t == "briefRow":
        def item(side, d):
            return (f'<div class="items lift" id="{cid}-{side}"><div class="item">'
                    f'<span class="num">{d["num"]}</span>'
                    f'<span class="item-text">{d["text"]}</span></div></div>')
        return (f'<div class="brief-row">{item("left", b["left"])}'
                f'{item("right", b["right"])}</div>')
    if t == "waveform":
        return (f'<div class="wave-wrap" id="{cid}-wavewrap">'
                f'<div class="wave liftimg" id="{cid}-wave"></div>'
                f'<div class="wave liftimg" id="{cid}-after"></div>'
                f'<div class="wave-meta lift" id="{cid}-meta">{b["beforeLabel"]}</div>'
                f'<div class="wave-meta meta-after lift" id="{cid}-metaAfter">{b["afterLabel"]}</div></div>')
    if t == "handoff":
        x = ("" if not b.get("strikeOut") else
             f'<span class="xbar liftimg" id="{cid}-x1" style="left:26px;top:48px"></span>'
             f'<span class="xbar liftimg" id="{cid}-x2" style="left:26px;top:332px"></span>')
        return (f'<div class="handoff"><div class="fig-wrap">'
                f'<svg class="fig liftimg" id="{cid}-figure" viewBox="0 0 100 100" fill="none" '
                f'stroke="#000" stroke-width="6.4" stroke-linecap="round">'
                f'<circle cx="50" cy="24" r="13"/>'
                f'<path d="M26 58c0-13 11-21 24-21s24 8 24 21"/>'
                f'<rect x="18" y="62" width="64" height="30" rx="3"/>'
                f'<path d="M30 74h40M30 82h26"/></svg>{x}</div>'
                f'<span class="arrow" id="{cid}-arrow"></span>'
                f'<img class="glyph liftimg" id="{cid}-glyph" src="{b["to"]}" alt=""></div>')
    if t == "split":
        return (f'<div class="split">'
                f'<img class="gh liftimg" id="{cid}-root" src="{b["root"]}" alt="">'
                f'<svg class="conn liftimg" id="{cid}-conn" viewBox="0 0 2600 700" fill="none" '
                f'stroke="#B32D1C" stroke-width="20" stroke-linecap="round">'
                f'<path d="M1300 356 V440 H640 V596"/><path d="M1300 356 V440 H1960 V596"/></svg>'
                f'<div class="tool lift" id="{cid}-left" style="left:140px">'
                f'<img class="liftimg" src="{b["left"]["img"]}" alt="">'
                f'<div class="name">{b["left"]["name"]}</div></div>'
                f'<div class="tool lift" id="{cid}-right" style="right:140px">'
                f'<img class="liftimg" src="{b["right"]["img"]}" alt="">'
                f'<div class="name">{b["right"]["name"]}</div></div></div>')
    if t == "checklist":
        rows = ""
        for i, r in enumerate(b["rows"], 1):
            rows += (f'<div class="crow"><span class="clabel lift">{r}</span>'
                     f'<span class="cmark lift" id="{cid}-m{i}">&#10003;</span>'
                     f'<span class="cstrike" id="{cid}-s{i}"></span></div>')
        if b.get("openRow"):
            rows += (f'<div class="crow" id="{cid}-open"><span class="cblank liftimg"></span>'
                     f'<span class="cmark lift">?</span></div>')
        return f'<div class="check-list">{rows}</div>'
    raise SystemExit(f"unknown block type: {t}")


# ── motion vocabulary ─────────────────────────────────────────────────────
ANIM = {
    "rise":  'tl.fromTo("{sel}", {{opacity:0,y:26}}, {{opacity:1,y:0,duration:{d},ease:"power3.out"}}, {t});',
    "pop":   'tl.fromTo("{sel}", {{opacity:0,scale:.78}}, {{opacity:1,scale:1,duration:{d},ease:"power3.out"}}, {t});',
    "fade":  'tl.fromTo("{sel}", {{opacity:0}}, {{opacity:1,duration:{d},ease:"power2.out"}}, {t});',
    "slide": 'tl.fromTo("{sel}", {{opacity:0,x:-34}}, {{opacity:1,x:0,duration:{d},ease:"power3.out"}}, {t});',
    "draw":  'tl.fromTo("{sel}", {{scaleX:0}}, {{scaleX:1,duration:{d},ease:"power3.out",transformOrigin:"left center"}}, {t});',
    "spin":  'tl.fromTo("{sel}", {{opacity:0,scale:.80,rotation:0}}, {{opacity:1,scale:1,rotation:360,duration:{d},ease:"power3.out"}}, {t});',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="edit/manifest.json")
    ap.add_argument("--analysis", default="edit/analysis")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    m = json.load(open(a.manifest))
    st, mo = m["style"], m["motion"]
    an = Path(a.analysis)
    env = json.load(open(an/"envelope.json"))
    sil = json.load(open(an/"silence.json"))

    # waveform bars, straight from the analysis — never invented
    NB = 80
    vals, W = env["values"], env["window"]
    total = env["duration"]
    bars = []
    for i in range(NB):
        t0, t1 = i*total/NB, (i+1)*total/NB
        chunk = vals[int(t0/W):max(int(t1/W), int(t0/W)+1)] or [-90.0]
        h = max(0.06, min(1.0, (max(chunk)+50.0)/40.0))
        mid = (t0+t1)/2
        bars.append({"h": round(h, 3),
                     "k": 1 if any(s <= mid <= e for s, e in sil["segments"]) else 0})

    sections, script = [], []
    for c in m["cards"]:
        cid = c["id"]
        anchor = " anchor-top-right" if c.get("anchor") == "top-right" else ""
        off = f' style="margin-top:{c["offsetY"]*2}px"' if c.get("offsetY") else ""
        body = "".join(block_html(cid, b) for b in c["blocks"])
        sections.append(
            f'      <section id="{cid}" class="clip{anchor}" data-start="{c["start"]}" '
            f'data-duration="{c["duration"]}" data-track-index="{c["track"]}">\n'
            f'        <div class="card"{off}><div class="content" id="{cid}-content">'
            f'{body}</div></div>\n      </section>')

        end = c["start"] + c["duration"]
        script.append(f'      // ── {cid} ──')
        script.append(f'      tl.fromTo("#{cid}-content", {{opacity:0,y:30}}, '
                      f'{{opacity:1,y:0,duration:{mo["in"]},ease:"{mo["ease_in"]}"}}, '
                      f'{round(c["start"]+0.12,2)});')

        for b in c.get("beats", []):
            tgt, at = b["target"], b["at"]
            anim, dur = b.get("anim"), b.get("dur", 0.45)
            sel = f'#{cid}-{tgt}'
            if tgt == "bars":
                script.append(f'      BARS.forEach(function(b,i){{ tl.fromTo("#{cid}-wb"+i, '
                              f'{{scaleY:0}}, {{scaleY:1,duration:.24,ease:"power2.out"}}, '
                              f'{at} + i*{b.get("stagger",0.01)}); }});')
            elif tgt == "strikes":
                script.append(f'      for (var s=0;s<NSTRIKE;s++) tl.fromTo("#{cid}-st"+s, '
                              f'{{scaleX:0}}, {{scaleX:1,duration:.34,ease:"power3.out"}}, '
                              f'{at} + s*{b.get("stagger",0.085)});')
            elif tgt == "collapse":
                script.append(
                    f'      tl.set("#{cid}-after",{{opacity:0}},0); tl.set("#{cid}-metaAfter",{{opacity:0}},0);\n'
                    f'      tl.to(".bar.rm",{{scaleY:0,opacity:0,duration:.40,ease:"power2.in"}},{at});\n'
                    f'      tl.to(".strike",{{opacity:0,duration:.28}},{round(at+0.05,2)});\n'
                    f'      tl.to("#{cid}-wave",{{opacity:0,duration:.36}},{round(at+0.35,2)});\n'
                    f'      tl.to("#{cid}-meta",{{opacity:0,duration:.30}},{round(at+0.35,2)});\n'
                    f'      tl.fromTo("#{cid}-after",{{opacity:0}},{{opacity:1,duration:.52,ease:"power3.out"}},{round(at+0.47,2)});\n'
                    f'      tl.to("#{cid}-metaAfter",{{opacity:1,duration:.36}},{round(at+0.57,2)});')
            elif tgt == "xmark":
                script.append(
                    f'      tl.set(["#{cid}-x1","#{cid}-x2"],{{scaleX:0}},0);\n'
                    f'      tl.fromTo("#{cid}-x1",{{scaleX:0,rotation:45}},{{scaleX:1,rotation:45,'
                    f'duration:{dur},ease:"power3.out",transformOrigin:"left center"}},{at});\n'
                    f'      tl.fromTo("#{cid}-x2",{{scaleX:0,rotation:-45}},{{scaleX:1,rotation:-45,'
                    f'duration:{dur},ease:"power3.out",transformOrigin:"left center"}},{round(at+0.18,2)});\n'
                    f'      tl.to("#{cid}-figure",{{opacity:.16,duration:.50}},{round(at+0.55,2)});\n'
                    f'      tl.to(["#{cid}-x1","#{cid}-x2"],{{opacity:.30,duration:.50}},{round(at+0.55,2)});')
            elif tgt == "rows":
                script.append(
                    f'      tl.set(["#{cid}-s1","#{cid}-s2","#{cid}-s3"],{{scaleX:0}},0);\n'
                    f'      tl.set(["#{cid}-m1","#{cid}-m2","#{cid}-m3","#{cid}-open"],{{opacity:0}},0);\n'
                    f'      [1,2,3].forEach(function(n,i){{ var t={at}+i*{b.get("stagger",0.65)};\n'
                    f'        tl.to("#{cid}-s"+n,{{scaleX:1,duration:.45,ease:"power2.out"}},t);\n'
                    f'        tl.to("#{cid}-m"+n,{{opacity:1,duration:.30}},t+.30); }});')
            elif anim in ANIM:
                script.append("      " + ANIM[anim].format(sel=sel, d=dur, t=at))

        if c.get("holdToEnd"):
            script.append(f'      // holds to the final frame — no exit')
        elif c.get("holdToNext"):
            script.append(f'      tl.to("#{cid}-content",{{opacity:0,duration:.14,'
                          f'ease:"power2.in"}},{round(end-0.14,2)});')
            script.append(f'      tl.set("#{cid}-content",{{opacity:0}},{round(end+0.05,2)});')
        else:
            script.append(f'      tl.to("#{cid}-content",{{opacity:0,y:-18,duration:{mo["out"]},'
                          f'ease:"{mo["ease_out"]}"}},{round(end-0.40,2)});')

    # rec timecode
    rec = next((c for c in m["cards"] if any(b["type"] == "rec" for b in c["blocks"])), None)
    if rec:
        b = next(b for b in rec["blocks"] if b["type"] == "rec")
        script.append(f'''      var tc={{v:0}};
      tl.to(tc,{{v:{b["runTo"]},duration:{b["runTo"]},ease:"none",onUpdate:function(){{
        var f=Math.floor(tc.v*60), el=document.getElementById("{rec["id"]}-tc");
        var p=function(n){{return String(n).padStart(2,"0");}};
        if(el) el.textContent="00:00:"+p(Math.floor(f/60))+":"+p(f%60); }}}},{rec["start"]+0.06});
      tl.to("#{rec["id"]}-dot",{{opacity:.2,duration:.5,yoyo:true,repeat:3}},{rec["start"]+0.5});''')

    wave_card = next((c for c in m["cards"]
                      if any(b["type"] == "waveform" for b in c["blocks"])), None)
    wid = wave_card["id"] if wave_card else None

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=3840, height=2160" />
    <title>{m['project']}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{css(st)}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0"
         data-duration="{m['duration']}" data-width="{m['resolution'][0]}"
         data-height="{m['resolution'][1]}" data-fps="{m['fps']}"
         data-layout-allow-overflow="true">

{chr(10).join(sections)}
    </div>

    <script>
      // GENERATED by edit/build.py from edit/manifest.json — do not hand-edit.
      const BARS = {json.dumps(bars, separators=(',', ':'))};
      var NSTRIKE = 0;
      (function(){{
        var wave=document.getElementById("{wid}-wave"), after=document.getElementById("{wid}-after"),
            wrap=document.getElementById("{wid}-wavewrap"), ka=0;
        if(!wave) return;
        BARS.forEach(function(b,i){{
          var el=document.createElement("span");
          el.className="bar"+(b.k?"":" rm"); el.id="{wid}-wb"+i;
          el.style.height=Math.round(b.h*240)+"px"; wave.appendChild(el);
          if(b.k){{ var e2=document.createElement("span"); e2.className="bar";
            e2.id="{wid}-wa"+(ka++); e2.style.height=Math.round(b.h*240)+"px"; after.appendChild(e2); }}
        }});
        after.style.width = Math.round(2600*ka/BARS.length)+"px";
        wave.style.width  = "2600px";
        var i=0;
        while(i<BARS.length){{
          if(BARS[i].k){{ i++; continue; }}
          var j=i; while(j<BARS.length && !BARS[j].k) j++;
          if(j-i>=3){{
            var s=document.createElement("span"); s.className="strike"; s.id="{wid}-st"+NSTRIKE++;
            s.style.left=(i/BARS.length*100)+"%"; s.style.width=((j-i)/BARS.length*100)+"%";
            s.style.top="118px"; wrap.appendChild(s);
          }}
          i=j;
        }}
      }})();

      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

{chr(10).join(script)}

      tl.seek(0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    Path(a.out).write_text(html)
    print(f"built {a.out}  ({len(html.splitlines())} lines, "
          f"{len(m['cards'])} cards, {sum(len(c.get('beats',[])) for c in m['cards'])} beats)")


if __name__ == "__main__":
    main()
