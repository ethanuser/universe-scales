# Interactive Presentation Layer

These files are presentation assets, not observation data or editorial descriptions.
The canonical values still come from `exports/frontend/<dimension>.yaml`.
Existing item prose remains unchanged; the explorer adds a separate caption about
what the current visualization means.

## Modes

- Length: two neighboring items, sized by their listed lengths, with a shared
  zoom slider and wheel zoom. Click either object to frame it. Full image frames
  approximate measured spans; backgrounds are not automatically segmented.
- Area: equivalent squares with side `sqrt(area)`. Inset photos identify objects
  but do not establish area. Earth surface area uses an Equal Earth projection;
  its entire projected footprint is normalized to the listed area.
- Volume: equivalent cubes with edge `cbrt(volume)`, drawn from 3D vertices using
  a shared orthographic projection. The rotation slider changes both views.
  These are not measured meshes of the original objects.
- Counts: bounded dot clusters with explicit multiplicities, and partial-cluster
  areas proportional to the represented fraction. Legal Go positions show four
  distinct illustrative 19x19 boards with isolated stones that retain liberties;
  they are not a uniform sample or enumeration of all legal boards.
- Speed, acceleration, jerk: two lanes with the same distance/time scale.
  The idealized segments use `x=vt`, `x=at^2/2`, or `x=jt^3/6` with zero initial
  velocity/acceleration where applicable. Both lanes reset together. These are
  mathematical comparisons, not relativistic simulations or actual trajectories.
- Frequency and sound frequency: schematic oscillation, pulse, or orbit at the
  recorded frequency, with a time slider. The waveform and displacement are not
  measurements. Angular velocity uses a rotating spoke and image instead.
- Brightness: uniform luminance patches with sRGB encoding, exposure, background,
  and user-supplied display peak/black estimates. An optional photo illustration
  dims the object's image but does not treat its pixels as photometric measurements. No automatic brightness setting,
  ambient-light sensing, or calibrated optical output is claimed. Luminance is
  not converted by an inverse-square viewing-distance rule.
- Angle and visual angle: manually calibrated image width using
  `width = 2 * distance * tan(angle/2)`. Measure the 100-CSS-pixel ruler to establish
  physical screen scale. Only one centered image is shown to avoid overlap.
  Angles too small or too large for the screen are reported, not silently resized.
  Two-ray diagrams also appear in the original plot's tooltips.
- Loudness: click-to-play controls inside original plot tooltips. Previews mute
  background music, stop after at most six seconds, and stop on close, mode change,
  navigation, or tab hiding. Playback volume is independent of the dataset's dB
  value. Reference thresholds have no sound preview.

Interactive views are the first-visit default for supported dimensions except
Loudness, which keeps its plot. A per-dimension `scale-view:<slug>` localStorage
entry remembers the choice. Unsupported dimensions retain their existing plot.
Animation starts only on Play, pauses when the tab is hidden, and never resumes
automatically. Above eight displayed cycles per second the illustration freezes
and asks for a slower time scale rather than displaying aliased motion.

## Asset Registry

`assets.json` has `schema_version`, `images`, and `audio` keys. Optional image
overrides are keyed first by dimension slug and then exact item name:

```json
{
  "images": {
    "length": {
      "Example item": {
        "src": "content/visualizations/example-cutout.png",
        "source": "https://example.org/original",
        "license": "License of the actual image",
        "note": "Full frame corresponds to the recorded span"
      }
    }
  }
}
```

No cutouts are bundled yet. Transparent PNGs can be supplied through this registry;
otherwise the explorer reuses the existing thumbnail/original lookup. Never place
a perspective photo into the dataset as evidence of measured geometry. In
particular, a familiar image does not resolve radius versus diameter, geographic
boundaries, or theoretical versus measured quantities in the underlying records.

Audio entries are keyed by exact Loudness item name and contain `src`, `title`,
`author`, `license`, `source`, and `download_url`. They identify a related sound,
not a recording at the exact distance or dB level of the observation. Field
recordings are currently incomplete. Missing or failed recordings never fall back
to synthesis. Add licensed recordings here without changing the corpus. Use
`python scripts/fetch_audio_assets.py --search 'search terms'` for discovery, inspect
the author/license/description (reject pronunciation recordings), then add reviewed
entries and run `--download`. Commit the printed SHA-256 hashes to the manifest.
An optional `start` field selects the beginning of a six-second excerpt.

