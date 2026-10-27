# usage: plan.py start end -> reframe.py's shot plan without encoding (dry run)
import sys; sys.path.insert(0,'edit'); sys.argv=[sys.argv[0]]+sys.argv[1:]
import reframe as r, cv2
F="footage/Ignite Oct 2026/15 Steven Hou Silicon Data and Angela Young Cerebras.mp4"
a,b=float(sys.argv[1]),float(sys.argv[2])
w,h,fps=r.probe(F); top,hh=r.letterbox(F,w,h,a,b); cw=int(round(hh*9/16))//2*2
cuts,_=r.shots(F,a,b,fps,28.0)
fr=cv2.CascadeClassifier(str(r.CASCADES/"haarcascade_frontalface_default.xml")); pr=cv2.CascadeClassifier(str(r.CASCADES/"haarcascade_profileface.xml"))
d=[(fr,None,False),(pr,None,False),(pr,None,True)]
for t0,t1 in zip(cuts,cuts[1:]):
    x=r.subject_x(F,a+t0,a+t1,w,h,top,hh,d); print(f"{t0:7.2f}-{t1:7.2f} (src {a+t0:.2f}) face_x {x}")
