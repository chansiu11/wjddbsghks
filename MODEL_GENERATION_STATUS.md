# K'Sante fan avatar: image-to-3D generation status (2026-10-20)

## Goal

Create a fan-study 3D humanoid avatar from visual references, not by extracting a game model, and use it with the existing Kalidoface camera and face/hand/body tracker on a Galaxy Tab S10 FE+.

## Checked and completed

- An official Riot Games full-character turnaround image was downloaded successfully from the Riot development article.
- Repo already supports local, user-selected VRM and skinned GLB imports through `assets/index.avatar.js` and `assets/glb-avatar-adapter.js`.
- Free, no-Hugging-Face-account model generation attempted from GitHub Actions using the public `trellis-community/TRELLIS` Space. Image preprocessing worked but the generation endpoint returned a non-verbose remote error, resulting in **no GLB**.
- An alternative generation attempt used the public `stabilityai/stable-fast-3d` Space. Its API signature was confirmed and the request adjusted to five parameters; the service then returned a non-verbose remote error. **No GLB** was returned.
- Failed runs preserved the original reference image and a cropped reference as temporary GitHub Actions artifacts. These artifacts are **not** 3D meshes.

## Last attempted builds

- TRELLIS run: https://github.com/chansiu11/wjddbsghks/actions/runs/39375857991
- SF3D (correct API) run: https://github.com/chansiu11/wjddbsghks/actions/runs/39376316567

## Safe next steps

1. Use a free image-to-3D website in a user-controlled browser, or retry the public Spaces after a service-side fix / anonymous GPU quota reset. The GH Actions scripts are reference-only; they do not run periodically.
2. Retrieve an actual GLB model and confirm that its appearance is acceptable.
3. Add a humanoid armature, skin weights, and (if desired) facial blend shapes / fingers. A raw image-to-3D mesh **cannot** directly support Kalidoface full-body finger/face movement.
4. Import the rigged model in Kalidoface or publish an appropriately licensed, noncommercial fan model in the repo, update the character default selection, and measure on the target tablet.

## References / licensing

- Official image article: https://www.leagueoflegends.com/en-us/news/dev/champion-insights-k-sante/
- Riot fan project limited permission (read all conditions): https://www.riotgames.com/en/legal
- Public free ZeroGPU quotas: https://huggingface.co/docs/hub/main/en/spaces-zerogpu
- GLB export Space: https://huggingface.co/spaces/trellis-community/TRELLIS
- SF3D Space: https://huggingface.co/spaces/stabilityai/stable-fast-3d

This project is an unofficial fan experiment, not affiliated with or endorsed by Riot Games. No source game model is bundled.
