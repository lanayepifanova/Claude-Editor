import json,sys
a=sys.argv[1]
d=json.load(open(a+'/transcript.json')); s=json.load(open(a+'/silence.json'))
segs=s['segments']; acc=[];c=0
for x,y in segs: acc.append((c,x,y)); c+=y-x
def src(t):
    for c0,x,y in acc:
        if t<=c0+(y-x)+1e-6: return x+(t-c0)
    return segs[-1][1]
print(a, 'cut', round(c,2), 'removed', s['removed_pct'], 'src', round(s['source_duration'],2))
print(' '.join(f"{w['w']}@{src(w['t0']):.2f}" for w in d['words']))
