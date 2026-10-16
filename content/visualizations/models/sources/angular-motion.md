# Angular velocity models

The renderer samples theta = omega * simulated seconds. The existing clock
controls determine simulated time; changing a unit never changes omega. Every
moving assembly has an explicit node and a local spindle axis. Its orientation
is computed from its authored pose on every frame, with no accumulated drift.
Cabinets, dials, tonearms, forks, jar walls and housings stay fixed.

The camera normally looks along the main spindle, perpendicular to the screen. Clockwise
is a consistent display convention for the dataset's unsigned speed magnitudes.
The same sign change applies to every geared member so relative ratios survive.
Earth and Jupiter are viewed from the south pole, where their usual spin appears
clockwise. The blender's lid is removed for this axial inspection view.
The engine uses an authored 55-degree inspection tilt to expose the crank
journals beyond its end flange; projected rotation keeps the same clockwise sense.

Procedural mechanisms are authored illustrations under the repository's MIT
code license. Their proportions are illustrative and are not length measurements.
They are generated locally; no remote geometry or runtime API is required.
The original Poly Haven CC0 ceiling fan and NASA planet assets retain their own
credits in models.json. Only the named ceiling_fan_blades node rotates on the fan.
The 337,696-byte [drone motor by arsdever](https://sketchfab.com/3d-models/brushless-motor-for-a-drone-with-propellers-90cbde0858584d6fb58a041600841df7)
is CC BY 4.0. The GLB retains the authored hierarchy: motor_rotor and its blades
turn around local Z, while motor_stator and motor_coils remain fixed. Room
reflections are added at runtime. The shaft is Y-up after the source transforms.

## October 13 sourced additions

- [devkrsm's four-cylinder engine](https://sketchfab.com/3d-models/4-cylinder-engine-448e9e6fdd0c469ba14573f1a35c2ee0),
  CC BY 4.0: retain the existing `Crank Shaft:1_4` subtree with
  `scripts/extract_glb_node.py`, then glTF Transform 4.5.0 `prune --keep-leaves true`.
  The 406 kB result has 7,560 triangles. Pistons and rods are omitted so they
  cannot misleadingly remain stationary or disconnect while the crank turns.
  The loader sanitizes the binding name to `Crank_Shaft1_4`; the local spindle
  is Z. The October 15 inspection pose is oblique so journals remain visible
  beyond the end flange.
- [NASA VTAD Saturn](https://science.nasa.gov/resource/saturn-3d-model/): source
  globe and ring topology retained; embedded textures resized to at most 1024 px
  with glTF Transform 4.5.0 `resize`. The self-contained GLB is 727 kB and 3,328
  triangles. Only `Saturn001` rotates around Y; `RingsTop` and `RingsBottom` remain
  stationary context. Ring-particle orbital motion and atmospheric differential
  rotation are not simulated. NASA media guidelines, rather than CC0, apply.

Rejected candidates remain outside the repository: the turbocharger compressor
is not an industrial gas turbine or dentist's turbine; the low-detail helicopter
rotor and duplicated cartoon mitochondrion do not improve the current visuals.
The downloaded London Eye needs a separately verified wheel/cabin/support rig
before import. No invented replacement geometry was added in this batch.

## References and representation

- Clock: [NIST history of timekeeping](https://www.nist.gov/pml/time-and-frequency-division/popular-links/walk-through-time).
  Only the selected hand is drawn, clockwise, at its listed speed. Other hands
  are omitted because fitting the time scale to the hour hand would make the
  second hand alias. The movement is a continuous sweep, not a ticking mechanism.
- Microwave: [FDA microwave oven explanation](https://www.fda.gov/radiation-emitting-products/resources-you-radiation-emitting-products/microwave-ovens).
  Cutaway cavity, exposed turntable and an off-center piece of food that makes
  the rotation visible. Only the turntable and its contents rotate.
- Centrifuge: [Beckman Coulter rotor types](https://www.beckman.com/centrifuges/rotors).
  An illustrative fixed-angle rotor, with eight sealed tubes. The rotor and
  tubes turn together. Lid and upper containment are omitted for inspection;
  this is not a reconstruction of one particular ultracentrifuge product.
- Record player: [Audio-Technica AT-LPA2 manual](https://docs.audio-technica.com/eu/AT-LPA2-UM-EN.pdf).
- Bicycle wheel: [Park Tool wheel and rim truing](https://www.parktool.com/en-us/blog/repair-help/wheel-and-rim-truing).
- Car wheel: [Brembo wheel/disc/caliper reference](https://www.brembo.com/en/solutions/for-your-car/sport-disc).
  Tire, hub, spokes and disc rotate together; the axle carrier and caliper stay fixed.
- Washing machine: [Bosch drum/spin reference](https://www.bosch-home.com/us/owner-support/washers/troubleshooting/not-spinning).
- Hard drive: [Seagate component diagram](https://www.seagate.com/support/disc/manuals/ata/1621pma.pdf).
- Blender: [Vitamix blade/container manual](https://www.vitamix.com/media/catalog/product/file/Container-Use-and-Care-Owners-Manual.pdf).

The small separate phase dial measures completed turns clockwise. Above eight
repeating patterns per real second, both the model and phase dial freeze. An
`angular_motion.repetitions` hint accounts for repeated spokes or blades: a
wheel can alias well below eight complete turns per second. These counts are
display-policy hints taken from the rendered geometry, not measured machine
specifications. Fitted time remains one complete turn per four real seconds.
The interface labels this as a static view, and Fit time to item exposes motion.

## Verification

`node scripts/model_lab.cjs angular /tmp/angular-review` opens every observation
in the production explorer, preserving duplicate names and orbital diagrams,
and records rotor quaternions, local pivots and stationary housing matrices in
audit.json. Names can follow the output directory to restrict the review.
Five phase screenshots include a non-symmetric 0.37-radian sample;
`--times 0.1,1,2` adds samples at explicit simulated seconds. Counter-rotating
capsules are allowed; only the primary rotor must turn clockwise.
Use the screenshots for visual review; matrix checks alone do not certify a model.

Angular framing measures a full rotation once, rather than fitting the rest
pose. This fixes the thin drone propeller's almost fourfold growth in projected
height as it turns. `angular_motion.view_tilt` optionally exposes a long shaft.

If Chromium cannot launch, `node scripts/audit_angular_models.mjs /tmp/angular
--previews` checks every dataset observation with the vendored glTF loader and
production rig/builders. `./venv/bin/python scripts/render_angular_preview.py
/tmp/angular` makes flat geometry phase sheets. These omit textures, reflections,
perspective, labels and production UI, and do not replace browser review.
See [the October 15 source notes](angular-inspection.md) for the new illustrations.
