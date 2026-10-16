#!/usr/bin/env python3
"""Build a real FlyWire v783 skeleton sample, in micrometres.

Preparation (pyarrow is needed only here; keep the 5.4 GB input outside the repo):
  python scripts/build_flybrain_model.py prepare --parquet /tmp/sk.parquet \
      --annotations /tmp/annotations.tsv --cache /tmp/flybrain.npz
Rendering (numpy/scipy/scikit-image, no network or pyarrow required):
  python scripts/build_flybrain_model.py build --cache /tmp/flybrain.npz \
      --output-dir /tmp/flybrain

Exact inputs, licenses, interpretation and registration: sources/flybrain.md.
The envelope is a skeleton-density isosurface, NOT a segmented brain membrane.
Lines are within-neuron paths, NOT synaptic edges between neurons.
"""
import argparse
import collections
import colorsys
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
from skimage import measure

from fetch_model_assets import pack_glb, inspect_glb
from geo_glb_common import GLB

MODEL_ID = "fruit-fly-brain-flywire"
PARQUET_MD5 = "a4c104776f33ec539ef859064c4de3df"
ANNOTATIONS_SHA256 = "30be6c73975a70c56d930e27911f36455d3886e15abf383b78edd2a5d679e0b6"
ANNOTATIONS_URL = ("https://media.springernature.com/original/springer-static/esm/"
                   "art%3A10.1038%2Fs41586-024-07686-5/MediaObjects/"
                   "41586_2024_7686_MOESM5_ESM.tsv")
QUOTAS = {"optic": 1000, "central": 700, "visual_projection": 400,
          "visual_centrifugal": 100}
PALETTE = {"optic": (0.24, 0.65, 1.0), "central": (1.0, 0.69, 0.28),
           "visual_projection": (0.68, 0.40, 1.0),
           "visual_centrifugal": (1.0, 0.32, 0.61)}
# All grid coordinates/lengths are micrometres; zeros outside this grid are checked.
ORIGIN = np.array([60., 20., -10.])
VOXEL = 2.0
SHAPE = (441, 231, 156)
COLUMNS = ["neuron", "node_id", "parent_id", "radius", "x", "y", "z"]


def digest(path, kind="sha256"):
    h = hashlib.new(kind)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def parent_indices(node, parent):
    """Resolve SWC identifiers, never treating an absent parent as another vertex."""
    index = np.searchsorted(node, parent)
    safe = np.minimum(index, len(node) - 1)
    return np.where((parent >= 0) & (index < len(node)) & (node[safe] == parent), safe, -1)


def rdp(points, tolerance=1.0):
    """Indices on a polyline; endpoints survive and chords deviate <= tolerance."""
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        delta = points[b] - points[a]
        length2 = delta @ delta
        middle = points[a + 1:b]
        t = np.clip((middle - points[a]) @ delta / length2, 0, 1) if length2 else np.zeros(len(middle))
        distance = np.linalg.norm(middle - (points[a] + t[:, None] * delta), axis=1)
        k = int(np.argmax(distance))
        if distance[k] > tolerance:
            k += a + 1
            keep.add(k)
            stack.extend([(a, k), (k, b)])
    return np.array(sorted(keep), dtype=np.int64)


