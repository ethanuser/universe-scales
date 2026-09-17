# Dataset Standard

Universe Scales is primarily an open scale-intuition dataset. The website is a generated demonstration layer.

## Phase-Two Goal

Build a high-quality template for five dimensions before expanding breadth:

1. `length`
2. `costs`
3. `duration`
4. `energy`
5. `temperature`

These dimensions should set the standard for item choice, source quality, derivations, descriptions, images, and exports.

## Item Acceptance Rules

A strong display item should do at least two jobs:

- fill a meaningful logarithmic gap
- act as a familiar anchor for general readers
- teach a useful mechanism, threshold, or concept
- have a clear source or derivation
- be imageable or culturally memorable

Familiar anchors win over perfect spacing when the two conflict, but large gaps should still be visible in coverage reports.

## Heavily Penalized Items

These should usually be excluded, deprecated, or left as non-display candidates:

- arbitrary fixed-quantity examples such as `1 kg of X` unless the quantity itself is culturally or physically meaningful
- repeated formula variants that differ only by chosen input size
- generic stars, planets, or galaxies without a specific story or reason for inclusion
- cryptographic or biological sequence spaces chosen only to fill bins
- placeholder/reference records
- technically valid values that do not help a reader build scale intuition

## Review Metadata

Observations carry lightweight review metadata so the project can remain forkable without requiring centralized maintainer work.

`review_status` values:

- `candidate`: plausible but not fully accepted
- `accepted`: suitable for display or reuse
- `needs_source`: needs a better source
- `needs_description`: needs museum-plaque prose
- `deprecated`: kept for history but should not be displayed
- `excluded`: intentionally excluded from display

`display_status` values:

- `display`: eligible for generated frontend output if selection rules choose it
- `hidden`: retained in the corpus but hidden from display

`quality_flags` are machine-readable notes such as:

- `boring_anchor`
- `arbitrary_quantity`
- `generic_celestial_body`
- `needs_primary_source`
- `weak_description`
- `formula_variant`

## Source Standard

Every accepted display item should have at least one source. Prefer:

1. primary sources, official datasets, standards bodies, mission pages, or scholarly papers
2. reputable secondary references, textbooks, reference works, or encyclopedias
3. Wikipedia/Wikidata for identity, aliases, and rough discovery

Derived values should include the source for each major input plus the formula or assumption used to derive the displayed value.

## Description Standard

The main item description should read like a concise museum plaque:

- usually 55-120 words
- average-reader friendly
- opinionated enough to explain why the item is included
- specific enough to teach something beyond the label
- free of source bookkeeping, formulas, and conversion notes

Derivations, formulas, assumptions, uncertainty, source locators, and caveats belong in structured metadata, not in the main prose.

See `DESCRIPTION_STYLE_GUIDE.md` for the full prose standard.

## Editable Source Model

Humans edit:

- `dataset/raw/curated/*.json`
- `content/descriptions/**/*.md`
- `dataset/raw/config/*.json`
- `dataset/raw/legacy_yaml/*.yaml` only for legacy seed data

The build combines those editable inputs and generates:

- `dataset/universe_scales.sqlite`
- `exports/json/*`
- `exports/frontend/*.yaml`
- `data/*.yaml`

SQLite is the canonical query artifact, not a hand-edited source file.
