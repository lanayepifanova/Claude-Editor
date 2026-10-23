---
name: find-shorts
description: Parse a long video (interview, panel, talk) in footage/, pull its timestamped script, and shortlist 3–6 self-contained 30–60s clips with strong verbal hooks for YouTube Shorts / TikTok / Reels. Use when Lana asks to "find shorts", "find clips", "find hooks" or "cut this into shorts". Shortlist only — she approves and does the clipping herself.
---

# Find shorts

Lana's ask (2026-10-23, Keith Newman × Carmen Li): *"convert this into a couple youtube
shorts clips (30-60sec)… 3-6… parse through it, find the script, and find places that would
be good cuts… good verbal hooks (talking about something that would be easy to clip). After
we find those and I approve of the clip choices, we will go in and actually clip it myself."*

**Deliverable is a shortlist, not a render.** Don't run preprocess/burn/captions unless she
asks for that after approving.

## Steps

1. `ffprobe` the clip: duration, resolution, fps. Note orientation. A landscape source
   becomes 9:16, so check a contact sheet for who sits where (crop has to follow the speaker).
2. Transcribe the **original** audio. Timestamps must be in source time, because she cuts
   from the source file:

   ```bash
   D=edit/shorts-<name>; mkdir -p $D
   ffmpeg -v error -y -i "footage/<clip>" -ac 1 -ar 16000 $D/audio.wav
   whisper-cli -m ~/.cache/whisper/ggml-small.en.bin -f $D/audio.wav -oj -of $D/transcript -np
   python3 -c "
   import json; d=json.load(open('$D/transcript.json'))
   for s in d['transcription']:
       a=s['offsets']['from']/1000; print(f'{int(a//60)}:{a%60:05.2f}', s['text'].strip())
   " > $D/script.txt
   ffmpeg -v error -y -i "footage/<clip>" -vf "fps=1/110,scale=480:-1,tile=3x2" -frames:v 1 $D/contact.jpg
   ```

3. Read all of `script.txt` and pick clips that are:
   - **Hooked in the first sentence.** It opens on a claim, number, question or analogy
     ("there's no way to short it", "3 → 300", "is it just a car loan?"). Never open on
     "so", "yeah" or setup that needs earlier context.
   - **Self-contained.** No dangling "as I said" or "that" that points outside the clip.
   - **Ending on a payoff line.** That's a punchline, number or thesis, not a trailing
     "right?" or the host's next question.
   - **30–60s**, with a little room under 60s so she can trim.
   - **Spread across the video**, with no two picks covering the same point. Where two
     overlap, offer one as an *alt in/out*.
   - A host question works as a cold open when it states the topic crisply. Offer it as
     "optional cold open" with its own timestamps. Don't silently include it.
4. Write `edit/shorts-<name>/shortlist.md`. Include:
   - a ranked table with title/hook, in → out, and length
   - one short paragraph per pick, quoting the opening and closing lines
   - a **bench** of 1–3 runners-up
   - whisper mis-hearings of names and jargon, for when captions come later

   Format reference: `edit/shorts-keith-carmen/shortlist.md`.
5. In chat, show the ranked table plus a one-line reason for each pick. Ask her which to keep.

## Notes

- Whisper segment starts are about ±0.3s. Say so, since she trims by ear.
- Whisper reliably mangles names and jargon ("Claude" → "VOD", "RFQ" → "RF-Hue"). Quote
  the corrected words in the shortlist and list the fixes.
- `audio.wav` is scratch. Don't commit it.
