#!/usr/bin/env python3
"""Recover upright, textured, unskinned Meshy geometry from the flawed manual skin.

Never reuse the manually estimated JOINTS_0 / WEIGHTS_0. Transform positions
and normals into an upright glTF mesh before passing to the automatic rigger.
"""
import json,struct,sys,math
from pathlib import Path
import numpy as np

inp,out=map(Path,sys.argv[1:3])
data=inp.read_bytes()
assert data[:4]==b"glTF" and struct.unpack_from("<I",data,4)[0]==2
json_length,typ=struct.unpack_from("<I4s",data,12)
assert typ==b"JSON"
doc=json.loads(data[20:20+json_length])
chunk_offset=20+json_length
bin_len,typ=struct.unpack_from("<I4s",data,chunk_offset)
assert typ==b"BIN\0",typ
binary=bytearray(data[chunk_offset+8:chunk_offset+8+bin_len])
root=doc["nodes"][0]
original_mesh=doc["nodes"][1]
assert original_mesh.get("mesh")==0 and original_mesh.get("skin")==0
q=root.get("rotation",[0,0,0,1])
x,y,z,w=q
rot=np.array([
 [1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
 [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
 [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]],dtype=np.float64)
trans=np.asarray(root.get("translation",[0,0,0]),dtype=np.float64)
scale=np.asarray(root.get("scale",[1,1,1]),dtype=np.float64)
assert np.all(scale>0)
prim=doc["meshes"][0]["primitives"][0]
attrs=prim["attributes"]
for name in ["POSITION","NORMAL","TANGENT"]:
    if name not in attrs:continue
    acc=doc["accessors"][attrs[name]]
    assert acc["componentType"]==5126
    view=doc["bufferViews"][acc["bufferView"]]
    stride=view.get("byteStride",4*(4 if name=="TANGENT" else 3))
    count=acc["count"];n=4 if name=="TANGENT" else 3
    offset=view.get("byteOffset",0)+acc.get("byteOffset",0)
    points=np.ndarray((count,n),dtype="<f4",buffer=binary,offset=offset,
                      strides=(stride,4))
    old=points[:,:3].astype(np.float64).copy()
    if name=="POSITION":new=(old*scale)@rot.T+trans
    else:
        new=(old/scale)@rot.T
        new/=np.maximum(np.linalg.norm(new,axis=1,keepdims=True),1e-12)
    points[:,:3]=new.astype("<f4")
    if name=="POSITION":
        acc["min"]=new.min(axis=0).tolist()
        acc["max"]=new.max(axis=0).tolist()
        assert acc["max"][1]-acc["min"][1]>0.9, "Avatar not upright"
        print("UPRIGHT_BOUNDS",acc["min"],acc["max"],flush=True)
# Old generated skin influences are the deformation bug: remove completely.
assert "JOINTS_0" in attrs and "WEIGHTS_0" in attrs
for attr in ["JOINTS_0","WEIGHTS_0"]:attrs.pop(attr,None)
doc.pop("skins",None)
doc["nodes"]=[
 {"name":"Meshy_Upright","children":[1]},
 {"name":"Meshy_Upright_Mesh","mesh":0}
]
doc["scenes"]=[{"nodes":[0]}];doc["scene"]=0
doc.pop("extras",None)
doc["asset"]["generator"]="Upright Meshy mesh restored for afk-rig automatic humanoid skinning"
# Retain the original material, textures, indices and binary buffers.
# Unreferenced accessor views are harmless and do not affect rendering.
doc["buffers"][0]["byteLength"]=len(binary)
js=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
js+=b" "*((-len(js))%4)
binary.extend(b"\0"*((-len(binary))%4))
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(struct.pack("<4sII",b"glTF",2,12+8+len(js)+8+len(binary))+
   struct.pack("<I4s",len(js),b"JSON")+js+
   struct.pack("<I4s",len(binary),b"BIN\0")+binary)
print("UNRIGGED_REBUILT",out,len(binary),"bytes",flush=True)
