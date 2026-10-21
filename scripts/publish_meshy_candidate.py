#!/usr/bin/env python3
"""Switch to a verified user-supplied Meshy GLB; preserve prior default as fallback."""
from pathlib import Path
import re,shutil,sys
candidate=Path(sys.argv[1]) if len(sys.argv)>1 else Path("assets/uploads/Meshy_Gilded_Vanguard_rigged_preview (1).glb")
target=Path("assets/models/meshy-gilded-vanguard-rigged.glb")
assert candidate.is_file()
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(candidate,target)
path=Path("assets/index.default-ai.js")
s=path.read_text()
entry='Yt=[{id:98,name:"Meshy Gilded Vanguard",type:"url",url:"./assets/models/meshy-gilded-vanguard-rigged.glb",icon:null,source:"User-created Meshy avatar",author:"Custom AI avatar",color:null},'
old='Yt=[{id:99,name:'
if entry not in s:
    assert s.count(old)==1,"Cannot locate original avatar picker"
    s=s.replace(old,entry+'{id:99,name:',1)
# Keep the old character accessible but choose a fresh preference key for new default.
s=s.replace('"userModel-ksante-ai-v1"','"userModel-meshy-v1"')
# Explicit Ashtra fallback, rather than any shifted numeric list index.
s=s.replace('p(z,Yt[1].url,Yt[1])','p(z,Yt.find(a=>a.name==="Ashtra").url,Yt.find(a=>a.name==="Ashtra"))')
assert s.count("Meshy Gilded Vanguard")>=1
path.write_text(s)
sw=Path("sw.js")
if sw.is_file():
    current=sw.read_text()
    def next_version(m):return "kalidoface-local-v"+str(int(m.group(1))+1)
    changed=re.sub(r"kalidoface-local-v(\d+)",next_version,current,count=1)
    assert changed!=current,"Service worker cache key missing"
    sw.write_text(changed)
print("INSTALLED",target,target.stat().st_size,"bytes")
