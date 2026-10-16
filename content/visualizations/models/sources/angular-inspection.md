# Angular inspection illustrations (2026-10-15)

`js/experiences/angular-additional-models.js` contains original procedural
geometry, under the repository's MIT license. No external meshes, photographs,
textures or private assets were copied. Scene coordinates, inspection angles,
blade counts, colors and beam widths are authored display choices, not physical
measurements. Angular speeds continue to come from each dataset observation.

## London Eye

The operator's [official FAQ](https://www.londoneye.com/plan-your-visit/information-and-support/faqs/)
states a full complement of **32 pods** and an approximately **30-minute** ride.
Its [design/history page](https://www.londoneye.com/about-us/) describes a
cantilevered observation wheel. Both pages were opened on October 15, 2026.
The FAQ currently mentions a capsule removed for refurbishment; the illustration
shows the full complement, not today's operational inventory.

The wire wheel turns around a fixed axle behind the hub; its A-frame stays fixed.
Every capsule is a child of the wheel and turns equally in the opposite direction
about its own pivot. Floors therefore stay level while capsule centers orbit.
This reproduces the visible leveling relationship, not its actual drive/control
mechanism. Cable layout and proportions are schematic, not surveyed architecture.

## Gas turbine

[NASA Glenn's animated power turbine](https://www.grc.nasa.gov/www/k-12/VirtualAero/BottleRocket/airplane/powturba.html),
opened October 15, describes a rotating row attached to the shaft and a stationary
stator row. The illustration shows an exposed axial turbine stage, not a
turbocharger compressor or a complete industrial turbine. The disk, shaft and
twisted blade row rotate; the separate nozzle row, casing and flange bolts stay
fixed. Tip geometry clears the stationary casing. Blade/nozzle counts and
profiles are authored; gas flow, combustion, thermal stress and spool gearing
are not modeled. The dataset's speed is not a rating for a specific machine.

## Dental air turbine

[W&H Alegra's product reference](https://www.wh.com/en_global/dental-products/restoration-prosthetics/turbines/alegra),
opened October 15, shows the handpiece, turbine rotor, bur/chuck relationship
and bearing support. It is used for component relationships only. This original
inspection diagram does not reconstruct the manufacturer's blade shape or
claim its performance specifications. The bucket rotor, chuck and bur turn
together; the opened head, grip, air nozzle and bearing outer races stay fixed.
The neck lies behind the rotating bucket row. The head cap is omitted for
inspection. Looking along the spindle foreshortens the bur; this is deliberate.

## Pulsars

[NASA Goddard's pulsar explanation](https://imagine.gsfc.nasa.gov/observatories/satellite/xmm/pulsar.html),
opened October 15, explains how differing rotation and magnetic axes sweep
beams like a lighthouse. The three dataset labels share an explicit schematic:
a neutron star with tilted magnetic-axis, polar-cap, beam and dipole guides.
These co-rotate, while a neutral reference circle stays still. The cones depict
radiation directions, not solid jets or material attached to the star. This is
not an observational reconstruction of any named pulsar, an emission model,
or a relativistic plasma solution. A viewer along the rotation axis need not
observe pulses; the illustration demonstrates beam sweep rather than claiming
a brightness signal from this viewing direction.

## Existing assets and corrections

- The [Innerscene city bicycle source](https://www.innerscene.com/tools/library/3d-parts/city-bicycle-58a2a324)
  was opened and explicitly confirms CC0. The existing rigged GLB is reused for
  all three bicycle labels. Its frame and drivetrain remain fixed while its
  wheels coast. Its nominal dimensions are not used to derive dataset speeds.
- [devkrsm's engine API record](https://api.sketchfab.com/v3/models/448e9e6fdd0c469ba14573f1a35c2ee0)
  was fetched directly on October 15. It reports license slug `by` and the
  CC BY 4.0 URL. The existing extracted crankshaft GLB is unchanged; an oblique
  inspection pose exposes it beyond its end flange.
- The existing Poly Haven fan has four rendered blades. Its angular presentation
  now explicitly views the underside. Only the blade mesh turns.
- Washer: fixed rear wall/counterweight bosses moved behind the rotating back
  plate; dampers moved outside the drum. Rear-face recesses make motion legible.
  These are recess cues rather than through-hole geometry.
- HDD: a continuous bearing/arm/suspension/head chain clears the top platter;
  the old slider intersected it. Gaps are illustrative, not flying-height claims.
- Record player: the stylus reaches the record instead of floating above it.
- Blender: an annular fixed bearing below the hub leaves rotating blades exposed.
- The unused procedural bicycle fallback was also corrected: fork legs straddle
  the wheel along the axle instead of crossing the rotating wheel plane.

All source checks concern representation and reuse. No dataset values, sources
or plaque text were changed by this job.
