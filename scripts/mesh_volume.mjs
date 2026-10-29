// Geometry-only audit using the same GLTFLoader as production. Does not edit meshes.
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import * as THREE from '../js/vendor/three/three.module.min.js';

export async function readScene(file) {
    const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
    const moduleURL = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
    const utilities = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/utils/BufferGeometryUtils.js', import.meta.url), 'utf8')
        .replace("from 'three'", `from '${threeURL}'`));
    const loaderURL = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/loaders/GLTFLoader.js', import.meta.url), 'utf8')
        .replace("from 'three'", `from '${threeURL}'`)
        .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
    globalThis.self = globalThis;
    // Texture decoding is irrelevant to geometric volume, not a material preview.
    globalThis.createImageBitmap = async () => ({ width: 1, height: 1, close() {} });
    globalThis.ProgressEvent ??= class { constructor(type, init) { Object.assign(this, init); } };
    const { GLTFLoader } = await import(loaderURL);
    const bytes = fs.readFileSync(file);
    const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
    if (gltf.animations.length) throw new Error('Animated scenes require a documented fixed-pose volume');
    return gltf.scene;
}

export function measureVolume(scene) {
    scene.updateMatrixWorld(true);
    const faces = [];
    scene.traverse(node => {
        if (node.isPoints || node.isLine || node.isSprite) throw new Error('Non-surface geometry');
        if (!node.isMesh) return;
        if (node.isSkinnedMesh || Object.keys(node.geometry.morphAttributes).length)
            throw new Error('Deformable geometry is not supported');
        const position = node.geometry.getAttribute('position'), index = node.geometry.index;
        const count = index ? index.count : position.count;
        if (count % 3) throw new Error('Incomplete triangle');
        for (let i = 0; i < count; i += 3) {
            const face = [0, 1, 2].map(k => new THREE.Vector3()
                .fromBufferAttribute(position, index ? index.getX(i + k) : i + k).applyMatrix4(node.matrixWorld));
            if (face.some(v => !v.toArray().every(Number.isFinite))) throw new Error('Non-finite vertex');
            // A reflected node reverses the baked winding, but not its solid orientation.
            if (node.matrixWorld.determinant() < 0) [face[1], face[2]] = [face[2], face[1]];
            faces.push(face);
        }
    });
    if (!faces.length) throw new Error('No surface triangles');
    const bounds = new THREE.Box3().setFromPoints(faces.flat());
    const extent = bounds.getSize(new THREE.Vector3()), origin = bounds.getCenter(new THREE.Vector3());
    const span = Math.max(...extent.toArray());
    if (!(span > 0)) throw new Error('Zero extent');
    // Weld seam copies for topology only. No coordinates or triangles are altered.
    const tolerance = span * 1e-7, vertices = [], buckets = new Map();
    function vertexId(point) {
        const cell = point.clone().sub(origin).divideScalar(tolerance).floor().toArray();
        for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
            const ids = buckets.get([cell[0] + x, cell[1] + y, cell[2] + z].join(','));
            for (const id of ids || []) if (vertices[id].distanceToSquared(point) <= tolerance ** 2) return id;
        }
        const id = vertices.length, key = cell.join(',');
        vertices.push(point);
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(id);
        return id;
    }
    const edges = new Map(), links = [], seenFaces = new Set();
    let signedVolume = 0;
    for (const face of faces) {
        const ids = face.map(vertexId);
        if (new Set(ids).size !== 3) throw new Error('Degenerate triangle');
        const faceKey = [...ids].sort((a, b) => a - b).join(',');
        if (seenFaces.has(faceKey)) throw new Error('Duplicate triangle');
        seenFaces.add(faceKey);
        const a = face[0].clone().sub(origin), b = face[1].clone().sub(origin), c = face[2].clone().sub(origin);
        if (b.clone().sub(a).cross(c.clone().sub(a)).lengthSq() <= (span ** 2 * 1e-14) ** 2)
            throw new Error('Zero-area triangle');
        signedVolume += a.dot(b.cross(c)) / 6;
        for (let k = 0; k < 3; k++) {
            const from = ids[k], to = ids[(k + 1) % 3], key = [Math.min(from, to), Math.max(from, to)].join(',');
            const edge = edges.get(key) || { count: 0, winding: 0 };
            edge.count++; edge.winding += from < to ? 1 : -1;
            edges.set(key, edge);
            (links[from] ||= new Set()).add(to); (links[to] ||= new Set()).add(from);
        }
    }
    if ([...edges.values()].some(e => e.count !== 2)) throw new Error('Surface is open or nonmanifold');
    if ([...edges.values()].some(e => e.winding !== 0)) throw new Error('Inconsistent surface winding');
    const visited = new Set(), stack = [0];
    while (stack.length) {
        const id = stack.pop();
        if (visited.has(id)) continue;
        visited.add(id);
        for (const next of links[id] || []) if (!visited.has(next)) stack.push(next);
    }
    if (visited.size !== vertices.length) throw new Error('Multiple shells require a separate overlap/cavity audit');
    const volume = Math.abs(signedVolume);
    if (!(volume > span ** 3 * 1e-12)) throw new Error('Zero enclosed volume');
    return { volume, referenceSize: Math.cbrt(volume), triangles: faces.length,
        weldedVertices: vertices.length, edges: edges.size, components: 1,
        boundaryEdges: 0, tolerance, extent: extent.toArray(),
        // Manifold topology alone does not establish absence of self-intersection.
        selfIntersectionChecked: false };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    for (const file of process.argv.slice(2)) {
        try { console.log(JSON.stringify({ file, ...measureVolume(await readScene(file)) }, null, 2)); }
        catch (error) { console.error(`${file}: ${error.message}`); process.exitCode = 1; }
    }
}
