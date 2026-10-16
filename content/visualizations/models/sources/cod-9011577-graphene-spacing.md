# Graphene layer spacing: graphite neutron-diffraction lattice

Two small hexagonal windows show neighboring AB-stacked sheets; a neutral,
tick-ended ruler measures the separation of the nuclear planes. The layers
continue beyond the windows. These are not isolated benzene molecules. Tube
thickness and color are display choices, not electron-density measurements.

## Source and license

- [COD 9011577](https://www.crystallography.net/cod/9011577.html),
  [official CIF](https://www.crystallography.net/cod/9011577.cif).
- Trucano, P.; Chen, R. (1975), [Structure of graphite by neutron
  diffraction](https://doi.org/10.1038/258136a0), *Nature* 258, 136–137.
- The [Crystallography Open Database](https://www.crystallography.net/cod/)
  dedicates its data and database to CC0. Rights policy verified on the official
  COD information-card footer on 2026-10-16; the CIF was downloaded directly.
- The retained CIF in `bio3d/9011577.cif` omits only the upstream comment header.
  Its scientific fields, fractional sites and symmetry operations are retained.
  The entry's `retained_cif_sha256` pins this derivative.

The cell has a = b = 2.464 Å, c = 6.711 Å, gamma = 120 degrees, with the
neighboring planes at fractional c coordinates 1/4 and 3/4. The paper states
the ABAB stacking and fractional-site geometry. A regular hexagon has bond
length a/sqrt(3); translating the next layer by one bond gives AB stacking.
Plane separation c/2 = **0.33555 nm**, consistent with the catalog's approximate
0.335 nm. No artificial vertical exaggeration is applied. One model unit is
one nanometre; `reference_size: 0.335` preserves the existing catalog scale.

## Rebuild

```sh
./venv/bin/python scripts/build_graphene_spacing.py
./venv/bin/python scripts/preview_bio3d_cpu.py
```

The retained CIF is the offline input. To refresh it, download the official CIF
URL, retain its `data_9011577` block and review any changed crystallography before
rebuilding. Final entry JSON and rest/side CPU geometry previews are in
`handoff/bio3d/`; production WebGL, perspective and mobile checks remain pending
because Chromium is known sandbox-blocked in this worktree.
