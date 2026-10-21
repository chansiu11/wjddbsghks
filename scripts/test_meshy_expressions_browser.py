#!/usr/bin/env python3
"""Test actual Meshy expression morphs in Chromium and synthetic webcam expression tracking."""
import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT="https://chansiu11.github.io/wjddbsghks/"
MODEL=Path(sys.argv[1]).resolve()
assert MODEL.is_file() and MODEL.stat().st_size>10_000_000
OUT=Path("build/meshy-expression-qa");OUT.mkdir(parents=True,exist_ok=True)
EXPECTED=["const meshFlipPanel=(show)=>","n.setValue(i.Blink,c-(l.isMeshyAvatar?0:r))"]
NAMES={"blink","blinkLeft","blinkRight","mouthOpen","smile","mouthO","mouthE","browUp"}
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=[
   "--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream",
   "--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
  reports=[]
  for name,size in (("desktop",(1280,800)),("mobile",(390,844))):
   context=await browser.new_context(viewport={"width":size[0],"height":size[1]},
     permissions=["camera","microphone"],service_workers="block")
   page=await context.new_page()
   errors=[]
   page.on("pageerror",lambda error:errors.append(str(error)))
   async def source_patch(route):
    response=None;source=""
    for attempt in range(20):
     response=await route.fetch(url=route.request.url.split("?")[0]+"?meshy-expression-ready=v2")
     source=await response.text()
     if all(marker in source for marker in EXPECTED):break
     await asyncio.sleep(3)
    if not all(marker in source for marker in EXPECTED):raise AssertionError("Face blink/smile correction not deployed on Pages CDN")
    hook='z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)'
    assert source.count(hook)==1
    fixture="""window.__faceQa={
      avatar:y,
      set:(eye,mouth,smile,brow)=>{
        const s=E(V);
        s.user.detected=true;
        const f=s.user.tracking.Face;
        f.eye.l=eye;f.eye.r=eye;
        f.mouth.x=smile;
        f.mouth.shape.A=mouth;
        f.mouth.shape.E=.1;
        f.mouth.shape.I=.1;
        f.mouth.shape.O=.2;
        f.mouth.shape.U=.1;
        f.brow=brow;
        V.set(s);
      },
      state:()=>{
        let m=null;y.scene.traverse(o=>{if(o.isSkinnedMesh&&o.morphTargetDictionary)m=o});
        const dict=m?.morphTargetDictionary||{};
        const weights=m?.morphTargetInfluences||[];
        return {name:y.name,isMeshy:y.isMeshyAvatar,rotation:y.scene.rotation.y,
          meshCount:!!m,keys:Object.keys(dict),values:Object.fromEntries(
          Object.entries(dict).map(([k,i])=>[k,weights[i]])),
          vertices:m?.geometry?.attributes?.position?.count,
          morphCount:m?.geometry?.morphAttributes?.position?.length,
          facingButton:document.querySelector('#meshy-facing-flip')?.style.display,
          tracking:E(V).user.detected
        };
      }
    },z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)"""
    source=source.replace(hook,fixture)
    await route.fulfill(response=response,body=source,headers={**response.headers,"cache-control":"no-store"})
   async def model_override(route):
    await route.fulfill(path=str(MODEL),status=200,content_type="model/gltf-binary")
   await page.route("**/assets/index.default-ai.js*",source_patch)
   await page.route("**/assets/models/meshy-gilded-vanguard-rigged.glb*",model_override)
   await page.goto(ROOT,wait_until="domcontentloaded",timeout=60000)
   await page.wait_for_function("()=>!!window.__faceQa",timeout=65000)
   await page.wait_for_timeout(1300)
   first=await page.evaluate("()=>window.__faceQa.state()")
   print("EXPRESSION_INITIAL",name,json.dumps(first),flush=True)
   assert first["isMeshy"],"Wrong character"
   assert NAMES.issubset(set(first["keys"])),"Missing GLB morph dictionaries"
   assert first["morphCount"]>=8 and first["vertices"]>50000
   assert first["facingButton"]=="block","User-facing front/back control unavailable"
   await page.screenshot(path=str(OUT/(name+"-neutral.png")),full_page=True)
   # Drive actual avatar through the same Svelte Face store as webcam tracker.
   for i in range(12):
    await page.evaluate("()=>window.__faceQa.set(.08,.9,.85,.85)")
    await page.wait_for_timeout(125)
   changed=await page.evaluate("()=>window.__faceQa.state()")
   print("EXPRESSION_TRACKED",name,json.dumps(changed),flush=True)
   assert changed["values"].get("blink",0)>.65,"Eye blink not animated"
   assert changed["values"].get("mouthOpen",0)>.45,"Open mouth not animated"
   assert changed["values"].get("smile",0)>.6,"Smile not animated"
   assert changed["values"].get("browUp",0)>.6,"Eyebrows not animated"
   await page.screenshot(path=str(OUT/(name+"-tracked.png")),full_page=True)
   await page.click("#meshy-facing-flip")
   await page.wait_for_timeout(300)
   reversed_state=await page.evaluate("()=>window.__faceQa.state()")
   print("REVERSED",name,reversed_state["rotation"],flush=True)
   assert abs(abs(reversed_state["rotation"])-3.141592653589793)<0.08,"Direction switch did not rotate model"
   assert not errors,"Page JavaScript errors: "+str(errors[:5])
   reports.append({"viewport":name,"before":first,"after":changed,"flipped":reversed_state,"errors":errors})
   await context.close()
  (OUT/"report.json").write_text(json.dumps(reports,ensure_ascii=False,indent=2))
  await browser.close()
if __name__=="__main__":asyncio.run(main())
