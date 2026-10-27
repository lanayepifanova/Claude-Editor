# srcenv.py t0 t1 -> 50ms RMS dB of original audio.wav, compact
import sys,wave,numpy as np
w=wave.open('edit/shorts-ignite-13/audio.wav'); sr=w.getframerate()
a,b=float(sys.argv[1]),float(sys.argv[2]); w.setpos(int(a*sr)); x=np.frombuffer(w.readframes(int((b-a)*sr)),np.int16)/32768
n=int(0.05*sr); k=len(x)//n
r=20*np.log10(np.sqrt((x[:k*n].reshape(k,n)**2).mean(1))+1e-9)
print(' '.join(f"{a+i*0.05:.2f}:{v:.0f}" for i,v in enumerate(r)))
