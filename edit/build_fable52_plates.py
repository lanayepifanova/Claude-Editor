#!/usr/bin/env python3
"""
build_fable52_plates.py — the opaque picture plates for the Fable 5.2 x Higgsfield
reel: the reaction opener, the six-category kit montage and the setup screen
recording. Output is a 1080x1920 30fps ProRes 4444 overlay (transparent wherever
she is on camera), frame-for-frame the length of the cut, so burn.py can stack it
under the labels and captions.

Every placement is in cut-timeline FRAMES, so beats join on whole frames.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "footage/Higgsfield Fable 5.2"
K = F / "Media Kit"
FPS = 30
TOTAL = 787                      # cut_duration 26.233s

# (label key, file, source start s, frames, landscape?)  -- landscape = fit over blur
MONTAGE_START = 134              # 4.467s, on "create commercials"
MONTAGE = [
    ("commercial", K/"commercial/hf_20261008_202518_2f8bcdf1-5f0f-4ca5-bf23-5f3eb67ec4eb.mp4", 1.00, 33, True),
    ("cinematic",  K/"cinematic/hf_20261017_194411_101c1509-6957-41cd-b54a-a20b734f03ef (1).mp4", 1.50, 33, True),
    ("ugc",        K/"ugc/hf_20260925_162704_e990569b-b05b-447d-87c3-4d23c6095242.mp4",          3.40, 36, False),
    ("product",    K/"hypermotion/05.mp4",                                                       3.10, 39, False),
    ("anime",      K/"anime/hf_20260722_201043_c59b7f81-b00a-4c92-a681-3e308007a269.mp4",        6.40, 36, True),
    ("motion",     K/"motion/hf_20260610_200935_eb82df6c-b33a-4907-93ae-dde455b502fa.mp4",      3.20, 39, True),
]
REACTION = (F/"Opening Reaction Surprise.mov", 0, 86)       # frames 0..85
SCREEN_START, SCREEN_FRAMES = 493, 174                       # 16.433-22.233s
# screen recording: (src in, src out, speed) — loading screens are simply not listed
SCREEN_REC = F/"claude-setup-mobile-fable.mp4"
SCREEN_CUTS = [(0.0, 2.0, 1.5), (2.0, 5.4, 2.5), (6.0, 8.0, 1.3), (8.3, 9.1, 1.0)]


def main(out):
    ins, chains, layers = [], [], []   # layers: (label, start_frame)
    def add_input(path): ins.extend(["-i", str(path)]); return len(ins)//2 - 1

    # reaction
    i = add_input(REACTION[0])
    chains.append(f"[{i}:v]fps={FPS},trim=start_frame=0:end_frame={REACTION[2]},setpts=N/{FPS}/TB,"
                  f"scale=1080:1920:flags=lanczos,format=yuv444p,setpts=PTS+0/TB[reac]")
    layers.append(("reac", 0))

    # montage
    start = MONTAGE_START
    for key, path, ss, n, land in MONTAGE:
        i = add_input(path)
        base = f"[{i}:v]fps={FPS},trim=start={ss}:duration={n/FPS+0.05},setpts=PTS-STARTPTS,trim=end_frame={n}"
        if land:
            chains.append(f"{base},split[a{key}][b{key}];"
                          f"[a{key}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                          f"gblur=sigma=28,eq=brightness=-0.10[bg{key}];"
                          f"[b{key}]scale=1080:-2:flags=lanczos[fg{key}];"
                          f"[bg{key}][fg{key}]overlay=0:(H-h)/2-40,format=yuv444p,setpts=PTS+{start}/{FPS}/TB[{key}]")
        else:
            chains.append(f"{base},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                          f"format=yuv444p,setpts=PTS+{start}/{FPS}/TB[{key}]")
        layers.append((key, start)); start += n

    # screen recording: piecewise speed, then conform to 30fps and length
    i = add_input(SCREEN_REC)
    parts = []
    for k, (a, b, sp) in enumerate(SCREEN_CUTS):
        parts.append(f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},fps={FPS}[s{k}]")
    chains.extend(parts)
    cat = "".join(f"[s{k}]" for k in range(len(SCREEN_CUTS)))
    chains.append(f"{cat}concat=n={len(SCREEN_CUTS)}:v=1:a=0,tpad=stop_mode=clone:stop_duration=2,"
                  f"trim=end_frame={SCREEN_FRAMES},setpts=N/{FPS}/TB,scale=842:1498:flags=lanczos,"
                  f"pad=1080:1920:119:60:color=0x121212,"
                  f"format=yuv444p,setpts=PTS+{SCREEN_START}/{FPS}/TB[screen]")
    layers.append(("screen", SCREEN_START))

    chains.append(f"color=c=black:s=1080x1920:r={FPS},format=yuv444p,trim=end_frame={TOTAL},setpts=N/{FPS}/TB[base0]")
    prev = "base0"
    for n, (lab, _) in enumerate(layers):
        chains.append(f"[{prev}][{lab}]overlay=0:0:eof_action=pass:format=yuv444[o{n}]")
        prev = f"o{n}"
    # the matte: white wherever a plate is up, black where she shows through
    spans = [(0, REACTION[2]-1), (MONTAGE_START, start-1), (SCREEN_START, SCREEN_START+SCREEN_FRAMES-1)]
    en = "+".join(f"between(n,{a},{b})" for a, b in spans)
    chains.append(f"color=c=black:s=1080x1920:r={FPS},format=gray,trim=end_frame={TOTAL},setpts=N/{FPS}/TB,"
                  f"drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='{en}',lutyuv=y='clip((val-16)*255/219,0,255)'[mat]")
    chains.append(f"[{prev}]format=yuv444p[vv];[vv][mat]alphamerge,format=yuva444p10le[outv]")
    cmd = ["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(chains), "-map", "[outv]",
           "-frames:v", str(TOTAL), "-r", str(FPS), "-c:v", "prores_ks", "-profile:v", "4444",
           "-pix_fmt", "yuva444p10le", "-vendor", "apl0", str(out)]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main(sys.argv[1])
