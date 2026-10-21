#!/usr/bin/env python3
"""Add gentle forehead, eyelid, lip and smile morph targets to Meshy rigged GLB.

The base skin, joints and original POSITION data are never changed.
The original model has a single sculpted face; these expressions are procedural
approximations and do not add physically modeled eyelids or a mouth cavity.
"""
from pathlib import Path
import json,struct,sys
import numpy as np

def build(src,dst):
    b=Path(src).read_bytes()
    assert b[:4]==b"glTF" and struct.unpack_from("<I",b,4)[0]==2
    jl,typ=struct.unpack_from("<I4s",b,12)
    assert typ==b"JSON"
    d=json.loads(b[20:20+jl])
    p=20+jl
    bl,t=struct.unpack_from("<I4s",b,p)
    assert t==b"BIN\0"
    raw=bytearray(b[p+8:p+8+bl])
    mesh=d["meshes"][0]
    prim=mesh["primitives"][0]
    assert "targets" not in prim,"Refusing to double-create expression targets"
    a=d["accessors"][prim["attributes"]["POSITION"]]
    assert a["type"]=="VEC3" and a["componentType"]==5126
    v=d["bufferViews"][a["bufferView"]]
    pos=np.ndarray((a["count"],3),dtype="<f4",buffer=raw,
        offset=v.get("byteOffset",0)+a.get("byteOffset",0),
        strides=(v.get("byteStride",12),4)).copy()
    x,y,z=(pos[:,k].astype(np.float64) for k in range(3))
    assert np.percentile(y,99)>1.72
    # Texture inspection confirms the FRONT of this Meshy mesh is +Z.
    front=np.clip((z-.055)/.045,0,1)
    facial=front*np.clip((1.85-y)/.03,0,1)*np.clip((y-1.632)/.035,0,1)
    def g(cx,cy,sx,sy):
        return np.exp(-.5*((x-cx)/sx)**2-.5*((y-cy)/sy)**2)*facial
    def zero():return np.zeros_like(pos,dtype=np.float32)
    el=g(-.044,1.773,.027,.018)
    er=g(.044,1.773,.028,.018)
    def lid(w):
        o=zero()
        o[:,1]=(-np.tanh((y-1.773)/.006)*.012*w).astype("f4")
        o[:,2]=(-.0055*w).astype("f4")
        return o
    left,right=lid(el),lid(er)
    lip=g(-.002,1.686,.043,.022)
    split=np.tanh((y-1.687)/.009)
    def mouth(opening=1,narrow=0,wide=0):
        o=zero()
        o[:,1]=(lip*split*(.015*opening+.004*wide)).astype("f4")
        o[:,2]=(lip*(.004*opening+.003*narrow)).astype("f4")
        o[:,0]=(lip*(-x)*(.36*narrow-.15*wide)).astype("f4")
        return o
    corner_l=g(-.039,1.686,.021,.025)
    corner_r=g(.039,1.686,.021,.025)
    corner=corner_l+corner_r
    smile=zero()
    smile[:,1]=(.0145*corner+.0035*lip).astype("f4")
    smile[:,0]=(.0055*(corner_r-corner_l)).astype("f4")
    smile[:,2]=(.0028*corner).astype("f4")
    brow=zero();brow[:,1]=(.009*g(0,1.802,.092,.019)).astype("f4")
    targets=[("blink",left+right),("blinkLeft",left),("blinkRight",right),
             ("mouthOpen",mouth()),("smile",smile),("mouthO",mouth(.8,1.1)),
             ("mouthE",mouth(.35,0,.85)),("browUp",brow)]
    for name,delta in targets:
        affected=np.linalg.norm(delta,axis=1)>.001
        assert int(affected.sum())>45,(name,"no face vertices")
        assert np.linalg.norm(delta,axis=1).max()<.045,(name,"too strong")
        assert not np.any(affected&(y<1.63)),(name,"neck affected")
        assert not np.any(affected&(np.abs(x)>.19)),(name,"other body affected")
        assert not np.any(affected&(z<.055)),(name,"rear surface affected")
        while len(raw)%4:raw.extend(b"\0")
        offset=len(raw)
        arr=np.asarray(delta,dtype="<f4",order="C")
        raw.extend(arr.tobytes())
        vid=len(d["bufferViews"])
        d["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":arr.nbytes})
        aid=len(d["accessors"])
        d["accessors"].append({"bufferView":vid,"componentType":5126,
            "count":len(pos),"type":"VEC3","min":arr.min(axis=0).tolist(),
            "max":arr.max(axis=0).tolist()})
        prim.setdefault("targets",[]).append({"POSITION":aid})
        print("EXPRESSION",name,"vertices",int(affected.sum()),flush=True)
    mesh["weights"]=[0.0]*len(targets)
    mesh["extras"]={"targetNames":[name for name,_ in targets]}
    d["buffers"][0]["byteLength"]=len(raw)
    d["asset"]["generator"]="Meshy humanoid safe facial morph rigging"
    data=json.dumps(d,separators=(",",":"),ensure_ascii=False).encode()
    data+=b" "*(-len(data)%4)
    raw.extend(b"\0"*(-len(raw)%4))
    dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True)
    out=struct.pack("<4sII",b"glTF",2,12+8+len(data)+8+len(raw))
    out+=struct.pack("<I4s",len(data),b"JSON")+data
    out+=struct.pack("<I4s",len(raw),b"BIN\0")+raw
    dst.write_bytes(out)
    assert len(d["skins"][0]["joints"])==66
    print("FACE_MORPHS_READY",dst,len(out),[x[0] for x in targets],flush=True)

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: build_meshy_face_morphs.py input.glb output.glb")
    build(sys.argv[1],sys.argv[2])
