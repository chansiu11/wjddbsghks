# Kalidoface 3D — performance-tuned rehost

This is a rehost of the public [Kalidoface 3D](https://github.com/yeemachine/kalidoface-3d) built website, with its original UI and functionality. The original project's README and license notices are preserved in `UPSTREAM_README.md` and `LICENSE`. Model and artwork credits and any model-specific terms remain with their creators; external files are loaded from the original URLs.

Changes for this GitHub Pages deployment:
- Set the Vite output's relative links to work under `/wjddbsghks/` and remove the upstream analytics tag.
- Request up to 60 camera FPS; schedule inference on newly presented video frames when supported, and never queue overlapping inference jobs.
- Use the lighter holistic model setting (`modelComplexity: 0`) and reduce motion smoothing to reduce processing delay on tablets.
- Send remote avatar pose updates at 30 Hz instead of 10 Hz, lowering the update interval from 100 ms to about 33 ms when the connection keeps up.
- Cap rendering pixel ratio at 1.0 on Android tablets (1.35 elsewhere), disable tablet shadow maps, and avoid multisample antialiasing to reduce GPU work.
- Limit the debug landmark overlay to 10 Hz on Android tablets and 15 Hz elsewhere; avoid redundant face inference while holistic tracking is active.
- Cache the same-origin application bundles for faster repeat visits. Models and backgrounds remain on their original hosts.

Tracking runs locally on the device. WebRTC call latency depends on the participants' network paths and cannot be guaranteed by a static GitHub Pages deployment. Video/voice calling uses the original app's PeerJS infrastructure, not a new server operated by this repository.

## K'Sante 3D model source (not yet installed)

A real K'Sante model can be previewed at [Khada's K'Sante viewer](https://modelviewer.lol/model-viewer?id=897000). It is not a verified redistributable VRM avatar: this application currently animates humanoid VRM rigs, and extracting/rehosting a third-party Riot-owned asset requires additional rights and conversion/rig compatibility checks. No placeholder K'Sante model has been generated or substituted. Existing `.vrm` upload support remains available for appropriately licensed rigs.

## GLB avatar support (2026-10)

The bundled client can now accept a user-supplied single-file `.glb` (or the original `.vrm`) using the character upload control, drag-and-drop, or direct file URL. Generic GLB humanoids require an actual skinned rig with common Blender/Mixamo bone names; the app maps head, torso, hips, arms, legs and the fingers whose named bones are available, and matches a few optional facial morph targets. Static GLB meshes are rejected with an error. It does not recreate absent facial morphs or finger joints, and not every arbitrary rig exports compatible rotations. VRM remains the preferred animation format. The app does **not** ship any K'Sante asset or an AI-made imitation.

To create an avatar from reference artwork using a separate authorized 3D service, use image-to-3D, add a standard humanoid skeleton/skin weights, export GLB, and use the site upload control. Check all permissions for the source imagery and generated model before public redistribution.
