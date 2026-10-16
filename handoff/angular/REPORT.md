# Angular Velocity model and spin review

Branch: `codex/angular`. No pushes, merges, rebases, dataset rebuilds, package
installs or changes to sibling worktrees. No GLB bytes changed.

**Commit blocked by the environment.** The requested `git add`/commit attempt
failed before staging: Git could not create
`universe-scales/.git/worktrees/angular/index.lock` (`Operation not permitted`).
The approval policy does not allow escalation. Changes remain in this worktree;
`venv` was already untracked on arrival and is excluded from the deliverable.
An apply-ready binary patch of all job files is provided as
[`angular.patch`](angular.patch), also saved at `/tmp/universe-angular.patch`.
No commit was created. After applying/staging in an unrestricted session, use
the commit message **“Fix angular models, full-turn framing and repeated-pattern
aliasing”**, ending with `Co-Authored-By: Codex <noreply@openai.com>`.

## Result and verification limit

Reviewed all **42 dataset observations**, including repeated names: **34 now use
animated 3D models**, and **8 retain circular orbital diagrams**. Previously six
of the spin observations had no model. Dataset inventory/rates are from
[`data/angular-velocity.yaml`](../../data/angular-velocity.yaml), opened locally;
no scalar value or plaque prose was edited.

**Production browser review is blocked.** Both initial and final
`node scripts/model_lab.cjs angular ...` attempts failed at Chromium launch:
`mach_port_rendezvous_mac.cc: bootstrap_check_in ... Permission denied (1100)`.
The sandbox does not permit an approval escalation. Consequently there are no
new production screenshots, mobile results, WebGL lighting checks or hardware
performance claims. The final attempted command was:

```sh
node scripts/model_lab.cjs angular /tmp/angular-browser-final --times 0.1,1,2
```

I generated and LOOKED at flat geometry previews of all 34 modeled observations
at five phases, iterating the engine, washer, clearance and framing corrections.
These deliberately omit textures, reflections, perspective and production UI.
The source GLBs are loaded with the vendored glTF loader, and previews/audit use
the production procedural builders and angular rig. They do **not** certify
browser appearance or final visual polish. Re-run the browser lab on main where
Chromium is allowed before considering the visual review finished.

## Changes

- Added original, sourced procedural inspection diagrams for the London Eye,
  axial gas-turbine stage, dental air turbine and three pulsar observations.
  Capsules travel around the wheel while counter-rotation keeps floors level.
  Source checks, authored assumptions and licensing are documented in
  [`angular-inspection.md`](../../content/visualizations/models/sources/angular-inspection.md).
- Reused the existing CC0 Innerscene bicycle for all three bicycle labels.
  Its frame/chain/pedals stay fixed and both wheels coast. Also corrected the
  unused procedural fallback's fork so it straddles the wheel along the axle.
- Corrected HDD arm/suspension/head continuity and clearance above the platter;
  moved washer stationary rear wall/counterweights behind the moving back plate
  and dampers outside the drum; added rear-face perforation recess cues.
  Blender bearing is now an annulus below its hub, and the record stylus reaches
  its record. Fan is explicitly viewed from underneath.
- Exposed the existing sourced crankshaft in an authored 55-degree oblique
  inspection view. Its journals previously disappeared behind an end flange in
  the axial view. Shaft rotation still projects clockwise.
- Framing now measures a full turn once. The existing thin drone propeller grew
  almost fourfold in projected height after a quarter turn; its full envelope
  now establishes size, grounding and camera-depth placement. This path applies
  only to angular rigs; Length framing is unchanged.
- Preserved `theta = omega * simulated seconds` and observation-specific speeds.
  Fitted time remains one turn per four real seconds. The freeze threshold now
  accounts for repeating spoke/blade details, since they can appear to reverse
  below the old eight-whole-turns-per-second threshold. Counts are display hints
  based on the rendered geometry. Both model and phase guide freeze together.
- Orbital centers now say Sun or Earth. The explanation identifies these as
  circular mean-speed diagrams with illustrative size/distance and a clockwise
  display convention; they are not ephemerides or rotation models.
- Browser lab now covers every observation instead of skipping missing models
  and collapsing duplicate names. It checks all phases, allows intentional
  geared counter-rotation, samples a non-symmetric phase, and accepts explicit
  simulated seconds with `--times`. Files include the observation index.
- Added browser-free geometry audit/preview scripts for restricted sessions.
  Updated AGENTS/source notes and ran content-hash versioning.

## Every observation

Indices below match the generated audit and preview filenames. “Keep” means
the geometry/rig review found the representation suitable within its stated
limitations; it does not mean a new browser screenshot passed. Every modeled
row passes fixed-part, local-pivot, clockwise-primary, rotation-envelope and
fitted-time checks. “Static at real time” is intentional alias protection;
Fit time reveals the correct direction at 0.25 turns per real second.

