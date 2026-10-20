#!/usr/bin/env python3
"""Repack auto-rigged GLB with mobile-sized PNG/JPEG textures WITHOUT changing its mesh, skin or inverse bind matrices."""
from pathlib import Path
import io, json, struct, sys
from PIL import Image, ImageOps
if len(sys.argv) not in (3,4):
    raise SystemExit("Usage: python build_rig_compatible.py source.glb output.glb [max_texture_edge]")
src,dst=map(Path,sys.argv[1:3])
max_edge=int(sys.argv[3]) if len(sys.argv)==4 else 1024
assert max_edge in (512,1024,1536,2048)
b=src.read_bytes()
assert b[:4]==b'glTF' and struct.unpack_from('<I',b,4)[0]==2
json_len,kind=struct.unpack_from('<I4s',b,12)
assert kind==b'JSON'
document=json.loads(b[20:20+json_len])
bin_offset=20+json_len
bin_len,kind=struct.unpack_from('<I4s',b,bin_offset)
assert kind==b'BIN\\0'
original=b[bin_offset+8:bin_offset+8+bin_len]
views=document['bufferViews']
images=document.get('images',[])
replacement={}
for i, entry in enumerate(images):
    original_type=entry.get('mimeType','')
    if original_type not in ('image/webp','image/jpeg','image/png'):
        continue
    index=entry['bufferView']
    view=views[index]
    lo=view.get('byteOffset',0)
    source_bytes=original[lo:lo+view['byteLength']]
    image=Image.open(io.BytesIO(source_bytes))
    image=ImageOps.exif_transpose(image).convert('RGBA')
    if max(image.size)>max_edge:
        image.thumbnail((max_edge,max_edge),Image.Resampling.LANCZOS)
    opaque=image.getchannel('A').getextrema()==(255,255)
    stream=io.BytesIO()
    if opaque:
        image.convert('RGB').save(stream,format='JPEG',quality=88,subsampling=0)
        content_type='image/jpeg'
    else:
        image.save(stream,format='PNG',compress_level=6)
        content_type='image/png'
    replacement[index]=stream.getvalue()
    entry['mimeType']=content_type
    print('IMAGE',i,'view',index,'old',len(source_bytes),'new',len(replacement[index]),'size',image.size,'type',content_type,flush=True)
for texture in document.get('textures',[]):
    ext=texture.get('extensions',{})
    webp=ext.pop('EXT_texture_webp',None)
    if webp is not None:texture['source']=webp['source']
    if not ext:texture.pop('extensions',None)
for key in ('extensionsUsed','extensionsRequired'):
    if key in document:
        document[key]=[x for x in document[key] if x!='EXT_texture_webp']
        if not document[key]:document.pop(key)
# Rebuild every bufferView in order (including skins and node inverses); no accessor, skin,
# joint or transform metadata is altered. Each view is 4-byte aligned in new BIN chunk.
rebuilt=bytearray()
for i,view in enumerate(views):
    if len(rebuilt)%4:rebuilt.extend(b'\\0'*(-len(rebuilt)%4))
    a=view.get('byteOffset',0)
    data=replacement.get(i,original[a:a+view['byteLength']])
    assert len(data)>0
    view['byteOffset']=len(rebuilt)
    view['byteLength']=len(data)
    rebuilt.extend(data)
document['buffers'][0]['byteLength']=len(rebuilt)
payload=json.dumps(document,ensure_ascii=False,separators=(',',':')).encode('utf8')
payload+=b' '*((-len(payload))%4)
rebuilt.extend(b'\\0'*(-len(rebuilt)%4))
total=12+8+len(payload)+8+len(rebuilt)
out=struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(payload),b'JSON')+payload+struct.pack('<I4s',len(rebuilt),b'BIN\\0')+rebuilt
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_bytes(out)
verify=json.loads(out[20:20+len(payload)])
assert len(verify.get('skins',[]))==len(document.get('skins',[]))==1
assert len(verify['skins'][0]['joints'])==66
assert 'EXT_texture_webp' not in verify.get('extensionsRequired',[])
pos=verify['meshes'][0]['primitives'][0]['attributes']['POSITION']
assert verify['accessors'][pos]['componentType']==5126
assert len(verify['nodes'])==len(document['nodes'])
print('BUILT',str(dst),'bytes',dst.stat().st_size,'skins',len(verify['skins']),'joints',len(verify['skins'][0]['joints']),'accessors',len(verify['accessors']),flush=True)
