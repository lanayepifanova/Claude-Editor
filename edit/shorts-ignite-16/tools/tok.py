# usage: tok.py t0 t1 -> whisper tokens with source times
import json,sys
a,b=float(sys.argv[1]),float(sys.argv[2])
d=json.load(open('edit/shorts-ignite-16/transcript.json'))
out=[]
for s in d['transcription']:
    for t in s.get('tokens',[]):
        x=t['offsets']['from']/1000
        if a<=x<=b and not t['text'].startswith('[_'): out.append(f"{t['text']}@{x:.2f}")
print(''.join(o if o.startswith(' ') else o for o in out))
