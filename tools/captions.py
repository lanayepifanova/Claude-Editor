#!/usr/bin/env python3
"""
captions.py — Lana's locked caption recipe.

Approved on "Intro to Claude Editor" (2026-08-15): single-line broadcast style,
max 42 chars, phrase-boundary breaks.

IMPORTANT: run this on the CUT audio, not the original — caption timings must
land on the edited timeline. Extract it from the proof render:
    ffmpeg -i PROOF.mp4 -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le cut.wav

Usage:
    whisper-cli -m ~/.cache/whisper/ggml-base.en.bin -f cut.wav -oj -ml 1 -of words
    python3 tools/captions.py words.json -o "project/My Sequence.srt"

Then in Premiere: import_media(srt) -> create_caption_track(seqId, srtItemId)
Then MANUALLY nudge captions up (~150-200px on 4K) — not scriptable.
"""
import argparse, json, re

MAXCHARS = 42     # single broadcast line
MAXDUR   = 3.5    # seconds
MINDUR   = 0.7    # seconds

# Known mis-hearings. Whisper reliably hears "Claude" as "VOD".
FIXES = [
    (r'\bV\.?O\.?D\b', 'Claude'),
    (r'\bVod\b',       'Claude'),
    (r'\bDead Space\b', 'dead space'),
]


def load_tokens(path):
    """Load whisper -ml 1 JSON, merging subword pieces into whole words."""
    d = json.load(open(path))
    raw = [{'w': s['text'],
            'start': s['offsets']['from'] / 1000.0,
            'end':   s['offsets']['to']   / 1000.0}
           for s in d['transcription'] if s['text'].strip()]
    toks = []
    for x in raw:
        # a piece with no leading space continues the previous word ("don"+"'t")
        if toks and not x['w'].startswith(' '):
            toks[-1]['w'] += x['w']
            toks[-1]['end'] = x['end']
        else:
            toks.append(dict(x))
    return toks


def group(toks):
    cues, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            txt = re.sub(r'\s+', ' ', ''.join(t['w'] for t in cur)).strip()
            if txt:
                cues.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': txt})
        cur = []

    for t in toks:
        prospective = re.sub(r'\s+', ' ', ''.join(x['w'] for x in cur + [t])).strip()
        dur = t['end'] - (cur[0]['start'] if cur else t['start'])
        # flush BEFORE appending the token that would overflow, never after
        if cur and (len(prospective) > MAXCHARS or dur > MAXDUR):
            flush()
        cur.append(t)
        bare = t['w'].strip()
        cur_len = len(re.sub(r'\s+', ' ', ''.join(x['w'] for x in cur)).strip())
        if re.search(r'[.!?]"?$', bare):
            flush()
        elif re.search(r'[,;:]$', bare) and cur_len >= MAXCHARS * 0.6:
            flush()
    flush()
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words_json")
    ap.add_argument("-o", "--out", default="captions.srt")
    ap.add_argument("--end", type=float, default=None,
                    help="timeline duration (s), to clamp the final cue")
    args = ap.parse_args()

    cues = group(load_tokens(args.words_json))

    for c in cues:
        for pat, rep in FIXES:
            c['text'] = re.sub(pat, rep, c['text'])

    end = args.end if args.end else (cues[-1]['end'] + MINDUR)
    for i, c in enumerate(cues):
        if c['end'] - c['start'] < MINDUR:
            nxt = cues[i + 1]['start'] if i + 1 < len(cues) else end
            c['end'] = min(c['start'] + MINDUR, nxt - 0.02)

    ts = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{s%60:06.3f}".replace('.', ',')
    with open(args.out, 'w') as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n")

    print(f"{len(cues)} cues -> {args.out}")
    for i, c in enumerate(cues, 1):
        print(f"{i:>2} [{c['start']:6.2f}-{c['end']:6.2f}] {len(c['text']):>2}ch  {c['text']}")
    bad = sum(1 for i in range(len(cues) - 1) if cues[i]['end'] > cues[i + 1]['start'])
    print(f"\noverlaps: {bad}   over {MAXCHARS}ch: "
          f"{sum(1 for c in cues if len(c['text']) > MAXCHARS)}")
    print("\nREMINDER: proper nouns need checking, and captions must be nudged up "
          "manually in Premiere (Essential Graphics -> Position Y).")


if __name__ == "__main__":
    main()
