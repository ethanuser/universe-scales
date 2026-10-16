# Brief: new Length items for Universe Scales

The Length explorer is a continuous zoom from the Planck length to the observable
universe; each item is shown at its true size beside its neighbors. It has 66 items
(list: `scratchpad/length-items.txt`, value<TAB>name). The owner wants about 4x more,
chosen to create a sense of wonder, and placed to fill the big gaps on the log scale.

## What makes a good item
- Real, specific and checkable: a measured or well-defined length with a citable number.
- Surprising or awe-inspiring: something people have heard of but never seen at scale,
  or a striking comparison (e.g. a tardigrade, the ISS, the Moon's diameter, Olympus Mons,
  a neutron star, Sagittarius A*'s event horizon, the KBC void, a SARS-CoV-2 spike, a
  transistor gate, a ribosome, the fruit-fly brain, a hummingbird egg...).
- Diverse: biology, physics, engineering, Earth, space, human culture.
- Spread out: prefer values that land in sparse decades (see the list). Avoid items within
  about 15% of an existing value unless they are exceptionally interesting.
- Visualizable: prefer things that could get a good 3D model (Sketchfab CC-BY/CC0, NASA 3D,
  NIH 3D, PDB structures, or a simple procedural shape). Say which in `model_idea`.
- No duplicates of existing names or concepts.

## Accuracy (non-negotiable)
- Every value must come from a source you actually opened (use WebFetch/WebSearch) and
  that states the number: Wikipedia is acceptable if the article states it with a citation;
  prefer NASA, NIST, ESA, PDB/RCSB, peer-reviewed papers, official sites.
- `value` is in meters, SI float (e.g. 4.2e-9). Say exactly what it measures (diameter vs
  radius vs length vs height) in the description, and prefer whole-object sizes (diameter,
  length, height) rather than radii, because the explorer draws the whole object.
- If the literature gives a range, pick a representative value and say "about".

## Description style (read DESCRIPTION_STYLE_GUIDE.md in the repo)
2 to 4 sentences, 55 to 110 words, museum-plaque tone: anchor what is measured, give one
genuinely interesting fact or mechanism, and situate it against a nearby scale. No source
bookkeeping in the prose. No exaggeration; every fact must be true.

## Deliverable
Write ONE file, `items-<band>.yaml` in your output directory, as a YAML list of entries:

```yaml
- name: Tardigrade            # unique, Title Case, concise
  value: 5.0e-4               # meters
  source: https://...         # page that states the number
  description: >-
    ...2 to 4 sentences...
  measures: body length of an adult      # short phrase
  model_idea: "Sketchfab CC-BY candidate uid ... / NIH 3D entry ... / procedural: ..."
  wonder: one line on why this item is worth the slot
```

Then report back briefly: how many items, the decade coverage you achieved, and any items
you were unsure about. Do NOT edit any file in the repository; the lead merges and builds.
