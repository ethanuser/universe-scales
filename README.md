# [Universe Scales](https://ethannguyenuser.github.io/universe-scales/)

An interactive visualization of the universe's dimensions, from quantum to cosmic scales.

## Features

- **Interactive Plots**: Visualize items across many dimensions on logarithmic or linear scales, depending on the quantity
- **Dimension Experiences**: Default to size, area, volume, count, motion, cycle, brightness, or viewing-angle explorers where available; switch back to the plot, with a remembered choice per dimension
- **Shared Simulation Controls**: Zoom, time scale, pause/restart, rotatable equivalent volumes, and manually calibrated viewing angles
- **Sound Previews**: Licensed real recordings, relative-dB playback, optional measured calibration, and background-music muting. Missing recordings remain unavailable rather than synthesized.
- **Dimension Browser**: Expand a grouped selector with search instead of using a long dropdown
- **Multiple Dimensions**: Length, Duration, Mass, Area, Volume, Density, Current, Temperature, Counts, Brightness, and many more
- **Pan & Zoom**: Drag to pan horizontally, scroll to zoom in/out, double-click to reset zoom
- **Item Editor**: Visual editor to add, edit, and delete items with image upload support
- **YAML Import/Export**: Import and export YAML files for easy data management
- **Canonical Dataset Pipeline**: Build a normalized SQLite corpus and derive the site YAML from it
- **Separate Description Layer**: Store museum-style descriptions in Markdown outside the structured JSON dataset
- **Curation Metadata**: Track review status, display status, and quality flags without requiring centralized collaborator management
- **Unit Conversion**: Switch between different units (meters/feet, seconds/minutes, etc.)
- **Number Notation Toggle**: Switch between scientific notation (1e10) and standard notation
- **Dark Mode**: Toggle between light and dark themes
- **Background Music**: Optional ambient background music
- **Responsive Design**: Works on desktop and mobile devices
- **URL Management**: Shareable links for specific dimensions and units

## Dimensions Covered

1. **Fundamental scales**: Length, duration, mass, electric current, temperature, counts, luminous intensity
2. **Geometry and scale**: Area, volume
3. **Motion and mechanics**: Speed, acceleration, jerk, force, torque, moment of inertia, angle, angular velocity
4. **Fields and waves**: Brightness, frequency, charge, magnetic field, loudness, sound frequency
5. **Materials and matter**: Pressure, density, viscosity, flow rate, surface tension, salinity, concentration, hardness, strain, thermal conductivity, specific heat
6. **Information and computation**: Information, information rate, FLOPs
7. **Senses and perception**: Scoville heat, odor concentration, roughness, coefficient of friction, visual angle
8. **Global and geography**: Population density, physiological density, agricultural density
9. **Abstract and social**: Costs, historical time, counts, counts per unit time, probability, precision and accuracy, correlation coefficient, effect size, utility, QALYs, micromorts, absorbed dose, disease rarity, cell count, attention

## Data Structure

The project separates editable inputs from generated artifacts:

- **Editable source data** in `dataset/raw/`, where structured observations, dimension metadata, and legacy imports live in JSON/YAML inputs.
- **Editable prose** in `content/descriptions/`, where long item descriptions live as Markdown.
- **Presentation assets** in `content/visualizations/`, separate from values and prose, for maps, sound recordings, and optional image cutouts.
- **Canonical dataset artifact** in `dataset/universe_scales.sqlite` and `exports/sqlite/`, where subjects, observations, sources, units, and content are normalized for querying.
- **Frontend payloads** in `exports/frontend/` and `data/`, where the browser reads generated YAML bundles for each dimension.

The site still consumes YAML, but YAML is no longer the source of truth for the pipeline-managed dimensions.

## Usage

1. Click the dimension selector to open the grouped browser, then browse or search for a dimension
2. Choose your preferred unit
3. **Navigate the plot**: Drag to pan horizontally, scroll to zoom in/out, double-click to reset zoom
4. Hover over items for descriptions and source links
5. Hover over bands for detailed sub-scales
6. Click items to open source links in new tabs
7. **Edit items**: Click "Edit Items" to open the visual editor where you can add, edit, or delete items
8. **Import/Export**: Use the editor to import YAML files or export your customizations
9. Toggle number notation with the 1e10 button
10. Toggle dark mode with the moon/sun button
11. Toggle background music with the music button

## Technical Details

- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Visualization**: D3.js for interactive plots
- **Data**: YAML files parsed with js-yaml
- **Currency API**: exchangerate-api.com for live rates
- **Deployment**: GitHub Pages compatible

## Canonical Dataset

The project includes a normalized SQLite-backed data pipeline that generates the frontend YAML bundles and supporting JSON exports.

- Build the dataset: `./venv/bin/python scripts/dataset/build_dataset.py`
- Verify the generated artifacts: `./venv/bin/python scripts/dataset/verify_dataset.py`
- Query the dataset: `./venv/bin/python scripts/query_dataset.py between mass 1e-9 1e9 --selected-only`