| # | Observation | Verdict / correction | At real time |
|---|---|---|---|
| 0 | Pluto orbit around the Sun | Keep circular orbit; label Sun center, clarify mean speed. | Extremely slow orbit |
| 1 | Mars orbit around the Sun | Keep circular orbit; label Sun center. | Extremely slow orbit |
| 2 | Earth orbit around the Sun | Keep circular orbit; label Sun center. | Extremely slow orbit |
| 3 | Venus orbit around the Sun | Keep mean-speed orbit; label Sun. Dataset prose error below. | Extremely slow orbit |
| 4 | Mercury orbit around the Sun | Keep mean-speed orbit; label Sun. | Extremely slow orbit |
| 5 | Moon orbit | Keep circular orbit; label Earth center. | Very slow orbit |
| 6 | Moon orbit around Earth | Same diagram, independently retained observation. | Very slow orbit |
| 7 | Earth rotation | Keep NASA globe, Y polar spindle, south-pole clockwise view. Texture not re-reviewed in browser. | Very slow spin |
| 8 | Hour hand (rounded value) | Keep selected short hand only; clockwise Z spindle, fixed dial/case. | Very slow spin |
| 9 | Hour hand (precise value) | Keep separate observation/rate; same hand mechanism. | Very slow spin |
| 10 | Saturn rotation | Keep NASA globe-only Y spin; rings fixed as orbital context, not claimed static matter. | Very slow spin |
| 11 | Jupiter rotation | Keep NASA globe, Y polar spindle and south-pole view; differential atmosphere not simulated. | Very slow spin |
| 12 | ISS orbit | Keep circular orbit; label Earth. Station image identifies orbiter; it is not spun about its own center. | Slow orbit |
| 13 | Minute hand (rounded value) | Keep long selected hand, fixed clock dial. | Slow spin |
| 14 | Minute hand (precise value) | Keep independent rate; same mechanism. | Slow spin |
| 15 | London Eye | Added full-complement 32-capsule wheel with fixed A-frame/axle and level capsule floors. | Slow spin |
| 16 | Second hand | Keep continuous sweep at listed speed; no ticking claim. | Visible spin |
| 17 | Microwave turntable | Keep plate/food/turntable Y rotation; cavity fixed, roof/door omitted. | Visible spin |
| 18 | 33 1/3 rpm record | Keep clockwise platter/record; fixed tonearm; stylus now reaches record. | Visible spin |
| 19 | 45 rpm vinyl record | Same corrected mechanism, independent listed rate. Record proportions illustrative. | Visible spin |
| 20 | 78 rpm record | Same corrected mechanism, independent listed rate. No specific historical disc size implied. | Visible spin |
| 21 | Ceiling fan (10 rad/s) | Existing four-blade source; view underside, only blades turn, fixture/light fixed. | Visible spin |
| 22 | Ceiling fan (15.7079632679 rad/s) | Same geometry; account for four repeated blades before aliasing. | Static |
| 23 | Bicycle wheel at 20 km/h | Replace broken-fork fallback with existing CC0 bicycle rig; wheels rotate, frame/drivetrain fixed. | Static |
| 24 | Bicycle wheel at city speed | Same replacement, preserving this observation's own speed. | Static |
| 25 | Bicycle wheel | Keep existing CC0 rig; add spoke-pattern alias protection. | Static |
| 26 | Car wheel at 60 mph | Keep tire/rim/hub/brake-disc Z rotation; red caliper and axle carrier fixed. No road translation. | Static |
| 27 | Washing machine spin | Correct fixed wall/counterweights/dampers; drum, recesses and lifters rotate. | Static |
| 28 | Washing machine spin cycle | Same corrected washer; independent listed rate. | Static |
| 29 | Car engine | Existing sourced crankshaft, local Z spindle; oblique view reveals journals. Pistons/rods/block omitted. | Static |
| 30 | Blender blade (500 rad/s) | Correct stationary bearing below hub; only blades/shaft turn; open jar/lid omitted. | Static |
| 31 | Hard drive platter at 5400 rpm | Correct connected fixed head/arm above rotating platter stack and spindle. | Static |
| 32 | Drone propeller | Keep real local-Z rotor bell/blades, fixed coils/stator; fix full-turn framing. | Static |
| 33 | Hard drive platter at 7200 rpm | Same corrected HDD, independently follows listed speed. | Static |
| 34 | Hard drive spindle | Same corrected HDD, independent rounded speed. | Static |
| 35 | Pulsar | Added neutron-star/tilted magnetic-axis/beam schematic; no observed texture or plasma reconstruction claim. | Static |
| 36 | Fast gas turbine | Added axial disk/blade/shaft rotor, fixed nozzle row/casing; not a compressor substitute. | Static |
| 37 | Blender blade (2094.3951023931954 rad/s) | Same corrected blender, retaining this separate speed observation. | Static |
| 38 | Fast millisecond pulsar | Same schematic, independent listed angular speed. | Static |
| 39 | Fastest known pulsar | Same schematic; no object-specific geometry or new claim about record-holder status. | Static |
| 40 | Ultracentrifuge rotor | Keep fixed-angle exposed rotor/tubes/caps on Y; stationary outer base. Protective cover omitted. | Static |
| 41 | Dentist drill turbine | Added air bucket rotor/chuck/bur on Z; housing/nozzle/outer bearing races fixed. Bur foreshortened axially. | Static |