Run `python scripts/fetch_audio_assets.py --audit` to check local files, hashes,
attribution and exact item-name matches, and list remaining coverage gaps. As of
2026-09-05, 20 unique real recordings cover 21 of 32 Loudness items. Five items
are thresholds/reference measurements rather than distinct sound sources. The
remaining six recording gaps are the gunshot, nightclub, rock concert, quiet
bedroom, quiet home at night, and quiet office.

Discovery includes museum sound archives (Work With Sounds and the Netherlands
Institute for Sound and Vision), public-domain PDSounds recordings, NASA launch
audio, and Freesound field recordings. `--files` resolves exact Commons file titles
when keyword search misses them. Searches pause between requests and retry with
backoff. Freesound public preview URLs are recorded explicitly; no login-only
originals are fetched. A takeoff recording is shared by both distance examples,
with that reuse and the unknown microphone distance stated in its attribution.

Large source recordings can use `extract: {start: 45, duration: 6}`. The downloader
requires FFmpeg for these entries and produces mono 48 kHz PCM WAV excerpts;
`source_sha256` pins the downloaded original, `sha256` pins the excerpt, and
`changes` describes the transformation. The original license is retained.

Playback normalizes excerpt RMS and applies amplitude gain `10^(delta_dB/20)`.
The fixed rain reference has digital RMS 0.008; the default uncalibrated mapping
places 70 dB at that reference. This is a relative mapping, not a physical SPL
claim. A digital RMS/peak ceiling caps louder examples, with an explicit message.
The attenuation slider only reduces output. Listen clearly bypasses scale matching.
Every playback requires a click, lasts at most six seconds, and pauses music.

Optional calibration asks for an SPL-meter reading of the rain reference at the
listener position. It is session-only and must be repeated after volume, device,
or distance changes. Calibrated playback additionally caps the estimated level at
75 dB; no digital setting can guarantee a safe physical level on unknown hardware.
Room acoustics, spectral response, meter weighting and recording compression limit
accuracy. Output-device selection is offered where supported, but browser APIs do
not reveal system volume, speaker sensitivity, or distance. No microphone or camera
access is requested. Do not turn device volume to maximum for these previews.

## Bundled Sources

- `land.geojson`: Natural Earth 1:110m land, public domain. Downloaded from
  https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
  SHA-256: `9e0729ee253ca7d7a5c4ae9395fb1902264c5377c52e224d13dd85010e2835d9`.
  Terms: https://www.naturalearthdata.com/about/terms-of-use/
- Recording attribution/download URLs and SHA-256 hashes are in `assets.json`, based on the
  individual Commons/Freesound file descriptions. Public-domain, CC0, CC BY and
  CC BY-SA terms apply per recording; the project license does not replace them.

Acquired 2026-09-04. Assets are stored locally so normal use does not fetch media
from third-party servers. Browser libraries retain the site's existing CDN setup.
The map uses the existing D3 dependency, and 3D cube projection needs no WebGL or
additional framework.

## Code and Checks

- `js/experiences/math.js`: pure conversion/geometry helpers, also loadable in Node.
- `controls.js`: reusable sliders, numeric fields, DOM helpers, and simulation clock.
- `controller.js`: mode registry, lifecycle, per-dimension preference, item detail,
  image loading, and integration with the original app.
- `spatial.js`, `motion.js`, `perception.js`, `audio.js`: independent renderers.
- `css/experiences.css`: scoped layout, mobile labels, and mode visibility.

Run `node --test tests/experience-math.test.cjs`. Serve the repository root with
`python3 -m http.server 8000`. `tests/browser-experiences.js` is an async expression
that can be evaluated in the browser console (or with `agent-browser eval`) to
exercise all modes, plot fallback, extremes, and preference persistence. It changes
the testing browser's view preferences but does not edit the dataset.

Audio gain tests: `node --test tests/audio-math.test.cjs`. After clicking Play once
to grant audio activation, evaluate `tests/browser-audio.js` in the browser to
check every bundled recording, calibration, missing assets and cancellation.

Future work: curated cutouts and measured image spans, actual meshes and outlines,
more field recordings, and optional camera-based distance estimation only with
appropriate calibration and explicit user consent. Browser audio output selection
does not expose speaker sensitivity or sound level at the listener. See
https://developer.mozilla.org/en-US/docs/Web/API/Audio_Output_Devices_API and
https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API.
