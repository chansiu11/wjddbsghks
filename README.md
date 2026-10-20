# Kalidoface 3D — performance-tuned rehost

This is a rehost of the public [Kalidoface 3D](https://github.com/yeemachine/kalidoface-3d) built website, with its original UI and functionality. The original project's README and license notices are preserved in `UPSTREAM_README.md` and `LICENSE`. Model and artwork credits and any model-specific terms remain with their creators; external files are loaded from the original URLs.

Changes for this GitHub Pages deployment:
- Set the Vite output's relative links to work under `/wjddbsghks/` and remove the upstream analytics tag.
- Request up to 60 camera FPS; schedule inference on newly presented video frames when supported, and never queue overlapping inference jobs.
- Use the lighter holistic model setting (`modelComplexity: 0`) and reduce motion smoothing to reduce processing delay on tablets.
- Send remote avatar pose updates at 30 Hz instead of 10 Hz, lowering the update interval from 100 ms to about 33 ms when the connection keeps up.
- Cap rendering pixel ratio at 1.0 on Android tablets (1.35 elsewhere), disable tablet shadow maps, and avoid multisample antialiasing to reduce GPU work.
- Limit the debug landmark overlay to 10 Hz on Android tablets and 15 Hz elsewhere; avoid redundant face inference while holistic tracking is active.
- Cache the same-origin application bundles for faster repeat visits. Existing background assets remain externally hosted; the new default AI fan avatar is stored in this repository.

Tracking runs locally on the device. WebRTC call latency depends on the participants' network paths and cannot be guaranteed by a static GitHub Pages deployment. Video/voice calling uses the original app's PeerJS infrastructure, not a new server operated by this repository.

## K'Sante-inspired AI avatar (installed as the default)

The default avatar in this rehost is an **unofficial AI-generated fan study** informed by visual reference images of K'Sante. It was generated using 3D Valley / TRELLIS.2, given a 66-bone humanoid skeleton with afk-rig, and integrated into the existing webcam avatar animation. **It is not a model ripped from League of Legends** or an official Riot asset.

- Live GitHub Pages: https://chansiu11.github.io/wjddbsghks/
- Shipped rigged model: `assets/models/fan-ksante-ai.glb`, ~13.1 MB
- Rendering: original skinned geometry and joint matrices retained; standard textures resized to 1024px. Earlier 5.3MB gltfpack attempt was rejected because it distorted skin deformation in the legacy loader.
- Fixed compatibility: legacy GLTFLoader and WebP textures, initial rig, camera reset/overzoom, and front lighting.
- Original VRM character list remains available for manually switching avatars.
- Camera head/body/hand **bone mapping** tested in Chromium. No facial expression morph targets were generated, so mouth, blinks, and expressive face movement are limited; real mobile-device FPS and motion quality are **not verified**.
- The default face/body tracking runs locally. PeerJS calling service errors may affect multiplayer/remote avatar functions.

**Rights:** This is an unofficial fan experiment and is not endorsed by Riot Games. AI generation does not automatically grant permission to publicly distribute a recognizable game character. Verify the applicability of [Riot's fan content guidelines](https://www.riotgames.com/en/legal) and any source-image rights, and replace or remove the model if its use is not permitted.

## GLB avatar support (2026-10)

The bundled client can now accept a user-supplied single-file `.glb` (or the original `.vrm`) using the character upload control, drag-and-drop, or direct file URL. Generic GLB humanoids require an actual skinned rig with common Blender/Mixamo bone names; the app maps head, torso, hips, arms, legs and the fingers whose named bones are available, and matches a few optional facial morph targets. Static GLB meshes are rejected with an error. It does not recreate absent facial morphs or finger joints, and not every arbitrary rig exports compatible rotations. VRM remains the preferred animation format. The app currently ships the AI-generated fan avatar noted above and supports user-supplied rigged GLB/VRM files.

To create an avatar from reference artwork using a separate authorized 3D service, use image-to-3D, add a standard humanoid skeleton/skin weights, export GLB, and use the site upload control. Check all permissions for the source imagery and generated model before public redistribution.
