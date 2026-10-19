# earth3d4 — public scans only, 2026-10-18

Branch: `codex/earth3d4`. **Two models registered; nineteen targets skipped.**
Every added surface comes from an existing CC BY scan. No geometry was authored,
no missing anatomy was invented, and no dataset, exports, images, runtime JS/CSS,
or other branch was edited. No packages were installed. Work is uncommitted for
the lead, as instructed for the known git sandbox limit; no commit was attempted.
The pre-existing `.DS_Store` modification and untracked `venv` symlink were left alone.

## Registered entries

| Item | Source / specimen | Delivered GLB | Triangles | Rest extent / value |
| --- | --- | ---: | ---: | ---: |
| Fruit Fly | ETAIN female *Drosophila melanogaster* micro-CT scan; Southampton laboratory specimen | 2,193,556 bytes | 89,963 | 1.185× |
| Tyrannosaurus Rex SUE | Rigsters scan of a different T. rex skeleton replica at Knuthenborg Safaripark, Denmark; uniformly scaled to SUE's catalog length | 1,897,736 bytes | 55,000 | 0.973× |

Both are new matches, not replacements. **The T. rex is not SUE.** The user
explicitly permitted another T. rex skeleton; the registry note and source document
identify this as a replica, whose underlying fossil identity is not established.
The replica has gaps from the source's rapid capture; they were not filled.

The fly's orange, translucent material comes from its CT author. It is not natural
color. The source pose, whole legs, wings and bristles are retained. Body calibration
uses vertices at the posterior abdomen tip and anterior head surface, not the
whole-animal bounding box. `fly-calibration.json` records the original source
coordinates and the 1.7721210623885464-source-unit reference; see the annotated
projection. This is a representative 2.5 mm scale assignment, not a measured
physical length reported for that particular laboratory individual. The fly
exceeds the ideal 60k-triangle target to retain the CT surface, but meets the
job's 3 MB limit; it is one draw call.

Source notes:

- [Fruit fly](../../content/visualizations/models/sources/earth3d4-fruit-fly.md).
- [T. rex replica](../../content/visualizations/models/sources/earth3d4-trex-skeleton.md).
- Pinned public license/staging manifests:
  `content/visualizations/models/sources/earth3d4/`.
- Final entries, including computed hashes/statistics:
  `earth3d4-fruit-fly.entry.json`, `earth3d4-trex-skeleton.entry.json`.

Licenses were checked directly in each Sketchfab model API on 2026-10-18;
both are downloadable with slug `by` (CC BY 4.0). Authenticated downloads use the
existing importer and the owner's external token file. Neither credentials nor
temporary signed download URLs were saved in the repository.

## Search coverage and skips

All 21 exact item names were checked against `models.json` before registration;
none already had a Length match. `model_lab coverage` unexpectedly launched
Chromium and failed with the documented `MachPortRendezvous ... Permission denied`
sandbox error. It was not retried. The registry was inventoried directly after
that failure. No existing model was redone.

Searches used the public Sketchfab API, including queries without the downloadable
filter to distinguish unavailable specimens from absent ones. Candidate detail
requests checked actual license slugs. Additional searches covered Smithsonian,
NIH, MorphoSource, NHM London, Wikimedia Commons, university resources, NCAR/UCAR,
IBHS, scientific papers and public AFM repositories. `search-audit.json` preserves
query counts and relevant API/license results. This is an acquisition audit, not
a claim that no suitable source exists anywhere.

