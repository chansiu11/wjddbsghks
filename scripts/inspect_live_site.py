#!/usr/bin/env python3
"""Open deployed GitHub Pages in Chromium and report observed avatar state."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

OUT=Path("build/live-site-check")
OUT.mkdir(parents=True,exist_ok=True)
URLS={
 "main":"https://chansiu11.github.io/wjddbsghks/",
 "rig-test":"https://chansiu11.github.io/wjddbsghks/avatar-rig-test.html"
}
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=["--no-sandbox","--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
  context=await browser.new_context(viewport={"width":1280,"height":800},service_workers="block",permissions=["camera"])
  results={}
  for key,url in URLS.items():
   page=await context.new_page()
   console=[];pageerrors=[];responses=[]
   page.on("console",lambda m:console.append(m.type+": "+m.text[:600]) if m.type in ("error","warning") else None)
   page.on("pageerror",lambda e:pageerrors.append(str(e)))
   page.on("response",lambda r:responses.append({"status":r.status,"url":r.url}) if (r.status>=400 and ("/assets/" in r.url or "avatar-rig-test" in r.url)) else None)
   try:
    response=await page.goto(url,wait_until="domcontentloaded",timeout=45000)
    await page.wait_for_timeout(8500)
    state=await page.evaluate("""() => ({
     title:document.title,
     url:location.href,
     canvasCount:document.querySelectorAll('canvas').length,
     canvasDimensions:[...document.querySelectorAll('canvas')].map(c=>({width:c.width,height:c.height})),
     moduleScripts:[...document.querySelectorAll('script[type=module]')].map(s=>s.src),
     modelUrls:[...document.querySelectorAll('a[href],script[src],img[src]')].map(e=>e.getAttribute('src')||e.getAttribute('href')).filter(x=>x&&/\\.(glb|vrm)(\\?|$)/i.test(x)),
     fileInputs:[...document.querySelectorAll('input[type=file]')].map(x=>x.accept),
     body:document.body.innerText.slice(0,2300),
     loadedTestModel:window.__glbLoaded||null
    })""")
    state["httpStatus"]=response.status if response else None
    state["consoleErrors"]=console[-12:]
    state["pageErrors"]=pageerrors[-12:]
    state["badResponses"]=responses[-12:]
    await page.screenshot(path=str(OUT/(key+".png")),full_page=True,timeout=25000)
    results[key]=state
    print("SITE_INSPECTION",key,json.dumps(state,ensure_ascii=False),flush=True)
   except Exception as err:
    results[key]={"error":str(err)}
    print("SITE_INSPECTION_ERROR",key,repr(err),flush=True)
   await page.close()
  (OUT/"site-results.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
  await browser.close()

if __name__=="__main__":asyncio.run(main())
