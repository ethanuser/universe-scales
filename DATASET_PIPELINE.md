# Canonical Dataset Pipeline

This project has a canonical data pipeline that builds a normalized SQLite dataset and then derives the JSON and YAML artifacts used by the frontend.

The human-editable source of truth is `dataset/raw/`. SQLite is the canonical built artifact for querying, validation, and sharing; it is not the place contributors are expected to hand-edit records.

## Canonical Artifacts

- Canonical database: `dataset/universe_scales.sqlite`
- SQLite export: `exports/sqlite/universe_scales.sqlite`
- Observation export: `exports/json/observations.jsonl`
- Observation content export: `exports/json/observation_content.jsonl`
- Writer packet export: `exports/json/writer_packets.jsonl`
- Dimension catalog export: `exports/json/dimension_catalog.json`
- Coverage report: `exports/json/coverage_report.json`
- Dimension bundles: `exports/json/dimensions/<slug>.json`
- Frontend YAML export: `exports/frontend/<slug>.yaml`
- Site copy of frontend YAML: `data/<slug>.yaml`

The `data/*.yaml` files are generated deployment copies. The dataset side lives under `dataset/` and `exports/`.

## Interactive Presentation

The dimension-specific frontend modes also read `exports/frontend/<slug>.yaml`.
Their renderer registry and shared controls live in `js/experiences/`; they do not
introduce another editable copy of observation values. Maps, optional cutouts,
and sound metadata live in `content/visualizations/`, outside the canonical corpus
and outside `content/descriptions/`. Visualization captions explain equivalent
geometry, assumed motion, grouping, and display limitations without rewriting
the item prose. Dataset builds do not overwrite these assets.

See [the visualization guide](content/visualizations/README.md) for the mode
defaults, numerical assumptions, asset registry, licensing, and tests. Presentation
geometry is not a new measured observation and must not be imported as one.

## Phase-One Dimensions

Phase one focuses on six flagship physical dimensions:

- `length`
- `mass`
- `area`
- `volume`
- `density`
- `duration`

Each flagship dimension has a configuration entry in `dataset/raw/config/flagship_dimensions.json` with:

- `required_min_items`
- `preferred_target_items`
- `preferred_max_items`
- `selection_bin_count`

The current configuration allows dimensions like `length` and `duration` to grow beyond 24 selected items when the candidate pool supports it.

## Raw Inputs

- `dataset/raw/legacy_yaml/` preserves legacy hand-authored YAML as seed inputs.
- `dataset/raw/curated/` holds curated observation facts for newer dimensions.
- `dataset/raw/config/dimensions.json` holds structured metadata for non-legacy dimensions.
- `dataset/raw/config/dimension_profiles.json` holds cross-cutting metadata such as frontend grouping, sort order, status, and extra units.
- `dataset/raw/config/legacy_overrides.json` holds identity, eligibility, and qualifier overrides for legacy imported items.
- `dataset/raw/config/wikidata_subjects.json` holds the small cached Wikidata identity map used to attach QIDs, names, and aliases.
- `content/descriptions/` holds optional writer-facing Markdown descriptions outside the structured dataset.

Python now owns the pipeline logic. The dataset itself no longer lives in a Python module.

## Source Model

There is one editable dataset source and several generated artifacts:

- `dataset/raw/` is edited by humans and review scripts for structured facts.
- `content/descriptions/` is edited by humans or writing tools for prose.
- `dataset/universe_scales.sqlite` is generated from `dataset/raw/` and is the canonical query artifact.
- `exports/json/` and `exports/frontend/` are generated exports for other tools and the website.
- `data/*.yaml` is a generated deployment copy for the current frontend loader.

Keeping SQLite as a generated artifact avoids making every user parse many JSON files for basic queries, while keeping JSON as the contributor-facing format avoids asking people to edit a database directly. Description prose is stored separately in Markdown because it is editorial content, not the measured or derived value itself.

## Canonical Schema

The main tables are:

- `dimensions`
- `units`
- `subjects`
- `observations`
- `observation_content`
- `observation_qualifiers`
- `sources`
- `observation_sources`
- `coverage_bins`

`observations` includes lightweight curation metadata:

