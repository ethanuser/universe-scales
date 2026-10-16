# Tobacco Mosaic Virus: PDB 2TMV

A 300 nm-long flat-cut lattice reconstruction from PDB 2TMV protein and RNA coordinates and its deposited helical symmetry. The coat is teal and the RNA amber. The central channel and repeating surface follow the structural coordinates. This representative rod length uses repeated structural subunits; the two end planes are authored cuts, not experimentally reconstructed virion ends. The smooth display surface does not resolve individual atoms.

## Source and rights

- [RCSB PDB 2TMV entry](https://www.rcsb.org/structure/2TMV): VISUALIZATION OF PROTEIN-NUCLEIC ACID INTERACTIONS IN A VIRUS. REFINED STRUCTURE OF INTACT TOBACCO MOSAIC VIRUS AT 2.9 ANGSTROMS RESOLUTION BY X-RAY FIBER DIFFRACTION.
- Namba, K., Pattanayek, R., Stubbs, G.. Visualization of protein-nucleic acid interactions in a virus. Refined structure of intact tobacco mosaic virus at 2.9 A resolution by X-ray fiber diffraction. (1989). [J.Mol.Biol.](https://doi.org/10.1016/0022-2836(89)90391-4).
- [Original coordinate download](https://files.rcsb.org/download/2TMV.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `fede46c1b745eb14de56ffc9529b8020c03855cdd51ec27d4cafb35bb85a9da9`.
- Retained coordinate derivative: `bio3d/2TMV.npz`; matching metadata and assembly operations: `bio3d/2TMV.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 300` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models tmv
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 2TMV --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-2tmv-tmv.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
