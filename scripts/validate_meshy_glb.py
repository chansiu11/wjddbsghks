#!/usr/bin/env python3
"""Validate uploaded skinned Meshy GLB before publishing publicly."""
import json, struct, sys
from pathlib import Path
p=Path(sys.argv[1])
raw=p.read_bytes()
assert len(raw)<26_214_400,"Candidate too large for regular GitHub upload"
assert raw[:4]==b"glTF" and struct.unpack_from("<I",raw,4)[0]==2,"Not GLB2"
n,typ=struct.unpack_from("<I4s",raw,12)
assert typ==b"JSON"
doc=json.loads(raw[20:20+n])
assert len(doc.get("skins",[]))==1,"Missing humanoid skin"
skin=doc["skins"][0]
joints=skin["joints"]
assert len(joints)>=70,"Missing finger and secondary motion bones"
names={doc["nodes"][i].get("name") for i in joints}
needed={"pelvis","spine_01","spine_02","spine_03","neck_01","head",
"upperarm_l","lowerarm_l","hand_l","upperarm_r","lowerarm_r","hand_r",
"thigh_l","calf_l","foot_l","thigh_r","calf_r","foot_r",
"hair_spring","cloth_front_l","cloth_front_r"}
for side in ("l","r"):
    for digit in ("thumb","index","middle","pinky","ring"):
        for ix in range(1,4):needed.add(f"{digit}_0{ix}_{side}")
missing=needed-names
assert not missing,f"Missing rig joints: {sorted(missing)}"
prim=doc["meshes"][0]["primitives"][0]
a=prim["attributes"]
for key in ("POSITION","NORMAL","JOINTS_0","WEIGHTS_0"):
    assert key in a,key
num=doc["accessors"][a["POSITION"]]["count"]
assert num>2000,"Mesh unexpectedly small"
for key in ("JOINTS_0","WEIGHTS_0"):
    assert doc["accessors"][a[key]]["count"]==num
assert doc.get("images"),"No texture images"
assert all(x.get("mimeType") in ("image/jpeg","image/png") for x in doc["images"]),"Legacy loader cannot use compressed textures"
assert len(raw)<24_000_000
assert "EXT_texture_webp" not in doc.get("extensionsRequired",[])
assert "KHR_draco_mesh_compression" not in doc.get("extensionsRequired",[])
print("MESHY_VALIDATION_SUCCESS",p,"bytes",len(raw),"vertices",num,
"joints",len(joints),"textures",len(doc["images"]))
