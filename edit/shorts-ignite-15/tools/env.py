import json,sys
e=json.load(open(sys.argv[1]+'/envelope.json')); w=e['window']; v=e['values']
a,b=float(sys.argv[2]),float(sys.argv[3])
print(' '.join(f"{i*w:.2f}:{v[i]:.0f}" for i in range(int(a/w),min(len(v),int(b/w)))))
