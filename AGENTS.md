# Agent Handoff Guide

## 2026-10-30 full-page data editor, scale bands, options choices (Claude)

- Data editor is a full page (`#data-editor-dialog`, default tab Items). app-shell builds a
  sidebar (`.data-editor__nav`: filter, Add item, rows grouped by scale band, Delete all items)
  and shows only the selected `.item-editor-card` (`.is-selected`) in the detail pane. All cards
  stay in `#items-list` because editor.js saves by reading every card; the sidebar is rebuilt from
  them by a MutationObserver (keeps the selection by card key; selects a newly added item; starts
  on the explorer's current item). Detail = Details and Image blocks plus the 3D model panel.
  One scroll region per pane (no nested `#editor-content` scroll).
- `ScaleModels.ModelPreview` (models.js): one item's model on its own canvas, resolved like the
  explorer (registry match, `proceduralLength`, `angularEntry`, `overrideEntry` for uploads and
  size/rotation) and refreshed on `scale-model-override`. Drag turns, wheel zooms, double-click
  resets. app-shell keeps one instance and disposes it when the editor closes.
- `ScaleSearch.band(value, dimension)` / `groups(items, dimension, value)`: length/area/volume use
  named bands over the equivalent length (Subnuclear ... Human scale ... Cosmic); other dimensions
  use powers of a thousand (Thousandths, Thousands, Millions, then 10^n ranges). Used for headers
  in both item pickers (hidden while searching) and the editor sidebar; skipped on linear scales.
- Options: number notation, theme (Light / Dark / Auto, which follows the system) and music are
  segmented choices (`.app-choice`, `aria-checked`), so every option and the current one are
  visible. `app.setTheme`, `app.setNotation`; shortcuts T/N/M still cycle.
- The explorer opens unlocked at human scale (Human Height / Human skin area / Human body volume)
  via the renderer's `overview(index)`: camera at the item's ring size, nothing selected, nearest
  object choice resumes on the first zoom or pan. A `?item=` link still opens selected.

## 2026-10-30 model adjustments, full-width item picker (Claude)

- `js/model-overrides.js` (`ModelOverrides`): per dimension+item size (`display_scale`) and
  rotation (`yaw`/`pitch`/`roll`) overrides in localStorage, uploaded GLBs in IndexedDB served as
  object URLs; fires `scale-model-override`. `ModelStage.applyOverride` merges them into the entry
  (uploads replace src with an `upload:` id); draw multiplies size by `display_scale`; uploads
  dispose the old instance. Browser-only: they never change the registry or exports.
- Data editor item cards get a "3D model" panel when opened: model id, author, license, source,
  basis and item source; Download GLB; Upload / Replace upload; Reset; Size/Turn/Tilt/Roll sliders
  that preview live. Global editor actions moved to a footer bar; section headers are plain rows.
- Item picker (explorer and chart) opens as a full-width sheet with a multi-column grid. The chart
  toolbar has a panel toggle (P), sharing `scale-panel-hidden` with the explorer.
- Owner dislikes the middle dot as a separator: link groups use flex gaps, titles use words
  ("Edit Length data"). Only the unit-multiplication sign in symbols like N·m remains.

## 2026-10-30 data editor dialog, lock vs selection, input polish (Claude)

- Data editor: `#editor-content` lives in `#data-editor-dialog` (app-shell moves it there) with
  Dimension / Units / Items tabs (counts from the lists), an items filter, item cards collapsed to
  one row until opened, section headers that no longer collapse. Closing the dialog calls
  `editor.toggleEditor()` so editor.js state stays consistent. The drawer row only opens it.
- Scroll latching (app-shell): a wheel gesture stays with the pane it started in for 400 ms;
  inner scrollable fields under the pointer do not take over.
- Explorer: `lockActive` separates the view lock (centering + 1-decade zoom-in limit) from the
  selection. Panning ends the lock but keeps the item selected; zooming 0.5 decades out still
  deselects.
- Chart: horizontal wheel/swipes are prevented in chart mode and `overscroll-behavior-x: none`
  stops browser back/forward; found items pulse once.
- Solid carets for all dropdowns; one masked clear (x) for every search input; unit picker is a
  menu (name, muted symbol, check on current); item list scrollbar sits in its own gutter.
- `setDimension` clears the controller's debounced detail timer (stale item + new dimension made
  404 image requests).

## 2026-10-30 UI cohesion pass (Claude)

- Typeface: Inter (Google Fonts) for all UI and SVG text (`--app-font`), tabular digits for values.
- One chevron (CSS mask) for every dropdown/collapsible: dimension, item and unit pickers, the data
  editor and its sections. Collapsed sections point right.