def simplify_tree(xyz, node, parent, radius, tolerance=1.0, prune=7.0, max_segments=None):
    """Remove short terminal subtrees, simplify only chains between branch points.

    Source edges healed by the authors remain as published. We add no graph edges
    between neurons, or between disconnected source components. No fake jitter.
    """
    order = np.argsort(node)
    xyz, node, parent, radius = (a[order] for a in (xyz, node, parent, radius))
    if np.any(np.diff(node) == 0):
        raise ValueError("Duplicate node IDs in a source skeleton")
    pi = parent_indices(node, parent)
    has = pi >= 0
    length = np.zeros(len(node))
    length[has] = np.linalg.norm(xyz[has] - xyz[pi[has]], axis=1)
    # Topological leaf-to-root traversal also validates that the source is a forest.
    children = np.bincount(pi[has], minlength=len(node))
    pending = children.copy()
    queue = collections.deque(np.flatnonzero(pending == 0).tolist())
    cable = length.copy()
    visited = 0
    while queue:
        i = queue.popleft()
        visited += 1
        p = pi[i]
        if p >= 0:
            cable[p] += cable[i]
            pending[p] -= 1
            if pending[p] == 0:
                queue.append(p)
    if visited != len(node):
        raise ValueError("Cyclic skeleton")
    while True:
        alive = (cable >= prune) | ~has
        children = np.bincount(pi[has & alive], minlength=len(node))
        critical = alive & ((children != 1) | ~has)
        chains = []
        for child in np.flatnonzero(critical & has):
            chain = [child]
            p = pi[child]
            while p >= 0 and not critical[p]:
                chain.append(p)
                p = pi[p]
            if p >= 0:
                chain.append(p)
            chain = np.array(chain)
            chain = chain[rdp(xyz[chain], tolerance)]
            chains.extend(zip(chain[:-1], chain[1:]))
        if max_segments is None or len(chains) <= max_segments:
            break
        prune *= 1.4
    if not chains:
        return np.empty((0, 3)), np.empty((0, 2), dtype=np.int64), np.empty(0)
    edges = np.array(chains)
    used, inverse = np.unique(edges, return_inverse=True)
    return xyz[used], inverse.reshape(-1, 2), radius[used]


def select_neurons(annotations):
    """Deterministic type/side round robin; aesthetic diversity, not a census."""
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    with Path(annotations).open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            sc = row["super_class"]
            if sc not in QUOTAS or row.get("status"):
                continue
            key = (row["side"], row["cell_type"] or row["cell_class"])
            groups[sc][key].append(row)
    selected = {}
    for sc, quota in QUOTAS.items():
        bins = groups[sc]
        rank = lambda row: hashlib.sha256(("flybrain-v1:" + row["root_id"]).encode()).digest()
        for rows in bins.values():
            rows.sort(key=rank)
        keys = sorted(bins, key=lambda key: hashlib.sha256(repr(key).encode()).digest())
        count = 0
        depth = 0
        while count < quota:
            progress = False
            for key in keys:
                if depth < len(bins[key]) and count < quota:
                    row = bins[key][depth]
                    selected[int(row["root_id"])] = row
                    count += 1
                    progress = True
            if not progress:
                break
            depth += 1
    return selected


def prepare(args):
    import pyarrow.parquet as pq
    if digest(args.parquet, "md5") != PARQUET_MD5:
        raise ValueError("Skeleton file does not match the publisher's MD5; do not use a partial download")
    if digest(args.annotations) != ANNOTATIONS_SHA256:
        raise ValueError("Annotations do not match the 2024 published supplement")
    selected = select_neurons(args.annotations)
    density = np.zeros(SHAPE, np.float64)
    sample = {}
    population = 0
    # Carry the final neuron so no source graph is broken at a batch boundary.
    carry = None
    for batch in pq.ParquetFile(args.parquet).iter_batches(batch_size=1_000_000, columns=COLUMNS):
        current = {k: batch.column(k).to_numpy(zero_copy_only=False) for k in COLUMNS}
        if carry is not None:
            current = {k: np.concatenate([carry[k], current[k]]) for k in COLUMNS}
        cuts = np.flatnonzero(np.diff(current["neuron"]) != 0) + 1
        if not len(cuts):
            carry = current
            continue
        last = cuts[-1]
        carry = {k: v[last:] for k, v in current.items()}
        current = {k: v[:last] for k, v in current.items()}
        population += consume(current, selected, sample, density)
    if carry:
        population += consume(carry, selected, sample, density)
    if set(sample) != set(selected):
        raise ValueError(f"Missing selected neurons: {set(selected) - set(sample)}")
    ids, offsets, edge_offsets, vertices, edges, radii = [], [0], [0], [], [], []
    for identifier, (xyz, links, radius) in sorted(sample.items()):
        ids.append(identifier)
        vertices.append(xyz.astype(np.float32))
        edges.append(links.astype(np.uint32) + offsets[-1])
        radii.append(radius.astype(np.float32))
        offsets.append(offsets[-1] + len(xyz))
        edge_offsets.append(edge_offsets[-1] + len(links))
    metadata = {"source_md5": PARQUET_MD5, "annotations_sha256": digest(args.annotations),
                "annotations_url": ANNOTATIONS_URL, "population_skeletons": population,
                "quotas": QUOTAS, "rdp_tolerance_um": 1.0, "terminal_pruning_start_um": 7.0,
                "max_segments_per_neuron": {"optic": 55, "central": 70, "visual_projection": 100, "visual_centrifugal": 100},
                "selected": [{k: selected[i][k] for k in ("root_id", "super_class", "cell_class", "cell_type", "side")} for i in ids]}
    np.savez_compressed(args.cache, xyz=np.concatenate(vertices), edges=np.concatenate(edges),
                        radius=np.concatenate(radii), offsets=offsets, edge_offsets=edge_offsets,
                        density=density.astype(np.float32), metadata=json.dumps(metadata))
    print(f"Prepared {len(ids)} neurons / {edge_offsets[-1]:,} line segments; {population:,} source skeletons", flush=True)


