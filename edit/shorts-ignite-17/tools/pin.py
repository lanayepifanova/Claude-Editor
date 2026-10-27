# Local workaround: reframe.py follows the largest face, which in a wide shot can be the
# listener. Re-encode the vertical with one shot's crop pinned on the speaker.
# usage: pin.py N new_end shot_index crop_x   (reuses the reframe plan in .shots.json)
import json,subprocess,sys
N,end,idx,cx=sys.argv[1],float(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
out=f"graphics/ignite-17-short{N}-vertical.mp4"; j=json.load(open(out+".shots.json"))
plan=j["shots"]; plan[idx]["crop_x"]=cx; plan[idx]["pinned"]=True
plan=[s for s in plan if s["t0"]<end-j["start"]]
expr=str(plan[-1]["crop_x"])
for s in reversed(plan[:-1]): expr=f"if(lt(t,{s['t1']}),{s['crop_x']},{expr})"
cw,hh=j["crop"]; top=j["active"][0]
vf=f"crop={cw}:{hh}:'{expr}':{top},scale=1080:1920:flags=lanczos,setsar=1"
cmd=["nice","-n","10","ffmpeg","-nostdin","-v","error","-y","-ss",f"{j['start']:.3f}","-t",f"{end-j['start']:.3f}",
     "-i",j["source"],"-vf",vf,"-c:v","libx264","-crf","12","-preset","slow","-pix_fmt","yuv420p",
     "-af","loudnorm=I=-18:TP=-2:LRA=11,aresample=48000","-c:a","aac","-b:a","320k",out]
print(vf); subprocess.run(cmd,check=True,stdin=subprocess.DEVNULL)
j["end"]=end; j["shots"]=plan; json.dump(j,open(out+".shots.json","w"),indent=1)