- Chart mode has the explorer's item picker in the top bar (dropdown with thumbnails + search,
  previous/next, arrow keys). Choosing an item calls `app.focusChartItem`, which zooms the value
  axis to the item and ~3 neighbors each side (`zoomChartToLogRange`; it sets
  `isResettingView` during the animation so handleZoom's range clamp does not cancel it),
  centers the row and pins the panel. `chart-selection` events keep the picker label current.
- Axis ticks: `thinTicksByLabelWidth` keeps exponent multiples so labels never overlap; pinned
  axes hide labels that would be clipped at the edges.
- Search: `[hidden]` results really hide; description-only matches appear only when nothing
  matches by name. Tooltips measure at the left edge (no squish) and stay on one line.
- Data editor restyled in the drawer (drawer widens to 680px while open): flat sections, one solid
  Save, quiet secondary buttons, red-text destructive actions, soft cards. Rows renamed
  "Edit this dimension's data" and "Related links" with icons.
- Dimension browser decluttered (no group boxes, borderless entries, colored headings with a
  hairline). Shortcuts dialog uses two roomy columns. About dialog: no scale-note box; links use
  the accent color. Chili icon redrawn.

## 2026-10-29 search, re-lock fix, desktop-style controls (Claude)

- `js/item-search.js` (`ScaleSearch.rank`): normalized name matching (word starts, prefix,
  initials prefix such as "lhc"/"iss", plural stemming incl. -ies), a curated synonym list, then
  word-start matches in summary/hook/description. Explorer picker reorders by rank; arrow keys move
  the highlight, Enter selects. Chart mode gets a search box in the top-bar item slot
  (`app-shell.js`) that scrolls to the row and pins it (`app.focusChartItem`); / and Ctrl/Cmd+K
  focus it. Tests: `tests/item-search.test.cjs`.
- Chart: a ResizeObserver on the plot container refits the SVG whenever its width changes
  (details panel, rail, full screen), fixing clipped large items and the first-click resize.
- Re-lock fix (root cause): a locked selection's pan now eases to the shared center as you zoom
  out (over 0.5 decades, `panAt`), and the lock releases there with no anchor left, so returning
  toward the item's size never re-centers it.
- Controls styled like the Claude desktop app (owner's exception to square corners for buttons):
  borderless icon buttons with rounded hover highlight, rounded segmented view switch, round zoom
  buttons, soft-filled selector triggers; panels/menus/dialogs stay square. Native title tooltips
  are replaced by `.app-tooltip` (shortcut shown as a key cap). Phones keep 40px touch targets.

## 2026-10-29 chart details panel, zoom limit, ISS (Claude)

- Chart view (desktop): no floating tooltips. `#tooltip` docks as a left panel (`tooltip--panel`,
  `chartPanelMode()`); hover previews, click pins until another item is clicked; leaving an item
  keeps it shown; `showChartPanelPlaceholder()` prompts when nothing is selected. Touch keeps the
  old pinned tooltip.
- Chart lines (item and grid) span the full SVG height and meet the pinned axes; the plot
  container has no padding.
- Locked selection: zoom-in is capped 1 decade past the framing (`lockLimit` in `navigation`) and
  no longer releases; zoom-out still releases after 0.5 decades.
- ISS: `sketchfab-iss-calebcram` (CC BY, textured, 4.3k tris) replaced the grey NASA model; the
  angular "ISS orbit" view uses it too (`angular-orbits.js`).
- Icons: full screen back to corner brackets; the chart's reset is a "home" icon. The first-visit
  gesture hint shows only in the size explorers.

## 2026-10-29 chart v3, no re-lock, icons (Claude)

- Chart axes: `setupStickyTopAxis` now draws two pinned axes (`#sticky-top-axis`,
  `#sticky-bottom-axis`, class `chart-axis`) from the chart's own scale and ticks on every plot
  update/resize; the SVG's own axes are hidden (`#plot-svg .axis`). No swap-in transition.
- Chart right column (`--chart-rail` 64px): overview rail flush right, the five chart controls
  docked under it as a 2x3 block (`--chart-control` 32px). Rail, controls and axes are appended
  to `.app`, so they show in full screen. The plot container reserves the column and axis bands.
- Chart tooltips: `chooseTooltipPosition` tries below-right, above-left, above-right, below-left of
  the cursor and keeps the one covering the least area of other item groups, inside the chart.
- Explorer: a selection releases after 0.5 decades out or 1.5 in; a frozen view (drag or
  released selection) now also eases back to the shared center when zooming out (over 1.5
  decades), so returning to an item's scale never re-centers on it.
- Full-screen icons: diagonal arrows with solid triangular heads. Dimension group titles are
  colored text (no swatch).

## 2026-10-29 dimension icons, colors, shared full screen (Claude)

- `js/dimension-icons.js`: a stroke icon for every available dimension (`DimensionIcons.icon(slug)`,
  fallback for new slugs; add one when adding a dimension) and a light/dark color per dimension
  group. Used in the dimension browser chips, group titles and the picker toggle; the current
  group color (`--dimension-color`) marks the panel's value and model-note border.
- Item search lists each item's photo thumbnail (lazy `images/thumbs/...jpg`) as its symbol.
- Full screen: one `#fullscreen-toggle` in the top bar (F) works in Explore and Chart and stays on
  across view and dimension switches (controller only exits when there is no app shell).
- Chart: `.app-main` scrollbar hidden in chart mode (the overview rail replaces it), no horizontal
  overflow, chart buttons use the toolbar's stroke icons. Explorer zoom: opaque track, knob and
  +/- buttons without an enclosing box.

## 2026-10-29 pan, pinch, selection lock, chart rework (Claude)

- Radial explorers: drag on empty space pans (frozen world-point anchor, `manual: true`, returns
  toward the origin over 2 decades of zoom-in); Shift-drag or middle-drag pans over objects; two
  touch points pinch-zoom (`createSpatialInput` `onPinch`); Ctrl+wheel (trackpad pinch) zooms
  faster. Linear layouts keep drag-to-zoom.
- A selected object stays centered while zooming into it (`panAt` returns its world point while
  `pinnedFocus` matches); the lock releases after 0.5 decades out or 3 decades in, freezing the
  current view first. Framing: `frameZoom(ctx)` puts the object at ~55% of the stage's smaller
  side (renderer `frameOffset()`; model_lab navigation/mobile use it).
- Explorer zoom bar is an opaque strip. Help dialog and first-visit hint describe pan/pinch.
- Logarithmic chart in the shell: plain wheel scrolls rows inside `.app-main` (d3 zoom only takes
  Ctrl/Cmd wheel and pinch); horizontal swipe / Shift+wheel pans the value axis; the sticky top
  axis pins under the bar and listens to `.app-main` scroll; `js/plot-overview.js` draws an
  overview rail (all items + current rows/value window; click or drag to jump). Chart buttons are
  one compact row.

## 2026-10-29 app shell v2: one toolbar, left panel, shortcuts, performance (Claude)

- One top bar: logo (inline SVG, follows theme) | dimension picker + (i) popover | item toolbar
  (panel toggle, item search, prev/next, full screen, center) | Explore/Chart | unit | help | options.
  The controller mounts its toolbar into `#app-item-slot` when present (else into the host, as
  before). The (i) popover (`#dimension-info`) holds the dimension and unit descriptions plus
  "This view" (caption and model attribution, moved from the old toolbar info button).
- Description panel is on the left (`--app-panel-width`), toggled with P / the panel button
  (`ctx.togglePanel`, saved as `scale-panel-hidden`). Phones keep it below the stage.
- Full screen targets the whole `.app` (`ctx.fullscreenTarget()`), so the bar stays usable; the
  no-API fallback only overlays when there is no app shell. model_lab checks follow the target.
- Shortcuts (js/app-shell.js, help dialog lists them): arrows, / or Ctrl/Cmd+K search, D dimension,
  U unit, L explorer/chart, C center, P panel, F full screen, + and - zoom (`renderer.zoomBy`),
  T theme, N notation, M music, O options, ? help, Esc closes. Ignored while typing.
- Zoom +/- buttons beside the camera slider; one-time controls hint (`scale-hint-seen`).
  Explicit selections update `?item=` with replaceState. Spatial explorers never scroll the page;
  scrollbars are thin. Favicon swaps favicon-light.svg / favicon-dark.svg with the site theme.
- Performance: `ModelStage.adaptResolution` lowers the pixel ratio in 0.25 steps (to 1) when
  back-to-back frames run slower than ~40 fps and restores it when they keep up.
- Storage: `scripts/optimize_images.py` capped item photos at 2400 px / q85 (only files over
  2400 px or 1 MB); images/ went from 732 MB to 284 MB. Thumbnails are unchanged. Git history
  still holds the old originals (.git ~1 GB); the deployed site no longer does.

## 2026-10-29 measured models and Codex round 7 (Claude)

- `scripts/build_measured_models.py` + `register_measured_models.py` (CC0, by Claude): Great
  Pyramid (Petrie base 230.33 m, height 146.6 m, ~210 courses as texture), Earth's Inner Core
  (PREM 1221.5 km, cut open to the ~650 km innermost inner core), Kola borehole (SG-3 column,
  Proterozoic/Archean contact at 6,842 m), DVD and Blu-ray track pitch (ECMA-267 / BD-ROM pitch,
  channel bit and run-length limits; pit sequences are deterministic examples) and TON 618
  (Schwarzschild horizon for 4.07e10 suns with Neptune's orbit and the heliopause to scale).
  Citations live in each `sources/measured-*.md`. Re-run the register script after edits.
- Codex round 7 (public data only): volume3d added sugar-cube scan (enclosed-volume calibrated),
  NIAID influenza and SARS-CoV-2 virions and a clawfoot bathtub to Volume (29/55 covered).
  `node scripts/register_volume3d.mjs` re-adds the coronavirus entry, which reuses an existing GLB
  (the merge helper only re-registers entries with their own GLB). length3d3 found no new
  qualifying Length source; see `handoff/length-source-completion/ledger.json`.
- model_lab `spatial-models` and `area-maps` ruler checks now use `RADIAL_SIZE` (all spatial
  dimensions are radial).

## 2026-10-29 app shell, radial Area/Volume/Counts, selection model (Claude)

- **App shell** (`index.html`, `css/app.css`, `js/app-shell.js`): the site is a full-window app.
  Top bar: brand, dimension picker, view switch, unit picker, Options. The explorer fills the
  rest. The Options drawer holds notation/theme/music toggles, the dimension and unit
  descriptions, Edit Plot and Explore More; the About dialog holds credits and the scale note.
  There is no footer. All original element ids are unchanged, so script.js/editor.js wiring is
  untouched. `app.css` loads last and sets `border-radius: 0` everywhere (owner preference:
  no rounded corners in UI; SVG content shapes are unaffected).
- **Radial everywhere**: Area, Volume and Counts use the radial layout (`radial = true` in
  `R.spatial`; `R.counts` uses `radialPlacement/radialLayout` with `exponentFactor: 0.5`).
  Area maps feed `widthFactor`/`extentFactor` from their projected width/height.
- **Selection model** (`navigation` in spatial.js, `controller.js`): `ctx.focus(i, true)` is
  an explicit selection (bold label, `ctx.explicitSelection`). It holds through small manual
  zooms and is released beyond +0.5 / -0.4 decades from where it was framed. Otherwise the
  panel follows the on-screen object nearest the ring size (renderers report it via
  `navigationControl.observe`), never bolded; with nothing in view `ctx.clearFocus()` shows a
  "No objects at this scale" panel.
- Labels: `LABEL_EM` is 0.1 (placement and drawn labels agree), font clamped 9..40 px, fading
  only between 12 and 28 px of drawn object size.
- model_lab `mobile` waits 4 s before its final navigation: aborting in-flight prefetched
  texture decodes logged GLTFLoader errors that were not app errors.

## 2026-10-29 sourced Area and Volume expansion (Codex)

- Added seven paired Area/Volume observations (Mercury, Venus, Mars, Saturn,
  Uranus, Neptune, Pluto), derived from pinned JPL equivalent-volume mean radii.
  Input radii/formulas remain in raw qualifiers and the 14 new plaques are separate
  Markdown files. Existing values and plaques are unchanged. Scoped rebuilds only
  changed Area/Volume outputs; Volume's target is 60 so Earth/Jupiter are retained.
  Current display counts: Area 47, Volume 55.
- Seven Volume entries reuse existing NASA GLBs, independently normalized by
  enclosed mesh volume. No new/duplicated GLB or scratch mesh. Rebuild/check with
  `node scripts/register_planet_volumes.mjs [--check]`. The original Length
  calibrations are unchanged; Saturn retains its oblate body without rings.
- `area-maps.js` and `content/visualizations/area-maps.json` provide 17 equal-area
  views: 11 whole-globe textured Equal Earth maps and six source GIS outlines
  (Tahoe, NYC, Caspian, Texas, Greenland, Australia). The actual colored footprint
  is normalized to area, not the bounding rectangle. Regional projections rotate
  the sphere to local latitude first to avoid severely flattening Greenland.
  The maps have separate source/interpretation notes and no Area WebGL context.
- `build_planet_area_maps.cjs` samples actual NASA GLB UVs, including cube atlases,
  into 11 local PNGs (8.27 MB total). `prepare_area_gis.py` prepares 855 kB of
  public-domain boundaries. Do not re-add rejected Manhattan/Rhode Island shapes:
  source coastline/water omissions conflict with their quantities. NYC is a
  generalized land outline, uniformly calibrated, not a cadastral shoreline.
  GeoJSON/output/source hashes and reproduction: `handoff/area-gis/REPORT.md`;
  projection conventions: `content/visualizations/area-maps/README.md`.
- `register_area_maps.cjs [--check]` merges the sources. Planet photo aliases and
  inherited credits are reproducible with `prepare_planet_area_volume_images.cjs`.
  `model_lab.cjs area-maps OUT [names...] [--mobile] [--unit "square kilometers"]`
  checks filled area, images, source note and selected-unit ruler, and screenshots
  the production view. All 17 maps and seven new Volume mappings pass desktop/
  mobile checks without load/page errors. Screenshots were visually reviewed.
  A Luna visual critic scored both dimensions 9/10 execution and 8/10 accuracy;
  mobile checks are Chromium emulation, not physical-phone guarantees.
- 262 Node tests pass; Python runs 169 with one existing skip; two optional GIS
  tests pass with Shapely/pyshp preparation dependencies staged outside the repo.
  All 212 registry asset entries/223 exact matches, calibration/version checks,
  scoped dataset verification, 13 touch/fullscreen checks and navigation pass.
  Remaining Length/Volume sourcing decisions are in `handoff/length-source-completion/`
  and `handoff/volume-source-completion/`; no new Length candidate qualified in
  this bounded review. These ledgers do not claim internet-wide exhaustion.
  No push performed.

## 2026-10-28 source review and Volume calibration (Codex)

- Added three Volume mappings using existing licensed binaries: Sand Atlas's
  micro-CT Caicos ooid, IMU eLearning's educational red blood cell, and NASA's
  Jupiter. No new mesh geometry, duplicated GLBs, dataset values or plaques.
  The RBC remains explicitly an illustration, not a measured specimen. The
  scanned grain is scaled to a representative volume, not its original volume.
- `scripts/mesh_volume.mjs` checks a closed, oriented single shell and computes
  enclosed volume using the vendored loader. Separate Volume entries normalize
  the sand/RBC using `reference_size = cbrt(meshVolume)`; original Length entries
  are unchanged. Topology checks do not certify absence of self-intersections.
  `node scripts/register_volume_reuse.mjs --check` verifies the pinned source
  hashes and calibration; write mode preserves unrelated registry formatting.
- `model_lab.cjs spatial-models OUT "Item" ... --dimension volume [--mobile]`
  checks visible production instances, normalized enclosed volume and the ruler,
  and captures resting/rotated views. All three passed desktop/mobile checks
  without page/load errors; screenshots were visually reviewed. Area/Volume
  rulers now express square/cube roots of the correct selected-unit quantity
  instead of labeling a linear length as an area/volume. Two missing Volume
  photo/thumbnail aliases were restored with credits in `images/credits/volume.json`.
- No new Length source passed this bounded review. Dust-mite candidates failed
  anatomy/quality/calibration review; NCAR's Vivian hailstone has noncommercial
  terms; Dinkinesh's numerical source/version and mesh rights remain unverified.
  Rejected binaries are not bundled. Search decisions: `handoff/source3d-bio/`,
  `source3d-hail/`, `source3d-space/`. Existing photos remain.
- Checks: 256 Node tests pass; Python runs 167 with one existing skip; all 205
  registry asset entries/216 exact-name matches verify (entries reuse binaries).
  All 13 touch/fullscreen checks and version hashes pass. The full Length audit
  still loads 212 models with 46 photo-only items and the same five existing
  size flags (Weak Force Range, Proton Radius, Electron, DNA Helix Width, Virus).
  The mobile Volume ruler also passes with liters selected. No push performed.

## 2026-10-25 inward zoom and bounded model caches (Codex)

- Radial inward zoom returns a selected-object pan to the shared world origin
  over one decade, with monotonic screen-space offset and an exact zero endpoint.
  `journey.js` `radialReturnPan` includes magnification in its decay; wheel events
  no longer reset the anchor exponent. Only an interrupted selection glide freezes
  a new reference. Outward zoom keeps the selected world point; click/arrow glides
  still center objects. Models remain drawn down to 4 CSS px (previously 14),
  then disappear without photo substitution. No new opacity fade was added.
- `model-cache.js` is an async, reference-counted LRU. Renderer instances target
  32 entries/96 MiB on desktop and 20/48 MiB for coarse pointers. The shared parsed
  source cache targets 64/192 MiB, reduced to 40/96 MiB for coarse pointers. These
  are decoded-buffer/texture estimates per cache, NOT hard combined CPU/GPU caps.
  Visible models and pending leases are protected and can temporarily exceed
  targets. Inactive least-recently-used entries are evicted first; prefetching
  fits its nearest candidates into remaining estimated instance capacity.
- `model-resources.js` reference-counts source resources and closable image data.
  Original source snapshots release removed/flattened geometry and unused image
  data after normalization. Shared soft-point/yard-number textures are persistent.
  Environment materials are stage-local; stage eviction disposes overlays, these
  materials and skin textures, then releases its source lease. A four-job global
  source queue skips abandoned queued work; mode disposal releases pending pins.
- Shader warm-up now uses cancellable polling of the pinned vendored renderer's
  compile/program readiness API. Its old `compileAsync` timer could access a
  disposed material after a mode change. Abort warm-up before destroying contexts.
- New model-lab commands: `zoom-origin OUT [--mobile]` checks repeated-wheel return
  to zero without drift; `cache OUT` uses 2-instance/3-source budgets to exercise
  eviction, reacquisition, warm reuse and final pin release. `streaming` now
  checks persistence between 4 and 14 px and permits instance recreation after
  a long zoom journey. `ModelStage.cacheStats()`/`setCacheLimits()` aid diagnostics.
- Browser checks: desktop/mobile origin return, cache eviction/reload/disposal,
  mobile streaming, all 13 touch/fullscreen checks and navigation pass. Sourced
  clock, record deck, Earth rotation and Moon-orbit motion remain correct.
  Node: 250 tests pass. Python: 167 run, one existing skip. All 203 GLBs/213
  exact-name matches verify. No dataset values, plaques or model geometry changed.
- Whole-Length production audit loads all 212 modeled items (46 photo-only) with
  no page/load errors. Existing size flags remain Weak Force Range, Proton Radius,
  Electron, DNA Helix Width and Virus; this runtime pass does not redefine them.

## 2026-10-23 Codex round 6 merged (Claude)

- upgrade3d: of 32 illustrated models reviewed, only Basketball had a clearly better open scan
  (robin.sculac CC BY photoscan, replaces earth3d-basketball). The rest stay; see its REPORT.md.
- retry3d: M87 Jet now has the XJET Hubble WFPC2 F555W image as a flat sky-plane point map.
  Mauna Kea and Lake Baikal ETOPO 2022 (CC0) terrain GLBs are in the repo but **unregistered**:
  at true horizontal scale they are 18x / 26x wider than the listed height/depth, which would
  need a measure_axis framing decision from the owner. 22 other items still lack open data.
- Merge helper now lives at ../universe-scales-codex/merge_codex.py (the scratchpad copy was
  cleared); it re-registers every handoff entry, so unregister rejected candidates afterwards.

## 2026-10-23 explorer smoothness and click-to-center (Claude)

- Prefetch: `spatial.js` `prefetchModels` loads models (3 at a time, nearest the current
  scale first) from about a decade before they reach the 14 px draw threshold, including
  larger offscreen items that zooming out brings in. `ModelStage.prefetch/ensure/warm`:
  hidden instances get textures uploaded (`initTexture`) and shaders compiled
  (`compileAsync`) before their first visible frame.
- `renderer.debug.checkShaderErrors` is off (add `?shaderchecks` to debug). Its
  synchronous `getProgramInfoLog` was most of the main-thread time when models appeared.
- Pick outlines are lazy: `finish` stores a bounding circle per model and projects the
  convex hull only when the pointer is inside it (was the top script cost while zooming).
  The stage size comes from a ResizeObserver (`ScaleRenderers.stageSize`) instead of a
  per-frame `getBoundingClientRect`.
- Side panel: the thumbnail box reserves its 160 px height and fades the image in;
  the same element is reused when the panel rebuilds for the same item (registry
  arrival, units). Automatic selections during zoom rebuild the panel after 160 ms.
- Click-to-center (radial): an explicit selection (click, arrows, search, `?item=`) pans
  the view so the object sits at the center. `radialLayout` takes `pan` in world units;
  `navigation` glides it as one zoom about the fixed point shared by the start and end
  views (straight-line motion, monotonic navigation checks). The pan holds while zooming
  out, decays when zooming in past the item, and manual zoom freezes it first.
- GPU benchmark (headless Chrome on Metal, wheel zoom over ~13 decades and back):
  empty model slots 114 -> 0 (from Rafflesia) and 260 -> 129 (from Earth); worst frame
  134 -> 50 ms. Swiftshader has no parallel shader compile, so it still stalls.

## 2026-10-20 explorer streaming/performance continuation

- Modeled spatial objects never fall back to photos while loading or below the
  radial 14 CSS-pixel readability threshold. Until the registry is ready, defer
  spatial photos too, preventing an initial photo-to-mesh flash. Genuinely
  photo-only items and the no-WebGL fallback retain images; Area is unchanged.
- Registry matches (including misses) are cached per item after readiness.
  Radial placement/dimensions are prepared once per viewport class and registry
  readiness, instead of rebuilding presentation lookups/cache keys every frame.
  Ruler markup/credits update only when changed; model load completions share a
  redraw. Geometry, quantities, plaques and radial positions are unchanged.
- Explicit radial selections now remain pinned after glides/remounts, even with
  nearby-sized items. Wheel, slider or panning resumes automatic scale selection.
  Rotation does not clear the pin. The navigation harness now measures the
  radial layout and includes each entry's focus-scale factor.
- Parsed models already live in a page-wide promise cache; stage instances stay
  available offscreen. This batch preserves that behavior, without preloading
  the whole catalog. The cache remains unbounded; decoded geometry/textures can
  consume much more memory than GLB bytes. GPU state is recreated on mode
  remounts. A future bounded cache needs resource ownership/refcounts before
  disposing shared textures/geometries, not blind offscreen disposal.
- `node scripts/model_lab.cjs streaming OUT [--mobile]` deliberately delays the
  registry/Earth mesh, checks tiny-model hiding and photo-only preservation,
  then verifies instance reuse and shared parsed geometry across a mode remount
  with just one model request. Both desktop/mobile pass all eight checks.
- Milky Way rotation CPU median fell from ~3.4 to ~1.3 ms; desktop/mobile
  Chromium SwiftShader frame medians stayed ~16.7 ms. These are emulation results,
  not physical-phone guarantees. All 13 touch/fullscreen checks pass.
- Repaired Hyperion Moon's missing original/thumbnail using NASA Photojournal
  PIA17194, with NASA/JPL-Caltech/Space Science Institute credit in length.json.
  Older handoff integration claims were checked against main, not reimported.
- Checks: 236 Node tests pass; Python runs 161 with one existing skip. All 202
  GLBs/212 exact-name matches and version hashes verify. Existing NumPy/SQLite
  warnings remain. No dataset values, descriptions or model geometry changed.

## 2026-10-20 sourced clock/deck continuation

- Imported Innerscene's CC0 Round Time clock (894 kB, 9,468 triangles) and Walnut
  Spin deck (1.223 MB, 13,688 triangles) for five angular observations. Existing
  hour/minute hands and record/mat/groove parts rotate about the source hub;
  the case/dial/tonearm stay fixed. The source has no second hand, so that slot
  retains Claude's illustration. The deck motor pulley is omitted.
- `prepare_angular_imports.py` pins source hashes and groups existing parts
  without generating mesh geometry. Follow with glTF Transform 4.5.0 `tangents`
  for portable normal-map shading. Both GLBs validate with zero errors/warnings.
  Full provenance/rebuild/limitations: `sources/angular-imports.md`.
- Clock variants use distinct cache IDs and hide the other hand. Angular model
  creation now waits for the registry to prevent an early procedural fallback
  from persisting over a downloaded model. Failed registry loads still allow
  fallbacks. `model_lab.cjs angular --start "Item name"` verifies fresh deep links
  and checks actual loaded IDs against the selected registry entry.
- Reviewed production rest/rotated and 393 px screenshots. A Luna visual critic
  scored clock execution/accuracy 8/8 and deck 9/8. Existing symmetric grooves
  and a plain label make the small phase dial useful. No dataset values, plaques
  or authored mechanisms were changed in this batch.
- Checks: 232 Node tests; Python ran 161 with one existing skip; all 32 angular
  observations passed the browser audit. Final tangent-corrected imports passed
  all five examples at mobile width. Asset verification covers 202 self-contained
  GLBs and 212 exact-name matches; version hashes and diff whitespace pass.

## 2026-10-20 display deduplication

- Display selection now recognizes explicit `display_equivalents` groups in
  dimension profiles. Moon orbit, clock rounding, washing-machine spin, bicycle
  variants, 7200-rpm spindle and 716-Hz pulsar duplicates are consolidated. Angular
  Velocity exports contain 32 distinct examples and seven orbital examples.
- Generic quantity/derivation qualifiers do not split identical examples;
  conditions, dates and unknown measurement definitions remain distinct. The
  selected site corpus has no repeated display labels. Original alternate source
  records remain in the database with `selected_for_display: false`.
- Rebuilt 18 affected dimensions through staged scoped merges; 135 unrelated
  per-dimension files stayed byte-identical. The non-flagship `data/` deployment
  copy is now refreshed by scoped rebuilds, fixing stale duplicate lists. The
  acceleration fallback is synchronized with the existing canonical export.
- 230 Node tests pass; Python runs 159 tests with one existing skip. Dataset
  verification without determinism passes, and all 32 angular observations pass
  the production browser audit. No description Markdown or GLB was edited.
- Removed four obsolete registry aliases for retired soda-can/container/bicycle
  labels; the surviving entries keep the same models. All 200 GLBs and 207
  remaining exact-name matches verify.

## 2026-10-20 angular sourced-body continuation

- All eight orbital observations now reuse existing local NASA/public-source
  assets: Pluto, Mars, Earth, Venus, Mercury, Moon (two labels), and ISS. Sun/Earth
  centers also use their existing models. No mesh, dataset value or plaque changed.
- `angular-orbits.js` maps source IDs; `ModelStage.orbitalBodies` keeps distinct
  per-lane instances. `drawOrbit` positions/fits them without axial spin. Existing
  circular mean-speed guides remain illustrative, not ephemerides or size scales.
- Both asset source links appear in details. Source scope, assumptions and the
  Claude collaboration boundary: `sources/angular-orbits.md`. Existing authored
  mechanisms and Earth/Jupiter/Saturn spin rigs are preserved.
- Model lab angular mode now checks both orbital bodies at four phases, including
  fixed centers/attitudes and moving orbiters. Desktop and mobile-width orbital
  captures succeeded in this main-checkout session; earlier worktree sandbox
  failures do not apply to these new captures.
- Verification: 230 Node tests; all 38 displayed angular observations pass the
  browser motion audit (8 orbital, 30 spin). All 200 GLB asset checks and content
  hashes pass. Mobile gesture/fullscreen checks pass, but the suite exits nonzero
  for unrelated missing `length_hyperion_moon` original/thumbnail requests.

## 2026-10-18 earth3d4 handoff

- Public scans only: ETAIN's female Drosophila micro-CT and Rigsters' T. rex
  skeleton replica scan. The latter is a different replica, not SUE; the note
  states this. Nineteen targets remain photo-only for license, scope or data gaps.
- `scripts/prepare_earth3d4_imports.mjs` processes pinned external staging files;
  `audit_earth3d4_models.mjs` uses the vendored loader. CPU review:
  `./venv/bin/python scripts/preview_earth3d4_cpu.py`. Sources, final entries,
  detailed search/skip audit and lead integration: `handoff/earth3d4/REPORT.md`.
- Both assets are under 3 MB, validate with zero errors/warnings and pass CPU
  resting extents. No dataset/exports/images/runtime JS/CSS edits. Node: 228
  passing; Python: 140 run, one skip. Browser coverage hit the documented sandbox
  block; production WebGL/explorer/mobile review remains pending. Uncommitted.

## 2026-10-16 terrain3d handoff

- Nine geographic Length assets: Angel/Victoria Falls terrain, Gibraltar with
  explicit NOAA ETOPO1 bathymetry, Tanganyika shoreline/rift terrain, Grand Canyon
  from direct USGS 3DEP, Suez, 8,042 separate USGS San Andreas trace features,
  northern-African Sahara terrain, and 3,811 Reef Authority reef polygons.
- Offline builder: `scripts/build_terrain3d_models.py`; optional `--prepare`
  acquires sources. Pinned grids, compressed original vectors, source hashes,
  raster requests and reef license snapshot: `models/sources/terrain3d/`.
  No geographic footprint is stretched to a route length. Rulers are independent;
  vertical exaggeration is documented per entry. Waterfalls are terrain only.
- `scripts/audit_terrain3d_models.mjs` loads the actual vendored GLTFLoader;
  `scripts/preview_terrain3d_cpu.py` renders rest/quarter CPU previews. These
  do not certify WebGL, the production size audit, explorer or mobile behavior.
  Known browser/git sandbox limits were not retried; work remains uncommitted.
- Sources, final entries, integration commands, checks and deferred targets:
  `handoff/terrain3d/REPORT.md`. No dataset/exports/images/runtime JS/CSS changes.
- All nine are below 1.8 MB/44k triangles and validate with zero errors/warnings.
  Node: 228 passing; Python: 122 run with one skip. Asset/version checks pass.

Start here if you are an AI agent (Codex, Claude, ...) or a new contributor picking
up this repo. It is the shortest path to being productive; the longer READMEs linked
below hold the details. Keep this file current when you change workflows.

## 2026-10-16 space3d2 handoff

- Fourteen new Length entries: NASA Saturn globe and ringed-system views,
  Cassini hexagon cap, Juno Great Red Spot patch, measured Ryugu/Dimorphos shapes,
  Eris and three stellar size spheres, a CHARA-constrained Vega Roche surface,
  JPL Halley/Sedna orbital diagrams, and 4,615 actual selected Kuiper-region
  catalog locations. No synthetic filler points or invented asteroid terrain.
- A measured Cassini Hyperion asset/entry is ready but **unregistered**: the
  existing `Hyperion` item is a redwood. Add distinct `Hyperion Moon` first.
  Dinkinesh remains unchanged; a usable authoritative shape download was not
  obtained. Exact integration/data notes: `handoff/space3d2/REPORT.md`.
- Offline builder: `scripts/build_space3d2_models.py`; source refresh:
  `prepare_space3d2_sources.py` (preparation-only spiceypy needed for DSK).
  Pinned coordinates, element snapshots and identities: `models/sources/space3d2/`.
- Both rings and globe preserve physical source proportions, so the body item
  omits rings to satisfy its diameter extent rule. Ringed Saturn is shown under
  `Saturn's Rings`. Sedna's pinned solution gives ~1,011 AU, rather than the old
  catalog ~937 AU. The neutron star is explicitly the 2024 NICER estimate;
  a newer analysis differs. Cloud imagery is draped, not reconstructed cloud relief.
- All 15 GLBs validate with zero errors/warnings; Node: 225 passing; Python:
  103 tests with one skip. Asset/version checks pass. Vendored-loader and CPU
  rest extents pass; all rest/quarter CPU previews were viewed. These do not
  certify WebGL, production model-lab size audit, explorer/mobile or lighting.
  Known Chromium/git sandbox limits were not retried; work is uncommitted.

## 2026-10-16 earth3d handoff

- Added 14 Length models: eight dimensioned everyday/optical objects, four
  credited Sketchfab imports (egg scan, 747-8, Komodo dragon, Hindenburg), a
  weighted-catenary Gateway Arch and unexaggerated Meteor Crater terrain.
- Offline builders: `scripts/build_everyday_models.py`, `build_gateway_arch.py`,
  `build_meteor_crater.py`; imported asset preparation:
  `scripts/prepare_earth3d_imports.mjs`. Source notes are `sources/earth3d-*.md`.
  Final entries, integration commands and review limitations: `handoff/earth3d/REPORT.md`.
- No dataset, export, image or runtime JS/CSS changes. All 14 GLBs are under 3 MB,
  self-contained and validate with zero errors/warnings. CPU resting extents
  satisfy 0.6–1.3×; these are orthographic geometry checks, not model-lab approval.
- 224 Node tests pass; Python runs 88 tests with one existing skip. Asset and
  version checks pass. Full glTF validation still finds 17 errors in the existing
  `em-mitochondrion-jurkat` asset; that asset was not changed here.
- Chromium and git commits are documented sandbox limits. Per the lead's brief,
  neither was retried. All rest/quarter-camera CPU previews were viewed; WebGL
  shots, the actual explorer, the production size audit and mobile review remain
  pending. Changes are uncommitted for the lead to review and commit.

## 2026-10-15 neuron worktree handoff

- Neuron now uses the uncropped NeuroMorpho.Org NMO_109111 Feldmeyer archive
  reconstruction (CC BY 4.0), with measured process radii, original soma outline
  and a path-distance action-potential annotation. Soma depth and pulse timing/
  AIS location are authored proxies. Archive completeness does not rule out
  biological truncation in the source brain slice.
- Offline builder: `scripts/build_reconstructed_neuron.py`; optional source
  preparation: `scripts/prepare_neuron_source.py`. Source and license details:
  `content/visualizations/models/sources/neuron-model.md`.
- **Pending integration:** the items job must change Neuron from 100 µm to
  0.8 mm before publishing. Exact dataset text and entry JSON are in
  `handoff/neuron/REPORT.md`. No dataset/exports/images were edited here.
- `extras.hoverOverlay: false` excludes an annotation mesh/cloud from hover
  highlighting; used by the initially transparent electrical halo.
- 214 Node tests pass; Python suite runs 78 tests with one existing skip.
  Neuron glTF validation: zero errors/warnings. Chromium launch is sandbox-
  blocked (MachPortRendezvous permission denied), so production screenshots,
  model-lab size audit and mobile validation remain pending. CPU geometry
  previews are explicitly labeled and are not browser verification.
- Git staging/commit is also sandbox-blocked at the worktree `index.lock`.
  Files remain uncommitted; `handoff/neuron/commit.sh` prepares the requested
  local commit when run outside this sandbox. It does not push/change branches.

## 2026-10-13 continuation

- Explorer arrows are grouped after the item selector; Left/Right navigate items
  and Ctrl/Cmd+K opens its search. Info/fullscreen controls are both 44 px. Native
  range inputs have custom theme/sky-aware styling. Footer repository URL corrected;
  music uses `preload="none"`.
- `FocusTransition` in `journey.js` eases the lateral framing correction alongside
  zoom. It preserves the current pose through equal-size hops, repeated presses,
  and interrupted glides. Do not immediately replace the focus correction when
  starting a camera hop: that caused the reported teleport.
- `model_lab.cjs navigation /tmp/navigation` tests immediate position continuity,
  held target selection, repeated keys, arrow order, equal buttons and search.
  `performance --gpu --trace /tmp/trace.json` measures actual frame intervals,
  isolates visible models, and captures Chromium graphics work. JS timings alone
  missed the Milky Way slowdown. Tiny neighboring Tarantula points were submitted
  twice; opted-in clouds now use a single pass and deterministic full-cloud LOD
  prefixes. Full detail returns at 240 CSS px; desktop Milky Way frame intervals
  improved from ~50 to ~33 ms in SwiftShader and mobile emulation measured ~16.7 ms.
  These are software-renderer results, not hardware-phone guarantees.
- Angular rigs align the spindle with the camera and use clockwise display motion,
  retaining relative gear ratios. Earth/Jupiter/Saturn are south-polar views. The
  blender lid is omitted to expose its blades. Imported NASA Saturn (727 kB) and
  devkrsm's CC-BY engine crankshaft (406 kB); rings stay fixed context, and engine
  pistons/rods are omitted. No fabricated replacement geometry was added.
- `scripts/extract_glb_node.py` retains a named subtree and ancestor transforms;
  follow it with glTF Transform prune. It rejects skinned/animated sources.
- Browser navigation and 13 mobile/fullscreen checks pass. Asset GLBs verify;
  full provenance verification still reports the pre-existing Kenney license
  checksum mismatch. No dataset quantities or plaque prose changed.
- Final Node suite: 207 passing tests. Length audit loads all 65 models without
  errors, with Laniakea still photo-only; size flags are the proton profile,
  DNA and virus representations. This batch does not revise those definitions.

## 2026-10-15 angular inspection continuation

- Angular framing uses `angularSweepBounds` across a full turn, fixing the thin
  drone propeller's large change in projected height. The engine has an oblique
  inspection view (`angular_motion.view_tilt`) to expose its journals.
- `angular-additional-models.js` adds original observation-wheel, gas-turbine,
  dental-turbine and pulsar diagrams. Capsules counter-rotate to keep floors level.
  All bicycle labels reuse the existing CC0 city bicycle. Source/limitations:
  `content/visualizations/models/sources/angular-inspection.md`.
- `angular_motion.repetitions` freezes repeated spoke/blade patterns above the
  display threshold; Fit time still gives a quarter turn per real second.
- `model_lab.cjs angular OUT --times 0.1,1,2` now preserves all observations,
  including duplicate labels and orbital diagrams, and samples multiple phases.
  Chromium launch was blocked by the macOS sandbox in this worktree session.
  Browser-free geometry audit: `node scripts/audit_angular_models.mjs OUT --previews`,
  then `./venv/bin/python scripts/render_angular_preview.py OUT`. Those flat
  previews do not verify WebGL materials, perspective or UI. See handoff/angular.

## What this is

A static site (no build step, GitHub Pages) that visualizes quantities across many
dimensions. Each dimension has a log plot plus, for some, an interactive "explorer".
Current focus: the **Length size explorer**, a continuous camera from the Planck
length to the observable universe that shows each item as a calibrated 3D model,
a procedural model, or a photo.

Run it locally from the repo root:

```sh
python3 -m http.server 8000
# open http://localhost:8000/?dimension=length&item=Astronomical%20Unit
```

`?item=<exact item name>` deep-links to one item (first load only).
Bump the `?v=` query of any JS/CSS file you change in `index.html`; browsers cache hard.

## Map of the code

| Area | Files |
| --- | --- |
| App shell, plot, units, images, URL | `js/script.js`, `js/plot.js`, `js/formatting.js`, `js/constants.js`, `js/editor.js` |
| Explorer framework (mode registry, detail panel, picker, deep link) | `js/experiences/controller.js`, `controls.js`, `math.js` |
| Length/Area/Volume explorer (camera, layout, SVG labels) | `js/experiences/spatial.js`, `journey.js` |
| 3D models (loading, calibration, rotation, picking, overlays) | `js/experiences/models.js` |
| Procedural models (molecules, hair, solar system, field), distance bracket | `js/experiences/procedural-models.js` |
| Orbital atom and animated electromagnetic-wave models | `js/experiences/atomic-models.js`, `wave-models.js` |
| Particle-scale measurement diagrams (not hard particle boundaries) | `js/experiences/particle-scale-models.js` |
| Catalog-positioned nearby-space diagrams | `js/experiences/nearby-space-models.js` |
| Other explorers | `motion.js`, `perception.js`, `audio.js` (+ `*-math.js`) |
| Angular-velocity mechanisms and rotor binding | `angular-models.js`, `angular-machine-models.js`, `angular-rig.js` in `js/experiences/` |
| Model registry (runtime + provenance) | `content/visualizations/models.json` |
| Model files and licenses | `content/visualizations/models/` (see its README) |
| Dataset source of truth | `dataset/raw/` → built into `exports/` and `data/` (see `DATASET_PIPELINE.md`) |

Scripts: `scripts/sketchfab_models.py` (search/stage/import Sketchfab), `scripts/preview_glb.cjs`
(headless textured GLB preview), `scripts/model_lab.cjs` (audit, screenshots and contact
sheets of the production renderer; see Model lab), `scripts/register_model.py` (add/replace a registry entry),
`scripts/audit_glb_geometry.mjs` (bounds), `scripts/build_earth_moon_model.py` (orbital diagrams),
`scripts/build_everest_dem.py` (Mapzen elevation tiles → opaque sea-level block), `scripts/texture_padding.py`
(fix atlas seams), `scripts/fetch_model_assets.py --verify` (offline registry check).

## How a Length model is drawn

`models.js` picks a registry entry whose `matches.length` contains the exact item name
(or a procedural entry in `proceduralLength`). On load it removes `remove_nodes`,
applies `pre_rotation`, measures the bounding box, and scales so the calibrated extent
equals the item's value:

- `measure_axis` `x|y|z` chooses the extent (default: longest). `measure_fraction` says the
  calibrated part is that fraction of it (e.g. 0.8 for a body without its tail).
  `reference_size` overrides both with an explicit model-unit length.
- `yaw`/`pitch`/`roll` set the resting pose (degrees). Users can drag-rotate; the model
  springs back. The lowest point sits on the ground line.
- `layout_width_factor`, `focus_scale_factor`, `display_extent_factor` adjust spacing and framing
  for models much wider than their calibrated length.
- `display_label` optionally qualifies an explorer/review heading without renaming the
  dataset item or breaking exact-name matches and deep links (e.g. a putative structure).
- Material overrides: `tint`, `color_gain`, `roughness`, `metalness`, `opaque`, `double_sided`,
  `emissive` (+ `emissive_intensity`), and `environment` (reflection strength from a studio
  room map; metals look black without it).
- `distance_bracket: {"bodies": [A, B]}` (orbital diagrams) adds a white U-shaped bracket
  under two named sphere nodes: vertical lines drop from each body's center (distances are
  center to center) to a joining line below. It is part of the model, so it rotates with it.

Overlay conventions (set on any node's `userData`, including glTF `extras`):
`screenLine: {axis, length}` draws a box at a constant 1.4 px width; `label` (+ `labelClass`)
draws upright SVG text at the node; `outline` + `sphere` circle a unit-sphere node with a thin
line (so sub-pixel planets stay findable); `pointSize: {max, perPixel}` scales a point cloud
with the drawn model. `softPoints: true` opts into a shared, locally generated soft
circular sprite (`model-points.js`); hover overlays preserve it. Other clouds and
their shared materials are unchanged. See the header of `procedural-models.js`.

The model's projected convex hull (including the bracket) is its hover/drag/click area.

## Model lab (use this to see what you changed)

`scripts/model_lab.cjs` serves the repo itself and drives the production renderer in
headless Chromium, so no dev server or visible browser is needed:

```sh
node scripts/model_lab.cjs audit                       # every Length item: size vs listed value, load, triangles
node scripts/model_lab.cjs coverage --gap 1 --json      # provenance, photo fallbacks and logarithmic gaps
node scripts/model_lab.cjs shot /tmp/lab "Carbon Atom" --views rest,front,side --bg dark --time 1.5
node scripts/model_lab.cjs sheet /tmp/lab/all.png      # contact sheet of all models, red = flagged
node scripts/model_lab.cjs explorer /tmp/lab "Solar System"   # the real explorer after the camera settles
node scripts/model_lab.cjs angular /tmp/angular              # rest/quarter-turn screenshots and fixed-housing audit
node scripts/model_lab.cjs mobile /tmp/mobile                # real touch gestures and fullscreen lifecycle/screenshots
node scripts/model_lab.cjs performance "Galaxy Diameter" --mobile # continuous-rotation CPU/frame timings
```

`audit` reports each model's on-screen extent (the larger of width and height at its resting
pose) in units of its listed value (1.00x means it renders at the listed size) and flags anything over 1.3x, under 0.6x, wider than its
`layout_width_factor`, or failing to load, plus 404s and page errors. **Rule: a model should
render close to its listed size**; models much larger than their value overlap neighbours
and break framing while scrolling. Where a quantity is a radius (e.g. an atom's radius),
list the diameter the model shows. `model-review.html` is the same view for humans
(`?item=&view=&bg=&time=&zoom=`), and `window.modelLab` is its automation API.

`coverage` uses the production registry but does not load every mesh or certify
accuracy. It lists absent models, missing references/notes, unclassified
`representation` fields, large assets and adjacent gaps in decades. Use it to
plan new anchors, then run `audit` and inspect actual explorer screenshots.
A survey-window diagram is not a member catalog or a measured structure boundary;
a measurement diagram must not be labeled as a literal particle surface.

After editing JS/CSS run `python3 scripts/bump_versions.py`; it sets every `?v=` to the
file's content hash (HTML and nested module imports), so nothing is served stale and no
module loads twice under two version strings. It also adds missing hashes to local
first-party ES imports; vendored imports stay unchanged. `--check` fails if any are stale.

## Adding or replacing a model (proven workflow)

**Owner rule (2026-10-18), for Codex jobs only: public data only, no 3D models made from scratch.**
Claude may still build models (procedural, schematic, diagrams). A Codex model must be either an existing openly licensed model or scan (Smithsonian 3D, NASA/PDS, NIH 3D, MorphoSource,
museum scans, Sketchfab CC BY/CC0, Wikimedia Commons), lightly processed, or a direct conversion of a
public dataset whose values set the geometry (DEM/bathymetry, star and galaxy catalogs, 3D dust/gas
maps, CT volumes, public GIS vectors), optionally textured with public imagery. No procedural or
hand-authored geometry, schematics, scale diagrams, stand-in primitives or depth invented from a
photo. If no public source exists, the item keeps its photo. (Earlier procedural/diagram models
predate this rule.)

1. Find candidates: `SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py search 'query'`
   (CC-BY or CC0, downloadable). Prefer scientific sources (NIH 3D, PDB, scans) when they look good.
2. Stage outside the repo with the owner's token file (never commit or print the token):
   `... sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid UID --output-dir /tmp/x`
3. Clean and simplify with `npx @gltf-transform/cli@4.5.0` (weld, simplify, prune, resize, quantize).
   Do not use Draco/Meshopt/KTX2/WebP: the vendored GLTFLoader has no decoders.
   Budget: ideally ≤ 1.5 MB, ≤ 60k triangles, textures ≤ 1024 px.
4. Look at it: `node scripts/preview_glb.cjs model.glb out.png` (then view the PNG), and after
   registering, `node scripts/model_lab.cjs shot /tmp/lab "Item name" --views rest,side` and `audit`.
5. Copy the GLB to `content/visualizations/models/`, add a registry entry (copy an existing
   Sketchfab entry's shape; `bytes`/`sha256`/stats come from `inspect_glb` in
   `scripts/fetch_model_assets.py`), write an honest `note`, and credit the author.
6. Check it in the browser with `?item=`, run the checks below, commit.

## Checks

```sh
node --test tests/*.test.cjs tests/*.test.mjs
./venv/bin/python -m unittest discover -s tests -p "test_*.py"   # venv deps: requirements.txt
python3 scripts/fetch_model_assets.py --verify
python3 scripts/bump_versions.py --check
node scripts/model_lab.cjs audit
```

## Known issues and traps

- **Dataset rebuild drift.** The full builder still changes unrelated dimensions, and
  `verify_dataset.py` fails on the pre-existing `torque.yaml` selected-count mismatch.
  Use `./venv/bin/python -m scripts.dataset.rebuild_dimension length` for a Length-only
  edit; it stages a full build and merges only the requested dimension. Do not use a
  full rebuild or restore unrelated outputs as a workaround.
- The repo is ~720 MB, mostly `images/` originals (some over 30 MB). Runtime loads thumbnails, but
  GitHub's recommended repo limit is 1 GB.
- `models.json` mixes runtime fields with provenance (hashes, processing). Keep both; the
  site only reads a few fields.
- Hidden browser panes can pause `requestAnimationFrame`; inspect the visible explorer
  after the page and camera settle, not immediately after navigation.
- Never hand-edit `?v=` numbers; run `python3 scripts/bump_versions.py`.
- Import policy is CC-BY/CC0 only (`ALLOWED_LICENSES` in `sketchfab_models.py`). The owner's chosen
  sand grain (Sketchfab 8e7caaef…, "Sand Grain scaled to 75mm") is CC BY-NC-SA, so it was not imported;
  the CC-BY Sand Atlas micro-CT grain remains. Lincoln Financial Field and the suggested Everest
  model were not downloadable. The field is now a procedural NFL-sized diagram; Everest is derived
  from Mapzen elevation tiles with Mapzen/USGS attribution.

## Session log

- 2026-09-26 (Claude): 3D distance bracket for Earth-Moon/AU (replacing the SVG overlay), `?item=`
  deep links, red blood cell rests unrotated, metallic Eiffel Tower (`environment`), procedural
  light wave for Visible Light Wavelength, recolored-Sun Betelgeuse, Virus → SARS-CoV-2 (91 nm),
  Football Field corrected to 91.44 m (100 yd), `scripts/preview_glb.cjs`, junk files removed.
  Later the same day: bracket lines switched to center-to-center with thin body outlines; hydrogen
  cloud cut at its 95% sphere (3.15 Bohr radii) with the Bohr radius marked; light wave with E (red)
  and B (blue) arrows and labels; SEM-style procedural hair; date-accurate procedural solar system
  (JPL elements); weathered Eiffel Tower; football field (Milton Frank Stadium scan); Everest as a
  block diagram on sea level; DNA deduplicated (3.4 → 0.37 MB); new Statue of Liberty item (46.05 m)
  with a cropped replica scan (`scripts/crop_glb.py`). See the git log for details.

## 2026-09-27 continuation

- SI-prefix notation is capped at three significant figures; the notation toggle
  cycles through scientific, mathematical, human-readable, and SI modes.
- Hydrogen is bounded at one Bohr radius (about 32.3% enclosed probability), and
  carbon has a labeled independent-electron 1s²2s²2p² orbital diagram. Seven
  wavelength anchors were added to Length, with separate Markdown plaques.
- The animated EM wave uses E/B unit-vector labels. The bacterium is a CC-BY
  illustrative pilose rod, with species uncertainty stated. The mitochondrion
  and football field use procedural illustrations instead of the prior cartoon
  cutaway/stadium scan. Everest uses a 602 kB DEM-derived opaque terrain block.
  The Statue of Liberty now uses a hand-modeled CC-BY asset with an illustrative
  pedestal; its 46.05 m data value still measures the statue alone.
- `node --test tests/*.test.cjs tests/*.test.mjs` passes, as does model verification.
  Python dataset and Sketchfab tests pass separately under `venv` and system
  Python respectively; the combined invocation lacks Pillow or PyYAML in one
  environment. Full dataset verification still fails on the baseline torque drift.

## 2026-09-28 (Claude)

- Model lab + content-hash versioning (see above). Precise bounds for calibration/grounding.
- Size rule applied: hydrogen and carbon are listed as diameters (106 pm, 140 pm) and drawn
  inside those spheres (32.3% and 53.8% of electron probability inside); EM waves show one
  wavelength; Statue of Liberty is e-sfera's whole monument at 92.99 m ground to torch.
  Remaining intentional exceptions: DNA (one helical turn is 1.7x its 2 nm width) and the
  virus (spikes beyond the calibrated 91 nm envelope).
- New procedural models: iron-56 nucleus (Atomic Nucleus), Milky Way (Galaxy Diameter),
  Milky Way-Andromeda distance diagram. Andromeda Distance corrected to 2.37e22 m (2.5 Mly).
- Data note for the owner: Heliosphere is listed at 2.4e14 m (about 1,600 au) although the
  heliopause is about 120 au out; left unchanged pending a decision on the definition.
- Planet labels are placed at fixed offsets and hidden by priority (no per-frame shuffling);
  model annotations fade out below 240 px and item names below 12 px text.

## 2026-09-29 (Claude)

- Camera hops between items now `glide` (fixed 0.75-1.7 s smootherstep by pixel distance) instead of the
  spring; similar-sized neighbors previously slid a whole object width almost instantly. Similar-sized
  items keep a 0.2 (was 0.08) clearance. The renderer's near plane now hugs the nearest model, which
  removes z-fighting on thin decals.
- Football field: `football-model.js` (yard numbers, goalposts, dimension brackets), merged by material.
- Procedural `organelle-models.js`: lengthwise-cut mitochondrion (17 lamellar cristae) and a pyramidal
  neuron with an animated action potential (animation registry: `model-animation.js`; live mV readout).
  The Neuron dataset text now describes the neuron plus local dendrites (about 100 um), which is what the
  model spans.
- E and B labels carry vector arrows. Pillars of Creation (NASA/STScI) added.
- Sourcing results: no usable public model exists for Orion, Tarantula or Carina nebulae, Proxima, the
  Heliosphere or the Oort Cloud (build procedurally). Geography: Manhattan (OSM + Mapzen, value corrected to 21.6 km) and
  the Panama Canal strip (8x vertical exaggeration) were added via `scripts/build_manhattan_block.py` and
  `build_panama_canal_block.py`. Skipped as inaccurate at the size rule: Great Wall (route ~3,000 km of
  21,196), Amazon, Marathon.

## 2026-09-30 (Codex)

- Goalposts now have connecting gooseneck elbows, closed ground pads and protective
  sleeves; the old support stopped short of the crossbar and stood outside the turf.
- Added Proxima's distance diagram (Gaia DR3 distance quoted by Lauer et al. 2025)
  and a 16-member Local Group scene from McConnachie's catalog. Galaxy glyphs are
  enlarged eightfold, not physically sized. Reviewed the Jan-2021 FITS subset and
  corrected WLM/NGC 6822 distances and Leo I's coordinates. References and assumptions:
  `content/visualizations/models/sources/nearby-space-models.md`.
- Added a 672 kB Orion GLB sampled from the credited NASA/ESA Hubble field. The image
  stays 13 ly across within the listed ~25 ly region; a lower bracket indicates that
  full span. Only sky-plane color/position is observed; the shallow blister depth
  is authored from O'Dell et al. 2009, not NASA's inaccessible fly-through geometry.
  Rebuild with `scripts/build_orion_model.py`; provenance is `sources/orion-model.md`.
- Fixed optional callout offsets/leader lines keep Local Group labels from collapsing
  over the central galaxies. `labelAxis: {axis, length, minPixelLength}` hides depth
  annotations until their projected span is legible; Orion uses a side-on depth cue.
- GLB packing now handles valid nonindexed point/line primitives. Model source and
  separate scientific-basis links both appear in explorer details when provided.
- Visually inspected rest/side and actual-explorer views with the model lab. All
  157 Node tests and 21 Python tests passed; model asset/hash verification passed.
  No Length data/plaque text was changed. The audit has no page/load errors; its only
  flagged resting poses remain the documented DNA/virus size exceptions.
- Luna critic final execution/accuracy scores after three visual refinement passes:
  Proxima 8/9, Local Group 7/8, Orion 9/8. Local Group's central satellite callouts
  remain somewhat crowded; inferred nebula depth is explicitly not measured geometry.

## 2026-09-30 next model batch (Codex)

- Added an 810 kB Tarantula point cloud from ESO/R. Fosbury (ST-ECF)'s CC-BY image.
  The published angular field and distance calibrate a ~951 ly viewing aperture;
  sky-plane color/position is observed, depth is explicitly authored, not tomography.
  Rebuild with `scripts/build_tarantula_model.py`; provenance is `sources/tarantula-model.md`.
- Added AU-coordinate Oort Cloud and heliosphere scenes in `outer-solar-models.js`.
  Oort shows a flattened inner component and a diffuse outer sample, not cataloged
  comets. Heliosphere is a nose-side cutaway with a radial ruler and upwind arrow;
  no downstream boundary or physical tail length is claimed. References/assumptions:
  `content/visualizations/models/sources/outer-solar-models.md`.
- Corrected two mismatched Length definitions and values: Oort now explicitly uses
  the representative upper-range 200,000 AU diameter (2.991957414e16 m); heliosphere
  uses a 240 AU nose-region proxy (3.5903488968e13 m), not a full-tail extent.
  Existing plaque prose was retained except the necessary definition fixes.
  `scripts.dataset.rebuild_dimension length` regenerated Length only.
- Diffuse clouds opt into a generated 32px soft point sprite (`model-points.js`).
  Shader/texture behavior is local and tested; the rest of the model materials remain unchanged.
- Visually reviewed rest/side and actual-explorer screenshots. The whole-Length
  audit reports 52/66 modeled, 14 photo-only, no page/load errors. Node tests: 163;
  Python tests: 24; asset verification: 45 GLBs/53 exact-name registry matches.
- Researched Cosmicflows/SDSS/Virgo scientific catalogs; no new supercluster data
  were bundled because usable selection/redistribution rights remain unresolved.
- Independent Luna critic scores (execution/accuracy): Tarantula 8/8; after a
  second visual refinement, Oort 9/8 and heliosphere 9/8. All reached the requested
  8/10 threshold. Ruler-label separation in the heliosphere is optional remaining polish.

## 2026-09-30 Carina and horizon batch (Codex)

- Added Carina as a 735 kB, 10,400-triangle image-derived surface from ESO/J. Emerson/
  M. Irwin/J. Lewis's CC-BY VISTA field. The 193 by 157 ly image stays calibrated
  within a 300 ly context bracket. It is explicitly a gently bowed 2.5D sheet,
  not a reconstructed gas-density volume; a granular point-cloud prototype was
  replaced after visual review. Rebuild: `scripts/build_carina_model.py`;
  provenance: `sources/carina-model.md`.
- Corrected Carina's erroneous 3e20 m span to an approximate 300 ly
  (2.83821914177424e18 m) from NASA, retaining its plaque except the opening
  size definition. Only Length outputs were rebuilt.
- Added a 750 kB, 9,120-triangle Observable Universe cutaway with actual WMAP
  nine-year ILC sky data. `scripts/build_observable_universe_model.py` validates
  the original Galactic NESTED FITS, averages 64 child pixels into Nside=64,
  and samples an embedded equirectangular texture with tested HEALPix mapping.
  The original 24 MB FITS is a temporary build input, not a hosted asset.
- The textured 45.6 Gly last-scattering shell and ~46.5 Gly particle-horizon
  guides retain proportional present-distance radii. The smooth amber-rimmed
  cone is an authored viewing cut, not a hole or edge in the universe. Polar
  mesh UVs preserve Galactic directions and unwrap the longitude seam. Reference:
  `sources/observable-universe-model.md`. The existing diameter is unchanged;
  qualifiers and the plaque's misleading superluminal-recession explanation
  were corrected without a wholesale prose rewrite.
- Visually inspected rest/side and actual-explorer views and iterated with Luna
  critics: Carina execution/accuracy 8/8 after three passes; horizon 8/9 after
  two. Audit: 54/66 modeled, 12 photo-only; no page/load errors. All 163 Node
  and 34 Python tests pass. Asset verification: 47 GLBs/55 exact-name matches;
  content-hash version check passes. Baseline SQLite ResourceWarnings remain.
- A CC-BY scientist-authored CF2 nearby-Universe mesh was staged outside the repo,
  but not imported: its +/-80 Mpc/h density field is not Laniakea's boundary.
  No verified CC-BY/CC0 geometry for the original 2014 basin was found. Do not
  calibrate the wider field as a Laniakea model or invent a boundary around it.

## Open work (as of 2026-09-30, after the horizon batch)

- Intentional size exceptions flagged by `model_lab audit`: DNA (one helical turn is 1.7x its
  2 nm width) and the virus (spikes beyond the 91 nm envelope).
- The CC BY-NC-SA sand grain was declined; keep the existing CC-BY grain.
- Photo-only Length items include large-scale structures, route-length geography
  and subatomic cases without well-defined hard sizes. Carina and Observable
  Universe now have explicitly diagrammatic, calibrated assets.
- Cosmicflows-4 has a downloadable Laniakea watershed grid, but its data-reuse terms
  need confirmation. Virgo/Sloan need a documented member selection and distance basis.
- Investigate the full-build dataset drift (use `scripts.dataset.rebuild_dimension` meanwhile).

## 2026-09-30 route batch (Codex)

- Added three rotatable geographic GLBs with `scripts/build_route_models.py`:
  Boston Marathon course/terrain (638 kB), partial Amazon mainstem/basin (880 kB),
  and the mapped Great Wall network on a true-sized Earth (1.15 MB). Each is
  below 1.5 MB and 34k triangles, embeds its textures, and has no decoder/runtime
  source-data dependency. Inspect with `model_lab.cjs shot` and `explorer`.
- Route/inventory length is not geographic extent. No coordinate geometry is
  stretched to the catalog value: each has a separate straightened total-length
  ruler. The Amazon's selected 3,053 km reach ends inland, not at the Atlantic;
  tributaries are separate context. The Great Wall data is incomplete community
  mapping, not the official heritage inventory or one continuous wall.
- Boston's OSM relation has one connected 265-way start-to-finish path. Its
  42.417 km road-centerline sum is not the certified 42.195 km shortest running
  line. Drape on the rendered terrain triangles, not finer DEM samples that can
  be buried by the coarse mesh. Relief is 12x and bare-earth, not road grade.
- Minimum Length definition/source fixes only: Amazon now uses the NASA/ESA
  approximate 6,400 km estimate; Great Wall uses the reported 21,196.18 km
  combined walls-and-trenches survey total, explicitly not meter-level precision.
  Marathon remains 42,195 m. Only Length outputs were rebuilt.
- Geometry/source/license/rebuild details: `sources/route-models.md`. Compact
  GeoJSON inputs live under `content/visualizations/models/sources/routes/`.
  OSM-derived inputs retain ODbL and their machine-readable derivative databases;
  these are separate from the project's CC0 quantitative facts. Natural Earth
  land is the existing `content/visualizations/land.geojson`, public domain.
- Three visual refinement passes and separate Luna critics: all final execution
  and accuracy scores 8/10. Remaining limitation: exactly edge-on terrain/rulers
  compress naturally; Amazon's inland-end label is culled in the smaller scrolling
  view but remains visible in the isolated/rest review and stated in the note.
- Verification: 163 Node tests, 42 Python tests, 50 self-contained GLBs/58 exact-name
  matches. Length audit: 57/66 modeled, no page/load errors; only the previously
  documented DNA/virus resting-size exceptions. Content-hash check passes.

## 2026-10-01 remaining Length batch (Codex)

- Added five explicit particle-scale measurement diagrams in
  `particle-scale-models.js`: derived Planck length, HERA effective quark-radius
  upper limit, proton rms charge radius, classical electron radius, and a 1 MeV
  neutrino wavelength. They do not claim solid particle boundaries. The proton
  profile is schematic and continues beyond its rms marker. Definitions and
  primary sources: `sources/particle-scale-models.md`.
- Added SDSS DR17 catalog windows for Virgo (937 galaxies, 30 kB) and Sloan
  (7,998 galaxies, 200 kB). Native coordinates stay in comoving Mpc; calibration
  uses the item's reference length, not a stretched bounding box. The cuts are
  survey windows, not structure/member boundaries, explicitly labeled on stage.
  BOSS/eBOSS use the recommended NOQSO classification/redshift/warning fields;
  legacy spectra use their regular fields. Source CSVs and exact queries are
  retained. Rebuild offline with `build_large_scale_catalog_models.py
  --catalog-dir content/visualizations/models/sources/catalogs --output-dir /tmp/x`.
- Added a 40 kB Hercules-Corona Borealis evidence diagram: actual Swift
  spectroscopic GRB directions (42 at z=1.6-2.1), a separate comoving-distance
  inset, and a calibrated reported-extent ruler. It is not invented wall geometry.
  The 16 amber events are inside the broad 2020 sky guide, not the original
  2014 one-eighth-sky membership. The explorer title says "Putative ... structure".
  The immutable October 1 catalog snapshot and extraction/bias qualifications
  are in `sources/catalogs/` and `sources/grb-structure-model.md`.
- Corrected mismatched Length definitions/values for Virgo, Laniakea, Sloan,
  the putative GRB structure and particle scales; retained existing plaque prose
  except fact/definition corrections. Renamed the misleading intrinsic
  "Neutrino" size to "1 MeV Neutrino Wavelength" and copied its original/thumbnail
  to the new slug. Rebuilt Length only, not unrelated dimensions.
- Laniakea remains photo-only. `build_laniakea_model.py` can stage the credited
  CC-BY CF4 figure as a reference preview, but its metadata is intentionally
  non-importable. A flat article figure is not a calibrated 3D basin; the public
  grid's redistribution terms remain unverified. See `sources/laniakea-model.md`.
- Added `model_lab.cjs coverage --gap 1 --json` and `model_coverage.cjs` for
  model/provenance inventory and largest adjacent log gaps. `window.modelLab.catalog()`
  exposes the same inventory. This supports planning 200-300 meaningful anchors,
  not scientific approval or artificial gap-filling. Review source rights,
  quantity definitions, calibration, rest/rotated views and actual explorer views
  before importing; popularity/votes cannot replace those checks.
- Independent Luna critics after two refinement passes: all five particle
  diagrams execution/accuracy 8/9, Virgo and Sloan 8/8, GRB diagram 8/9.
  Own visual checks used isolated/rest/side and settled production explorers.
  Corrected a caption-transform bug: Python uses Three.js intrinsic XYZ ordering
  and maps pitch/yaw/roll explicitly; regression-tested with mixed-axis rotation.
- Verification: all 170 Node and 65 Python tests pass; 53 self-contained GLBs
  and 61 exact-name registry matches verify. Whole-Length audit: 65/66 visualized,
  only Laniakea photo-only, no load/page errors. Only the documented DNA/virus
  size exceptions remain flagged. Content hashes and diff whitespace pass.
  Pre-existing SQLite ResourceWarnings and full-dataset torque drift remain.

## 2026-10-02 Angular and mobile batch (Codex)

- Angular models now bind an absolute phase to named mechanical pivots through
  `angular-rig.js`; housings, coils, brake calipers, clock faces and fixtures stay
  fixed. Downloaded a CC-BY arsdever drone motor/propeller (338 kB, 6,300 triangles).
  Added illustrative clock-hand, record-player, microwave, bicycle/car wheel,
  washer, hard-drive, blender and centrifuge mechanisms. Existing fan blades and
  NASA planet models have angular-only bindings, leaving Length poses unchanged.
  Source and representation notes live in `sources/angular-motion.md` and
  `sources/angular-machines.md`. High apparent rates freeze rather than alias;
  the fitted-time control makes their rotation visible.
- Spatial touch gestures capture one pointer immediately, preserve vertical model
  rotation, snap the camera to the finger while panning, and retain release inertia.
  Touch hover is disabled; native controls and normal page/detail scrolling remain
  separate. Rotation redraws are coalesced without discarding velocity samples.
- All explorers have a fullscreen control: native element fullscreen where supported,
  an immersive fixed-viewport fallback otherwise. Escape, browser exit and
  mode/dimension changes restore overflow and scroll. Mobile toolbar rows and
  bounded detail panes keep controls reachable.
- Renderer resizing now happens only when dimensions change; projected picking
  hulls are cached by transform/viewport, using a combined projection matrix.
  Coarse-pointer devices cap rendering at 1.5 device pixels per CSS pixel and
  galaxy clouds at 4,500 points, retaining their structure and calibration. Mobile
  Chromium Milky Way rotation CPU render times fell from about 4.2 ms to 1-2 ms;
  this is not a physical-phone frame-rate guarantee.
- Reusable model-lab `angular`, `mobile` and `performance` commands exercise the
  production renderer. All 22 modeled angular labels passed rotor, fixed-fixture,
  pivot and high-rate checks; an independent visual critic rated execution 8/10
  and accuracy 9/10. No dataset values or plaque prose were changed in this batch.
- Every GLB, including the new drone, verifies. Full asset verification still fails
  on a pre-existing committed `licenses/kenney-food-kit.txt` provenance checksum
  mismatch; the license file and its lock entry were not changed here.
- Final checks: 198 Node tests and 11 Sketchfab Python tests pass; the mobile lab
  passes 13 touch/fullscreen/lifecycle checks with no page errors. Content hashes
  and diff whitespace checks pass. Chromium touch emulation is verified; actual
  iOS/Android hardware testing remains necessary.

## 2026-10-15 session (Claude + Codex): wonder pass

Models (all checked in the real explorer with model_lab):
- Nebulae as 3D glowing volumes from real photos: Orion (Hubble + KPNO wide image; O'Dell 2009 /
  Pabst 2019 geometry), Carina (NOIRLab/N. Smith), Tarantula (ESO), Crab (Hubble; prolate filament
  shell), Ring (Webb; barrel seen end-on), Pillars (STScI 3D mesh wearing Hubble's image).
  Pipeline: scripts/nebula_volume.py + build_nebula_volumes.py (crab/ring/orion/carina/tarantula),
  build_pillars_model.py. Sprites are calibrated so the front view reproduces the photo
  (tests/test_nebula_volume.py). `pointSize.conserve` keeps brightness when capped/thinned.
- Also from real catalogs: Local Group (74 McConnachie galaxies + M31 gas halo + MW dark halo,
  build_local_group_model.py), Virgo Supercluster (869 2MRS galaxies, build_laniakea_galaxies.py
  --region virgo), Pleiades (1,280 Gaia members, build_pleiades_model.py), Andromeda (KPNO image on a
  77-degree disk, build_nebula_volumes.py andromeda). New items Muonic Hydrogen Atom and Weak Force
  Range (procedural, atomic-models.js / particle-scale-models.js); Length caps now 300/320.
- Milky Way (NASA/JPL concept + 26k 3D stars), Laniakea (11,733 real 2MRS galaxies,
  build_laniakea_galaxies.py), Hercules-Corona Borealis (reported region as a light-cone slab,
  build_hcb_lightcone_model.py), Electron (field-energy picture of r_e), Compton wavelengths
  (electron/muon/proton/tau), Human Height (Renderpeople photoscan, CC BY).
- From Codex jobs: Neuron (NeuroMorpho NMO_109111 with axon + action-potential wave; item now
  0.8 mm), Fruit Fly Brain (2,200 FlyWire neurons, CC BY Zenodo deposit; 0.8 mm), angular models
  (34/42 observations animated), Mitochondrion (OpenOrganelle FIB-SEM, item now 4.3 um,
  build_em_mitochondrion.py; procedural override removed).
Data:
- Length now has 255 items (Codex items job + review). Pillars of Creation fixed to 5 ly.
  New photos are credited in images/credits/length.json (CC BY / CC0 / PD only).
- 25 items still show a gray placeholder; queued for Codex (images2 / space3d / bio3d / earth3d).
  Those worktrees branch from a15f1ff, before the later model commits: expect version-hash and
  models.json conflicts when merging (resolve as described below).
Tools: scripts/repair_glb.py (validator fixes); asset lock records Kenney licenses as stored (LF).

Codex workflow (the owner has spare Codex capacity):
- Worktrees in ../universe-scales-codex/<job> on branches codex/<job>; briefs in
  ../universe-scales-codex/briefs (common.md + <job>.md); run with ../universe-scales-codex/run.sh <job>
  (codex exec, workspace-write sandbox with network). The sandbox blocks git commits and Chromium:
  the lead commits each worktree, runs model_lab on it, then merges into main. Version-hash merge
  conflicts: keep either side and rerun scripts/bump_versions.py. models.json conflicts: keep main's
  and re-register from handoff/<job>/<id>.entry.json. Registering needs the dataset item to exist.
- Round 2 (2026-10-16, merged): earth3d (14 models), bio3d (9 PDB/COD molecules), space3d (29 NASA
  bodies/spacecraft + MOLA terrain; no report, Codex hit its usage limit), images2 (17 photos).
  The lead browser-checked every model (model_lab shots; extents 0.8-1.3x) before merging.
  129 of 257 Length items now have models; 6 still have no photo.
- Round 3 (merged 2026-10-16): space3d2 (15), earth3d2 (7; caveat labels hidden via
  presentation.remove_nodes, display labels plain), bio3d2 (12; OpenAI's bio filter refused a brief
  that listed viruses/bacteria, so keep microbes out of Codex briefs), images3 (4 CC0 diagrams plus a
  review of every Length photo: see handoff/images3/REPORT.md for wrong-subject findings).
  163 of 258 items now have models. Merge helper used: a script that keeps main's models.json /
  validation.json, union-merges sketchfab-length.json, appends AGENTS.md sections and re-registers
  handoff entries.
- Round 4 (merged 2026-10-16; Codex hit its usage limit after ~20 min, three jobs without reports):
  images4 (16 wrong-subject photos replaced, 9 added), earth3d3 (7), terrain3d (9 DEM models),
  space3d3 (15 diagrams; found Sun-Neptune stored in km, fixed to 4.515e12 m), micro3d (4 kept; six
  bare primitives left out because their photos/diagrams explained more). Lead added T4 phage and
  mimivirus (Sketchfab CC BY) and a Mycoplasma schematic (scripts/build_mycoplasma_model.py): OpenAI's
  bio filter blocks microbe briefs. 201 of 258 items modeled.
- Round 5 (merged 2026-10-18), under the owner's Codex-only public-data rule (see "Adding or replacing
  a model"): earth3d4 (fruit fly micro-CT, a T. rex replica scan scaled to SUE), terrain3d2
  (Appalachian Trail, El Reno, Chicxulub gravity), deepsky3d (Gaia LMC and Omega Centauri, Edenhofer
  dust Orion Arm, 2MRS Local Void, SDSS Bootes Void). Lead rejected after WebGL review: Mount Thor
  (DEM reads as a draped sheet), Hunga Tonga (sparse floating stereo samples) and the BOSS BAO slice
  (141 points read as noise); their builders keep them in `UNREGISTERED` with pinned inputs. Dataset
  wording fixed for Bootes Void (H0 = 50 convention) and Porphyrion (6.43 Mpc projected, ~7 Mpc total,
  checked against arXiv:2411.08630). 211 of 258 items modeled. Each job's REPORT.md lists what it
  searched for the 47 photo-only items; most lack openly licensed scans or data, so further models for
  them are Claude's to build (procedural is allowed for Claude, not Codex).

## 2026-10-16 radial Length explorer (Claude)

- journey.js `radialLayout`/`radialPlacement`/`radialFocus`: Scale-of-the-Universe layout. Each item
  sits at a fixed position whose distance from the center is proportional to its size (golden-angle
  directions; deterministic search over nearby angles and radii so boxes, including labels, of items
  within 60x in size never overlap; cached per item set and aspect). The camera only zooms; the
  selected item is the one at the camera's scale; hops glide the zoom. Used for Length only
  (spatial.js `radial`); area/volume/counts keep the linear layout. tests/radial-layout.test.cjs.
- Labels: readable minimum (11 px), max 26 px, fade in from 28-56 px objects, greedy collision culling.
  Objects under 14 px show photos instead of loading 3D models.
- Clip planes use a per-model bounding sphere (models.js boundRadius); additive glow writes
  premultiplied color with alpha = brightness (model-points.js) so Safari/Firefox show it.
- Note: the Hindenburg model keeps its historical swastika tail markings; the owner may want them
  removed. The 747 carries an Air China livery from the CC BY source.

Open questions for the owner: CF4 Laniakea basin mesh rights (unused; galaxies used instead);
alternative human models (X-ray skeleton, walking woman) available on request; public repo history
still contains an email address (removing it needs a history rewrite).
## 2026-10-16 bio3d worktree handoff

- Nine CC0 coordinate-derived assets add C60, graphite interlayer spacing,
  actin, nucleosome, spike ectodomain, microtubule, yeast ribosome, human nuclear
  pore scaffold and TMV. Native model units are nm, with explicit physical
  `reference_size` calibration. Do not normalize their bounding boxes to 1.
- Offline builders: `scripts/build_bio3d_models.py` and
  `scripts/build_graphene_spacing.py`. Source refresh is separate:
  `scripts/prepare_bio3d_sources.py`. Compact pinned coordinates, deposited
  assembly transforms and citations live in `models/sources/bio3d/`.
- `scripts/audit_bio3d_models.mjs` uses the actual vendored GLTFLoader and checks
  normalized geometry; `scripts/preview_bio3d_cpu.py` renders labeled CPU
  rest/side previews. These do not verify WebGL, perspective or mobile UI.
- Actin/microtubule/TMV ends are authored cuts; spike lacks the unresolved stalk;
  NPC is an integrative C-alpha scaffold envelope. Full notes, skipped items,
  final entry JSONs and integration checks: `handoff/bio3d/REPORT.md`.
- No dataset/exports/images changed. Browser and commit checks remain for the
  lead outside this sandbox. All nine new GLBs validate without errors/warnings;
  full validation encounters 17 existing non-unit normals in the unchanged
  `em-mitochondrion-jurkat` asset, owned by the mitochondrion job.

## 2026-10-16 earth3d2 handoff

- Added seven Length assets: African elephant and sperm-whale artistic exteriors,
  an original dimensioned Ever Given, Golden Gate **main span only**, Arecibo's
  **pre-collapse reflector only**, FAST's **nominal spherical reflector only**,
  and a true-relief Kilimanjaro **summit window above sea level**. No existing
  models replaced and no dataset/exports/images/runtime JS/CSS edits.
- Offline builders: `build_earth3d2_structures.py`, `build_earth3d2_ship.py`,
  `build_earth3d2_terrain.py`. Imported animals use the Python bind-pose bake and
  JS optimization in `prepare_earth3d2_imports.*`. The JS tool takes an optional
  `elephant` argument to preserve its original base color/textures. Regenerate
  tangents after skin baking. `display_label` belongs at registry top level.
- The elephant measures Y because its neutral pose's highest point is the withers,
  not the head; rest is almost frontal. Broadside body length is naturally larger
  than shoulder height. Kilimanjaro's sea-level walls are arbitrary display cuts,
  not real cliffs or the mountain's base. Telescope panel patterns are illustrative.
- Seven GLBs under 3 MB, zero validator errors/warnings; all CPU resting extents
  within 0.6–1.3×. Node: 225 passing; Python: 104 tests with one existing skip.
  All assets and version references verify. Browser/commit sandbox failures were
  not retried per the lead. CPU previews are not WebGL approval; production shots,
  size/picking/grounding audit, actual explorer and mobile review remain pending.
- Final entries, sources, deferred targets, integration and review details:
  `handoff/earth3d2/REPORT.md`. Official SUE scan is CC BY-NC and was excluded.

## 2026-10-18 terrain3d2 handoff

- (Lead: Thor and Hunga were later unregistered, see round 5 above.) Five direct public-data additions: Mount Thor terrain, the NPS Appalachian
  treadway over relief, an NWS El Reno damage-survey crop over USGS terrain/NAIP,
  measured NASA Hunga Tonga stereo cloud tops, and a Chicxulub gravity-anomaly
  surface. Ten other targets were skipped with specific source/calibration
  reasons in `handoff/terrain3d2/REPORT.md`. No dataset/exports/images/runtime
  JS/CSS changes; no invented rulers, blocks, walls, traces or plume volume.
- Offline builder: `scripts/build_terrain3d2_models.py`; `--prepare` optionally
  acquires sources (NASA preparation alone needs netCDF4). Pinned grids, original
  vectors, requests and rights metadata: `models/sources/terrain3d2/`.
- Thor's height map cannot resolve its overhang; Hunga intentionally retains
  sparse retrieval gaps; El Reno shows damage coverage, not a funnel-width
  boundary. Chicxulub's plotted vertical coordinate is 500 display m/mGal,
  **not crater depth**. The trail is the June-2023 alignment, not a 2024 inventory.
- Existing audit/CPU scripts now accept the new handoff: `node
  scripts/audit_terrain3d_models.mjs terrain3d2` and `./venv/bin/python
  scripts/preview_terrain3d_cpu.py --job terrain3d2`; original defaults unchanged.
- Five GLBs below 2.34 MB / 42k triangles, zero validator errors/warnings.
  Vendored-loader CPU resting extents pass 0.6–1.3×; all final rest/quarter CPU
  previews were viewed. Node: 228 passing; Python: 145 run, one skip. Asset and
  version checks pass. Full validation has zero errors and existing warnings in
  nine unchanged assets. Browser/mobile/production audit remain for the lead;
  known Chromium/git sandbox limits were not retried. Work is uncommitted.

## 2026-10-18 deepsky3d handoff

- (Lead: the BAO slice was later unregistered, see round 5 above.) Six additions from public data: inclined Gaia LMC candidates, bright Gaia Omega
  Centauri members on an explicitly flat distance plane, Edenhofer's actual local
  3D dust grid for Orion Arm, 2MRS Local Void and SDSS Bootes/BOSS BAO sections.
  No synthetic objects, depth, rulers or boundary shapes. Existing models untouched.
- Offline builder: `scripts/build_deepsky3d_models.py`; source preparation:
  `prepare_deepsky3d_sources.py` and `prepare_deepsky3d_dust.py`. Pinned numeric
  sources, original hashes and dust FITS byte-range hashes: `sources/deepsky3d/`.
  Dust acquisition uses exact source ranges rather than the entire 15.66-GB FITS.
- Native physical coordinates are calibrated by explicit `reference_size`, never
  stretched to the bounding box. Bootes retains its source's historical H0=50
  convention; BAO is a real catalog sample at the separation scale, not a shell.
- Six GLBs total 781 kB, each below 0.4 MB, with zero validator errors/warnings.
  Node: 228 passing. Python: 149 run, one existing skip. Assets/versions pass.
  All CPU rest/quarter/small previews viewed and vendored-loader extent checks pass.
  These do not certify WebGL, production size audit, radial explorer or mobile.
- Final entries, skipped-source research, exact Bootes/Porphyrion wording fixes
  and review limits: `handoff/deepsky3d/REPORT.md`. No dataset/exports/images or
  runtime JS/CSS changes. Browser/git sandbox restrictions were not retried;
  changes remain uncommitted for the lead. No shared-venv dependencies installed.

## 2026-10-23 upgrade3d handoff

- Reviewed 32 illustrated Length targets; only Basketball was replaced, using
  robin.sculac's CC-BY 3DF Zephyr photoscan. It retains the photographed wear,
  colors and proportions, uniformly calibrated to the representative catalog
  diameter; the source's own specimen size is unknown. No new geometry authored.
- Import: `scripts/prepare_upgrade3d_imports.mjs`; vendored-loader audit:
  `scripts/audit_upgrade3d_models.mjs`; old/new CPU comparisons:
  `scripts/preview_upgrade3d_cpu.py --old-model OLD.glb`. Source pins and full
  per-item search/skip decisions: `handoff/upgrade3d/REPORT.md`.
- Final scan is 434 kB / 16,472 triangles, with zero validator errors/warnings
  and 1.000x CPU resting extent. Titanic already has a black upper hull.
  Football Field's procedural override still precedes its stored scan; unchanged.
- Node: 236 passing; Python: 161 run, one existing skip; all 202 GLBs / 212
  matches and version hashes verify. Full validation has no errors and existing
  warnings in nine unchanged assets. No dataset/images/runtime JS/CSS edits.
  Browser and git sandbox limits were not retried per the lead; changes remain
  uncommitted, with production WebGL/explorer/mobile review for the lead.

## 2026-10-23 retry3d handoff

- Registered M87 Jet as a direct XJET HST/WFPC2 FITS sky-plane intensity map:
  9,689 original pixels, zero inferred depth, 156 kB, 1.041× resting extent.
  Source WCS/physical scale, public-domain grant, display cuts and date mismatch
  are documented in `sources/retry3d-m87-hst-map.md`; no jet volume was invented.
- `build_retry3d_m87.py` rebuilds/registers that map offline. The separate
  `build_retry3d_models.py` prepares NOAA ETOPO 2022 Baikal/Mauna Kea surfaces
  but deliberately does not register them: vertical ranges are faithful while
  overall footprints exceed the size rule. Axis/framing proposals, all 25 target
  searches and a rejected new Giza scan are in `handoff/retry3d/REPORT.md`.
- `preview_retry3d_cpu.py` and `audit_retry3d_models.mjs` supply CPU review and
  actual vendored-loader checks. All three GLBs validate without errors/warnings;
  236 Node tests and 167 Python tests (one existing skip) pass. Browser review
  and commit remain for the lead under the brief's known-sandbox instructions.
  No runtime, dataset, exports or image files changed.

## 2026-10-29 volume3d source imports

- Four independent Volume entries add five exact matches: Arkify's sugar-cube
  scan, NIAID influenza/SARS-CoV-2, and renderartestudio's tub for both bathtub
  labels. Coverage is 29/55; all 31 prior gaps are dispositioned in
  `handoff/volume3d/ledger.json`. Existing entries and Length calibration remain
  unchanged; SARS-CoV-2 reuses its existing binary.
- Only sugar is enclosed-volume calibrated: its scanned exterior is a closed
  bulk envelope. Four tiny reversed internal pore shells are excluded, with
  per-vertex containment checks. Virus cutaways/spikes and tub capacity use the
  brief's explicit equivalent-span fallback, not a mesh-volume measurement.
- Rebuild: `prepare_volume3d_imports.mjs STAGED_DIR MODULE_ROOT`; register/check:
  `register_volume3d.mjs [--check]`; loader audit: `audit_volume3d.mjs`.
  Three new binaries total 3.20 MB; each is below 1.2 MB. Source records,
  acquisition pins, final entries, CPU previews and limits: `handoff/volume3d/REPORT.md`.
  Browser/mobile review and commit remain for the lead per this round's brief.

