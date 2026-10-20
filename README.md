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
