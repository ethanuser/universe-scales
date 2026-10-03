# Angular velocity models

The renderer samples theta = omega * simulated seconds. The existing clock
controls determine simulated time; changing a unit never changes omega. Every
moving assembly has an explicit node and a local spindle axis. Its orientation
is computed from its authored pose on every frame, with no accumulated drift.
Cabinets, dials, tonearms, forks, jar walls and housings stay fixed.

Procedural mechanisms are authored illustrations under the repository's MIT
code license. Their proportions are illustrative and are not length measurements.
They are generated locally; no remote geometry or runtime API is required.
The original Poly Haven CC0 ceiling fan and NASA planet assets retain their own
credits in models.json. Only the named ceiling_fan_blades node rotates on the fan.
The 337,696-byte [drone motor by arsdever](https://sketchfab.com/3d-models/brushless-motor-for-a-drone-with-propellers-90cbde0858584d6fb58a041600841df7)
is CC BY 4.0. The GLB retains the authored hierarchy: motor_rotor and its blades
turn around local Z, while motor_stator and motor_coils remain fixed. Room
reflections are added at runtime. The shaft is Y-up after the source transforms.

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

The small separate phase dial measures completed turns; its projected direction
is not the three-dimensional spindle orientation. Above eight turns per real
second, both the model and phase dial freeze under the existing aliasing rule.
The interface labels this as a static view, and Fit time to item exposes motion.

## Verification

`node scripts/model_lab.cjs angular /tmp/angular-review` opens every available
angular model in the production explorer, saves rest/quarter-turn screenshots,
and records rotor quaternions, local pivots and stationary housing matrices in
audit.json. Names can follow the output directory to restrict the review.
Use the screenshots for visual review; matrix checks alone do not certify a model.
