// Compatibility repair for legacy GLTFLoader versions without EXT_texture_webp support.
// Keeps the humanoid rig, geometry, materials, all skin and node indices intact.
// Runs only for explicitly user-selected local .glb files; never downloads assets.
const decode = new TextDecoder();
const encode = new TextEncoder();
const pad = n => (n + 3) & ~3;
const WEBP = "EXT_texture_webp";
async function encodeTexture(bytes) {
  const image = await createImageBitmap(new Blob([bytes], {type: "image/webp"}));
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const ctx = canvas.getContext("2d", {willReadFrequently:true});
  if (!ctx) throw Error("텍스처를 변환할 Canvas를 생성할 수 없습니다.");
  ctx.drawImage(image,0,0);
  image.close?.();
  const pixels = ctx.getImageData(0,0,canvas.width,canvas.height).data;
  let opaque=true;
  for(let i=3;i<pixels.length;i+=4) if(pixels[i]!==255) {opaque=false;break}
  const mime = opaque ? "image/jpeg" : "image/png";
  const result = await new Promise((resolve,reject)=>{
    canvas.toBlob(blob=>blob?resolve(blob):reject(Error("텍스처 변환에 실패했습니다.")),mime,.9);
  });
  canvas.width=1;canvas.height=1;
  return {mime,bytes:new Uint8Array(await result.arrayBuffer())};
}
export async function prepareCompatibleGlb(file) {
  if(!/\.glb$/i.test(file.name)) return file;
  const array=await file.arrayBuffer();
  const data=new DataView(array);
  if(array.byteLength<28 || data.getUint32(0,true)!==0x46546c67 || data.getUint32(4,true)!==2) return file;
  const jsonLength=data.getUint32(12,true);
  if(data.getUint32(16,true)!==0x4e4f534a) throw Error("GLB JSON 청크를 읽을 수 없습니다.");
  const json=JSON.parse(decode.decode(new Uint8Array(array,20,jsonLength)));
  const extensions=json.extensionsRequired||[];
  if(!extensions.includes(WEBP) && !(json.images||[]).some(i=>i.mimeType==="image/webp")) return file;
  const binStart=20+jsonLength;
  const binLength=data.getUint32(binStart,true);
  if(data.getUint32(binStart+4,true)!==0x004e4942) throw Error("GLB BIN 청크를 읽을 수 없습니다.");
  const originalBin=new Uint8Array(array,binStart+8,binLength);
  let bin=new Uint8Array(pad(binLength));
  bin.set(originalBin);
  for(const entry of (json.images||[])){
    if(entry.mimeType!=="image/webp")continue;
    const view=json.bufferViews?.[entry.bufferView];
    if(!view || (view.buffer??0)!==0)throw Error("외부 버퍼 텍스처는 지원되지 않습니다.");
    const start=view.byteOffset||0;
    const end=start+view.byteLength;
    if(end>originalBin.length)throw Error("텍스처 데이터가 손상되었습니다.");
    const converted=await encodeTexture(originalBin.slice(start,end));
    const offset=pad(bin.length);
    const next=new Uint8Array(pad(offset+converted.bytes.length));
    next.set(bin);
    next.set(converted.bytes,offset);
    bin=next;
    entry.bufferView=json.bufferViews.length;
    entry.mimeType=converted.mime;
    json.bufferViews.push({buffer:0,byteOffset:offset,byteLength:converted.bytes.length});
  }
  for(const texture of (json.textures||[])){
    const ext=texture.extensions;
    const spec=ext?.[WEBP];
    if(spec) {
      texture.source=spec.source;
      delete ext[WEBP];
      if(!Object.keys(ext).length)delete texture.extensions;
    }
  }
  for(const key of ["extensionsRequired","extensionsUsed"]) {
    if(json[key]) {
      json[key]=json[key].filter(x=>x!==WEBP);
      if(json[key].length===0)delete json[key];
    }
  }
  json.buffers[0].byteLength=bin.length;
  const bytes=encode.encode(JSON.stringify(json));
  const paddedJSON=new Uint8Array(pad(bytes.length));
  paddedJSON.set(bytes);
  paddedJSON.fill(32,bytes.length);
  const total=12+8+paddedJSON.length+8+bin.length;
  const combined=new Uint8Array(total);
  const out=new DataView(combined.buffer);
  out.setUint32(0,0x46546c67,true);
  out.setUint32(4,2,true);
  out.setUint32(8,total,true);
  out.setUint32(12,paddedJSON.length,true);
  out.setUint32(16,0x4e4f534a,true);
  combined.set(paddedJSON,20);
  const loc=20+paddedJSON.length;
  out.setUint32(loc,bin.length,true);
  out.setUint32(loc+4,0x004e4942,true);
  combined.set(bin,loc+8);
  return new File([combined],file.name,{type:"model/gltf-binary",lastModified:file.lastModified});
}