def consume(data, selected, sample, density):
    """Accumulate intrinsic-neuron cable density and the selected real trees."""
    neuron = data["neuron"]
    starts = np.r_[0, np.flatnonzero(np.diff(neuron) != 0) + 1]
    ends = np.r_[starts[1:], len(neuron)]
    # Four intrinsic superclasses: no peripheral nerves define the envelope.
    for start, end in zip(starts, ends):
        identifier = int(neuron[start])
        if identifier not in selected:
            continue
        if identifier in sample:
            raise ValueError("A selected neuron recurs noncontiguously in the source file")
        xyz = np.column_stack([data[k][start:end] for k in "xyz"]).astype(np.float64) / 1000
        node, parent = (data[k][start:end] for k in ("node_id", "parent_id"))
        radius = data["radius"][start:end].astype(np.float64) / 1000
        cap = {"optic": 55, "central": 70, "visual_projection": 100, "visual_centrifugal": 100}
        sample[identifier] = simplify_tree(xyz, node, parent, radius, max_segments=cap[selected[identifier]["super_class"]])
        # Density uses the UNSIMPLIFIED sample, with edge-length weights.
        order = np.argsort(node)
        pi = parent_indices(node[order], parent[order])
        p = xyz[order]
        has = pi >= 0
        midpoint = (p[has] + p[pi[has]]) / 2
        weight = np.linalg.norm(p[has] - p[pi[has]], axis=1)
        grid = np.floor((midpoint - ORIGIN) / VOXEL).astype(int)
        valid = ((grid >= 0) & (grid < np.array(SHAPE))).all(axis=1)
        if not valid.all():
            raise ValueError("Source sample falls outside the density grid")
        np.add.at(density, tuple(grid.T), weight)
    return len(starts)


def model_coordinates(xyz):
    """Rigid 180-degree X rotation plus translation; one model unit = 1 um."""
    return (xyz - np.array([525., 250., 140.])) * np.array([1., -1., -1.])


