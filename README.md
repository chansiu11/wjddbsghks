# Motion Studio — web VTuber

Camera-based 3D avatar studio designed for phones and tablets. Open the GitHub Pages URL, allow camera access, and use the toolbar to change the avatar or background.

- Facial expressions, head movement, pose, and fingers use MediaPipe Tasks Vision. Processing runs in the browser.
- Includes an original procedural 3D character and supports locally uploaded VRM avatars via three-vrm.
- Supports custom backgrounds, chroma colors, a camera preview, screenshot download, orbit, zoom, and fullscreen.
- All files from the previous Android prototype have been removed from the active branch.

The app loads Three.js, three-vrm, MediaPipe, and tracking model weights from CDNs on first use. A camera requires HTTPS. Imported VRM files stay in browser memory for the current visit; the app does not upload them to a server.

This project is an original implementation inspired by the publicly documented capabilities of Kalidoface 3D. It does not include Kalidoface branding, code, or sample models.
