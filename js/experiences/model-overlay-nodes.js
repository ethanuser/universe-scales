// Overlay conventions read by ModelStage.finish() (set on any node's userData,
// including glTF `extras`, which three.js copies there):
//   screenLine = { axis: 'x' | 'y' | 'z', length }  box redrawn at a constant pixel width
//   label = text, labelClass = extra CSS class, labelVector = true  upright SVG text (with a vector arrow)
//   outline = true (with sphere = true)  thin SVG circle around a unit-sphere node
//   pointSize = { max, perPixel }  Points size follows the drawn model size
import * as THREE from '../vendor/three/three.module.min.js';

export const SCREEN_LINE_PX = 1.4;
const lineMaterials = new Map();
const unitBox = () => (unitBox.geometry ||= new THREE.BoxGeometry(1, 1, 1));
export function screenLine(axis, length, position, color = 0xffffff) {
    if (!lineMaterials.has(color)) lineMaterials.set(color, new THREE.MeshBasicMaterial({ color }));
    const mesh = new THREE.Mesh(unitBox(), lineMaterials.get(color));
    mesh.position.copy(position);
    mesh.userData.screenLine = { axis, length };
    mesh.scale.set(axis === 'x' ? length : 1e-6, axis === 'y' ? length : 1e-6, axis === 'z' ? length : 1e-6);
    return mesh;
}
export function labelNode(text, position, labelClass) {
    const node = new THREE.Object3D();
    node.position.copy(position);
    node.userData.label = text;
    if (labelClass) node.userData.labelClass = labelClass;
    return node;
}
