// Validate all delivered GLBs, including Neptune's deliberately unregistered asset.
const fs = require('node:fs');
const path = require('node:path');
const validator = require(process.argv[2] || 'gltf-validator');
const root = path.resolve(__dirname, '..');
const handoff = path.join(root, 'handoff/space3d3');

async function main() {
    const models = [];
    for (const file of fs.readdirSync(handoff).filter(f => f.endsWith('.entry.json')).sort()) {
        const entry = JSON.parse(fs.readFileSync(path.join(handoff, file)));
        const bytes = fs.readFileSync(path.join(root, entry.src));
        const result = await validator.validateBytes(new Uint8Array(bytes), { uri: entry.id, maxIssues: 1000 });
        models.push({ id: entry.id, sha256: entry.sha256, issues: result.issues, info: result.info });
        console.log(`${entry.id}: ${result.issues.numErrors} errors, ${result.issues.numWarnings} warnings`);
    }
    fs.writeFileSync(path.join(handoff, 'gltf-validation.json'), JSON.stringify({
        validator: 'Khronos glTF Validator', version: validator.version(), models
    }, null, 2) + '\n');
    if (models.some(m => m.issues.numErrors || m.issues.numWarnings)) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
