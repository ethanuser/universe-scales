const owners = new Map();
const retained = new WeakMap();

export function modelResources(model) {
    const resources = new Set();
    model.traverse(node => {
        if (node.geometry) resources.add(node.geometry);
        for (const material of [node.material].flat()) {
            if (!material) continue;
            resources.add(material);
            for (const value of Object.values(material)) {
                if (!value?.isTexture) continue;
                resources.add(value);
                const image = value.source?.data ?? value.image;
                if (!value.userData?.modelCachePersistent && image?.close) resources.add(image);
            }
        }
    });
    return resources;
}

// Estimated decoded buffers/texture storage, not the compressed GLB file size.
export function modelBytes(model) {
    const buffers = new Set();
    let bytes = 0;
    for (const resource of modelResources(model)) {
        if (resource.isBufferGeometry) {
            for (const attribute of [...Object.values(resource.attributes), resource.index,
                ...Object.values(resource.morphAttributes || {}).flat()]) {
                const buffer = (attribute?.array ?? attribute?.data?.array)?.buffer;
                if (!buffer || buffers.has(buffer)) continue;
                buffers.add(buffer);
                bytes += buffer.byteLength;
            }
        } else if (resource.isTexture) {
            const image = resource.source?.data ?? resource.image;
            bytes += (image?.data?.byteLength ?? ((image?.width || 0) * (image?.height || 0) * 4)) *
                (resource.generateMipmaps ? 4 / 3 : 1);
        }
    }
    return Math.ceil(bytes);
}

export function retainModelResources(model) {
    const resources = modelResources(model);
    retained.set(model, resources);
    for (const resource of resources) {
        if (resource.userData?.modelCachePersistent) continue;
        owners.set(resource, (owners.get(resource) || 0) + 1);
    }
    return model;
}

export function releaseModelResources(model) {
    const resources = retained.get(model);
    if (!resources) return;
    retained.delete(model);
    for (const resource of resources) {
        if (resource.userData?.modelCachePersistent) continue;
        const count = (owners.get(resource) || 0) - 1;
        if (count > 0) { owners.set(resource, count); continue; }
        owners.delete(resource);
        if (resource.dispose) resource.dispose();
        else resource.close?.();
    }
}
