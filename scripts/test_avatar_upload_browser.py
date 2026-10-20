#!/usr/bin/env python3
"""Browser test of a LOCAL drag/drop GLB in the public Kalidoface runtime.

The generated model is supplied only to the ephemeral browser process.
It is never uploaded to Pages, committed to the public repository, or
sent to a remote model-generation service by this script.
"""
import asyncio, base64, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

MODEL=Path(sys.argv[1])
OUT=Path("build/avatar-browser-qa")
OUT.mkdir(parents=True,exist_ok=True)
URL="https://chansiu11.github.io/wjddbsghks/"
assert MODEL.exists() and MODEL.stat().st_size>100000

async def test():
 async with async_playwright() as p:
  browser=await p.chromium.launch(
    headless=True,args=[
      "--no-sandbox",
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
      "--enable-webgl",
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
    ])
  context=await browser.new_context(viewport={"width":1280,"height":800},
   accept_downloads=False,permissions=["camera","microphone"],
   service_workers="block")
  page=await context.new_page()
  js_errors=[]
  js_logs=[]
  page.on("pageerror",lambda err:js_errors.append(str(err)))
  page.on("console",lambda msg:js_logs.append(msg.type+": "+msg.text[:500]) if msg.type in ("error","warning") else None)
  async def patch_bundle(route):
   response=await route.fetch()
   body=await response.text()
   print("BUNDLE_ORIGINAL_SIZE",len(body),flush=True)
   old="z.model=y,V.set(n),zs(y,z.tracking,z.id,!0)"
   new='window.__glbLoaded=y.isGenericGLB===true?{name:y.name,rig:true,bones:["Hips","Head","LeftHand","RightHand","LeftIndexProximal","RightIndexProximal"].map(k=>!!y.humanoid.getBoneNode(k)),meshes:y.scene.children.length}:window.__glbLoaded,z.model=y,V.set(n),zs(y,z.tracking,z.id,!0)'
   assert body.count(old)==1,("Model-ready hook not found",body.count(old))
   body=body.replace(old,new)
   old2='console.error("Character model import failed",err)'
   new2='window.__glbFailure=String(err?.message||err),console.error("Character model import failed",err)'
   assert body.count(old2)==1
   body=body.replace(old2,new2)
   await route.fulfill(response=response,body=body,headers={**response.headers,"cache-control":"no-store"})
  await page.route("**/assets/index.glbcompatible.js*",patch_bundle)
  await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
  await page.wait_for_timeout(7500)
  print("PAGE_TITLE",await page.title(),flush=True)
  print("BODY_BEFORE",(await page.locator("body").inner_text())[:1700],flush=True)
  await page.screenshot(path=str(OUT/"before-upload.png"),full_page=True,timeout=20000)
  data=base64.b64encode(MODEL.read_bytes()).decode("ascii")
  await page.evaluate("""(blob)=>{
    const bin=atob(blob),buf=new Uint8Array(bin.length);
    for(let k=0;k<bin.length;k++)buf[k]=bin.charCodeAt(k);
    const file=new File([buf],"experimental-humanoid.glb",{type:"model/gltf-binary"});
    const transfer=new DataTransfer();transfer.items.add(file);
    window.dispatchEvent(new DragEvent("dragenter",{dataTransfer:transfer,bubbles:true,cancelable:true}));
    window.dispatchEvent(new DragEvent("dragover",{dataTransfer:transfer,bubbles:true,cancelable:true}));
    window.dispatchEvent(new DragEvent("drop",{dataTransfer:transfer,bubbles:true,cancelable:true}));
  }""",data)
  print("DISPATCHED_GLB_FILE_BYTES",MODEL.stat().st_size,flush=True)
  for i in range(12):
   await page.wait_for_timeout(2500)
   state=await page.evaluate("({loaded:window.__glbLoaded||null,error:window.__glbFailure||null})")
   print("WAIT",i,"STATE",json.dumps(state,ensure_ascii=False),flush=True)
   if state["loaded"] or state["error"]:break
  await page.screenshot(path=str(OUT/"after-upload.png"),full_page=True,timeout=20000)
  final=await page.evaluate("({loaded:window.__glbLoaded||null,error:window.__glbFailure||null,canvasCount:document.querySelectorAll('canvas').length})")
  (OUT/"results.json").write_text(json.dumps({
    "status":final,
    "pageerrors":js_errors[-30:],
    "console":js_logs[-35:],
  },ensure_ascii=False,indent=2))
  print("FINAL",json.dumps(final,ensure_ascii=False),flush=True)
  print("PAGE_ERRORS",json.dumps(js_errors[-10:],ensure_ascii=False),flush=True)
  print("CONSOLE",json.dumps(js_logs[-20:],ensure_ascii=False),flush=True)
  await browser.close()
  if final["error"]:raise AssertionError("GLB loader failed: "+str(final["error"]))
  if not final["loaded"]:raise AssertionError("No character loaded after 30 seconds")
  if not final["loaded"]["rig"]:raise AssertionError("Loaded character is not using generic GLB adapter")
  if not all(final["loaded"]["bones"]):raise AssertionError("Required joints missing in loaded avatar")

if __name__=="__main__":
 asyncio.run(test())
