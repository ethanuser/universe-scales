# images3 handoff — 2026-10-16

**Four of six requested image slots completed.** Prelude FLNG and Danyang–Kunshan
Grand Bridge remain unresolved under the requested photo-license restrictions.
No excluded-license or wrong-subject substitute was imported. The user was asked
whether original CC0 schematics are acceptable for these two physical subjects;
no answer was available when this handoff was written. The original brief permits
explanatory diagrams for abstract scales, so that exception was not assumed to
extend to these two subjects.

Branch: `codex/images3`. Changes are **uncommitted**. The brief explicitly says
Chromium and commits are known sandbox limits and should not be retried; neither
was attempted. The pre-existing untracked `venv` symlink is not a deliverable.

## Delivered images

Each is a real JPEG, **1200 × 800**, with a **300 × 200** JPEG thumbnail in
`images/thumbs/`. All four are original, clearly labeled **CC0 explanatory
diagrams**; no source artwork, photographs or measured catalog coordinates were
copied. Editable SVGs and their CC0 dedication are in [diagrams/](diagrams/).
Credit records were appended to `images/credits/length.json`, and the exact four
records are copied in [credits-added.json](credits-added.json).

| Item | Filename under `images/` | Scientific basis and representation |
| --- | --- | --- |
| Helium Nucleus Charge Diameter | `length_helium_nucleus_charge_diameter.jpg` | [NIST CODATA 2022](https://physics.nist.gov/cuu/Constants/Table/allascii.txt) gives an alpha-particle rms charge radius of 1.6785(21) fm. Twice that is shown, rounded to approximately 3.36 fm. The soft charge cloud is schematic; the dashed rms marker is not a surface or an enclosed-charge percentage. |
| PSR J0437-4715 Neutron Star | `length_psr_j0437_4715_neutron_star.jpg` | [NASA NICER, 22 August 2024](https://heasarc.gsfc.nasa.gov/docs/nicer/science_nuggets/20240822.html) reports an inferred equatorial radius of 11.36 km. The diameter is twice the reported central radius, approximately 22.7 km. The image explicitly identifies the dataset's 2024 result. Surface color and grid are illustrative, with no invented hot spots or claimed surface photograph. |
| Milky Way Central Bar | `length_milky_way_central_bar.jpg` | [Wegg, Gerhard & Portail (2015)](https://arxiv.org/abs/1504.01401) find a two-component bar half-length of 5.0 ± 0.2 kpc and an orientation of 28–33 degrees to the Sun–center line. The diagram uses approximately 10 kpc end to end and 30 degrees. Stars, transverse width and Sun placement are explicitly illustrative; no spiral-arm map is asserted. |
| Baryon Acoustic Oscillation Scale | `length_baryon_acoustic_oscillation_scale.jpg` | [DESI's explanation](https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/) identifies a slight excess of tracer pairs separated by approximately 150 Mpc. The ruler marks one present-day comoving pair separation, not a bubble diameter. The pair and background dots are conceptual, not catalog data. |

The filenames follow the exact ASCII sanitization in `js/script.js`: strip
punctuation, replace runs of spaces/hyphens with underscores, lowercase, prefix
`length_`. In particular, the pulsar filename uses `psr_j0437_4715`.

## Two outstanding photographs

### Prelude FLNG

- [This CC0 Commons photo](https://commons.wikimedia.org/wiki/File:Prelude_(ship,_2017)_IMO_9360439,_Amerikhaven,_Port_of_Amsterdam.jpg)
  is a different ship. Its filename identifies **IMO 9360439**; Prelude FLNG is
  **IMO 9648714**. The misleading category association was not accepted as subject
  evidence. The file visibly shows a cargo ship, not the FLNG facility.
- [This Commons montage](https://commons.wikimedia.org/wiki/File:2022_4_15_Prelude_auf_Karte.png)
  carries a CC BY 3.0 declaration by the uploader, but visually includes a
  Shell-branded rendering, a map and several photographs whose individual rights
  are not established in the record. It was rejected rather than using the
  montage's license to assume rights to embedded third-party art.
- The [operator's photographs](https://www.shell.com.au/about-us/what-we-do/gas-and-lng/prelude-flng-facility.html)
  show the correct facility, but no qualifying CC BY, CC0 or public-domain release
  was established. Public availability and editorial/media reuse are not a
  public-domain dedication.
- Flickr restricted to BY/CC0/public-domain licenses and Openverse returned no
  matches for `Prelude FLNG`.

### Danyang–Kunshan Grand Bridge

- [The Wuxi photograph](https://commons.wikimedia.org/wiki/File:201603_Danyang-Kunshan_grand_bridge_(wuxi).JPG)
  and its crop are **CC BY-SA 4.0**, excluded by the brief. The Commons category's
  other bridge photo/maps also use ShareAlike licenses.
- [Edward Zhao's photograph](https://www.flickr.com/photos/edward_zhao/8224595088)
  identifies the correct viaduct, but its live photo page says **All rights reserved**.
- [The ANR2008 Yangcheng Lake photograph](https://www.flickr.com/photos/34703494@N07/5910608939)
  also says **All rights reserved** on the live page.
- Restricted-license Flickr and Openverse searches returned no matches for
  `Danyang Kunshan`.

Decisions and source links are retained in
[sources/rejected-candidates.json](sources/rejected-candidates.json).
The rejected Prelude montage was downloaded and viewed only in `/tmp`; no rejected
source-image pixels were added to the repository. A scoped original CC0
measurement schematic for each subject remains a possible fallback if authorized.

## Visual review of all other Length images

The current raw Length catalog has **258 items**, including seven additional
missing image slots beyond the six in this brief. Before this job it had 245
populated slots. After the four additions it has **249 images and nine missing
slots**. All **245 pre-existing populated slots** were visually inspected across
the 13 saved contact sheets, with closer views and source-page checks for the
cases below. The four additions were also viewed individually at full size.

- New-slot contact sheet, viewed: [contact-sheet.jpg](contact-sheet.jpg).
- All-Length contact sheets, all viewed: [review/](review/), files
  `length-01.jpg` through `length-13.jpg`, in catalog order.
- Item/file/source manifest: [all-length-manifest.json](all-length-manifest.json).
- Selected source checks: [sources/review-source-metadata.json](sources/review-source-metadata.json).

Some legacy `.jpg` files actually contain transparent PNG data. The review script
composites transparency onto white to preserve black chemical bonds and labels;
it does not alter those source assets. A dark rendering of Glucose or Water alone
must not be mistaken for an empty or wrong-subject image.

### Clear subject, specimen, event or structural mismatches to fix

These **existing assets were not changed**. Some show a related subject, but fail
the exact identity or structural definition of their named Length entry.

| Item | Existing image / finding | Suggested correction |
| --- | --- | --- |
| String Length | `length_string_length.jpg` shows a looped physical cord/wire. The dataset refers to a theoretical string scale. | An original labeled theoretical-scale diagram. |
| Carbon Atom | `length_carbon_atom.jpg` shows a macroscopic carbon specimen on an element display. | A carbon-atom schematic, explicitly distinct from bulk carbon. |
| Grain of Sand | `length_grain_of_sand.jpg` shows desert dunes, with no individual grain resolved. | A grain macrograph or micrograph. |
| Lolong the Crocodile | `length_lolong_the_crocodile.jpg` is [Maximo at the St. Augustine Alligator Farm](https://commons.wikimedia.org/wiki/File:SaltwaterCrocodile('Maximo').jpg), not Lolong. | A verified photograph of Lolong; do not use a generic saltwater crocodile for a named record specimen. |
| Titanosaur Cast | `length_titanosaur_cast.jpg` shows an outdoor fleshed dinosaur sculpture with a TRELEW sign ([source](https://commons.wikimedia.org/wiki/File:Patagotitan_model.jpg)). The item specifies the AMNH skeletal cast. | A verified photograph of that AMNH cast. |
| Hyperion | `length_hyperion.jpg` is [Saturn's moon Hyperion](https://commons.wikimedia.org/wiki/File:Hyperion_false_color.jpg), while the item is the California redwood. | A verified image of the named tree, or a labeled tree-height diagram if a permitted photograph is unavailable. |
| Ribosome | `length_ribosome.jpg` is [PDB 1FKA, the bacterial Thermus thermophilus 30S subunit](https://commons.wikimedia.org/wiki/File:010_small_subunit-1FKA.gif). The item describes a complete eukaryotic ribosome. | A complete eukaryotic ribosome illustration or structure. |
| Longest Lightning Flash | `length_longest_lightning_flash.jpg` shows [a storm at Port-la-Nouvelle, France](https://commons.wikimedia.org/wiki/File:Port_and_lighthouse_overnight_storm_with_lightning_in_Port-la-Nouvelle.jpg). The entry identifies a specific United States megaflash. | The record event's satellite detection/map, or a clearly labeled explanatory record-length diagram. |
| TRAPPIST-1 System | `length_trappist_1_system.jpg` is [NASA's fictional TRAPPIST-1e travel poster](https://commons.wikimedia.org/wiki/File:TRAPPIST-1e_Const_CMYK_Print.png). It illustrates the view from one planet, not the system's orbital span. | A sourced system/orbit diagram with scale. |
| Kuiper Belt | `length_kuiper_belt.jpg` shows [dust disks around other stars](https://commons.wikimedia.org/wiki/File:Kuiper_belt_remote.jpg), HD 53143 and HD 139664, not our Solar System's Kuiper Belt. | A Solar System Kuiper Belt diagram. |
| Andromeda Gas Halo | `length_andromeda_gas_halo.jpg` repeats the optical Andromeda Galaxy portrait. The gaseous halo is not visible or annotated. | A credited gas-halo measurement diagram or appropriately labeled halo illustration. |
| Hercules-Corona Borealis Great Wall | `length_hercules_corona_borealis_great_wall.jpg` is a brown geographic/terrain image, unrelated to the claimed GRB concentration. The tooltip thumbnail and alternate full `.png` instead show an unverified galaxy-clump illustration. Clicking through selects the terrain `.jpg` before the `.png`. Neither supplies identified GRB evidence. | A labeled GRB evidence diagram, with matching thumbnail and full image; do not portray the disputed inference as a photographed wall. |

### Related images with the wrong feature, frame or measurement emphasis

These are additional review findings, **not claims that every image shows a
completely unrelated object**. They should be considered when tightening subject
accuracy and captions.

| Item(s) | Finding |
| --- | --- |
| Hunga Tonga Eruption Plume | The saved still is labeled **2022-01-15 03:40 UTC** and shows ocean/clouds before the prominent eruption plume. The credited source is an animated eruption sequence; select a verified frame showing the plume. The current JPEG's subject is absent. |
| Chloroplast | [The credited figure](https://commons.wikimedia.org/wiki/File:Fmicb-07-02140-g002.jpg) is a rice-stripe-mosaic-virus infection montage. Some leaf-cell panels include a `CH` chloroplast label, but the main subject is virus/cytopathology. Use an isolated chloroplast image or a clearly captioned crop. |
| Graphene Layer Spacing | A graphite surface STM atomic-lattice image does not show the interlayer separation. Prefer a cross-sectional layer-spacing diagram. |
| Blu-ray Track Pitch | A whole Blu-ray disc photograph does not resolve or mark track spacing. |
| DVD Track Pitch | The source title identifies DVD tracks, but the stored image appears as a nearly featureless microscope field at review size. Inspect the original and choose a crop/magnification with visible tracks and a scale bar. This is a visibility finding, not a positive identification of another subject. |
| Quark | The proton's `uud` constituent cartoon is context, not a picture of an isolated quark or the effective-radius upper limit used by the entry. |
| Proton Radius | The same constituent-quark cartoon provides no charge-radius definition or marker. |
| Electron | The image is an atomic-orbital montage; it does not illustrate the entry's classical electron radius. |
| Human Hair | A labeled transverse follicle/anatomical drawing includes hair but does not isolate the shaft diameter. |
| Giant Siphonophore | The image is a multi-species siphonophore montage rather than an identified individual corresponding to the entry's exceptionally long specimen. |
| Very Large Telescope Mirror | The photograph shows the telescope structure; the primary mirror edge/diameter is not isolated. |
| Lituya Bay Megatsunami | A landscape view of the bay provides context, but the maximum run-up scar/height is not identified. |
| El Reno Tornado | The selected image shows the parent storm from a satellite, not the tornado or its measured ground width. Correct event context; add a caption or choose a tornado/track image. |
| Contiguous US Longest Distance | The credited satellite image covers the western United States, not the full contiguous-US span. |
| Earth-Moon Distance | Two Moon discs illustrate apparent size at perigee/apogee, not Earth-to-Moon separation. |
| James Webb Space Telescope Orbit; Parker Solar Probe Closest Approach; ISS Orbital Altitude; Geostationary Orbit | Spacecraft portraits show the object but not the specified orbital distance/altitude. |
| Sun-Neptune Distance; Sun-Mercury Distance; Sun-Jupiter Distance | Planet portraits show the endpoint but no separation from the Sun. |
| Betelgeuse Diameter; Vega Diameter; Proxima Centauri Diameter | A locator map or unresolved star photo identifies the target but does not resolve its diameter. |
| Halley's Comet Orbit; Alpha Centauri A-B Orbit; Sedna Aphelion | Object/sky photos do not show the orbital path or aphelion distance. |
| Sagittarius A* Event Horizon | The EHT emission ring/shadow image is related evidence, not a direct outline of the event horizon. Caption that distinction. |
| TON 618 Event Horizon | An unresolved optical quasar field does not image the event horizon. |
| Laniakea Supercluster | The existing labeled galaxy-layout illustration is not visibly a velocity-watershed reconstruction. Its original scientific provenance was not established in this review; verify it before treating it as the actual basin boundary. |

No other obvious subject mismatch was detected at contact-sheet review resolution.
This is a subject review, not full license recertification, per-pixel scientific
validation, or confirmation of every historical source identification.

### Additional missing slots outside this brief

No matching runtime JPEG/PNG was found for:

- Weak Force Range
- Tau Compton Wavelength
- Proton Compton Wavelength
- Muon Compton Wavelength
- Muonic Hydrogen Atom
- Electron Compton Wavelength
- Credit Card

The two unresolved requested photographs bring the current total missing to nine.
No dataset edits are required for the four delivered diagrams. The remaining
items need image sourcing or a decision on the permitted diagram fallback, not
changes to their dataset values.

## Verification and reproduction

- `node --test tests/*.test.cjs tests/*.test.mjs`: **225 passed**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **97 tests run, OK, one existing skip**.
- `./venv/bin/python handoff/images3/review_images.py`: all four delivered slots
  have valid 1200 × 800 JPEGs, 300 × 200 JPEG thumbnails, allowed licenses and
  source/author/change records. Dimensions, file bytes and SHA-256 hashes:
  [asset-audit.json](asset-audit.json).
- All four full images and the new-slot contact sheet were viewed. All 13
  all-Length sheets were viewed; questionable entries were inspected more closely.
- A thumbnail/full-image comparison across all 249 populated slots found one
  substantial mismatch: Hercules–Corona Borealis, inspected separately above.
  Results: [thumbnail-review.json](thumbnail-review.json). Every populated slot
  had a corresponding thumbnail. This comparison catches different subjects;
  ordinary resampling differences are not flagged.
- All **178 pre-existing credit records** are unchanged, with four new records and
  no duplicate filenames. `git diff --check` passes; the content-hash check reports
  zero stale references.
- No JS/CSS, HTML, dataset, exports or GLBs changed. No version bump or glTF
  validation is needed. No models were registered, so no model entry JSONs apply.
- Browser/explorer checks were **not run**, per the lead's instruction not to
  retry the known Chromium sandbox block. CPU image review does not certify UI
  appearance.

Test logs are in `/tmp/images3-node-tests.log` and
`/tmp/images3-python-tests.log`.

The shared project venv was **not modified**. The temporary rendering environment
`/tmp/images3-tools` was created with CairoSVG 2.9.1 and Pillow 12.3.0, plus their
dependencies (`cairocffi`, `cffi`, `cssselect2`, `defusedxml`, `tinycss2`,
`pycparser`, `webencodings`). The first preview used an already-existing temporary
PyMuPDF installation, but its incomplete SVG gradient support was caught by visual
inspection; all final assets were regenerated with CairoSVG and inspected again.

Rebuild the four images and their credits (Pillow + CairoSVG required):

```sh
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib /tmp/images3-tools/bin/python handoff/images3/build_diagrams.py
./venv/bin/python handoff/images3/review_images.py
```

When integrating on main, copy the **eight new JPEGs** to their exact `images/`
and `images/thumbs/` paths and **append only the four records from
`credits-added.json`** to the then-current credit file, preserving concurrent work.
Carry the handoff folder with them. Do not wholesale replace main's credit file.
There is no commit to cherry-pick from this sandbox session.
