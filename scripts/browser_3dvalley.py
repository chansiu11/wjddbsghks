#!/usr/bin/env python3
"""Single browser/UI attempt at a no-login image-to-3D tool.
No CAPTCHA bypass, credential use, or direct unpublished service endpoint access.
Output is preserved as a private Actions artifact for review, not published.
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from generate_ksante_ai import prepare, OUT

URL="https://3dvalley.com/tools/create/image-to-3d"

async def main():
    image=prepare()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        context=await browser.new_context(
          accept_downloads=True,
          viewport={"width":1280,"height":860},
          locale="en-US",
        )
        page=await context.new_page()
        page.on("console",lambda m:print("BROWSER CONSOLE",m.type,m.text[:250]) if m.type=="error" else None)
        print("NAVIGATING",URL,flush=True)
        try:
            response=await page.goto(URL,wait_until="domcontentloaded",timeout=30000)
            print("HTTP",response.status if response else "no response",flush=True)
            await page.wait_for_timeout(5000)
            print("PAGE TITLE",await page.title(),flush=True)
            async def diagnostics(name):
                print("DIAGNOSTICS",name,flush=True)
                print("URL",page.url,flush=True)
                print("BUTTONS",json.dumps((await page.locator("button").all_text_contents())[:40],ensure_ascii=False),flush=True)
                print("INPUTS",str(await page.locator("input").evaluate_all("(els)=>els.map(e=>({type:e.type,accept:e.accept,placeholder:e.placeholder}))")),flush=True)
                print("BODY", (await page.locator("body").inner_text())[:3000],flush=True)
                await page.screenshot(path=str(OUT/f"3dvalley-{name}.png"),full_page=True,timeout=15000)
            await diagnostics("initial")
            file_inputs=page.locator("input[type=file]")
            if await file_inputs.count()==0:
                print("No file input available; stopping without bypass.",flush=True);return
            await file_inputs.first.set_input_files(str(image.absolute()))
            await page.wait_for_timeout(3500)
            await diagnostics("uploaded")
            button=page.get_by_role("button",name="Generate 3D",exact=True)
            if await button.count()==0:
                button=page.get_by_role("button",name="Generate",exact=True)
            if await button.count()==0:
                button=page.get_by_role("button",name="Convert to 3D",exact=True)
            if await button.count()==0:
                button=page.get_by_role("button",name="Create model",exact=True)
            if await button.count()==0:
                labels=await page.locator("button").all_text_contents()
                for idx,label in enumerate(labels):
                    if any(x in label.lower() for x in ["generate", "create model", "convert", "make 3d"]):
                        button=page.locator("button").nth(idx)
                        break
            if await button.count()==0:
                print("Generate button not recognized; stopping without guessing.",flush=True);return
            if await button.is_disabled():
                print("Generate button disabled, inspect reference image and UI.",flush=True);return
            print("CLICK",await button.inner_text(),flush=True)
            await button.click(timeout=12000)
            # Service does all AI generation itself. We only wait for the
            # documented client-side 'Download GLB' export control.
            for second in range(0,150,5):
                await page.wait_for_timeout(5000)
                body=(await page.locator("body").inner_text())
                if second%20==0:print("WAIT",second+5,"body tail",body[-620:],flush=True)
                if "captcha" in body.lower() or "verification required" in body.lower():
                    print("Human verification required, stopping.",flush=True);return
                download=page.get_by_text("Download GLB",exact=False)
                if await download.count()>0 and await download.first.is_visible():
                    print("DOWNLOAD CONTROL FOUND",flush=True)
                    async with page.expect_download(timeout=15000) as info:
                        await download.first.click()
                    artifact=await info.value
                    out=OUT/"experimental-avatar-unrigged.glb"
                    await artifact.save_as(str(out))
                    print("DOWNLOAD",str(out),out.stat().st_size,flush=True)
                    if out.stat().st_size<1024 or out.read_bytes()[:4]!=b"glTF":
                        raise RuntimeError("Not a valid GLB file")
                    return
            await diagnostics("timeout")
            print("NO MODEL GENERATED before deadline",flush=True)
        except Exception as exc:
            print("WORKFLOW FAILURE",repr(exc),flush=True)
            try: await page.screenshot(path=str(OUT/"3dvalley-error.png"),full_page=True)
            except Exception: pass
            raise
        finally:
            await browser.close()
if __name__=="__main__":
    asyncio.run(main())