- `review_status`: `candidate`, `accepted`, `needs_source`, `needs_description`, `deprecated`, or `excluded`
- `display_status`: `display` or `hidden`
- `quality_flags_json`: machine-readable issue tags such as `arbitrary_quantity`, `weak_description`, or `needs_primary_source`

`observation_content` is the writing-oriented layer. It stores structured text fields separate from the raw measured or derived observation:

- `summary_short`
- `description_medium`
- `description_long`
- `hook`
- `caveats`
- `facts_json`
- `content_format`
- `content_origin`
- `content_status`

This is the layer intended to feed future writing agents. The default content format is markdown, and the frontend renders richer markdown plus math-friendly text.

The `facts_json` payload can also carry `source_trace`, which explains whether a number was:

- read directly from the source
- converted from source units into the canonical base unit
- derived from a source-reported quantity such as a period, wavelength, star count, or solar-mass count

## Commands

Build the canonical dataset and regenerate exports:

```bash
./venv/bin/python scripts/dataset/build_dataset.py
```

Run verification checks, including an optional determinism rebuild:

```bash
./venv/bin/python scripts/dataset/verify_dataset.py
./venv/bin/python scripts/dataset/verify_dataset.py --skip-determinism
```

Query the SQLite artifact directly through the CLI:

```bash
./venv/bin/python scripts/query_dataset.py between mass 1e-9 1e9 --selected-only
./venv/bin/python scripts/query_dataset.py nearest density 1000 --selected-only
./venv/bin/python scripts/query_dataset.py dimension-stats area
./venv/bin/python scripts/query_dataset.py subject sub:entity-earth --selected-only
./venv/bin/python scripts/query_dataset.py observation obs:frequency:entity-cesium-clock-transition
```

Audit generated descriptions against the museum-plaque style standard:

```bash
./venv/bin/python scripts/dataset/audit_content.py --dimension length --dimension costs --dimension duration --dimension energy --dimension temperature
```

## Contributor Workflow

1. Add or revise curated observations in `dataset/raw/curated/<dimension>.json`.
2. Add or revise dimension metadata in `dataset/raw/config/dimensions.json` and `dataset/raw/config/dimension_profiles.json`.
3. Update legacy normalization rules in `dataset/raw/config/legacy_overrides.json` when a legacy imported item needs identity, qualifier, or eligibility changes.
4. Add or revise optional narrative descriptions in `content/descriptions/<dimension>/<item-slug>.md`.
5. Rebuild with `scripts/dataset/build_dataset.py`.
6. Verify with `scripts/dataset/verify_dataset.py`.
7. Audit content with `scripts/dataset/audit_content.py`.
8. Review `exports/json/coverage_report.json`, `exports/json/writer_packets.jsonl`, and `exports/json/dimension_catalog.json`.

See `DATASET_STANDARD.md` for item acceptance rules, review statuses, and description expectations.

## Licensing

Universe Scales uses a mixed license model:

- Code is MIT licensed.
- Original structured dataset facts are dedicated under CC0 1.0 where legally possible.
- Original prose, descriptions, and documentation are licensed under CC BY 4.0.
- Images, music, and third-party source material retain their original licenses.

See `LICENSE.md` and `CITATION.cff` at the repository root.

## Notes

- The canonical model distinguishes `subjects` from `observations`, so one subject can accumulate multiple dimension values.
- Phase one still admits `measured` and `derived` values only.
- The writer packet export is intended to support future text-generation workflows without asking an agent to rediscover the facts from scratch.
- Generated frontend YAML stays compatible with the existing site loader while the canonical data remains in SQLite and JSON exports.

## Sound Recording Assets

Sound recordings are presentation assets, not evidence for a dataset dB value.
`content/visualizations/assets.json` records local files, original download URLs,
authors, licenses and SHA-256 hashes. Discover candidates with
`python scripts/fetch_audio_assets.py --search 'search terms'`, review their
meaning and reuse rights, then run `--download` after adding approved entries.
Missing recordings have no synthesized fallback. Playback uses relative dB gain
and optional session-only measured calibration; it cannot infer physical SPL from
device settings. See `content/visualizations/README.md` for calibration limitations.

Use `python scripts/fetch_audio_assets.py --audit` to verify recording coverage,
file hashes and attribution. `--files` resolves exact Commons titles. Optional
FFmpeg excerpts retain both original and output hashes plus transformation notes.
