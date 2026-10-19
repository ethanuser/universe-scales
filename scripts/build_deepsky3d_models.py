#!/usr/bin/env python3
"""Offline, deterministic conversion of pinned public catalogs to GLB points.

No fitted shapes, synthetic stars, random depths, glyphs, or rulers. Native
units stay physical; reference_size is the catalog item's value in those units.
See content/visualizations/models/sources/deepsky3d-models.md for scope and cuts.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from build_laniakea_galaxies import galactic_unit, supergalactic_matrix
from fetch_model_assets import inspect_glb
from nebula_volume import srgb_to_linear
from volume_glb import VolumeGLB

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "content/visualizations/models/sources/deepsky3d"
HANDOFF = ROOT / "handoff/deepsky3d"
MODELS = ROOT / "content/visualizations/models"
PC_M = 3.085677581491367e16
MPC_M = PC_M * 1e6
LY_M = 9.4607304725808e15
C_KM_S = 299792.458
GAIA_CREDIT = "https://gea.esac.esa.int/archive/documentation/GDR3/Miscellaneous/sec_credit_and_citation_instructions/"
SDSS_POLICY = "https://www.sdss.org/collaboration/image-use-policy/"


def read_rows(name):
    path = SOURCES / name
    manifest = json.loads((SOURCES / "manifest.json").read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][name]["sha256"]:
        raise ValueError(f"Pinned source hash mismatch: {name}")
    with gzip.open(path, "rt", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != manifest["files"][name]["rows"]:
        raise ValueError(f"Pinned source row count mismatch: {name}")
    return rows


def columns(rows, *names):
    return [np.array([float(row[name]) for row in rows]) for name in names]


def unit_vectors(ra, dec):
    a, d = np.radians(ra), np.radians(dec)
    return np.stack([np.cos(d)*np.cos(a), np.cos(d)*np.sin(a), np.sin(d)], -1)


def sky_frame(ra, dec):
    """Rows are east, north, away from observer; orthonormal ICRS basis."""
    a, d = np.radians([ra, dec])
    return np.array([[-np.sin(a), np.cos(a), 0],
                     [-np.sin(d)*np.cos(a), -np.sin(d)*np.sin(a), np.cos(d)],
                     [np.cos(d)*np.cos(a), np.cos(d)*np.sin(a), np.sin(d)]])


def sky_plane(ra, dec, ra0, dec0, distance):
    """Gnomonic plane at a common measured distance, no individual depths."""
    v = unit_vectors(ra, dec) @ sky_frame(ra0, dec0).T
    return np.column_stack([-distance*v[:, 0]/v[:, 2],
                             distance*v[:, 1]/v[:, 2], np.zeros(len(v))])


def lmc_disk(ra, dec):
    """Intersect observed sightlines with the published inclined stellar plane.

    van der Marel & Cioni (2001): i=34.7 deg, Theta=122.5 deg (E of N).
    The northeastern side is nearer. Pietrzynski et al. (2019): D0=49.59 kpc.
    Plane position uses Gaia Collaboration (2021) kinematic center 81.28,-69.78.
    Output x is west, y north, z towards observer, in kpc.
    """
    v = unit_vectors(ra, dec) @ sky_frame(81.28, -69.78).T
    inc, theta = np.radians([34.7, 122.5])
    # Components in (east,north,away); positive distance on NE is smaller.
    normal = np.array([np.sin(inc)*np.cos(theta),
                       -np.sin(inc)*np.sin(theta), -np.cos(inc)])
    distance = -49.59*np.cos(inc)/(v @ normal)
    p = v*distance[:, None] - [0, 0, 49.59]
    return p * [-1, 1, -1]


def comoving_mpc(z, h0=70, omega_m=0.27):
    """Flat LCDM line-of-sight integral; vectorized deterministic trapezoid grid."""
    z = np.asarray(z, float)
    grid = np.linspace(0, max(float(z.max()), 1e-8), 32769)
    f = 1/np.sqrt(omega_m*(1+grid)**3 + 1-omega_m)
    integral = np.concatenate([[0], np.cumsum((f[1:]+f[:-1])*.5*np.diff(grid))])
    return C_KM_S/h0*np.interp(z, grid, integral)


def stellar_rgb(bp_rp):
    """Display palette ordered by observed BP-RP; not a calibrated RGB spectrum."""
    stops = [-.5, 0, .5, 1, 1.5, 2.5, 4]
    rgb = np.array([[.55,.69,1], [.7,.8,1], [.88,.92,1],
                    [1,.94,.8], [1,.78,.49], [1,.53,.28], [1,.35,.19]])
    return np.stack([np.interp(bp_rp, stops, rgb[:, k]) for k in range(3)], 1)


def write_cloud(glb, name, positions, rgb, alpha, per_pixel, max_px):
    """One point per input record, including all faint records; no stochastic cull."""
    rgba = np.column_stack([srgb_to_linear(rgb), np.clip(alpha, 1/255, 1)])
    material = glb.unlit(name)
    primitive = glb.points(positions, rgba, material)
    glb.node(name, [primitive], extras={"softPoints": True, "additive": True,
             "pointSize": {"perPixel": per_pixel, "max": max_px, "conserve": True}})


def catalog_geometry(kind):
    """Return source-derived positions, colors, weights and exact row identities."""
    if kind == "orionarm":
        path=SOURCES/"edenhofer-local-dust.npz"
        meta=json.loads((SOURCES/"manifest.json").read_text())["files"][path.name]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta["sha256"]:
            raise ValueError("Pinned dust grid hash mismatch")
        with np.load(path) as data:
            density=data["density"]
            coord=data["coordinates_pc"]
        threshold=np.nanquantile(density,.95)
        iz,iy,ix=np.nonzero(np.isfinite(density)&(density>=threshold))
        p=np.column_stack([coord[ix],coord[iy],coord[iz]])
        value=density[iz,iy,ix]
        t=np.clip(np.log(value/threshold)/np.log(20),0,1)
        # Extinction density is false-colored, not emitted optical light.
        rgb=(1-t[:,None])*[.33,.63,1.] + t[:,None]*[1.,.83,.44]
        alpha=.01+.02*np.sqrt(t)
        ids=[f"{z}:{y}:{x}" for z,y,x in zip(iz,iy,ix)]
        return p,rgb,alpha,ids
    if kind == "lmc":
        rows = read_rows("gaia-dr3-lmc.csv.gz")
        ra, dec, mag, color = columns(rows, "ra", "dec", "phot_g_mean_mag", "bp_rp")
        p = lmc_disk(ra, dec)
        keep = np.linalg.norm(p, axis=1) <= CONFIG[kind]["reference"]/2
        return p[keep], stellar_rgb(color[keep]), np.clip(10**(-.15*(mag[keep]-16)), .2, 1), [r["source_id"] for r,k in zip(rows,keep) if k]
    if kind == "omega":
        rows = read_rows("gaia-edr3-omega-members.csv.gz")
        ra, dec, mag, color = columns(rows, "ra", "dec", "g_mag", "bp_rp")
        p = sky_plane(ra, dec, 201.69699, -47.47947, 5430)
        keep = (np.linalg.norm(p, axis=1) <= CONFIG[kind]["reference"]/2) & (mag<16)
        return p[keep], stellar_rgb(color[keep]), np.clip(10**(-.14*(mag[keep]-16)), .12, 1), [r["source_id"] for r,k in zip(rows,keep) if k]
    if kind == "localvoid":
        rows = read_rows("2mrs.csv.gz")
        lon, lat, kmag, cz = columns(rows, "GLON", "GLAT", "Ktmag", "cz")
        sg = (galactic_unit(lon,lat)*(cz/75)[:,None]) @ supergalactic_matrix().T
        # A physical 60 by 60 Mpc section through the three published minima.
        # SGX horizontal, SGZ vertical, SGY depth. No galaxy is removed to make a hole.
        center = np.array([19., -6., 15.])
        rel = sg-center
        keep = (cz>0)&(np.abs(rel[:,0])<=30)&(np.abs(rel[:,2])<=30)&(np.abs(rel[:,1])<=10)
        p = np.column_stack([rel[:,0], rel[:,2], -rel[:,1]])[keep]
        rgb = np.tile([.76,.84,1.], (len(p),1))
        return p, rgb, np.full(len(p), .72), [r["row"] for r,k in zip(rows,keep) if k]
    if kind in {"bootes", "bao"}:
        rows = read_rows(f"sdss-dr17-{kind}.csv.gz")
        ra, dec, z = columns(rows, "ra", "dec", "z")
        if kind == "bootes":
            # Kirshner et al. (1987) used H0=50 for the quoted 124-Mpc diameter.
            # Published center is B1950. ICRS center below is the FK4 conversion.
            ra0, dec0 = 222.9458392059863, 45.795532678784106
            distance = C_KM_S*z/50
            center_distance = 15500/50
            width, depth = 150., 40.
        else:
            ra0, dec0 = 180., 20.
            distance = comoving_mpc(z)
            center_distance = float(comoving_mpc([.475])[0])
            width, depth = 150., 40.
        frame = sky_frame(ra0,dec0)
        v = unit_vectors(ra,dec)*distance[:,None]
        q = v @ frame.T - [0,0,center_distance]
        p = q * [-1,1,-1]
        keep = (np.abs(p[:,0])<=width/2)&(np.abs(p[:,1])<=width/2)&(np.abs(p[:,2])<=depth/2)
        p = p[keep]
        # False-color redshift palette: depth is measured, palette is not spectral RGB.
        t = np.clip((z[keep]-z.min())/(z.max()-z.min()),0,1)[:,None]
        rgb = (1-t)*[.50,.76,1.] + t*[1.,.72,.43]
        return p,rgb,np.full(len(p),.9),[r["specObjID"] for r,k in zip(rows,keep) if k]
    raise ValueError(kind)


CONFIG = {
    "orionarm": {"id":"orion-arm-edenhofer-dust", "item":"Orion Arm", "reference":33112556654032800000/PC_M,"unit":"pc",
        "source":"https://zenodo.org/records/8187943", "basis":"https://arxiv.org/abs/2308.01295",
        "author":"Gordian Edenhofer, Catherine Zucker, Philipp Frank, Andrew K. Saydjari, Joshua S. Speagle, Douglas Finkbeiner & Torsten Ensslin",
        "license":"CC-BY-4.0","license_url":"https://creativecommons.org/licenses/by/4.0/", "representation":"survey",
        "note":"Direct conversion of Edenhofer et al.'s three-dimensional extinction-density reconstruction around the Sun. The 1,072-pc-wide local window lies within the Local/Orion Arm and approximately matches this item's 3,500-light-year width. It is not a measurement of the arm's full width, length or boundary. Each point is a 16-pc-spaced sample of the published Cartesian mean grid; the densest 5% of finite samples reveal nearby cloud structure. Colors encode log extinction density, not emitted light, and omitted low-density or unavailable samples are not empty space. No invented clouds, stars, depth or arm shape.", "per_pixel":1/25,"max_px":30},
    "lmc": {"id":"lmc-gaia-disk", "item":"Large Magellanic Cloud", "reference":3.042478095350488e20/(PC_M*1000), "unit":"kpc",
        "source":"https://gea.esac.esa.int/archive/", "basis":"https://arxiv.org/abs/astro-ph/0105339",
        "author":"ESA/Gaia/DPAC; van der Marel & Cioni (2001); Pietrzynski et al. (2019)",
        "license":"Gaia open data (credit required)", "license_url":GAIA_CREDIT,
        "note":"Gaia DR3 candidate LMC stars at their measured sky positions and observed BP-RP colors, intersected with the published 34.7-degree stellar disk plane at 49.59 kpc. Proper-motion and parallax cuts reduce Milky Way contamination. The plane is an ensemble distance approximation: individual stellar depths, disk thickness and gas are not measured here. The 9.86-kpc disk aperture follows this item's characteristic diameter; fainter outskirts continue beyond it. Brightness is compressed for display and colors are an ordered BP-RP palette. No invented stars or depth scatter.", "per_pixel":1/170, "max_px":6},
    "omega": {"id":"omega-centauri-gaia-members", "item":"Omega Centauri", "reference":150*LY_M/PC_M,"unit":"pc",
        "source":"https://zenodo.org/records/4891252", "basis":"https://arxiv.org/abs/2102.09568",
        "author":"Eugene Vasiliev & Holger Baumgardt; ESA/Gaia/DPAC", "license":"CC-BY-4.0", "license_url":"https://creativecommons.org/licenses/by/4.0/",
        "note":"Gaia EDR3 stars brighter than G=16 assigned greater than 99% membership probability by Vasiliev & Baumgardt (2021), with observed BP-RP colors. Sky positions are projected onto a plane at the measured 5.43-kpc cluster distance; individual stellar depths cannot be resolved, so rotation reveals a flat map, not a reconstructed sphere. A 150-light-year aperture matches this item's characteristic span; members outside it are excluded. The bright cut avoids the strong central incompleteness of faint Gaia sources, but the innermost core remains incomplete. Astrometric quality flags are retained in the source subset but not used to cut sky positions. Brightness is compressed and the color palette follows BP-RP; no synthetic core, stars or depth scatter.", "per_pixel":1/150,"max_px":6},
    "localvoid": {"id":"local-void-2mrs-slice", "item":"Local Void", "reference":60.,"unit":"Mpc",
        "source":"https://lweb.cfa.harvard.edu/~dfabricant/huchra/2mass/", "basis":"https://arxiv.org/abs/1905.08329",
        "author":"Huchra et al. (2012), 2MASS Redshift Survey; Tully et al. (2019)", "license":"2MRS public scientific catalog (credit required)", "license_url":"https://lweb.cfa.harvard.edu/~dfabricant/huchra/2mass/",
        "note":"Actual 2MASS Redshift Survey galaxies in a 60 by 60 by 20 Mpc section through the Local Void's Aquila, Lacerta and Andromeda minima. Positions are barycentric redshift-space distances cz/H0, H0=75 km/s/Mpc, in supergalactic coordinates. The displayed window is a section through the void and surrounding galaxies, not its boundary or full volume. Flux limits, peculiar velocities and the Milky Way's zone of avoidance affect the apparent emptiness; missing survey regions must not be read as empty space. Every displayed point is a catalog galaxy; none were deleted to sculpt a cavity. Colors are for visibility, not observed galaxy colors.", "per_pixel":1/85,"max_px":8},
    "bootes": {"id":"bootes-void-sdss-slice", "item":"Bootes Void", "reference":124.,"unit":"Mpc",
        "source":"https://www.sdss4.org/dr17/", "basis":"https://articles.adsabs.harvard.edu/pdf/1987ApJ...314..493K",
        "author":"Sloan Digital Sky Survey; Kirshner et al. (1987)", "license":"SDSS public-release catalog data (public domain)", "license_url":SDSS_POLICY,
        "note":"SDSS DR17 spectroscopic galaxies in a 150 by 150 by 40 Mpc slice centered on the published Bootes Void position and cz=15,500 km/s. The historical H0=50 km/s/Mpc convention is retained because this item's 124-Mpc diameter comes from that convention; adopting H0=70 changes that diameter to about 89 Mpc. Catalog redshifts are converted using cz/H0 without a peculiar-velocity correction. The plotted slice includes the sparse center and surrounding galaxies; it does not define membership or a spherical boundary. Survey incompleteness remains. Colors encode redshift, not galaxy color, and every point is an actual catalog location.", "per_pixel":1/95,"max_px":7},
    "bao": {"id":"bao-boss-galaxy-slice", "item":"Baryon Acoustic Oscillation Scale", "reference":150.,"unit":"Mpc",
        "source":"https://www.sdss4.org/dr17/", "basis":"https://arxiv.org/abs/astro-ph/0501171",
        "author":"Sloan Digital Sky Survey / BOSS", "license":"SDSS public-release catalog data (public domain)", "license_url":SDSS_POLICY,
        "note":"Actual BOSS galaxy redshifts from SDSS DR17 in a 150 by 150 by 40 Mpc comoving slice centered at RA=180 degrees, Dec=20 degrees, z=0.475. Positions use flat LCDM with H0=70 km/s/Mpc and Omega_m=0.27. This is a survey sample spanning the approximate BAO separation scale, not an individual acoustic shell or an identified BAO structure. The BAO excess requires a statistical pair-correlation measurement across a much larger sample and cannot be inferred by eye from this patch. Colors encode redshift, not galaxy color. All points come from the catalog; no patterns are imposed.", "per_pixel":1/90,"max_px":7},
}


def build(kind, output_dir=MODELS):
    cfg = CONFIG[kind]
    positions, colors, alpha, ids = catalog_geometry(kind)
    if len(ids)!=len(set(ids)) or not np.isfinite(positions).all() or not len(positions):
        raise ValueError(f"Invalid or duplicated source rows for {kind}")
    glb = VolumeGLB("Universe Scales direct public catalog conversion")
    # Interleave deterministic source records to make the production LOD prefixes
    # spatially representative. This changes ordering only, never positions.
    order = sorted(range(len(ids)),key=lambda i:hashlib.sha256(ids[i].encode()).digest())
    write_cloud(glb, cfg["id"], positions[order], colors[order], alpha[order],cfg["per_pixel"],cfg["max_px"])
    out = Path(output_dir)/f"{cfg['id']}.glb"
    glb.write(out)
    entry = {k:cfg[k] for k in ["id","source","author","license","license_url","note"]}
    entry.update({"src":str(out.relative_to(ROOT)) if out.is_relative_to(ROOT) else str(out),
        "matches":{"length":[cfg["item"]]}, "geometry":"point cloud",
        "representation":cfg.get("representation","catalog"), "reference":cfg["basis"], "reference_label":"Scientific basis",
        "license_files":["licenses/CC-BY-4.0.txt","sources/deepsky3d-models.md"] if kind in {"omega","orionarm"} else ["sources/deepsky3d-models.md"],
        "volume_semantics":"not_a_volume", "closed_volume_checked":False,
        "presentation":{"reference_size":cfg["reference"],"yaw":0,"pitch":0,"roll":0,
                        "layout_width_factor":1.25 if kind=="bootes" else 1.05},
        "processing":{"generator":"scripts/build_deepsky3d_models.py", "operations":["Direct conversion of hash-pinned public catalog coordinates; physical units retained.",
                      f"Native units: {cfg['unit']}; {len(positions)} distinct source records.",
                      "One soft point per selected record; no generated geometry, rulers, random depths or filler stars."]},
        "derived_statistics":{"records":len(positions),"unit":cfg["unit"],
                              "extent":np.ptp(positions,axis=0).tolist()}})
    entry.update(inspect_glb(out.read_bytes()))
    HANDOFF.mkdir(parents=True,exist_ok=True)
    (HANDOFF/f"{cfg['id']}.entry.json").write_text(json.dumps(entry,indent=2)+"\n")
    return {"id":cfg["id"],"records":len(ids),"bytes":entry["bytes"],"extent":entry["derived_statistics"]["extent"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",choices=CONFIG)
    args=parser.parse_args()
    for kind in ([args.only] if args.only else CONFIG):print(json.dumps(build(kind)))


if __name__=="__main__":
    main()
