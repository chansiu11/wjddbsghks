#!/usr/bin/env python3
"""Losslessly shrink a glTF GLB containing dense, mostly-zero facial morph targets.

Convert POSITION morph targets from dense float32 arrays to core glTF 2.0
sparse accessors, preserving *exact* float32 values, skin and texture buffers.
No KHR extensions required. Valid with Three GLTFLoader on desktop/mobile.
"""
from pathlib import Path
import json
import struct
import sys
import numpy as np


def load(path):
    raw=Path(path).read_bytes()
    assert raw[:4]==b"glTF" and struct.unpack_from("<I",raw,4)[0]==2
    jl,kind=struct.unpack_from("<I4s",raw,12)
    assert kind==b"JSON"
    document=json.loads(raw[20:20+jl])
    bo=20+jl
    bl,kind=struct.unpack_from("<I4s",raw,bo)
    assert kind==b"BIN\0"
    binary=raw[bo+8:bo+8+bl]
    assert len(binary)==bl
    return document,binary


def build(input_path, output_path):
    gltf,blob=load(input_path)
    prim=gltf["meshes"][0]["primitives"][0]
    targets=prim.get("targets",[])
    assert len(targets)>=6,"Expected Meshy facial morph targets"
    accessor_defs=gltf["accessors"]
    views=gltf["bufferViews"]
    dense_views=set()
    pending={}
    for item in targets:
        ix=item["POSITION"]
        a=accessor_defs[ix]
        assert a["type"]=="VEC3" and a["componentType"]==5126
        count=a["count"]
        assert count>10_000
        view_id=a["bufferView"]
        view=views[view_id]
        assert not view.get("byteStride") or view["byteStride"]==12
        start=view.get("byteOffset",0)+a.get("byteOffset",0)
        arr=np.frombuffer(blob,dtype="<f4",count=count*3,offset=start).reshape(count,3)
        idx=np.flatnonzero(np.any(arr!=0,axis=1))
        assert 10<len(idx)<count*.2,(len(idx),count)
        indices=idx.astype("<u4",copy=False)
        values=arr[idx].astype("<f4",copy=False)
        pending[ix]=(indices.tobytes(),values.tobytes(),len(indices))
        dense_views.add(view_id)
        # The accessor's dense buffer is replaced with sparse metadata below.
        a.pop("bufferView")
        a.pop("byteOffset",None)
        print("SPARSE_TARGET",ix,"old_bytes",count*12,"affected",len(idx),
              "new_bytes",len(indices)*16,flush=True)
    # append all pending sparse views before rebuilding binary, preserving the
    # existing bufferView indexes used by indices, images, joint matrices, etc.
    for accessor_id,(indices,values,count) in pending.items():
        iv=len(views)
        views.append({"buffer":0,"byteLength":len(indices)})
        vv=len(views)
        views.append({"buffer":0,"byteLength":len(values)})
        accessor_defs[accessor_id]["sparse"]={
            "count":count,
            "indices":{"bufferView":iv,"componentType":5125},
            "values":{"bufferView":vv}
        }
    added=[]
    for indices,values,_ in pending.values():
        added.extend([indices,values])
    newbuf=bytearray()
    old_len=len(views)-len(added)
    for i,view in enumerate(views):
        while len(newbuf)%4:newbuf.append(0)
        if i<old_len:
            if i in dense_views:
                # Legacy zero-copy accessor views no longer referenced by
                # morph targets. Retain a harmless placeholder to preserve
                # bufferView indexing without a fragile recursive rewrite.
                data=b"\0\0\0\0"
            else:
                a=view.get("byteOffset",0)
                data=blob[a:a+view["byteLength"]]
                assert len(data)==view["byteLength"],(i,len(data))
        else:
            data=added[i-old_len]
        view["byteOffset"]=len(newbuf)
        view["byteLength"]=len(data)
        newbuf.extend(data)
    while len(newbuf)%4:newbuf.append(0)
    gltf["buffers"][0]["byteLength"]=len(newbuf)
    gltf["asset"]["generator"]="Meshy verified facial morphs, losslessly sparse-encoded"
    payload=json.dumps(gltf,ensure_ascii=False,separators=(",",":")).encode()
    payload+=b" "*((-len(payload))%4)
    output=(
       struct.pack("<4sII",b"glTF",2,12+8+len(payload)+8+len(newbuf))
       +struct.pack("<I4s",len(payload),b"JSON")+payload
       +struct.pack("<I4s",len(newbuf),b"BIN\0")+newbuf
    )
    dest=Path(output_path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(output)
    verify_binary(dest,input_path)
    print("MESHY_COMPACT_READY",dest,"bytes",len(output),
        "saved_percent",round((1-len(output)/Path(input_path).stat().st_size)*100,1),flush=True)


def verify_binary(new_path,old_path):
    old,oldbin=load(old_path)
    new,newbin=load(new_path)
    assert len(old["skins"][0]["joints"])==len(new["skins"][0]["joints"])==66
    assert old["meshes"][0]["extras"]["targetNames"]==new["meshes"][0]["extras"]["targetNames"]
    assert len(old["meshes"][0]["primitives"][0]["targets"])==len(new["meshes"][0]["primitives"][0]["targets"])
    def get_view(g,bin,idx):
        v=g["bufferViews"][idx]
        x=v.get("byteOffset",0)
        return memoryview(bin)[x:x+v["byteLength"]]
    for i,(a,b) in enumerate(zip(old["accessors"],new["accessors"])):
        if "sparse" not in b:
            assert a==b,("Changed accessor metadata",i)
            if "bufferView" in a:
                assert bytes(get_view(old,oldbin,a["bufferView"]))==bytes(
                   get_view(new,newbin,b["bufferView"])),("Changed mesh or skin bytes",i)
        else:
            count=b["count"]
            old_view=get_view(old,oldbin,a["bufferView"])
            dense=np.frombuffer(old_view,dtype="<f4",count=count*3,offset=a.get("byteOffset",0)).reshape(count,3)
            sparse=b["sparse"]
            ix=np.frombuffer(get_view(new,newbin,sparse["indices"]["bufferView"]),dtype="<u4",count=sparse["count"])
            val=np.frombuffer(get_view(new,newbin,sparse["values"]["bufferView"]),dtype="<f4",count=sparse["count"]*3).reshape(-1,3)
            restored=np.zeros_like(dense)
            restored[ix]=val
            assert np.array_equal(restored,dense),(i,"morph position changed")
    assert len(newbin)<len(oldbin)*.65
    print("SPARSE_ROUNDTRIP_BIT_EXACT",len(oldbin),len(newbin),flush=True)


if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: compact_meshy_morphs.py existing_dense.glb compact.glb")
    build(*sys.argv[1:3])
