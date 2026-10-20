#!/usr/bin/env python3
"""Fallback to Stability AI's public Stable Fast 3D Space (no HF token)."""
import os, shutil
from pathlib import Path
from gradio_client import Client, handle_file
from generate_ksante_ai import prepare, extract_path, OUT

def run():
    ref=prepare()
    client=Client("stabilityai/stable-fast-3d",download_files=True,verbose=True)
    input_image=handle_file(str(ref))
    # Verified from public Space API: /run_button takes five parameters.
    # It performs background removal and model generation as one action.
    print("Calling confirmed 5-argument /run_button endpoint.")
    try:
        out=client.predict(input_image,0.85,"None",-1,1024,api_name="/run_button")
    except Exception as exc:
        print("Anonymous SF3D generation failed:",str(exc)[:1400])
        raise
    source=extract_path(out)
    if not source:
        print("SF3D result metadata:",str(out)[:1000])
        raise RuntimeError("Generator returned no usable GLB")
    dest=OUT/"ksante-sf3d-unrigged.glb"
    shutil.copyfile(source,dest)
    if dest.stat().st_size<1024 or dest.read_bytes()[:4]!=b"glTF":
        raise RuntimeError("Invalid or incomplete GLB")
    print("3D generated:",dest, dest.stat().st_size)
    print("Generated geometry needs a humanoid skeleton before Kalidoface animation.")
if __name__=="__main__": run()
