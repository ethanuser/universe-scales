# Microtubule: PDB 6DPU

A 20 nm-long, flat-cut window through a reconstructed 14-protofilament GMPCPP microtubule lattice from PDB 6DPU. Alpha tubulin is teal and beta tubulin violet. Neighboring-protofilament and longitudinal transforms are fitted to matching deposited C-alpha coordinates. The seam is inferred; seam-specific conformations and disordered tails are unresolved. The generic 25 nm diameter is approximate; this in-vitro 14-protofilament example is wider than a common 13-protofilament cellular microtubule.

## Source and rights

- [RCSB PDB 6DPU entry](https://www.rcsb.org/structure/6DPU): Undecorated GMPCPP microtubule.
- Zhang, R., LaFrance, B., Nogales, E.. Separating the effects of nucleotide and EB binding on microtubule structure. (2018). [Proc. Natl. Acad. Sci. U.S.A.](https://doi.org/10.1073/pnas.1802637115).
- [Original coordinate download](https://files.rcsb.org/download/6DPU.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `609965497713f3f86d796167a80d02bbf1c02720951b0e6a8d00915ba5af8977`.
- Retained coordinate derivative: `bio3d/6DPU.npz`; matching metadata and assembly operations: `bio3d/6DPU.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 25` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models microtubule
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 6DPU --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-6dpu-microtubule.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
