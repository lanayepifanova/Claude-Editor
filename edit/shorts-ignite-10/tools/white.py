import cv2,sys
for f in sys.argv[1:]:
    cap=cv2.VideoCapture(f); n=int(cap.get(7)); step=max(1,n//40); res={y:0 for y in (0.55,0.6,0.65,0.7,0.75)}; tot=0; k=0
    while True:
        ok=cap.grab()
        if not ok: break
        if k%step==0:
            ok,im=cap.retrieve(); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); H,W=g.shape; tot+=1
            for y in res:
                b=g[int((y-0.03)*H):int((y+0.03)*H), int(0.14*W):int(0.86*W)]
                res[y]+= (b>200).mean()>0.25
        k+=1
    print(f,{y:round(v/tot,2) for y,v in res.items()}, flush=True)