See [DATASET_PIPELINE.md](DATASET_PIPELINE.md) for the source model, output artifacts, and contributor workflow.
See [DATASET_STANDARD.md](DATASET_STANDARD.md) for item acceptance rules, review statuses, and the description standard.
See [content/visualizations/README.md](content/visualizations/README.md) for the interactive modes, physical assumptions, asset licenses, and browser checks. The initial modes use approximate photos or equivalent geometry; they do not automatically remove backgrounds, reconstruct objects, or calibrate device brightness/sound output.
See [content/visualizations/models/README.md](content/visualizations/models/README.md) for the 3D model registry and the Sketchfab Length import workflow.

Test visualization math with `node --test tests/experience-math.test.cjs`.

## File Structure

```
/
├── index.html          # Main HTML file
├── css/
│   ├── styles.css      # Main CSS styling with dark mode
│   └── mobile.css      # Mobile-specific styles
├── js/
│   ├── constants.js    # Configuration constants
│   ├── script.js       # Main JavaScript application
│   ├── plot.js         # D3.js plot rendering and zoom/pan handling
│   ├── editor.js       # Item editor functionality
│   ├── formatting.js   # Number formatting utilities
│   └── mobile.js       # Mobile-specific functionality
├── data/               # Generated frontend YAML files
│   ├── length.yaml
│   ├── duration.yaml
│   ├── speed.yaml
│   ├── acceleration.yaml
│   ├── jerk.yaml
│   ├── brightness.yaml
│   ├── force.yaml
│   ├── energy.yaml
│   ├── costs.yaml
│   ├── pressure.yaml
│   ├── youngs-modulus.yaml
│   └── yield-strength.yaml
├── dataset/            # Canonical raw inputs and SQLite artifacts
├── exports/            # Generated JSON, YAML, and SQLite exports
├── scripts/            # Python utility scripts
│   ├── download_images.py     # Automatic image downloader
│   ├── generate_thumbnails.py # Generate optimized thumbnails for bandwidth savings
│   ├── check_images.py        # Validate image + thumbnail coverage for all exported items
│   ├── ensure_images.py       # One-command image backfill + thumbnail build + coverage audit
│   └── sort_yaml_items.py     # YAML item sorter
├── images/             # Item images
│   └── thumbs/         # Optimized thumbnail versions (generated)
└── README.md           # This file
```

## Contributing

To add new items or dimensions:

**Using the Visual Editor (Recommended):**
1. Open the "Edit Items" panel in the browser
2. Click "+ Add Item" to create a new item
3. Fill in the item details (name, value, description, source)
4. Upload an image if desired
5. Click "Save All Changes" to persist your edits
6. Export YAML to save your changes to a file

**Using the canonical dataset pipeline:**
1. Add or revise structured facts in `dataset/raw/curated/<dimension>.json`
2. Add or revise narrative descriptions in `content/descriptions/<dimension>/<item-slug>.md`
3. Update dimension metadata in `dataset/raw/config/`
4. Rebuild with `./venv/bin/python scripts/dataset/build_dataset.py`
5. Verify with `./venv/bin/python scripts/dataset/verify_dataset.py`
6. Audit descriptions with `./venv/bin/python scripts/dataset/audit_content.py --dimension length --dimension costs`
7. Review the generated artifacts in `exports/` and `data/`

**Using YAML Files directly:**
1. Edit a generated YAML file only for quick frontend-only experiments
2. Expect pipeline rebuilds to overwrite managed dimensions
3. Prefer putting durable changes back into `dataset/raw/`

**Utility Scripts:**
- `scripts/download_images.py`: Automatically downloads images for items from public sources
- `scripts/sort_yaml_items.py`: Sorts YAML file items by their value field
- `scripts/generate_thumbnails.py`: Generates optimized thumbnail versions of images to reduce bandwidth usage (see SCALABILITY_ANALYSIS.md)
- `scripts/check_images.py`: Audits image and thumbnail coverage for `exports/frontend/*.yaml` and validates files are readable images
- `scripts/ensure_images.py`: Convenience wrapper that runs downloader, thumbnail generation, and final coverage audit in one command
- `scripts/dataset/audit_content.py`: Audits generated descriptions against the museum-plaque style standard
- `scripts/suppress_broken_pipe.py`: HTTP server wrapper that suppresses harmless BrokenPipeError exceptions for cleaner logs

## Performance & Scalability

The site uses optimized thumbnails by default to reduce bandwidth usage:
- Thumbnails load automatically for faster browsing
- Click thumbnails to view full-resolution images
- See `SCALABILITY_ANALYSIS.md` for detailed scalability analysis and optimization strategies

## License

Universe Scales uses a mixed license model:

- Code is licensed under the MIT License.
- Original structured dataset facts are dedicated under CC0 1.0 where legally possible.
- Original prose, descriptions, and documentation are licensed under CC BY 4.0.
- Images, music, and third-party source material retain their original licenses.

See [LICENSE.md](LICENSE.md) and [CITATION.cff](CITATION.cff).
