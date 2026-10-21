# Upload Meshy avatar for automatic GitHub Pages installation

**Upload one file here and name it `Meshy_Gilded_Vanguard_rigged_preview.glb`.**

Use the `Meshy_Gilded_Vanguard_rigged_preview.glb` created by ChatGPT from your Meshy FBX, with 72 bones including auxiliary hair and cloth springs.

GitHub Actions workflow `Validate and install Meshy VTuber model` will automatically:
1. Validate a real skinned GLB and named full-body/hand/finger/helper joints.
2. Check the skeleton maps to Kalidoface.
3. Open the deployed site in Chromium, intercept the currently shipped avatar URL with the uploaded candidate, and verify animated bone mappings and camera framing.
4. Only if all checks pass, install the candidate in `assets/models/meshy-gilded-vanguard-rigged.glb`, switch the default model, and publish it through Pages.

The existing avatar stays untouched when verification fails. No external 3D model service or installation is required on your device. GitHub Actions runs the checks.

**Limitations:** The current GLB is a geometry-guided rig prototype. Hair/cape spring effects are approximate, not a fully simulated cloth or manual weight-painted production rig. This model is a fan recreation and any public redistribution needs appropriate rights.