def build(args):
    cache = np.load(args.cache, allow_pickle=False)
    meta = json.loads(str(cache["metadata"]))
    xyz, edges, radius = cache["xyz"], cache["edges"], cache["radius"]
    positions = model_coordinates(xyz)
    field = ndimage.gaussian_filter(cache["density"], sigma=2.5)
    # Visual context only. This level/smoothing is not an anatomical measurement.
    level = field.max() * 0.012
    sv, faces, _, _ = measure.marching_cubes(field, level, spacing=(VOXEL,) * 3, step_size=4)
    sv = model_coordinates(sv + ORIGIN)
    # Coordinates are never stretched to match either envelope or data item.
    g = GLB("Universe Scales FlyWire v783 skeleton sample")
    g.doc["asset"]["copyright"] = ("FlyWire Consortium; Schlegel, Jefferis et al. (2024), CC BY 4.0 "
                                   "via Zenodo 10877326. Simplification and density envelope: Universe Scales.")
    g.doc["extensionsUsed"] = ["KHR_materials_unlit", "KHR_mesh_quantization"]
    g.doc["extensionsRequired"] = ["KHR_mesh_quantization"]
    all_positions = np.concatenate([sv, positions])
    center = (all_positions.min(axis=0) + all_positions.max(axis=0)) / 2
    half = np.max(np.ptp(all_positions, axis=0)) / 2 * 1.001

    def draw(name, vertices, indices, material, mode, colours=None):
        """8-byte normalized SHORT positions; rigid units restored on each node."""
        q = np.round((vertices - center) / half * 32767).astype(np.int16)
        padded = np.zeros((len(q), 4), np.int16)
        padded[:, :3] = q
        pos = g._accessor(padded, 5122, "VEC3", 34962)
        g.doc["accessors"][pos].update(normalized=True, min=q.min(axis=0).tolist(), max=q.max(axis=0).tolist())
        g.doc["bufferViews"][g.doc["accessors"][pos]["bufferView"]]["byteStride"] = 8
        attributes = {"POSITION": pos}
        if colours is not None:
            c = np.round(np.clip(colours, 0, 1) * 255).astype(np.uint8)
            colour = g._accessor(c, 5121, "VEC4", 34962)
            g.doc["accessors"][colour]["normalized"] = True
            attributes["COLOR_0"] = colour
        indices = np.asarray(indices).ravel()
        small = indices.max() < 65535
        ix = g._accessor(indices.astype(np.uint16 if small else np.uint32), 5123 if small else 5125, "SCALAR", 34963)
        g.mesh_node(name, [{"attributes": attributes, "indices": ix, "mode": mode, "material": material}])
        g.doc["nodes"][-1].update(translation=center.tolist(), scale=[float(half)] * 3)
    line_mat = g.material("Neuronal paths · categorical colours", blend=True)
    g.doc["materials"][line_mat]["extensions"] = {"KHR_materials_unlit": {}}
    shell_mat = g.material("Smoothed sampled-skeleton density envelope", color=(0.20, 0.37, 0.62, 0.065), blend=True)
    draw("Derived density envelope (not a segmented membrane)", sv, faces, shell_mat, 4)
    rng = np.random.default_rng(19)
    by_class = collections.defaultdict(list)
    for index, row in enumerate(meta["selected"]):
        by_class[row["super_class"]].append(index)
    for sc, neurons in by_class.items():
        verts, links, colours = [], [], []
        offset = 0
        part = 1
        for index in neurons:
            a, b = cache["offsets"][index:index + 2]
            ea, eb = cache["edge_offsets"][index:index + 2]
            p = positions[a:b]
            if offset + len(p) > 60000 and verts:
                draw(f"{sc} paths {part}", np.concatenate(verts), np.concatenate(links), line_mat, 1, np.concatenate(colours))
                verts, links, colours, offset = [], [], [], 0
                part += 1
            h, s, v = colorsys.rgb_to_hsv(*PALETTE[sc])
            rgb = np.array(colorsys.hsv_to_rgb((h + rng.uniform(-0.025, 0.025)) % 1, s, v))
            linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055)**2.4)
            brightness = 0.48 + 0.52 * np.clip(radius[a:b] / .4, 0, 1)**.6
            c = np.ones((len(p), 4))
            c[:, :3] = linear[None, :] * brightness[:, None]
            c[:, 3] = .72
            verts.append(p)
            links.append(edges[ea:eb] - a + offset)
            colours.append(c)
            offset += len(p)
        draw(f"{sc} paths {part}", np.concatenate(verts), np.concatenate(links), line_mat, 1, np.concatenate(colours))
        g.doc["nodes"][-1]["extras"] = {"superClass": sc, "neuronCount": len(neurons)}
    ruler = g.material("100 micrometre scale", color=(.56, .66, .78, 1))
    g.doc["materials"][ruler]["extensions"] = {"KHR_materials_unlit": {}}
    ruler_y = float(positions[:, 1].min()) - 20
    ruler_positions = np.array([[200, ruler_y + 4, 0], [200, ruler_y, 0],
                                [300, ruler_y, 0], [300, ruler_y + 4, 0]])
    draw("100 micrometre ruler", ruler_positions, [0, 1, 1, 2, 2, 3], ruler, 1)
    g.label_node("Scale label", [250, ruler_y - 15, 0], "100 µm",
                 labelAxis={"axis": "x", "length": 100, "minPixelLength": 40})
    g.doc["extras"] = {"units": "micrometres", "source": "https://doi.org/10.5281/zenodo.10877326",
                         "license": "CC-BY-4.0", "neuronCount": len(meta["selected"]),
                         "semantics": "sampled neuron morphology; lines do not encode synaptic connectivity"}
    for key in ("images", "textures", "samplers"):
        if not g.doc[key]:
            del g.doc[key]
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    payload = pack_glb(g.doc, g.bin)
    path = output / f"{MODEL_ID}.glb"
    path.write_bytes(payload)
    entry = {"id": MODEL_ID, "matches": {"length": ["Fruit Fly Brain"]},
             "source": "https://zenodo.org/records/10877326",
             "basis_url": "https://doi.org/10.1038/s41586-024-07686-5",
             "basis_label": "Schlegel et al. (2024): annotation and skeletonization",
             "author": "FlyWire Consortium; Schlegel, Jefferis et al. (2024); adaptation: Universe Scales",
             "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
             "license_files": ["licenses/CC-BY-4.0.txt"],
             "geometry": "lines_and_density_envelope", "representation": "scientific_reconstruction",
             "volume_semantics": "not_applicable", "closed_volume_checked": False,
             "presentation": {"reference_size": 800, "yaw": -12, "pitch": 10, "focus_scale_factor": 1.35},
             "note": (f"{len(meta['selected']):,} real FlyWire v783 neurons, sampled across both optic lobes and central brain. "
                      "Blue: optic; amber: central; violet: visual projection; pink: visual centrifugal. "
                      "Simplified centreline paths in true micrometres; line thickness and colours are for visibility. "
                      "The faint shell is a smoothed density envelope of this sample, not a segmented membrane. "
                      "This is a small morphological sample of the whole-brain connectome, not its full synapse graph; "
                      "crossing lines do not imply synapses. Approximately 800 µm across the sampled optic lobes, including lamina."),
             "processing": {"script": "scripts/build_flybrain_model.py", "source_md5": PARQUET_MD5,
                            "cache_sha256": digest(args.cache), "annotations_sha256": meta["annotations_sha256"],
                            "neuron_count": len(meta["selected"]), "line_segments": len(edges),
                            "rdp_tolerance_um": 1.0, "terminal_pruning_start_um": 7.0,
                            "max_segments_per_neuron": meta["max_segments_per_neuron"],
                            "density_voxel_um": VOXEL, "density_sigma_voxels": 2.5,
                            "density_relative_isovalue": .012, "density_surface_step_voxels": 4, "units": "micrometres",
                            "source_notes": "content/visualizations/models/sources/flybrain.md"}}
    entry.update(inspect_glb(payload))
    (output / f"{MODEL_ID}.entry.json").write_text(json.dumps(entry, indent=2) + "\n")
    (output / "sample.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"bytes": len(payload), "segments": len(edges), "sample_extent_um": np.ptp(positions, axis=0).tolist(),
                      "envelope_extent_um": np.ptp(sv, axis=0).tolist()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--parquet", required=True)
    prep.add_argument("--annotations", required=True)
    prep.add_argument("--cache", required=True)
    out = commands.add_parser("build")
    out.add_argument("--cache", required=True)
    out.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else build)(args)


if __name__ == "__main__":
    main()
