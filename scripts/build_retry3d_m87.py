#!/usr/bin/env python3
"""Convert public XJET HST pixels to a calibrated, explicitly flat sky map.

No inferred line-of-sight depth, emitted particles, volume, ruler, quad or mesh.
Each point is one retained original FITS pixel at its WCS tangent-plane position.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.ndimage import label

from fetch_model_assets import inspect_glb
from nebula_volume import srgb_to_linear
from register_model import register
from volume_glb import VolumeGLB

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'content/visualizations/models'
SOURCE = MODELS / 'sources/retry3d/m87'
HANDOFF = ROOT / 'handoff/retry3d'
URL = 'https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.fits'
POLICY = 'https://hea-www.harvard.edu/XJET/image_policy.txt'
PC_M = 3.085677581491367e16
ITEM_M = 47303652362904000000
PC_PER_ARCSEC = 77.  # XJET M87 source/image documentation: 0.077 kpc/arcsec.
MODEL_ID = 'retry3d-m87-hst-map'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def read_image(data):
    """Read this checked 2D float32 primary FITS array, including native WCS."""
    header = {}
    for offset in range(0, len(data), 80):
        card = data[offset:offset+80].decode('ascii')
        key = card[:8].strip()
        if key == 'END':
            start = ((offset + 80 + 2879) // 2880) * 2880
            break
        if card[8:10] == '= ':
            # '/' inside a quoted FITS value (notably DATE-OBS) is not a comment.
            value = card[10:].lstrip()
            if value.startswith("'"):
                header[key] = value[1:value.index("'", 1)].strip()
            else:
                value = value.split('/')[0].strip()
                try:
                    header[key] = float(value.replace('D', 'E'))
                except ValueError:
                    header[key] = value
    else:
        raise ValueError('Missing FITS END')
    if (header.get('BITPIX'), header.get('NAXIS'), header.get('NAXIS1'), header.get('NAXIS2')) != (-32, 2, 800, 800):
        raise ValueError('Unexpected FITS primary image')
    if (header.get('BSCALE', 1), header.get('BZERO', 0)) != (1, 0):
        raise ValueError('Unexpected FITS scaling')
    if (header['CTYPE1'], header['CTYPE2']) != ('RA---TAN', 'DEC--TAN'):
        raise ValueError('Expected TAN WCS')
    image = np.frombuffer(data, dtype='>f4', count=800*800, offset=start).reshape(800, 800)
    return image, header


def geometry():
    data = gzip.decompress((SOURCE / 'm87_hst_f555w.fits.gz').read_bytes())
    meta = json.loads((SOURCE / 'provenance.json').read_text())
    if sha(data) != meta['original_sha256']:
        raise ValueError('Pinned FITS changed')
    image, header = read_image(data)
    yy, xx = np.indices(image.shape)
    # A fixed rectangular image aperture, not a hand-drawn jet silhouette.
    aperture = (xx >= 150) & (xx <= 620) & (yy >= 190) & (yy <= 610)
    segmented, _ = label(aperture & np.isfinite(image) & (image > 150))
    sizes = np.bincount(segmented.ravel())
    keep_ids = np.flatnonzero(sizes >= 31)
    keep_ids = keep_ids[keep_ids != 0]
    selected = np.isin(segmented, keep_ids)
    y, x = np.nonzero(selected)
    # One-based FITS pixel convention. CD directly supplies the tangent-plane
    # east/north offsets. No extra cos(dec) and no resampling or invented depth.
    pixel = np.column_stack([x + 1 - header['CRPIX1'], y + 1 - header['CRPIX2']])
    cd = np.array([[header['CD1_1'], header['CD1_2']], [header['CD2_1'], header['CD2_2']]])
    tangent_arcsec = (pixel @ cd.T) * 3600
    points = np.column_stack([-tangent_arcsec[:, 0] * PC_PER_ARCSEC,
                              tangent_arcsec[:, 1] * PC_PER_ARCSEC, np.zeros(len(x))])
    values = image[y, x].astype(float)
    return points, values, np.column_stack([x, y]), header


def prepare(cache):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / 'm87_hst_f555w.fits'
    if not path.exists():
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--max-time', '90', URL, '--output', str(path)], check=True)
    data = path.read_bytes()
    image, header = read_image(data)
    SOURCE.mkdir(parents=True, exist_ok=True)
    (SOURCE / 'm87_hst_f555w.fits.gz').write_bytes(gzip.compress(data, mtime=0))
    write_json(SOURCE / 'provenance.json', dict(source=URL, acquired='2026-10-23',
        original_sha256=sha(data), original_bytes=len(data),
        compressed_sha256=sha((SOURCE / 'm87_hst_f555w.fits.gz').read_bytes()),
        documentation='https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.txt',
        rights=POLICY, physical_scale_pc_per_arcsec=PC_PER_ARCSEC,
        scale_basis='XJET source/image documentation: 16 Mpc, 0.077 kpc/arcsec (historical H=71 convention).',
        image_shape=list(image.shape),
        header={k: header[k] for k in ['INSTRUME', 'EXPTIME', 'DATE-OBS', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2',
                                      'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2', 'CTYPE1', 'CTYPE2']},
        selection=dict(aperture_zero_based_xy=[150, 190, 620, 610], minimum_native_value_exclusive=150,
                       connectivity=4, minimum_connected_pixels=31),
        interpretation='Original observed emission pixels on the WCS tangent plane. The third coordinate is zero. No deprojection or 3D jet boundary inferred.'))


def build(register_entry=True):
    points, values, pixels, header = geometry()
    # False-color, asinh-compressed intensity; not natural-color photometry.
    t = np.clip(np.arcsinh(values / 200) / np.arcsinh(values.max() / 200), 0, 1)
    rgb = (1 - t[:, None]) * [.20, .53, 1.] + t[:, None] * [1., 1., 1.]
    alpha = .10 + .25 * np.sqrt(t)
    rgba = np.column_stack([srgb_to_linear(rgb), alpha])
    glb = VolumeGLB('Universe Scales measured HST WCS pixel map')
    material = glb.unlit('False-color HST F555W intensity')
    primitive = glb.points(points, rgba, material)
    glb.node('Original HST pixels on sky plane', [primitive], extras={
        'softPoints': True, 'additive': True,
        'pointSize': {'perPixel': .007, 'max': 4, 'conserve': True}})
    path = MODELS / (MODEL_ID + '.glb')
    glb.write(path)
    meta = json.loads((SOURCE / 'provenance.json').read_text())
    entry = dict(id=MODEL_ID, src=str(path.relative_to(ROOT)), matches={'length': ['M87 Jet']},
        source='https://hea-www.harvard.edu/XJET/source-d.cgi?M87', download_url=URL,
        source_sha256=meta['original_sha256'], source_bytes=meta['original_bytes'],
        author='NASA/ESA Hubble Space Telescope, WFPC2; original PI W. Sparks; image contributed by E. Perlman; Perlman et al. (1999), AJ 117, 2185; XJET archive.',
        license='Public-domain XJET image; archive requires owner permission and observer/contributor acknowledgement',
        license_url=POLICY, license_files=['sources/retry3d/m87/rights.md'],
        reference='content/visualizations/models/sources/retry3d-m87-hst-map.md',
        geometry='points', representation='observed_sky_projection',
        volume_semantics='not_a_volume_measurement', closed_volume_checked=False,
        note='Measured February 1995 Hubble WFPC2 F555W emission pixels from the public XJET FITS image, drawn at their original WCS positions on a flat sky plane. This is a projected optical intensity map, not a recovered 3D jet, solid surface, particle trajectory or animation of flowing plasma. Rotation exposes the deliberately zero line-of-sight thickness. The physical scale retains XJET\'s historical 0.077 kpc per arcsecond (16 Mpc) convention, without stretching the pixel distribution to the catalog value. A fixed image aperture, native intensity threshold and connected-pixel display filter exclude the noisy outer field; they are not a measured jet boundary. Blue-to-white color and glow encode compressed monochromatic intensity, not natural RGB color or deprojected dimensions. The source WCS is not registered to accurate radio maps; no multi-band alignment is claimed.',
        presentation=dict(reference_size=ITEM_M / PC_M, layout_width_factor=1.3,
                          focus_scale_factor=1.1),
        processing=dict(builder='scripts/build_retry3d_m87.py',
            pinned_input=str((SOURCE / 'm87_hst_f555w.fits.gz').relative_to(ROOT)),
            point_count=len(points), depth_pc=0, physical_scale_pc_per_arcsec=PC_PER_ARCSEC,
            selection=meta['selection'], color='asinh(native value / 200), blue-white false color',
            smoothing='None; one point per retained native pixel. Shared screen-space soft sprites only.'),
        **inspect_glb(path.read_bytes()))
    write_json(HANDOFF / (MODEL_ID + '.entry.json'), entry)
    if register_entry:
        register(HANDOFF / (MODEL_ID + '.entry.json'), path, 'length')
    print(f'{MODEL_ID}: {len(points):,} measured pixels, {np.ptp(points, axis=0)} pc; reference {ITEM_M / PC_M:.6f} pc')
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--no-register', action='store_true')
    parser.add_argument('--cache', type=Path, default=Path('/tmp/retry3d-source-cache'))
    args = parser.parse_args()
    if args.prepare:
        prepare(args.cache)
    build(not args.no_register)


if __name__ == '__main__':
    main()
