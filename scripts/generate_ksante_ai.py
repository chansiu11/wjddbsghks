#!/usr/bin/env python3
"""Single anonymous/free attempt at generating a 3D fan-study from an official Riot image.

This script only creates a local workflow artifact. It does not publish an unrigged
mesh as a working avatar. Official turnaround: Riot Games Champion Insights: K'Sante.
Hugging Face ZeroGPU usage is subject to anonymous quotas and availability.
"""
import os
import shutil
from pathlib import Path
import requests
import numpy as np
from PIL import Image
from gradio_client import Client, handle_file

SOURCE = "https://cmsassets.rgpub.io/sanity/images/dsfx7636/news_live/5fc3a2624909cc868d45514e6abc5d5d1854d1e5-2734x600.jpg"
SPACE = "trellis-community/TRELLIS"
OUT = Path("build/ksante-ai")
OUT.mkdir(parents=True, exist_ok=True)

def prepare():
    resp = requests.get(SOURCE, timeout=35, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    (OUT / "official-turnaround.jpg").write_bytes(resp.content)
    image = Image.open(OUT / "official-turnaround.jpg").convert("RGB")
    w, h = image.size
    # Reference source is Riot's multi-view line-up. Keep frontmost panel.
    frame = image.crop((0, 0, int(w / 5), h)).convert("RGBA") if w > h * 3 else image.convert("RGBA")
    # Keep this input untouched: remote demo will remove its uniform backdrop.
    frame.save(OUT / "reference.png")
    print("Downloaded official model turnaround:", image.size, "reference:", frame.size)
    return OUT / "reference.png"

def extract_path(value):
    if isinstance(value, (str, os.PathLike)):
        p = Path(str(value))
        if p.is_file() and p.suffix.lower() == ".glb": return p
    if isinstance(value, dict):
        for v in value.values():
            result = extract_path(v)
            if result: return result
    if isinstance(value, (list, tuple)):
        for v in value[::-1]:
            result = extract_path(v)
            if result: return result
    return None

def main():
    reference=prepare()
    client=Client(SPACE, download_files=True, verbose=True)
    # The Space uses Gradio's image preprocessor ahead of the generation function.
    input_file=handle_file(str(reference))
    try:
        preprocessed=client.predict(input_file, api_name="/preprocess_image")
        print("Preprocessing completed.")
    except Exception as exc:
        print("Preprocessing API unavailable; passing original:",str(exc)[:280])
        preprocessed=input_file
    args=[
        preprocessed, [], False, 0, 7.5, 12, 3.0, 12,
        "stochastic", 0.95, 1024
    ]
    try:
        result=client.predict(*args, api_name="/generate_and_extract_glb")
    except Exception as exc:
        print("Free anonymous GPU generation failed:",str(exc)[:1200])
        raise
    filename=extract_path(result)
    if not filename: raise RuntimeError("3D API completed, but no GLB output was returned.")
    path=OUT/"ksante-unrigged.glb"
    shutil.copyfile(filename,path)
    if path.stat().st_size < 1024 or path.read_bytes()[:4] != b"glTF":
        raise RuntimeError("Invalid GLB header / unexpectedly small output")
    print("Generated GLB:", path,"size:",path.stat().st_size)
    try:
        import trimesh
        loaded=trimesh.load(path, force="scene")
        print("Mesh geometry objects:",len(loaded.geometry))
    except Exception as exc:
        print("GLB mesh inspection not available:",exc)
    print("NOT auto-deploying; an AI mesh usually has no humanoid skeleton.")

if __name__ == "__main__":
    main()
