#!/usr/bin/env python3
"""Convert EXT_texture_webp GLB textures to standard PNG/JPEG, retaining rig and geometry."""
from pathlib import Path
import io, json, struct, sys
from PIL import Image
if len(sys.argv)!=3:
    raise SystemExit("Usage: python scripts/convert_glb_textures.py input.glb output.glb")
src,dst=map(Path,sys.argv[1:])
b=src.read_bytes()
assert b[:4]==b'glTF' and struct.unpack_from('<I',b,4)[0]==2
jlen,jkind=struct.unpack_from('<I4s',b,12)
assert jkind==b'JSON'
d=json.loads(b[20:20+jlen])
bpos=20+jlen
binlen,binkind=struct.unpack_from('<I4s',b,bpos)
assert binkind==b'BIN\\x00'.replace(b'\\x00',b'\x00')
raw=bytearray(b[bpos+8:bpos+8+binlen])
for idx,entry in enumerate(d.get('images',[])):
    if entry.get('mimeType')!='image/webp':continue
    view=d['bufferViews'][entry['bufferView']]
    off=view.get('byteOffset',0)
    image=Image.open(io.BytesIO(raw[off:off+view['byteLength']])).convert('RGBA')
    opaque=image.getchannel('A').getextrema()==(255,255)
    output=io.BytesIO()
    if opaque:
        image.convert('RGB').save(output,format='JPEG',quality=88,subsampling=0)
        mime='image/jpeg'
    else:
        image.save(output,format='PNG',compress_level=1)
        mime='image/png'
    while len(raw)%4:raw.append(0)
    dstoffset=len(raw)
    encoded=output.getvalue()
    raw.extend(encoded)
    entry['bufferView']=len(d['bufferViews'])
    entry['mimeType']=mime
    d['bufferViews'].append({'buffer':0,'byteOffset':dstoffset,'byteLength':len(encoded)})
    print('image',idx,'converted to',mime,'bytes',len(encoded))
for texture in d.get('textures',[]):
    ex=texture.get('extensions',{})
    webp=ex.pop('EXT_texture_webp',None)
    if webp is not None:texture['source']=webp['source']
    if not ex:texture.pop('extensions',None)
for key in ['extensionsUsed','extensionsRequired']:
    if key in d:
        d[key]=[x for x in d[key] if x!='EXT_texture_webp']
        if not d[key]:d.pop(key)
d['buffers'][0]['byteLength']=len(raw)
serialized=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode('utf8')
serialized+=b' ' * ((-len(serialized))%4)
raw.extend(b'\x00'*((-len(raw))%4))
length=12+8+len(serialized)+8+len(raw)
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_bytes(struct.pack('<4sII',b'glTF',2,length)+struct.pack('<I4s',len(serialized),b'JSON')+serialized+struct.pack('<I4s',len(raw),b'BIN\x00')+raw)
check=dst.read_bytes()
outlen=struct.unpack_from('<I',check,12)[0]
out=json.loads(check[20:20+outlen])
assert len(out.get('skins',[]))==len(d.get('skins',[]))
assert len(out['skins'][0]['joints'])==len(d['skins'][0]['joints'])
assert 'EXT_texture_webp' not in out.get('extensionsRequired',[])
assert all('source' in x for x in out.get('textures',[]))
print('Compatible GLB:',dst,'bytes',len(check),'required extensions',out.get('extensionsRequired',[]))
