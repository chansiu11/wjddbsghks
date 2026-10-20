#!/usr/bin/env python3
"""Visit production Pages in real Chromium, check default fan avatar loading and screenshot."""
import asyncio, json, time, sys
from pathlib import Path
from playwright.async_api import async_playwright

URL="https://chansiu11.github.io/wjddbsghks/"
OUT=Path("build/noquant-avatar-qa"); OUT.mkdir(parents=True,exist_ok=True)
MODEL_OVERRIDE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if MODEL_OVERRIDE: assert MODEL_OVERRIDE.is_file() and MODEL_OVERRIDE.stat().st_size>500000

async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=[
   "--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream",
   "--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
  context=await browser.new_context(viewport={"width":1280,"height":800},service_workers="block",permissions=["camera","microphone"])
  page=await context.new_page()
  errors=[];requests=[];responses=[];console=[]
  page.on("pageerror",lambda err: errors.append(str(err)))
  page.on("console",lambda m:console.append(m.type+": "+m.text[:450]) if m.type in ("error","warning") else None)
  page.on("request",lambda r:requests.append(r.url) if (".glb" in r.url or "index.default-ai.js" in r.url) else None)
  page.on("requestfailed",lambda r:errors.append("Request failed "+r.url+" "+str(r.failure)))
  page.on("response",lambda r:responses.append({"status":r.status,"url":r.url,"size":r.headers.get("content-length")}) if (".glb" in r.url or "index.default-ai.js" in r.url) else None)
  async def patch(route):
   r=await route.fetch()
   text=await r.text()
   print("BUNDLE_SIZE",len(text),flush=True)
   old='z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)'
   patched='window.__getAvatarCamera=()=>{const active=E(Qn);for(const c of [jt,It,active])c?.updateMatrixWorld?.(true);const props=c=>c?({name:c===jt?"main":c===It?"firstperson":"unknown",position:[c.position.x,c.position.y,c.position.z],world:Array.from(c.matrixWorld.elements).slice(12,15),fov:c.fov,zoom:c.zoom,aspect:c.aspect,near:c.near,far:c.far,forward:[-c.matrixWorld.elements[8],-c.matrixWorld.elements[9],-c.matrixWorld.elements[10]]}):null;return {position:[jt.position.x,jt.position.y,jt.position.z],target:[Dt.target.x,Dt.target.y,Dt.target.z],active:props(active),main:props(jt),first:props(It),mode:E(Ie)};},window.__mountedDefaultAvatar={name:y.name,generic:y.isGenericGLB,bones:["Hips","Head","LeftHand","RightHand","LeftIndexProximal","RightIndexProximal"].map(k=>!!y.humanoid.getBoneNode(k))},window.__modelRef=y,z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)'
   if text.count(old)!=1: raise AssertionError(f"hook missing, count={text.count(old)}")
   text=text.replace(old,patched)
   old_err='console.error("Character model import failed",err)'
   text=text.replace(old_err,'window.__avatarLoadError=String(err?.message||err),console.error("Character model import failed",err)')
   await route.fulfill(response=r,body=text,headers={**r.headers,"cache-control":"no-store"})
  await page.route("**/assets/index.default-ai.js*",patch)
  if MODEL_OVERRIDE:
   async def use_local_model(route):
    print("MODEL_OVERRIDE",str(MODEL_OVERRIDE),"bytes",MODEL_OVERRIDE.stat().st_size,flush=True)
    await route.fulfill(path=str(MODEL_OVERRIDE),status=200,content_type="model/gltf-binary")
   await page.route("**/assets/models/fan-ksante-ai.glb*",use_local_model)
  await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
  print("PAGE",await page.title(),flush=True)
  status={}
  for tick in range(20):
   await page.wait_for_timeout(2000)
   status=await page.evaluate("""()=>{
     const model=window.__modelRef;
     const coord=(name)=>{
       const node=model?.humanoid?.getBoneNode?.(name);
       if(!node) return null;
       let v={x:0,y:0,z:0};
       node.updateWorldMatrix(true,false);
       const e=node.matrixWorld.elements;return [e[12],e[13],e[14]];
     };
     return {
      state:window.__mountedDefaultAvatar||null,
      modelLoadError:window.__avatarLoadError||null,
      hips:coord("Hips"),
      head:coord("Head"),
      feet:[coord("LeftFoot"),coord("RightFoot")],
      camera:window.__getAvatarCamera?.()||null,\n      meshDebug:(()=>{
       const info={meshCount:0,vertices:0,samples:0,boundsMin:[Infinity,Infinity,Infinity],boundsMax:[-Infinity,-Infinity,-Infinity],skinMethodNames:[]};
       if(!model)return null;
       model.scene.updateMatrixWorld(true);
       model.scene.traverse(o=>{
        if(!o.isSkinnedMesh)return;
        info.meshCount++;
        const a=o.geometry?.attributes?.position;
        if(!a)return;
        info.vertices+=a.count;
        const meth=typeof o.boneTransform==="function"?"boneTransform":typeof o.applyBoneTransform==="function"?"applyBoneTransform":null;
        info.skinMethodNames.push(meth);
        const v=o.position.clone(),step=Math.max(1,Math.floor(a.count/1200));
        for(let i=0;i<a.count;i+=step){
         v.fromBufferAttribute(a,i);
         try{if(meth)o[meth](i,v)}catch(_){continue}
         v.applyMatrix4(o.matrixWorld);
         if(!Number.isFinite(v.x)||!Number.isFinite(v.y)||!Number.isFinite(v.z))continue;
         info.samples++;
         for(const [k,n] of [v.x,v.y,v.z].entries()){info.boundsMin[k]=Math.min(info.boundsMin[k],n);info.boundsMax[k]=Math.max(info.boundsMax[k],n)}
        }
       });
       return info;
      })(),
      canvasCount:document.querySelectorAll("canvas").length,
      source:document.querySelector('script[src*="default-ai"]')?.src||null
     };
   }""")
   print("STATUS",tick,json.dumps(status,ensure_ascii=False),flush=True)
   if status.get("state") and status["state"]["generic"]: break
  await page.wait_for_timeout(3500)
  await page.screenshot(path=str(OUT/"default-avatar-live.png"),full_page=True,timeout=25000)
  extra=await page.evaluate("""()=>window.__getAvatarCamera?.()||null""")
  print("ACTIVE_CAMERA_POST_SCREENSHOT",json.dumps(extra),flush=True)
  report={"status":status,"requests":requests,"responses":responses,"pageerrors":errors[-12:],"console":console[-15:]}
  (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
  print("REPORT",json.dumps(report,ensure_ascii=False),flush=True)
  await browser.close()
  if status.get("source") is None: raise AssertionError("Deployment not switched to default bundle")
  if not (status.get("state") or {}).get("generic"): raise AssertionError("GLB not loaded as default")
  if not all(status["state"]["bones"]): raise AssertionError("Incomplete humanoid mapping")
  if not status.get("camera") or (status["camera"]["position"][2]-status["camera"]["target"][2])<2.5: raise AssertionError("Camera is still too close to avatar")
  if status.get("head") and all(status.get("feet") or []):
   if status["head"][1]-sum(x[1] for x in status["feet"])/2 < 0.7:raise AssertionError("Avatar skeleton appears folded or lying down")
  if not any(q["status"]==200 and "fan-ksante-ai.glb" in q["url"] for q in responses):
   raise AssertionError("No HTTP 200 GLB asset")
if __name__=="__main__":asyncio.run(main())
