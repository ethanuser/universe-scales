# Description Content

This directory stores long-form item descriptions separately from the structured dataset.

The structured dataset under `dataset/raw/` should focus on values, units, sources, identities,
derivations, and selection metadata. Prose belongs here because it is interpretive editorial
content rather than the measured or derived value itself.

## File Format

Use one Markdown file per described item:

```text
content/descriptions/<dimension>/<item-slug>.md
```

Each file starts with YAML frontmatter:

```markdown
---
dimension: duration
item_name: All Human Hours Ever
summary_short: The total conscious time spent by every human who has ever lived.
content_status: curated
---

The main museum-plaque description goes here.
```

The Markdown body becomes `description_medium` in the generated SQLite, JSON, and frontend
exports. Keep formulas, source figures, assumptions, and conversion notes in structured dataset
fields rather than in the body text.

## Current Role

These files are loaded by `scripts/dataset/raw_loader.py` after any legacy JSON content files,
so Markdown descriptions take precedence.

