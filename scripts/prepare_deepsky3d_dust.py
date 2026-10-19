#!/usr/bin/env python3
"""Extract a physical local cube from Edenhofer's public CC BY 4.0 mean grid.

Use HTTP byte ranges rather than acquiring the entire 15.66-GB source FITS.
No interpolation or fitting: take every eighth 2-pc grid coordinate. Cache the
original response strips outside the repository; preserve SHA-256 per response.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import ssl
import urllib.request

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"content/visualizations/models/sources/deepsky3d"
URL="https://zenodo.org/api/records/8187943/files/mean_and_std_xyz.fits/content"


def acquire(cache,start,end,total=None):
    path=cache/f"{start}-{end}.bin"
    if path.exists():data=path.read_bytes()
    else:
        request=urllib.request.Request(URL,headers={"Range":f"bytes={start}-{end}","User-Agent":"UniverseScales public dust grid conversion/1.0"})
        with urllib.request.urlopen(request,timeout=90,context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as r:
            expected=f"bytes {start}-{end}/"
            if r.status!=206 or not r.headers.get("Content-Range","").startswith(expected):
                raise ValueError("Server did not honor exact byte range")
            if total is not None and r.headers["Content-Range"]!=expected+str(total):
                raise ValueError("Source FITS byte length changed")
            data=r.read()
        path.write_bytes(data)
    if len(data)!=end-start+1:raise ValueError("Truncated FITS range")
    return data


def header_fields(block):
    fields={}
    for i in range(0,len(block),80):
        card=block[i:i+80].decode("ascii");key=card[:8].strip()
        if key=="END":break
        if card[8:10]!="= ":continue
        value=card[10:].split("/")[0].strip()
        fields[key]=value.strip("'").strip() if value.startswith("'") else float(value)
    return fields


def prepare(cache):
    cache.mkdir(parents=True,exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
    header=acquire(cache,0,5759,15662543040)
    h=header_fields(header[2880:5760])
    expected={"XTENSION":"IMAGE","EXTNAME":"MEAN","BITPIX":-32,"NAXIS":3,
        **{f"NAXIS{k}":1251 for k in [1,2,3]},**{f"CDELT{k}":2 for k in [1,2,3]},
        **{f"CRVAL{k}":-1250 for k in [1,2,3]},**{f"CRPIX{k}":1 for k in [1,2,3]}}
    for key,value in expected.items():
        if h.get(key)!=value:raise ValueError(f"Unexpected FITS {key}: {h.get(key)}")
    n=1251;low=357;high=893;step=8
    indices=np.arange(low,high+1,step)
    def plane(z):
        start=5760+4*(int(z)*n*n+low*n)
        end=5760+4*(int(z)*n*n+(high+1)*n)-1
        raw=acquire(cache,start,end,15662543040)
        density=np.frombuffer(raw,dtype=">f4").reshape(high-low+1,n)[::step,low:high+1:step].astype(np.float32)
        return density,{"start":start,"end":end,"sha256":hashlib.sha256(raw).hexdigest()}
    with ThreadPoolExecutor(max_workers=8) as pool:planes=list(pool.map(plane,indices))
    density=np.stack([p[0] for p in planes])
    target=DEST/"edenhofer-local-dust.npz"
    np.savez_compressed(target,density=density,coordinates_pc=-1250+2*indices)
    manifest_path=DEST/"manifest.json"
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files":{}}
    manifest["files"][target.name]={"source":URL,"license":"CC-BY-4.0",
        "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"shape":list(density.shape),
        "source_bytes":15662543040,"header_sha256":hashlib.sha256(header).hexdigest(),
        "fits_mean_header":{k:h[k] for k in ["BITPIX","NAXIS1","NAXIS2","NAXIS3","CDELT1","CDELT2","CDELT3","CRVAL1","CRVAL2","CRVAL3","CRPIX1","CRPIX2","CRPIX3","CTYPE1","CTYPE2","CTYPE3","CUNIT1","CUNIT2","CUNIT3","CUNIT"]},
        "ranges":[p[1] for p in planes],"selection":"Indices 357..893 inclusive, stride 8 on X/Y/Z, in the first (MEAN) image HDU. Physical centers -536..+536 pc, step 16 pc. Native density values and NaNs retained; no reinterpolation.",
        "note":"SHA-256 per original HTTP range, not a whole-file checksum: the 15.66-GB source was not acquired in full."}
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Pinned {density.shape} grid, {np.isfinite(density).sum()} finite samples, {target.stat().st_size} bytes")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,default=Path("/tmp/deepsky3d-dust-cache"))
    prepare(parser.parse_args().cache)
