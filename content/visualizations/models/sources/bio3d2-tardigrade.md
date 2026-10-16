# Tardigrade — native-scale nano-CT cutaway

## Source, permission and specimen

- [Gross et al. (2019), X-ray imaging of a water bear offers a new look at tardigrade internal anatomy](https://doi.org/10.1186/s40851-019-0130-6), Zoological Letters 5:14. This is one fixed/dried **Hypsibius exemplaris**. Its published **152 µm anterior-to-posterior body length excludes the fourth leg pair**. It is a small specimen; fixation/drying can shrink tissue.
- [Tardigraph resources](https://tardigraph.meow-meow.io/resources/), by **Meow-Ludo / Tardigraph**: CT-traced external surface and organ meshes derived from Gross et al.’s whole-body label fields, supplied in µm under **CC BY 4.0**. The resources page explicitly permits modification and redistribution with both project and original-data credits. [Their tracing method](https://tardigraph.meow-meow.io/xray/) documents the mounting-film removal and limitations.
- Raw derivative GLB: <https://tardigraph.meow-meow.io/resources/files/tardigrade-organs-glb.glb>. Pinned URL, bytes, SHA-256, license and unit record: [bio3d2/tardigrade.json](bio3d2/tardigrade.json). The large upstream file stays outside the repository.

## What is shown

The whole-body organ meshes retain their common coordinates: gut, pharynx, buccal tube, esophagus, ovary, storage cells, tubules, ganglia/connectives and other annotated structures. Tardigraph's probable identifications remain interpretive; no new identification is asserted here. We omit all meshes from the independently registered head scan, including its brain and salivary glands, avoiding dependence on its inferred head voxel calibration. No muscles from a different specimen are mixed in.

The dorsal/front quarter of the CT-derived body shell is removed for inspection. This is an authored viewing opening, not missing cuticle in the animal. Organs are not repositioned, rescaled or mirrored. False colours distinguish structures; they do not represent pigments. Meshes are simplified separately and normals recomputed. The shell is a two-sided surface with an open cut, not a volumetrically certified cuticle layer. Claws and fine detail remain limited by tracing, scan resolution and simplification.

The full mesh spans about 164 µm, including the retained legs. `reference_size: 152` measures the published body length, rather than fitting that full box. Units remain µm.

## Required dataset integration

**Before publishing this model, change the Tardigrade item from the generic 500 µm to this specimen’s 152 µm body length.** Exact YAML/plaque wording is supplied in [REPORT.md](../../../../handoff/bio3d2/REPORT.md). Neither the model nor its reference should be enlarged to 500 µm. There is no changeset touching the protected dataset or exports in this worktree.

## Offline rebuild

Download the pinned source to `/tmp/bio3d2/tardigrade.glb` separately, then:

```sh
./venv/bin/python scripts/build_bio3d2_tardigrade.py /tmp/bio3d2/tardigrade.glb /tmp/bio3d2/bio3d2-tardigrade.glb
```

The builder rejects a changed source hash and retains only whole-body meshes. It uses the repo’s existing offline simplifier and recomputes unit normals. Final registry JSON, CPU previews, validation and integration notes are in `handoff/bio3d2/`. CPU preview rotation/lighting is not production WebGL approval.