The Length 0.6–1.3x size audit cannot compare a machine's physical dimensions
with a value in rad/s. Angular models are illustrative apparatus, fitted to
the existing display budget. The full-turn audit checks their envelopes;
actual browser/UI framing still needs the blocked production review.

## Checks and artifacts

- `node --test tests/*.test.cjs tests/*.test.mjs`: **217 passing**, zero failures.
  Regression coverage includes level capsules, blade/casing clearance,
  HDD clearance, washer fixed rear geometry, oblique direction, thin-propeller
  framing and spoke-aware aliasing.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **73 run, OK, 1 skipped**. Baseline SQLite ResourceWarnings remain.
- `python3 scripts/fetch_model_assets.py --verify`: all GLBs pass their
  hash/self-containment checks. Overall command fails on the pre-existing
  `licenses/kenney-food-kit.txt` provenance-record checksum mismatch.
- `python3 scripts/bump_versions.py --check`: zero stale references.
- `git diff --check`: passes.
- No GLBs were changed, so the requested conditional glTF validator run was
  not applicable. No packages were installed in the shared venv or elsewhere.
- `node scripts/audit_angular_models.mjs /tmp/angular-final --previews`:
  passes all 34 model observations at six phases including return to rest;
  retains all 8 orbital observations in inventory. Saved in
  [`geometry-audit.json`](geometry-audit.json).
- `./venv/bin/python scripts/render_angular_preview.py /tmp/angular-final`:
  five geometry phase images per modeled observation, with simulated seconds.
  All six grouped phase sheets were visually inspected.
- Full geometry artifact directory: `/tmp/angular-final/`; initial geometry:
  `/tmp/angular-geometry-before/`. Browser launch logs: `/tmp/angular-browser.log`.
  Test logs: `/tmp/angular-node-tests.log`, `/tmp/angular-python-tests.log`;
  asset check: `/tmp/angular-assets.log`.
- Packaged selected geometry previews: [`previews/overview.png`](previews/overview.png),
  plus `previews/15-phases.png` (wheel), `23` (bicycle), `27` (washer),
  `29` (crankshaft), `30` (blender), `31` (HDD), `32` (drone), `35` (pulsar),
  `36` (gas turbine), `41` (dental turbine). These are clearly labeled geometry
  previews, **not production screenshots**.

## Applying this work on main

The two registry edits update existing entries: all bicycle exact-name matches,
and the engine's inspection pose/note. Corresponding full entry JSON copies are
included. No model ID was removed and no GLB was replaced, so there is no
`replaces` field. The source GLBs already exist on the starting branch.

The new and corrected procedural mechanisms are registered by
`angular-models.js` at runtime, consistent with the pre-existing workflow.
Their final effective `*.entry.json` copies are included for review, along
with the fan's angular-only effective entry. Those procedural JSONs have no
standalone GLB: carry over the JS modules rather than passing them to the
GLB-only `register_model.py` helper. Re-run content hashing after integration
with concurrent JS changes. Review the production browser lab (including
mobile layout/performance) where Chromium can launch.

## Dataset follow-up for the items/lead job

No dataset edit is required to use these model fixes. The following existing
issues were found and deliberately left with the data owner:

1. `Venus orbit around the Sun` currently says “Venus orbits more slowly than
   Earth because its year is longer.” Its stored angular speed is already
   greater than Earth's; the prose is reversed. In the curated record for
   subject key `entity:venus-orbit-angular-velocity`, replace that summary with:
   **“Venus completes an orbit in about 225 Earth days, so its mean orbital
   angular speed is greater than Earth's.”** Then rebuild only Angular Velocity
   through the data owner's workflow. [NASA Venus Facts](https://science.nasa.gov/venus/venus-facts/),
   opened for this review, states the approximately 225-day year. Leave its
   existing stored rate unchanged.
2. Hour hand, Minute hand, Ceiling fan and Blender blade each appear twice with
   the same exact name. The first two pairs differ in rounding; fan and blender
   pairs describe different representative operating speeds. The lab now
   preserves all of them, but a future curation pass should consolidate rounding
   duplicates and qualify distinct speed scenarios. Renaming requires matching
   model selectors to be updated together; this job does not rename them.
3. The CC0 bicycle's nominal wheel diameter is illustrative. It is not used to
   re-derive the dataset's “20 km/h” scenario, whose source derivation assumes a
   different wheel radius. The model's note explicitly avoids manufacturer or
   speed-rating claims.
