# Hoover Dam

Original CC0 dimensioned structural illustration by Universe Scales. Offline:
`./venv/bin/python scripts/build_earth3d3_models.py hoover`.

## Sources and constraints

- [US Bureau of Reclamation history](https://www.usbr.gov/history/hoover.html):
  1,244 ft developed crest, 660 ft base thickness, 45 ft crest thickness and four
  395 ft intake towers.
- [USACE Water Control Manual, December 1982](https://water.usace.army.mil/cda/documents/wc/3249/Hoover%20Dam%20WCM%20121982.pdf):
  structural height 726.4 ft in the main-dam description; Plate 3 (PDF page 98)
  supplies plan, profile and section context. The plate was rendered and viewed.
  Download SHA-256: `b0346c5b3b52d2177ef9dbe8acf1518796e457dc0f39e3cb5d1b7dde537d8be9`.
- [CEC-hosted 2008 historical study, printed p. 5 / PDF p. 9](https://efiling.energy.ca.gov/GetDocument.aspx?tn=48082):
  500 ft arch-axis radius. This is a historical secondary source, not an original
  construction drawing.

Feet are converted using 0.3048 m/ft. The crest is a circular developed arc,
not a straight line stretched to 1,244 ft. The core body's structural height is
221.40672 m, uniformly calibrated to the catalog's 221.4 m. Parapets and tower
caps extend slightly above the structural crest.

The narrowing canyon footprint, intermediate elevation sections, thickness
interpolation, joints, parapets, tower diameters, cap geometry and tower/bridge
placement are authored approximations. Their broad organization follows Plate 3;
they are not extracted engineering sections. Canyon terrain, powerhouses,
spillways and the bypass bridge are omitted. Tower bottoms are exposed because
water is omitted. This is not a structural analysis model or a surveyed scan.

The oblique resting view exposes the massive wedge section and keeps the screen
extent within the explorer's size rule. No scope labels are embedded.

Sources opened 2026-10-16. PyMuPDF was installed only under
`/private/tmp/earth3d3/python` to inspect the source PDF, not in the shared venv.
