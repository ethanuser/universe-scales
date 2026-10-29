# Volume Model Coverage and Source Review

**Checked:** 2026-10-29

**Scope:** Final production Volume export after integration of the seven
planetary observations.

No source model was imported or downloaded for this bounded continuation. The
candidate leads and dispositions below are from the existing source-review
record; they are not a claim that the internet was exhausted. JPL/NASA pages
were consulted only to verify the new planetary radius inputs and explanatory
facts.

## Coverage snapshot

Compared exact `name` values in `exports/json/dimensions/volume.json` against
`matches.volume` in `content/visualizations/models.json`. The final snapshot has
55 display items, 24 exact registered model matches, and 31 unmatched items.
All seven new planet observations are included and have exact registered matches.
The 31 unmatched names are listed exactly once in `ledger.json`, in production
export order. Candidate leads below are prior bounded source-review findings,
not assets downloaded or registered in this continuation.

The 24 exact matches include all seven planetary bodies, sourced Earth, Moon,
Jupiter and Sun models; the wine bottle, human body, mug, soda can, car, bucket,
glass, freight car, bus, shipping container and teaspoon; and the sand-grain and
red-blood-cell models. Bus and teaspoon entries in
`content/visualizations/models/sketchfab-volume.json` are already exact matches,
not gaps.

## Focused candidate review

### Great Pyramid of Giza volume

The dataset value is an approximate geometric envelope around 2.6 million m^3.
The Egyptian Ministry of Tourism and Antiquities gives the original height as
146.5 m; Harvard's Giza project discussion reports about 2.6 million m^3 of
material. A [CC BY Sketchfab model by consciousfractal](https://sketchfab.com/3d-models/giza-great-pyramid-khufu-papp-6ed9c8b0d7a14bce8ac8947b7550cbb9)
describes a procedural, watertight relief of the whole plateau and says its
Great Pyramid has a square plan and a Petrie-slope calibration (~51.844 degrees).
It also contains the Queen pyramids, Sphinx, causeway, temple and generated
terrain. The license is promising, but the current page does not establish an
isolated Khufu mesh, metric model units, or rights for the mentioned PAPP/Hopf-
derived surface details. **Do not import or claim its whole-scene enclosed
volume as the pyramid volume.** Isolate and inspect the original source scene,
verify all dependency rights, then measure only the pyramid shell against the
stated geometric-envelope convention. A normalized mesh volume would not by
itself validate the model's shape or source dimensions.

The earlier [ianicolo CC BY model](https://sketchfab.com/3d-models/the-great-pyramid-of-giza-4a251113722f4d969b6cf2ca5f35c502)
is photogrammetry from YouTube videos (about 360k triangles). The previous
source review found no reliable metric scale/completeness evidence, so it remains
rejected. Length's height-to-width screen-fit rule is irrelevant to this Volume
decision; no deformation or cropping is warranted.

### Bathtub and Bathtub volume

Both observations are water capacity (~0.15 m^3), not the solid material volume
of a tub. Public Sketchfab pages show authored CC BY bathtub props, including
[Aparicio Silva 3D's wooden tub](https://sketchfab.com/3d-models/wooden-bathtub-game-ready-asset-137881949bb14f78a0ac1fb4d6f3d2f1)
and [Igrium's photorealistic recreation](https://sketchfab.com/3d-models/photorealistic-bathtub-ba60ba7d0a4a4b6899021741f450395b).
Neither page provides metric dimensions or rated basin capacity. The source
does not pass a volume-calibrated mesh criterion. At most, a separately reviewed
and rights-verified tub asset may be tagged **capacity proxy** for a 150 L
representative fill; it must not be described as mesh-volume calibrated. The
[Museum of Engineering and Technology's photogrammetric tub](https://sketchfab.com/3d-models/freestanding-cast-iron-bathtub-6103df62a5a84bc2a391a3e4bab4f4ae)
is CC BY-NC-SA and is not eligible under the project's CC BY/CC0 source policy.

## Ledger interpretation and disposition

`no_qualified_model_identified` means no exact registered match or qualified
candidate surfaced in the bounded source/repository reviews represented here; it
does **not** claim no model exists anywhere. The ledger separately marks bathtub assets as
`illustrative_only_unregistered` and the broader PAPP pyramid scene as
`unregistered_candidate_requires_review`. It records the specific scientific
boundary or calibration issue per item, including capacity versus solid volume,
interior air versus exterior envelope, and modelled cosmic boundaries versus
observed 3D surfaces.

No GLB was acquired or staged. Neither focused candidate passed requirements
for a measurement-bearing new asset: the pyramid is not yet isolated/rights-
cleared at dependency level, and the bathtub assets have no scale/capacity
evidence and can only illustrate capacity. Accordingly, no `sourcevolume*`
builder/importer or model files were added. No registry, runtime, raw dataset,
export, or other integration files were edited.
