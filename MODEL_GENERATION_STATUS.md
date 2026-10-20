# Experimental character model — 2026-10-20 update

## Results obtained

The previous "no GLB" report is superseded. Account-free image-to-3D generation, automatic humanoid rigging and tablet optimization **all completed**. These generated review files are **not shipped in the public GitHub Pages site**.

| Stage | Result | Evidence |
| --- | --- | --- |
| Official Riot visual reference crop | 546 × 600 px, prepared without rehosting source in public app | [browser run](https://github.com/chansiu11/wjddbsghks/actions/runs/39377380594) |
| 3D Valley free browser generation | Valid GLB, 8,840,812 bytes, 198,840 triangles, no skeleton | [generation artifact](https://github.com/chansiu11/wjddbsghks/actions/runs/39377380594/artifacts/12244360734) |
| afk-rig local automatic rig | 66 bones, 1 skin, rigged GLB 12,143,196 bytes | [rig run](https://github.com/chansiu11/wjddbsghks/actions/runs/39377923319) |
| gltfpack tablet optimization | 119,280 triangles, 5,312,360 bytes, skin and 66 bones preserved | [optimization run](https://github.com/chansiu11/wjddbsghks/actions/runs/39378621626) |
| Kalidoface GLB mapping tests | All 49 required body and individual finger bone names mapped | `scripts/validate_glb_adapter.mjs` |
| Galaxy Tab physical test | **Not yet performed** | Requires actual tablet |

Local additional export: PNG/JPEG variant removes the optional `EXT_texture_webp` dependency from the 5.3MB gltfpack output, but grows to 12,757,412 bytes; the `KHR_mesh_quantization` extension remains. This conversion only affected a local review copy.

## Compatibility and legal limits

- Kalidoface's generic GLB adapter supports Mixamo- and afk-rig-style skeletal names. It has not yet been browser-tested on the generated character.
- The model is a fan-study produced from visual references, **not a downloaded Riot game asset**. It has no VRM-style facial expression blend shapes; tracking of the head, body and hand/finger bones is possible, but facial expression fidelity is limited.
- Riot's [Legal Jibber Jabber](https://www.riotgames.com/en/legal) explicitly restricts the use of its character appearances in third-party apps, including web apps, unless separately authorized. For that reason this review model was not committed as a default avatar asset to GitHub Pages. Current upload UI is generic, not character-specific.
- GitHub Actions artifacts are temporary; do not rely on those artifact URLs permanently. The model may be kept for offline, personal review and testing subject to applicable rights.

## Files added to repo

- `assets/glb-avatar-adapter.js`: humanoid and finger mappings.
- `scripts/browser_3dvalley.py`: browser-driven non-authenticated generation experiment.
- `scripts/validate_glb_adapter.mjs`: validate bone matching.
- `.github/workflows/avatar-browser-test.yml`, `rig-avatar-glb.yml`, `optimize-avatar-glb.yml`: one-off development workflows.

## Remaining development tasks

1. Validate import, materials, deformation and avatar orientation in the real Kalidoface browser.
2. Test on Samsung Galaxy Tab S10 FE+ to measure detection, animation delay, and FPS. Optimize further only from measured results.
3. For a publicly deployed default avatar, use an original or expressly licensed humanoid model. Do not put Riot character likenesses into the web app without authorization.
