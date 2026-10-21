# Current default: corrected Meshy Gilded Vanguard (2026-10-21)

- **Live site:** https://chansiu11.github.io/wjddbsghks/
- **Current default model:** `assets/models/meshy-gilded-vanguard-rigged.glb`, 7,030,508 bytes.
- **Previous default preserved:** `assets/models/fan-ksante-ai.glb` and remains in the avatar picker.
- **Cause of prior deformation:** old `assets/uploads/Meshy_Gilded_Vanguard_rigged_preview (1).glb` used manually approximated skin weights; GLB format and neutral bind checks alone were insufficient.
- **Correction:** `scripts/recover_meshy_unskinned.py` restores upright original Meshy geometry, discards unreliable skin weights; `afk-rig auto ... --skeleton human` rebuilds 66 joints and their skin weights; `build_rig_compatible.py` keeps real inverse bind matrices while compressing textures.
- **Visual correction:** Meshy is front-facing at yaw 0. The generic model adapter marks its type independently from existing VRM avatars; the live default script and service worker were cache-busted.
- **Confirmed live QA:** workflow [39534077329](https://github.com/chansiu11/wjddbsghks/actions/runs/39534077329) completed successfully. Skinned scene loads via HTTP 200; 49 mapped torso/limb/finger bones, upright height and camera bounds; desktop/mobile synthetic face and arm tracking with stable feet/hips and nonzero neck motion. Live screenshots captured.
- **Not verified:** actual human webcam tracking on user's specific device, facial mouth/blink morph targets, high-quality authored secondary hair/cloth rigging. The new 66-joint stable model has **no accessory spring helper bones**, so accessory springs do not run; this is deliberate to prevent reintroducing mesh distortion. Manual sculpting/skin weights may still be needed for production-quality movement.
- **Safety:** `install-meshy-candidate.yml` has its unsafe old manual-skin deployment disabled. Repaired Meshy model publishing is gated on browser QA and a verified artifact.

---

# Default AI fan avatar — implementation status (2026-10-20)

## Deployed and browser-verified

- Live app: https://chansiu11.github.io/wjddbsghks/
- Default AI fan study model: `assets/models/fan-ksante-ai.glb` (13,128,760 bytes).
- Model creation: 3D Valley / TRELLIS.2 from an official visual reference.
- Auto rigging: afk-rig, 66 joints, one skinned mesh, including individually named finger joints.
- Mobile-oriented texture preparation: 1024px max texture edge, legacy GLTFLoader-compatible PNG/JPEG, original unquantized mesh, inverse bind matrices and joint weights preserved.
- Correct default loading and asset HTTP 200 verified in a real Chromium browser.
- Active camera no longer zooms into the model after Kalidoface UI initialization. The full figure is visible in recorded screenshots, and 49 standard humanoid/finger bones are mapped by the adapter.
- Added a gentle frontal directional light so the character is not left silhouetted.

## QA evidence

- Generated reference and mesh: https://github.com/chansiu11/wjddbsghks/actions/runs/39377380594
- Original 66-bone rig: https://github.com/chansiu11/wjddbsghks/actions/runs/39377923319
- Final corrected default model publishing, with delayed camera test: https://github.com/chansiu11/wjddbsghks/actions/runs/39440278880
- Latest default-avatar render/lighting smoke test: https://github.com/chansiu11/wjddbsghks/actions/runs/39441523252

The older 5,312,360-byte gltfpack mesh is not the currently shipped model. Although that mesh reported valid joints, its legacy runtime deformation was severely distorted. The original armature/mesh combined with smaller *textures only* is the correct working version.

## Important remaining limits

- No actual Galaxy Tab S10 FE+ benchmark or physical-camera latency test has been performed.
- This generated model does not contain facial expression blend shapes, limiting blinks and mouth expressions. Its humanoid armature provides head/neck/torso/limb/finger bones for Kalidoface tracking, but movement quality has not yet been fully validated with a real human on camera.
- The original PeerJS server at `kalidoface-pair.glitch.me` returns WebSocket 410 in browser QA; remote connection / multiplayer features may fail independently of local 3D avatar operation.
- Some legacy external background assets hosted on Glitch may also fail to load.
- A public AI likeness of K'Sante is **not automatically licensed by virtue of AI generation**. Check [Riot Games fan-use guidelines](https://www.riotgames.com/en/legal), and obtain any required authorization or replace the model with an original permitted design.

The AI fan model is not an extracted Riot game mesh and does not contain redistributed original game model files. The site and model are unofficial and are not endorsed by Riot Games.