| Skipped item | What was found / why it was not imported |
| --- | --- |
| Dust Mite | Sketchfab `dust mite` / `Dermatophagoides`, NIH and micro-CT searches. [paumarti's model](https://sketchfab.com/models/29ea8fe6ca89488db3affe730818b59d) is a cute stylized animal; the [Trnio capture](https://sketchfab.com/models/38d385d956044fa3a2e9d71bfa7d4e8c) appears to be a sculpture/decorative object, not a biological specimen. [Dermatophagoides](https://sketchfab.com/models/9a4d5dfa1d8e4165928d0aa6d7d54310) is NC-ND. NIH's result was an allergen protein, not a mite. No qualifying specimen surface obtained. |
| Cat Flea | [UF herpetology's real scan](https://api.sketchfab.com/v3/models/e343c81f94354dbaacb965d4381b60de) is downloadable but `by-nc`. Other `flea` hits were a vehicle or authored illustrations; no licensed CT/SEM specimen obtained. |
| Paedophryne Amauensis | [Actual LSUMZ95004 skeleton](https://api.sketchfab.com/v3/models/1c5be391573e4753917239ab091f2a2a) is not downloadable. [P. verrucosa](https://api.sketchfab.com/v3/models/e41959eb372f482380813a3323fbf9cb) is CC BY but only pelvis/hindlimb anatomy, not the complete 7.7 mm frog. Searched Microhyla, Gastrophryne, Kaloula, Microhylidae and MorphoSource; the [other microhylid CT mesh](https://api.sketchfab.com/v3/models/d95bbc16552c4f859fdc1409f4a709ad) also contains only pelvis/hindlimbs. MorphoSource's linked whole-volume route did not yield an accessible verified complete surface. Partial limbs were not scaled as whole frogs. |
| Bumblebee Bat | No downloadable match for `bumblebee bat` or `Craseonycteris thonglongyai`. Museum/research searches found skull, sternum or nasal-passage material and 2D illustrations, not an admissible complete scan calibrated to body length. No unrelated bat substituted. |
| Bee Hummingbird | No *Mellisuga helenae* scan obtained. The [Rudy27 hummingbird scan](https://api.sketchfab.com/v3/models/871c039a49d44adcbd0b1a4afa8c6bd6) appears to be a different hummingbird and its API does not establish it as this species. Other results were authored/animated birds or unavailable commercial assets. No species identity was invented. |
| Titan Beetle | Searched Titanus giganteus, museums and Sketchfab. [Domindik's Titanus](https://api.sketchfab.com/v3/models/b24ac5cea56e43f6b2ebe2ae43fa67e8) is not downloadable and uses a standard license. Other `Dorcus titanus` scans are stag beetles, not this longhorn beetle. No qualifying Titanus scan obtained. |
| Queen Alexandra's Birdwing | The [NHM/Adobe collection](https://data.nhm.ac.uk/dataset/the-art-of-3d-insects) describes assets made from image references and distributed through Adobe Stock. The [specific model](https://stock.adobe.com/in/3d-assets/ornithoptera-alexandrae/319491339) requires an Adobe license; CC0 catalog metadata is not a CC0 mesh grant. The portal API returned HTTP 403. Sketchfab's Cairn's birdwing is a different species and `by-sa`. No licensed scan obtained. |
| Meganeura | Searched Meganeura, Meganeuropsis and fossil/reconstruction scans. [The reconstruction with scholarly references](https://api.sketchfab.com/v3/models/e92f3170453345eca475776dfe1dedec) is not downloadable. Several nominal CC BY hits explicitly reupload Dinoraul/game assets; no verifiable source rights or fossil/reconstruction scan obtained. |
| Wandering Albatross | No downloadable exact match. [A CC BY museum scan](https://api.sketchfab.com/v3/models/7dcfe97830d64b1ba45492fca6dfc9b2) has folded wings and no species identification in the API. [The waved albatross scan](https://api.sketchfab.com/v3/models/408ddeff70f740e49c4e4a7c6c880e5c) is unavailable for download. The [Aves3D result](https://www.aves3d.org/specimens/37-Diomedea-nigripes/specimen_elements/50-Sternum) is an isolated sternum with no public STL. No wings were repositioned to invent a span. |
| Giant Pacific Octopus | [The exact species scan](https://api.sketchfab.com/v3/models/7fb48f6cbcd54149bb23837a3ac09b2e) is CC0 and was staged/inspected outside the repo. Its arms lie together behind the mantle. Posed whole length is not unfolded arm span; the source does not supply an arm-span calibration for that pose. [Monterey Bay Aquarium](https://www.montereybayaquarium.org/animals/animals-a-to-z/giant-pacific-octopus) explicitly defines span tip-to-tip. Do not calibrate this folded animal's box to the item's 4.3 m span. Nothing was registered. |
| Titanosaur Cast | [MebaLab's Patagotitan skeleton](https://api.sketchfab.com/v3/models/a48cde44e8a045d2968fca28ce62c7ae) is `by-sa`, outside this job's permitted licenses. [The landmark scan](https://api.sketchfab.com/v3/models/d32ebb0bac7f4ae983b6a6c558519934) is a fleshed statue, not a skeleton. [Carnegie Dreadnoughtus scans](https://api.sketchfab.com/v3/models/efd757df9f3e493e9e741971e63deeb8) are CC BY but incomplete/disarticulated, lacking the whole skull/neck/tail needed for the cast length. No missing skeleton was authored. |
| Giant Siphonophore | [MBARI's real Praya dubia scan](https://api.sketchfab.com/v3/models/1b68540b71fc435c92614963a022a00c) and its DeepPIV Apolemia scans are `by-nc-sa`. A [CC BY Nanomia lab scan](https://api.sketchfab.com/v3/models/bf0b8d2378914a66a2e1f94f63d63543) is a different small colony; it cannot stand for the complete 45.7 m Ningaloo colony. No repeated zooid geometry added. |
| Vivian Hailstone | The [IBHS/NCAR scan poster](https://ams.confex.com/ams/28SLS/webprogram/Handout/Paper300876/SLS2016_3DScanning_Poster.pdf) and [paper](https://doi.org/10.1175/JAMC-D-17-0344.1) establish that the real cast was scanned. [UCAR's catalog record](https://ckanprod.data-commons.k8s.ucar.edu/dataset/comparisons-of-electromagnetic-scattering-properties-of-real-hailstones-and-spheroids) exposes only an article resource (`ark:/85065/d7qf8wv4`), whose endpoint presents a browser challenge. No openly licensed STL/PLY or numerical shape grid obtained. Other freely downloadable hailstones are different stones and were not substituted. |
| Great Pyramid of Giza | [A CC BY photogrammetry candidate exists](https://api.sketchfab.com/v3/models/4a251113722f4d969b6cf2ca5f35c502), described as reconstructed from YouTube videos. It includes broad surroundings. The item measures original height while the existing pyramid's base is substantially wider: a natural whole-pyramid view at height calibration conflicts with the 1.3× overall-extent rule. No shrinking the footprint, restoring a capstone, or calibrating width as height. Candidate was not registered. |
| Kola Superdeep Borehole | No public admissible wellhead scan obtained. Independently, the catalog measures underground bore depth, not the physical cap. Scaling a surface wellhead to 12,262 m would misrepresent the quantity; no fabricated underground shaft was added. |
| Spider Silk Fiber | [Scientific Data's AFM study](https://www.nature.com/articles/sdata201440) exposes roughness/mechanical statistics and images, not a complete fiber surface with a diameter calibration. A [contrast-enhanced CT study](https://www.omicsdi.org/dataset/biostudies-literature/S-EPMC6637458) demonstrates silk imaging, but no accessible licensed full-volume/mesh input was obtained. No cylinder or invented fiber segment created. |
| Blu-ray Track Pitch | Found [real AFM images](https://antrg.com/blog/2012/12/19/afm-bluray/), university SEM/AFM teaching material and papers. No verified, openly licensed numerical height map obtained. A contrast/shaded SEM image is not measured height. No groove/pit geometry invented from track-pitch specifications. |
| DVD Track Pitch | [HardwareX's open AFM controller paper](https://doi.org/10.1016/j.ohx.2022.e00341) and [its CC BY OSF repository](https://osf.io/wgx4p/) contain figures, instrument designs/code and calibration videos; the examined figure folder supplies TIFF publication figures rather than raw calibrated height arrays. Other searches produced example images/manuals, not a verified height grid. No rendered publication screenshot was treated as raw AFM geometry. |
| Danyang-Kunshan Grand Bridge | No downloadable Sketchfab match. Public map searches found [OSM-derived Commons cartography](https://commons.wikimedia.org/wiki/File:Gro%C3%9Fe_Br%C3%BCcke_Danyang_-_Kunshan.png) under CC BY-SA and a [Google Earth KMZ reference](https://www.googlesightseeing.com/2012/06/the-worlds-longest-bridge/) without a verified permitted reuse license. No PD/CC BY bridge line with documented endpoints was obtained. No schematic viaduct or stretched route created. |

## Dataset changes

**None required for the two registered models.** Retain the exact names and
current values (`Fruit Fly`: 0.0025 m; `Tyrannosaurus Rex SUE`: 12.3 m).
Other items remain photo fallbacks. The Pyramid and Kola entries need a deliberate
measurement-definition decision before a differently scoped asset can be used;
this job does not request or apply a dataset edit.

## Preparation and integration

Original downloads remain in `/tmp/earth3d4-staged`; processed intermediates in
`/tmp/earth3d4-final`. These are optional local caches, not required at runtime.

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/sketchfab_models.py stage \
  --token-file ~/.config/universe-scales/sketchfab-token \
  --uid ad29b897bd2b4e27bb04ab9d31baa117 \
  --uid 77e21c4e5d65468bbe11780ae0557b95 \
  --output-dir /tmp/earth3d4-staged --max-archive-mb 90 \
  --max-glb-mb 95 --texture-size 1024

# MODULE_ROOT contains @gltf-transform/{core,extensions,functions}@4.5.0,
# plus meshoptimizer. Used the pre-existing npm cache; no install was needed.
node scripts/prepare_earth3d4_imports.mjs /tmp/earth3d4-staged /tmp/earth3d4-final MODULE_ROOT
```

The preparer checks pinned source-archive and staged-GLB hashes. A changed upstream
archive must be reviewed, not silently accepted. Processing preserves original
material colors/alpha, pose and proportions. Only existing mesh surfaces are
merged/decimated/quantized. There are no source network dependencies at runtime.

To re-register on main **after review**, with the delivered files copied first:

```sh
python3 scripts/register_model.py handoff/earth3d4/earth3d4-fruit-fly.entry.json \
  content/visualizations/models/earth3d4-fruit-fly.glb
python3 scripts/register_model.py handoff/earth3d4/earth3d4-trex-skeleton.entry.json \
  content/visualizations/models/earth3d4-trex-skeleton.glb
```

`register_model.py` also keeps `sketchfab-length.json` consistent. No `replaces`
field is needed. Suggested lead commit message:

```text
Add licensed fruit fly CT and T. rex replica scans

Co-Authored-By: Codex <noreply@openai.com>
```

## Verification and visual review

- `node --test tests/*.test.cjs tests/*.test.mjs`: **228 passing**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **140 run, OK, one skip**. Existing ResourceWarnings remain.
- Full `validate-models.cjs`: **192 assets, zero errors**. Both new GLBs have
  **zero warnings**; 1,867 warnings belong to pre-existing assets. Registry-wide
  `validation.json` only appends the two new records. The local subset is
  `handoff/earth3d4/validation.json`.
- `fetch_model_assets.py --verify`: **192 GLBs / 203 exact-name matches**, pass.
- `bump_versions.py --check`: **zero stale references**. No runtime JS/CSS changed.
- `node scripts/audit_earth3d4_models.mjs`: both load with the **actual vendored
  GLTFLoader**, pinned registry/file hashes agree, normals exist, exact geometry
  extents pass the 0.6–1.3× resting rule and declared layout widths. Image decoding
  is stubbed in this Node audit. See `loader-audit.json`.
- `./venv/bin/python scripts/preview_earth3d4_cpu.py --staged /tmp/earth3d4-staged`:
  texture-aware orthographic rest/side previews; all final pairs and the original
  fly calibration projection were opened and inspected. First decimation pass
  was too coarse for the fly; the final 90k target retains more CT detail.
  The fly landmark was refined against the original scan's abdomen silhouette;
  final rest extent is 1.185×.

Review images are in `handoff/earth3d4/previews/`:

- `earth3d4-fruit-fly.png`
- `earth3d4-trex-skeleton.png`
- `fly-calibration.png`
- `overview.png`

**Deferred to the lead:** production WebGL screenshots (`shot ... --views rest,side`),
the actual `model_lab audit`, radial-explorer screenshots and mobile review.
CPU previews approximate lighting and do not composite the fly's source
transparency; they are not browser approval. In particular, inspect the retained
CT alpha material in production and the T. rex's source gaps from the reverse side.
No Chromium or git retry was made after the coverage failure.
