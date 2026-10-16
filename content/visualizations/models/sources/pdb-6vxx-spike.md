# SARS-CoV-2 Spike: PDB 6VXX

PDB 6VXX closed prefusion spike ectodomain trimer, colored by protein chain, with only deposited glycan residues shown in gold. This engineered soluble construct resolves about 16 nm of the roughly 20 nm membrane-projecting spike; missing flexible stalk, membrane anchor and unresolved glycans are not invented. It is not the whole virus.

## Source and rights

- [RCSB PDB 6VXX entry](https://www.rcsb.org/structure/6VXX): Structure of the SARS-CoV-2 spike glycoprotein (closed state).
- Walls, A.C., Park, Y.J., Tortorici, M.A., Wall, A., McGuire, A.T., Veesler, D.. Structure, Function, and Antigenicity of the SARS-CoV-2 Spike Glycoprotein. (2020). [Cell](https://doi.org/10.1016/j.cell.2020.02.058).
- [Original coordinate download](https://files.rcsb.org/download/6VXX.cif.gz).
- [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies), opened 2026-10-16: PDB archive data are CC0 1.0. Original structural authors are credited. No article figures or PDB-101 artwork are redistributed.
- Original decompressed mmCIF SHA-256: `74ceac62dc45e34818f7c6f32fc12690f250ad803b999c1d7399a362ecd86984`.
- Retained coordinate derivative: `bio3d/6VXX.npz`; matching metadata and assembly operations: `bio3d/6VXX.json` in this directory.

## Geometry and calibration

One GLB unit is **one nanometre**. Retained PDB coordinates are in angstroms; conversion divides by ten, with rigid translations/rotations only. `presentation.reference_size = 20` nm corresponds to the existing catalog value. It is an explicit physical calibration, **not** a fitted bounding-box extent. The runtime multiplies by the item's value; changing that value without changing this reference would change the physical scale.

The molecular surfaces are authored display envelopes around coordinate sites, not experimental EM-density isosurfaces or solvent-accessible surfaces. Grid spacing, display-site radius and smoothing are recorded in the entry's `processing` object. The nearest coordinate site's chain/entity assigns vertex color. Colors have no observed-color meaning. Unresolved coordinates are left absent. The mesh is simplified with glTF Transform 4.5.0 (weld then simplify, maximum error setting 0.01 of mesh radius); normals are recomputed with outward, counterclockwise faces. There are no decoder extensions or network dependencies at runtime.

The fullerene is a thin bond cage instead of a surface; its 60 carbon sites form a validated 90-edge trivalent graph. The NPC deliberately uses C-alpha sites and a coarser display envelope. The actin and microtubule flat ends are segment cuts. TMV uses deposited screw symmetry with authored end planes. See the entry note for this model's specific limitations.

## Rebuild and verification

Offline (repo venv, cached glTF Transform CLI):

```sh
./venv/bin/python scripts/build_bio3d_models.py --models spike
./venv/bin/python scripts/preview_bio3d_cpu.py
```

Optional source refresh (network; full upstream files stay outside the repo):

```sh
./venv/bin/python scripts/prepare_bio3d_sources.py --pdb 6VXX --cache /tmp/bio3d-source
```

`handoff/bio3d/pdb-6vxx-spike.entry.json` is the final registry entry. Final GLB rest/side geometry previews and an orthographic size audit live in `handoff/bio3d/previews/`. They do not certify WebGL materials, camera perspective, hover behavior, or mobile rendering. Chromium and commits are known sandbox-blocked in this worktree; production `model_lab` checks remain for integration. Full check results and all skipped items are in `handoff/bio3d/REPORT.md`.
