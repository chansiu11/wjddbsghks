# Kalidoface 3D — performance-tuned rehost

This is a rehost of the public [Kalidoface 3D](https://github.com/yeemachine/kalidoface-3d) built website, with its original UI and functionality. The original project's README and license notices are preserved in `UPSTREAM_README.md` and `LICENSE`. Model and artwork credits and any model-specific terms remain with their creators; external files are loaded from the original URLs.

Changes for this GitHub Pages deployment:
- Set the Vite output's relative links to work under `/wjddbsghks/` and remove the upstream analytics tag.
- Set webcam capture to a maximum of 30 FPS and throttle tracking to 30 processed frames per second.
- Use the lighter holistic model setting (`modelComplexity: 0`) to reduce processing delay on tablets.
- Send remote avatar pose updates at 20 Hz instead of 10 Hz, lowering the update interval from 100 ms to 50 ms when the connection keeps up.
- Cache the same-origin application bundles for faster repeat visits. Models and backgrounds remain on their original hosts.

Tracking runs locally on the device. WebRTC call latency depends on the participants' network paths and cannot be guaranteed by a static GitHub Pages deployment. Video/voice calling uses the original app's PeerJS infrastructure, not a new server operated by this repository.
