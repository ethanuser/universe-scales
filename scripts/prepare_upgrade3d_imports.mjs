#!/usr/bin/env node
// Process an existing CC-BY photoscan. No new surface or texture artwork.
// node scripts/prepare_upgrade3d_imports.mjs STAGED_DIR OUTPUT_DIR MODULE_ROOT
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const [staged, output, modules] = process.argv.slice(2);
if (!staged || !output || !modules) throw new Error('Expected STAGED_DIR OUTPUT_DIR MODULE_ROOT');
const moduleAt = relative => import(pathToFileURL(path.resolve(modules, relative)).href);
const { NodeIO } = await moduleAt('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await moduleAt('@gltf-transform/extensions/dist/index.js');
const { metalRough, dedup, flatten, join, weld, prune, quantize } =
    await moduleAt('@gltf-transform/functions/dist/index.js');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const uid = '008e9eacb9044b11b358a0c2bdae1934';
const metadata = JSON.parse(fs.readFileSync(path.join(staged, `${uid}.json`)));
const file = path.join(staged, `${uid}.glb`);
const hash = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
if (metadata.uid !== uid || metadata.author !== 'robin.sculac' || metadata.license !== 'by'
    || metadata.texture_size !== 1024
    || metadata.source_sha256 !== 'e9808befbc1d65281c7598e758edb1fc03d0f8435fad44c10aa69e161396ea0b'
    || hash !== '83fbb446e3c60921548e74188597dfaffe2e6ae170d1d933c2e9f9aab3d4d626')
    throw new Error('Staged scan identity/license/hash differs from reviewed source');
const doc = await io.read(file);
if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
    throw new Error('Expected a static scan');
// Convert the source's legacy specular/glossiness material, preserving its
// photographed color. The runtime and CPU reviewer can then use standard PBR.
await doc.transform(metalRough(), dedup(), flatten(), join(), weld(), prune(),
    quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }));
fs.mkdirSync(output, { recursive: true });
const destination = path.join(output, 'upgrade3d-basketball-scan.glb');
await io.write(destination, doc);
const bytes = fs.statSync(destination).size;
if (bytes > 3000000) throw new Error('Asset exceeds 3 MB');
console.log(`upgrade3d-basketball-scan: ${bytes.toLocaleString()} bytes`);
