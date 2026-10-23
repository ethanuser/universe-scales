# M87 jet: observed HST intensity on a calibrated sky plane

Source: [XJET M87](https://hea-www.harvard.edu/XJET/source-d.cgi?M87),
[original HST FITS image](https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.fits),
[image descriptor](https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.txt).
Rights and observer credits: [XJET policy/credit notes](retry3d/m87/rights.md).

This is a direct conversion of measured image pixels into a point map, with
**zero line-of-sight thickness**. It is not a 3D plasma volume, deprojection,
surface, trajectory, jet-launch simulation, or a time sequence. Every point is
an original observed pixel, and its third coordinate is exactly zero. No particles
are scattered, duplicated into depth, or generated to fill the spaces between
observed knots. The owner's allowance for observed sky positions on a stated
plane is the basis for this representation. A rotating view becomes a line when
edge-on; that reveals the observational scope rather than inventing unseen depth.

The public array is an 800×800 WFPC2/PC F555W optical image with 2,400 s exposure.
The source descriptor dates it 1995-02-04, while the FITS header says 1995-02-03;
the registry deliberately says February 1995. The descriptor's nominal pixel size
is 0.0455 arcsec; the actual FITS CD matrix, including rotation, is used instead.
The image is not north-up and is explicitly not registered to accurate radio
maps. We do not combine it with a radio/X-ray layer.

The source's basic-data table supplies **0.077 kpc per arcsecond** at a historical
16 Mpc distance convention. Native model coordinates are parsecs; every pixel's
east/north tangent-plane offsets come directly from the FITS CD matrix, using
the one-based CRPIX convention. West is display +X and north +Y. No extra
cos(declination) is applied: the CD matrix already maps pixels to the tangent
plane. The coordinates are not normalized to the model box. The registry's
`reference_size` converts the existing item's 5,000-light-year value to parsecs.
This is projected extent, not a deprojected jet length or its full radio extent.

The fixed zero-based rectangular image aperture is X=150…620, Y=190…610.
Only finite native values >150 in four-connected components of at least
31 pixels are displayed. These are reproducible **display cuts**, not a claimed
noise-sigma threshold, knot membership catalog, or physical outer boundary.
The threshold retains 9,689 original pixels. Brightness uses an asinh transfer
function and a blue-white false-color palette. The source array has no asserted
photometric unit here, so the code does not call its values counts, flux or
surface brightness in a specified unit. Screen-space soft sprites blend nearby
observations without creating mesh geometry or depth. They are display kernels,
not physical plasma elements.

The fixed cuts preserve the observed gaps. Low-level residuals near the nucleus
and imperfect subtraction/calibration belong to the public source; this is not
a freshly re-reduced HST observation. A wider field or different intensity cut
would retain other emission/noise. No arbitrary silhouette is drawn around the jet.

Pinned source: `retry3d/m87/m87_hst_f555w.fits.gz` (lossless compression of the
complete original FITS array and header). Hashes, WCS and cuts:
`retry3d/m87/provenance.json`. Source descriptor and policy hashes are also pinned
in `source-metadata.json`. No runtime request to Harvard is needed.

Offline rebuild and registration:
`./venv/bin/python scripts/build_retry3d_m87.py`.
`--prepare` refreshes the optional external cache and losslessly pins the source;
`--no-register` builds only. CPU previews do not certify WebGL, sprite blending,
mobile point LOD, picking, or the radial explorer. Those remain for the lead.

