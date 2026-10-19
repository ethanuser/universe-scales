# T. rex: scan of a different skeleton replica scaled to SUE's size

This is [Rigsters' photogrammetric scan](https://sketchfab.com/3d-models/tyrannosaurus-rex-skeleton-77e21c4e5d65468bbe11780ae0557b95)
of a **Tyrannosaurus rex skeleton replica at Knuthenborg Safaripark, Denmark**.
It is not SUE, not a scan of SUE's fossils, and not Smithsonian's Wankel Rex.
The source does not identify the replica's underlying fossil specimen; none is
invented here. The user permitted another T. rex skeleton scaled to SUE's length.

## License and pinned inputs

The [Sketchfab API](https://api.sketchfab.com/v3/models/77e21c4e5d65468bbe11780ae0557b95)
was opened on 2026-10-18: `isDownloadable: true`, license slug `by`,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit Rigsters.
License and source manifests are in [earth3d4/](earth3d4/).

- Original glTF archive SHA-256:
  `8b9e4c5c9af64593eb2c44b920ce58fae1411501a6d0ee61e6034b9e05c04d16`.
- Packed staging GLB SHA-256:
  `7c5a120a081f6b0b3f574ce44807fd533933dccf8ea9d51bd506a7059da11e74`.
- Originals remain temporary build inputs outside the repository.

The [Smithsonian object page](https://www.si.edu/object/3d/tyrannosaurus-rex%3Ad8c62d28-4ebc-11ea-b77f-2e728ce88125)
was also opened: it currently restricts reuse of the 3D asset to noncommercial,
educational and personal purposes. Its **metadata** being CC0 does not establish
that the mesh is CC0. That candidate and a third-party reupload were not used.

## Measurement, limitations and processing

The [Field Museum's SUE page](https://www.fieldmuseum.org/blog/how-well-do-you-know-sue)
gives 40.5 feet in length, consistent with the catalog's approximate **12.3 m**.
The replica is uniformly scaled along its longitudinal skull-to-tail box after
a rigid 55-degree orientation about the vertical axis. Its own proportions and
posture remain intact; this is a representative size comparison with a different
replica, not a new measurement of SUE or a tracing of SUE's curved backbone.

The source was captured with 133 photographs in a rapid single loop, according
to Rigsters. It has holes and incomplete surfaces, particularly from the reverse
side. We retain those limitations rather than fabricate missing bones or fill
gaps with authored anatomy. No skeleton layout was authored for this job.

The offline preparer verifies pinned hashes, merges static mesh splits,
welds/decimates the existing surface toward 55,000 triangles with error limit
0.002, prunes and quantizes. Original texture colors and material are retained;
textures are resized to at most 1024 pixels during staging. No new geometry,
labels, skins, animation, or decoder compression is added.

Both sides were inspected in CPU previews. Those orthographic images do not
certify WebGL materials, the production size audit, the radial explorer or mobile.
