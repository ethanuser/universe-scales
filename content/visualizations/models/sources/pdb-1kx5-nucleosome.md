# Nucleosome: PDB 1KX5

PDB 1KX5 nucleosome core particle: both 147-base DNA strands and all eight histones, including resolved histone tails. DNA is amber; histones are colored by chain. The approximate 11 nm value describes the DNA-wrapped disc; resolved tails extend beyond it. Unresolved residues, water and ions are omitted.

## Source and rights

- [RCSB PDB 1KX5 entry](https://www.rcsb.org/structure/1KX5): X-Ray Structure of the Nucleosome Core Particle, NCP147, at 1.9 A Resolution.
- Davey, C.A., Sargent, D.F., Luger, K., Maeder, A.W., Richmond, T.J.. Solvent Mediated Interactions in the Structure of the Nucleosome Core Particle at 1.9 A Resolution (2002). [J.Mol.Biol.](https://doi.org/10.1016/S0022-2836(02)00386-8).
- [Original coordinate download](https://files.rcsb.org/download/1KX5.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `a55dc600553caf7b7b14f217768fed1566c5101ab0543dc86895224238b284a0`.
- Retained coordinate derivative: `bio3d/1KX5.npz`; matching metadata and assembly operations: `bio3d/1KX5.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 11` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models nucleosome
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 1KX5 --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-1kx5-nucleosome.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
