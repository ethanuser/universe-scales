#!/usr/bin/env python3
"""Acquire public catalogs; pin numeric records without archive contact metadata.

Run with the repository venv. No added dependencies are needed. The --cache
directory keeps larger original inputs outside the repository. This is a source
refresh operation; ordinary offline builds use the checked-in gzip snapshots.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import ssl
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/"content/visualizations/models/sources/deepsky3d"
LMC_QUERY = """select source_id,ra,dec,phot_g_mean_mag,bp_rp,pmra,pmdec,parallax,parallax_error,random_index from gaiadr3.gaia_source where 1=contains(point('ICRS',ra,dec),circle('ICRS',81.28,-69.78,7)) and phot_g_mean_mag<19.5 and bp_rp is not null and pmra between 0.8 and 2.9 and pmdec between -0.7 and 1.4 and parallax between -0.2 and 0.2 and random_index between 0 and 10000000"""
SDSS_BASE = "select ra,dec,z,specObjID from SpecObj where sciencePrimary=1 and class='GALAXY' and zWarning=0 "
QUERIES = {
    "bootes": SDSS_BASE+"and ra between 198 and 247 and dec between 27 and 65 and z between 0.027 and 0.075",
    "bao": SDSS_BASE+"and survey='boss' and ra between 170 and 190 and dec between 15 and 25 and z between 0.43 and 0.52",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def acquire(cache, name, url):
    path=cache/name
    if not path.exists():
        request=urllib.request.Request(url,headers={"User-Agent":"UniverseScales public catalog preparation/1.0"})
        with urllib.request.urlopen(request,timeout=300,context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as r:
            data=r.read()
        path.write_bytes(data)
    return path.read_bytes()


def pin(name, rows, fields, source, original, selection, manifest):
    stream=io.StringIO(newline="")
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n")
    writer.writeheader()
    writer.writerows({k:row[k] for k in fields} for row in rows)
    payload=gzip.compress(stream.getvalue().encode(),compresslevel=9,mtime=0)
    (DEST/name).write_bytes(payload)
    manifest["files"][name]={"source":source,"original_sha256":sha(original),
        "sha256":sha(payload),"rows":len(rows),"columns":fields,"selection":selection}
    print(name,len(rows),len(payload))


def prepare(cache):
    cache.mkdir(parents=True,exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
    manifest={"method":"Public catalog numeric snapshots; original input SHA-256 and exact selections retained. Gzip timestamp fixed at zero.","files":{}}
    # The dust grid has a separate ranged-download preparation command.
    old_manifest=DEST/"manifest.json"
    if old_manifest.exists():
        old=json.loads(old_manifest.read_text())["files"]
        if "edenhofer-local-dust.npz" in old:manifest["files"]["edenhofer-local-dust.npz"]=old["edenhofer-local-dust.npz"]
    params={"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"csv","QUERY":LMC_QUERY}
    url="https://gea.esac.esa.int/tap-server/tap/sync?"+urllib.parse.urlencode(params)
    raw=acquire(cache,"lmc.csv",url)
    rows=list(csv.DictReader(io.StringIO(raw.decode())))
    if not rows or "source_id" not in rows[0]:raise ValueError("Unexpected Gaia response")
    pin("gaia-dr3-lmc.csv.gz",rows,list(rows[0]),url,raw,LMC_QUERY,manifest)

    url="https://zenodo.org/api/records/4891252/files/clusters.zip/content"
    raw=acquire(cache,"clusters.zip",url)
    archive=zipfile.ZipFile(io.BytesIO(raw))
    text=archive.read("catalogues/NGC_5139_oCen.txt").decode()
    fields="source_id ra dec x y plx pmra pmdec plxe pmrae pmdece pmcorr g_mag bp_rp Sigma qflag memberprob".split()
    rows=[dict(zip(fields,line.split())) for line in text.splitlines() if line and not line.startswith("#")]
    # Do not use uncertain parallaxes as individual cluster distances. The source
    # quality flags include density filters that would excise the dense center.
    rows=[r for r in rows if float(r["memberprob"])>.99 and r["bp_rp"] not in {"nan","NaN"}]
    keep="source_id ra dec x y g_mag bp_rp qflag memberprob".split()
    pin("gaia-edr3-omega-members.csv.gz",rows,keep,url,raw,
        "catalogues/NGC_5139_oCen.txt from CC BY 4.0 Zenodo record 4891252 v2; memberprob>0.99, finite BP-RP. No quality-flag cut; aperture applied by builder.",manifest)

    url="https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/199/26/table3&-out=2MASX,RAJ2000,DEJ2000,GLON,GLAT,Ktmag,cz&-out.max=unlimited"
    raw=acquire(cache,"2mrs.tsv",url)
    rows=[]
    for line in raw.decode().splitlines():
        fields=line.split("\t")
        if len(fields)!=6 or line.startswith("#"):continue
        try:values=[float(v) for v in fields]
        except ValueError:continue
        rows.append(dict(zip(["row","RAJ2000","DEJ2000","GLON","GLAT","Ktmag","cz"],[str(len(rows)+1),*map(str,values)])))
    pin("2mrs.csv.gz",rows,["row","RAJ2000","DEJ2000","GLON","GLAT","Ktmag","cz"],url,raw,
        "All numeric rows with finite redshift. Identity is the 1-based usable row in the original magnitude-ordered table; RA/Dec retained for cross-identification.",manifest)

    for kind,query in QUERIES.items():
        url="https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch?"+urllib.parse.urlencode({"cmd":query,"format":"csv"})
        raw=acquire(cache,kind+".csv",url)
        rows=list(csv.DictReader(io.StringIO("\n".join(l for l in raw.decode().splitlines() if not l.startswith("#")))))
        if not rows or "specObjID" not in rows[0]:raise ValueError("Unexpected SDSS response")
        pin(f"sdss-dr17-{kind}.csv.gz",rows,list(rows[0]),url,raw,query,manifest)
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,default=Path("/tmp/deepsky3d-source-cache"))
    prepare(parser.parse_args().cache)
