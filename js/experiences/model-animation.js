// Registry for animated procedural models. A model marks its root with
// `userData.animation = { kind, ... }` (plain data, so it survives the JSON
// copy Object3D.clone makes) and registers an updater for `kind`; ModelStage
// calls `runAnimation(root, elapsedSeconds)` each frame while the model is visible.
const updaters = new Map();
export const registerAnimation = (kind, update) => updaters.set(kind, update);
export function runAnimation(root, elapsed) {
    updaters.get(root.userData.animation?.kind)?.(root, elapsed);
}
