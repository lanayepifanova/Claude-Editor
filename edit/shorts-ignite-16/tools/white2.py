# neutral-white share (bright AND low saturation, so a yellow dress doesn't count)
import cv2,sys
for f in sys.argv[1:]:
    cap=cv2.VideoCapture(f); n=int(cap.get(7)); step=max(1,n//40); ys=(0.62,0.66,0.70,0.74,0.78); res={y:0 for y in ys}; tot=0; k=0
    while cap.grab():
        if k%step==0:
            _,im=cap.retrieve(); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); H,W=im.shape[:2]; tot+=1
            m=(hsv[...,2]>200)&(hsv[...,1]<50)
            for y in ys:
                res[y]+= m[int((y-0.03)*H):int((y+0.03)*H), int(0.14*W):int(0.86*W)].mean()>0.10
        k+=1
    print(f.split('/')[-1],{y:round(v/tot,2) for y,v in res.items()}, flush=True)
