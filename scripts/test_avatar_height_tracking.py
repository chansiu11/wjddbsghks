#!/usr/bin/env python3
"""Browser regression for generated GLB flying upward when face/body detection starts.

The production JS is instrumented in memory, never changed on the deployed site.
Use synthetic landmark input to exercise the exact Kalidoface runtime tracking path.
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE="https://chansiu11.github.io/wjddbsghks/"
OUT=Path("build/height-regression")
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED='let h=l.isGenericGLB?l.humanoid.restPose.hips.position[1]:i?u:K.lerp(o.position.y,u,.5+Ke*4)'
CAMERA_FIX="isGenericGLB?Dt.target.z+3.7"

async def visit(browser,label,width,height):
    ctx=await browser.new_context(
        viewport={"width":width,"height":height},
        device_scale_factor=1,
        permissions=["camera","microphone"],
        service_workers="block"
    )
    page=await ctx.new_page()
    console=[]
    errors=[]
    asset_status=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.on("console",lambda m:console.append(m.type+": "+m.text[:350]) if m.type=="error" else None)
    page.on("response",lambda r:asset_status.append({"url":r.url,"status":r.status}) if r.url.endswith("fan-ksante-ai.glb") else None)
    async def instrument(route):
        response=await route.fetch()
        source=await response.text()
        if EXPECTED not in source:raise RuntimeError("Hip-height fix not yet deployed")
        if CAMERA_FIX not in source:raise RuntimeError("Camera zoom fix not deployed")
        target='z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)'
        if source.count(target)!=1:raise RuntimeError("Avatar instance hook not found")
        hook="""z.model=y,V.set(n),y.isGenericGLB&&(window.__heightProbe={
          model:y,
          info:()=>{
            const hip=y.humanoid.getBoneNode("Hips");
            const neck=y.humanoid.getBoneNode("Neck");
            const head=y.humanoid.getBoneNode("Head");
            y.scene.updateMatrixWorld(true);
            const h=new hn,p=new hn;
            hip.getWorldPosition(h);head.getWorldPosition(p);
            const s=E(V).user;
            return {hipY:hip.position.y,baseY:y.humanoid.restPose.hips.position[1],
              hipWorldY:h.y,headWorldY:p.y,sceneY:y.scene.position.y,
              neckQuat:neck?[neck.quaternion.x,neck.quaternion.y,neck.quaternion.z,neck.quaternion.w]:null,
              detected:s.detected,poseEnabled:s.tracking.Pose.enable};
          },
          setPose:(enabled)=>{
            const s=E(V);
            s.user.detected=enabled;
            if(enabled){
              const p=s.user.tracking.Pose;
              p.enable=true;
              p.RightUpperLeg.z=.75;p.LeftUpperLeg.z=.72;
              p.RightUpperArm.z=.3;p.LeftUpperArm.z=-.3;
              p.Hips.position.x=.04;p.Hips.position.z=.1;
              const f=s.user.tracking.Face;
              f.head.x=.25;f.head.y=.32;f.head.z=.12;
            }
            V.set(s);
          }
        }),y.isGenericGLB||zs(y,z.tracking,z.id,!0)"""
        source=source.replace(target,hook)
        await route.fulfill(response=response,body=source,headers={**response.headers,"cache-control":"no-store"})
    await page.route("**/assets/index.default-ai.js*",instrument)
    response=await page.goto(BASE,wait_until="domcontentloaded",timeout=45000)
    if not response or response.status!=200:raise RuntimeError("Live page failed to open")
    await page.wait_for_function("() => !!window.__heightProbe",timeout=45000)
    await page.wait_for_timeout(600)
    initial=await page.evaluate("() => window.__heightProbe.info()")
    print("INITIAL",label,json.dumps(initial),flush=True)
    await page.evaluate("()=>window.__heightProbe.setPose(true)")
    samples=[]
    for idx in range(60):
        await page.wait_for_timeout(65)
        await page.evaluate("()=>window.__heightProbe.setPose(true)")
        if idx%6==0:
            samples.append(await page.evaluate("()=>window.__heightProbe.info()"))
    await page.screenshot(path=str(OUT/(label+"-face-detected.png")),full_page=True)
    await page.evaluate("()=>window.__heightProbe.setPose(false)")
    await page.wait_for_timeout(300)
    after=await page.evaluate("() => window.__heightProbe.info()")
    dy=max(abs(v["hipY"]-initial["hipY"]) for v in samples)
    world_dy=max(abs(v["hipWorldY"]-initial["hipWorldY"]) for v in samples)
    scene_dy=max(abs(v["sceneY"]-initial["sceneY"]) for v in samples)
    detected_count=sum(bool(v["detected"]) for v in samples)
    report={"initial":initial,"samples":samples,"after":after,
            "hipLocalMaxDelta":dy,"hipWorldMaxDelta":world_dy,"sceneMaxDelta":scene_dy,
            "detectedSamples":detected_count,"assetStatus":asset_status,"errors":errors,"console":console[-10:]}
    (OUT/(label+".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print("REGRESSION",label,json.dumps({
        "hipLocalMaxDelta":dy,"hipWorldMaxDelta":world_dy,"sceneMaxDelta":scene_dy,
        "detectedSamples":detected_count,"assets":asset_status,"errors":errors[-5:]},ensure_ascii=False),flush=True)
    await ctx.close()
    assert detected_count>4,"Did not exercise face-detected tracking path"
    assert dy<0.015,f"Generic GLB hips drift during face detection: {dy}"
    assert world_dy<0.5,f"Avatar flies up when tracked: {world_dy}"
    assert scene_dy<0.04,f"Avatar origin unexpectedly moves up: {scene_dy}"
    assert asset_status and any(r["status"]==200 for r in asset_status),"No model asset"
    assert not any("Character model import failed" in x for x in console),"GLB import error"

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(
            headless=True,args=["--no-sandbox","--use-fake-device-for-media-stream",
                                 "--use-fake-ui-for-media-stream","--enable-webgl",
                                 "--use-gl=angle","--use-angle=swiftshader",
                                 "--enable-unsafe-swiftshader"]
        )
        try:
            await visit(browser,"desktop",1280,800)
            await visit(browser,"mobile",390,844)
        finally:
            await browser.close()
if __name__=="__main__":
    asyncio.run(main())
