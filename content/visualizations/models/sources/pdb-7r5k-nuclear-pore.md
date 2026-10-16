# Nuclear Pore Complex: PDB 7R5K

Full eightfold assembly of PDB 7R5K, a constricted human nuclear pore scaffold modeled integratively using cryo-electron tomography and predicted protein structures. A deliberately coarse C-alpha envelope, colored by nucleoporin entity, preserves the central channel and deposited eightfold transforms. Disordered transport barrier, nuclear membranes and unresolved basket/filaments are absent. It is not an atomically resolved complete pore.

## Source and rights

- [RCSB PDB 7R5K entry](https://www.rcsb.org/structure/7R5K): Human nuclear pore complex (constricted).
- Mosalaganti, S., Obarska-Kosinska, A., Siggel, M., Taniguchi, R., Turonova, B., Zimmerli, C.E., Buczak, K., Schmidt, F.H., Margiotta, E., Mackmull, M.T., Hagen, W.J.H., Hummer, G., Kosinski, J., Beck, M.. AI-based structure prediction empowers integrative structural analysis of human nuclear pores. (2022). [Science](https://doi.org/10.1126/science.abm9506).
- [Original coordinate download](https://files.rcsb.org/download/7R5K.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `49c272f79bc55af95b846b6ffe6ebf9cd401f478abb82cdfe53ba13ea057fd2a`.
- Retained coordinate derivative: `bio3d/7R5K.npz`; matching metadata and assembly operations: `bio3d/7R5K.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 120` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models nuclear-pore
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 7R5K --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-7r5k-nuclear-pore.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
