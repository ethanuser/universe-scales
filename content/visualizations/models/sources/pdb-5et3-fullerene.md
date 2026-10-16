# Buckminsterfullerene: PDB 5ET3

Experimental C60 cage from the 60C ligand in PDB 5ET3. The thin atoms and bonds mark nuclear positions, not van der Waals radii; the listed 0.71 nm is a nucleus-to-nucleus cage diameter. The surrounding binding peptide is omitted.

## Source and rights

- [RCSB PDB 5ET3 entry](https://www.rcsb.org/structure/5ET3): Crystal Structure of De novo Designed Fullerene organizing peptide.
- Kim, K.-H., Ko, D.-K., Kim, Y.-T., Kim, N.H., Paul, J., Zhang, S.-Q., Murray, C.B., Acharya, R., DeGrado, W.F., Kim, Y.H., Grigoryan, G.. Protein-directed self-assembly of a fullerene crystal. (2016). [Nat Commun](https://doi.org/10.1038/ncomms11429).
- [Original coordinate download](https://files.rcsb.org/download/5ET3.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `7bc315ea040c2a7c5462eedbffb69a346fdbea5d3576d0198a99404da71ffbee`.
- Retained coordinate derivative: `bio3d/5ET3.npz`; matching metadata and assembly operations: `bio3d/5ET3.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 0.71` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models fullerene
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 5ET3 --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-5et3-fullerene.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
