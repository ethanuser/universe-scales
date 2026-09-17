// Usage: node validate-models.cjs /path/to/node_modules/gltf-validator
// Install the validator outside the repository; this only writes validation.json.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const validator = require(process.argv[2] || 'gltf-validator');

async function main() {
    const registry = JSON.parse(fs.readFileSync(path.join(__dirname, '../models.json')));
    const results = [];
    for (const model of registry.models) {
        const bytes = fs.readFileSync(path.join(__dirname, path.basename(model.src)));
        const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
        if (sha256 !== model.sha256) throw new Error(`Stale registry hash: ${model.id}`);
        const report = await validator.validateBytes(new Uint8Array(bytes), {
            uri: path.basename(model.src),
            maxIssues: 1000
        });
        results.push({ id: model.id, sha256, issues: report.issues, info: report.info });
        console.log(`${model.id}: ${report.issues.numErrors} errors, ${report.issues.numWarnings} warnings`);
    }
    const report = {
        validator: 'Khronos glTF Validator',
        version: validator.version(),
        source: 'https://github.com/KhronosGroup/glTF-Validator',
        models: results
    };
    fs.writeFileSync(path.join(__dirname, 'validation.json'), JSON.stringify(report, null, 2) + '\n');
    if (results.some(result => result.issues.numErrors)) process.exitCode = 1;
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
