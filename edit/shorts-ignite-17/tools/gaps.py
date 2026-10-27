# usage: gaps.py t0 t1 -> quiet runs (< -45 dB, >= 60ms) in original audio, 20ms windows
import sys,wave,numpy as np
w=wave.open('edit/shorts-ignite-17/audio.wav'); sr=w.getframerate()
a,b=float(sys.argv[1]),float(sys.argv[2]); w.setpos(int(a*sr)); x=np.frombuffer(w.readframes(int((b-a)*sr)),np.int16)/32768
n=int(0.02*sr); k=len(x)//n
r=20*np.log10(np.sqrt((x[:k*n].reshape(k,n)**2).mean(1))+1e-9)
out=[];i=0
while i<k:
    if r[i]<-45:
        j=i
        while j<k and r[j]<-45: j+=1
        if j-i>=3: out.append(f"{a+i*0.02:.2f}-{a+j*0.02:.2f}")
        i=j
    else: i+=1
print(' '.join(out))
