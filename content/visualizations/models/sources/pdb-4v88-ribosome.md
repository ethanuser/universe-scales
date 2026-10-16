# Ribosome: PDB 4V88

Author-defined biological assembly 1 of PDB 4V88: one yeast 80S ribosome, not the two particles in the asymmetric unit. Ribosomal RNA is gold; protein chains use a contrasting palette. Includes the deposited Stm1 protein; unmodeled residues, water and ions are omitted. Native coordinates are preserved, independently of the approximate 30 nm catalog value.

## Source and rights

- [RCSB PDB 4V88 entry](https://www.rcsb.org/structure/4V88): The structure of the eukaryotic ribosome at 3.0 A resolution..
- Ben-Shem, A., Garreau de Loubresse, N., Melnikov, S., Jenner, L., Yusupova, G., Yusupov, M.. The structure of the eukaryotic ribosome at 3.0 angstrom resolution. (2011). [Science](https://doi.org/10.1126/science.1212642).
- [Original coordinate download](https://files.rcsb.org/download/4V88.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `549c09673d17c603de0eba49ae6ed50830d4bbfecedb8dd765d8028e6276fd30`.
- Retained coordinate derivative: `bio3d/4V88.npz`; matching metadata and assembly operations: `bio3d/4V88.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 30` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models ribosome
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 4V88 --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-4v88-ribosome.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
