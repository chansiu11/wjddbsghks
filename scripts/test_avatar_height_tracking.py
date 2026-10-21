#!/usr/bin/env python3
"""Browser regression for generated GLB flying upward when face/body detection starts.

The production JS is instrumented in memory, never changed on the deployed site.
Use synthetic landmark input to exercise the exact Kalidoface runtime tracking path.
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE="https://chansiu11.github.io/wjddbsghks/"
CANDIDATE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if CANDIDATE:assert CANDIDATE.is_file() and CANDIDATE.stat().st_size>500000
OUT=Path("build/height-regression")
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED='if(l.isGenericGLB){const anchor=l.humanoid.restPose.hips.position;o.position.set(anchor[0],anchor[1],anchor[2]);return}'
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
        source=""
        response=None
        for attempt in range(8):
            # Bust cached JS across independent GitHub Pages CDN edge nodes.
            response=await route.fetch(url=route.request.url.split("?")[0]+"?face-height-regression=20261021v2")
            source=await response.text()
            if EXPECTED in source:break
            print("CHECKING_DEPLOYMENT_CDN_EDGE",attempt,len(source),flush=True)
            await asyncio.sleep(2)
        if EXPECTED not in source:raise RuntimeError("Hip-height fix not yet visible on browser CDN edge")
        if CAMERA_FIX not in source:raise RuntimeError("Camera zoom fix not deployed")
        if CANDIDATE and "meshy" in CANDIDATE.name.lower():
            rig_call='createGenericGLBAvatar(g,v.name||"Model.glb")'
            if source.count(rig_call)!=1:raise RuntimeError("GLB avatar loader call not found")
            source=source.replace(rig_call,'createGenericGLBAvatar(g,"Meshy Gilded Vanguard.glb")')
        target='z.model=y,V.set(n),y.isGenericGLB||zs(y,z.tracking,z.id,!0)'
        if source.count(target)!=1:raise RuntimeError("Avatar instance hook not found")
        hook="""z.model=y,V.set(n),y.isGenericGLB&&(window.__heightProbe={
          model:y,
          info:()=>{
            const hip=y.humanoid.getBoneNode("Hips");
            const neck=y.humanoid.getBoneNode("Neck");
            const head=y.humanoid.getBoneNode("Head");
            const leftFoot=y.humanoid.getBoneNode("LeftFoot"),rightFoot=y.humanoid.getBoneNode("RightFoot");
            y.scene.updateMatrixWorld(true);
            const h=new rl,p=new rl,lf=new rl,rf=new rl;
            leftFoot.getWorldPosition(lf);rightFoot.getWorldPosition(rf);
            hip.getWorldPosition(h);head.getWorldPosition(p);
            const s=E(V).user;
            return {hipY:hip.position.y,baseY:y.humanoid.restPose.hips.position[1],
              hipWorldY:h.y,headWorldY:p.y,footWorldY:[lf.y,rf.y],sceneY:y.scene.position.y,
              neckQuat:neck?[neck.quaternion.x,neck.quaternion.y,neck.quaternion.z,neck.quaternion.w]:null,
              hipQuat:[hip.quaternion.x,hip.quaternion.y,hip.quaternion.z,hip.quaternion.w],
              detected:s.detected,poseEnabled:s.tracking.Pose.enable,
              springBones:y.secondaryMotion?.bones||[],
              isMeshy:y.isMeshyAvatar||false, sceneRotation:y.scene.rotation.y};
          },
          setPose:(enabled)=>{
            const s=E(V);
            s.user.detected=enabled;
            if(enabled){
              const p=s.user.tracking.Pose;
              p.enable=true;p.legsTracked=false; // Only face visible; ankles and knees are off-screen.
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
    if CANDIDATE:
        async def override_avatar(route):
            await route.fulfill(path=str(CANDIDATE),status=200,content_type="model/gltf-binary")
        await page.route("**/assets/models/fan-ksante-ai.glb*",override_avatar)
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
    feet_dy=max(max(abs(a-b) for a,b in zip(v["footWorldY"],initial["footWorldY"])) for v in samples)
    head_dy=max(abs(v["headWorldY"]-initial["headWorldY"]) for v in samples)
    detected_count=sum(bool(v["detected"]) for v in samples)
    hip_rotation_delta=max(max(abs(a-b) for a,b in zip(x["hipQuat"],initial["hipQuat"])) for x in samples)
    neck_rotation_delta=max(max(abs(a-b) for a,b in zip(x["neckQuat"],initial["neckQuat"])) for x in samples if x["neckQuat"])
    report={"initial":initial,"samples":samples,"after":after,
            "hipLocalMaxDelta":dy,"hipWorldMaxDelta":world_dy,"sceneMaxDelta":scene_dy,
            "detectedSamples":detected_count,"hipRotationMaxDelta":hip_rotation_delta,
            "neckRotationMaxDelta":neck_rotation_delta,"feetMaxDelta":feet_dy,"headMaxDelta":head_dy,"assetStatus":asset_status,"errors":errors,"console":console[-10:]}
    (OUT/(label+".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print("REGRESSION",label,json.dumps({
        "hipLocalMaxDelta":dy,"hipWorldMaxDelta":world_dy,"sceneMaxDelta":scene_dy,
        "detectedSamples":detected_count,"hipRotationMaxDelta":hip_rotation_delta,
        "neckRotationMaxDelta":neck_rotation_delta,"feetMaxDelta":feet_dy,"headMaxDelta":head_dy,"assets":asset_status,"errors":errors[-5:]},ensure_ascii=False),flush=True)
    await ctx.close()
    assert detected_count>4,"Did not exercise face-detected tracking path"
    assert dy<0.015,f"Generic GLB hips drift during face detection: {dy}"
    assert world_dy<0.5,f"Avatar flies up when tracked: {world_dy}"
    assert scene_dy<0.04,f"Avatar origin unexpectedly moves up: {scene_dy}"
    assert hip_rotation_delta<0.005,f"GLB pelvis was rotated by old VRM animation: {hip_rotation_delta}"
    assert feet_dy<0.1,f"Face-only detection caused untracked feet to fly: {feet_dy}"
    assert head_dy<0.25,f"Face-only detection shifted the avatar head vertically: {head_dy}"
    assert neck_rotation_delta>0.03,"Face tracking did not animate the neck"
    if CANDIDATE and "meshy" in CANDIDATE.name.lower():
        assert initial["isMeshy"],"Did not recognize Meshy avatar orientation"
        assert abs(after["sceneRotation"])<0.001,"Meshy should face the camera at its neutral yaw"
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
