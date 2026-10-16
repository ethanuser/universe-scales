#!/usr/bin/env python3
"""Offline geographic models from pinned elevation and vector data.

--prepare downloads source tiles/vectors and pins compact derived grids. Normal
builds verify their hashes and need no network. Geographic axes are metres;
large scenes retain spherical Earth curvature, rather than stretching maps.
"""
import argparse
import concurrent.futures
import gzip
import hashlib
import io
import json
import math
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
from PIL import Image, ImageDraw

from build_everyday_models import mesh
from build_route_models import add_lines, add_ruler, clip_lines, geographic_frame, lines_from_geojson
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'content/visualizations/models/sources/terrain3d'
HANDOFF = ROOT/'handoff/terrain3d'
NE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
ATTRIBUTION = ('Mapzen / Tilezen; SRTM, GMTED2010 and United States 3DEP terrain courtesy of the U.S. Geological Survey; '
               'ETOPO1 ocean bathymetry courtesy of NOAA; Natural Earth public-domain map data; adaptation by Universe Scales.')
CONFIG = {
    'angel-falls': dict(item='Angel Falls', value=979, center=(-62.53556, 5.9675), span=(1100, 1100), zoom=14, shape=(121, 121), gain=1, pitch=22, yaw=-90,
        basis='https://en.wikipedia.org/wiki/Angel_Falls', palette='green',
        note='A cropped DEM of the Auyan-tepui escarpment at the published waterfall coordinate. The 1.1 km window is geographic context for the 979 m total descent, not a scan of the falling water. SRTM rounds the cliff and does not resolve an overhang, water column or each cascade. No water ribbon, artificial cliff or height correction is added.'),
    'victoria-falls': dict(item='Victoria Falls', value=1708, center=(25.858, -17.925), span=(2000, 1800), zoom=15, shape=(129, 145), gain=1, pitch=58,
        basis='https://whc.unesco.org/en/list/509/', palette='green',
        note='The present Zambezi gorge and upstream terrain around the falls, with a 2 km east-west context window. Calibration is the published 1,708 m width, not the DEM relief. SRTM smooths the narrow gorge; this is terrain, not a reconstruction of the seasonally changing water curtain. No invented waterfall surface is added.'),
    'gibraltar': dict(item='Strait of Gibraltar', value=14200, center=(-5.57,35.95), span=(18000,18000), zoom=12, shape=(161,161), gain=1, pitch=63,
        basis='https://en.wikipedia.org/wiki/Strait_of_Gibraltar', palette='green', ocean=True,
        note='An 18 km geographic window of the narrow crossing between Spain and Morocco, with actual NOAA ETOPO1 ocean-floor relief and a flat sea-level surface. The context window is larger than the catalog 14.2 km narrowest crossing; its crop edges are not measurement endpoints. Ocean depth is sampled explicitly from the coarse 1 arc-minute ETOPO1 grid, not a detailed strait sounding survey.'),
    'tanganyika': dict(item='Lake Tanganyika', value=673000, bounds=(28.7,-9.1,31.6,-3.15), zoom=8, shape=(257,129), gain=4, pitch=68, roll=-12,
        basis='https://en.wikipedia.org/wiki/Lake_Tanganyika', palette='green', lake='Lake Tanganyika',
        note='The actual Natural Earth Lake Tanganyika shoreline in sampled East African Rift terrain. The complete lake remains at geographic horizontal scale; relief is exaggerated 4 times. The lake is rendered at its sampled surface elevation: there is no invented lake-floor bathymetry. The 673 km reference is the catalog long-axis length, not a sum around the shoreline.'),
    'grand-canyon': dict(item='Grand Canyon Length', value=446000, bounds=(-114.2,35.55,-111.45,36.95), zoom=10, shape=(161,257), gain=5, pitch=58, direct_usgs=True,
        basis='https://www.nps.gov/grca/faqs.htm', palette='sand', rivers=['Colorado'], ruler='446 km',
        note='Regional terrain sampled directly from the USGS 3DEP elevation service and a clipped Natural Earth Colorado River centerline. Relief is exaggerated 5 times; the cyan line is widened for visibility and draped on the mesh, not a water-depth survey. The map window includes context beyond the canyon and does not define its rim or exact Lees Ferry-to-Grand Wash endpoints. The independent 446 km ruler represents the published river-course length; the geographic map is not stretched to that route length.'),
    'suez': dict(item='Suez Canal', value=193300, bounds=(31.95,29.8,32.8,31.5), zoom=10, shape=(257,129), gain=3, pitch=66, roll=8,
        basis='https://www.suezcanal.gov.eg/English/About/SuezCanal/Pages/CanalCharacteristics.aspx', palette='sand', rivers=['Suez Canal'], ocean=True, ruler='193.3 km',
        note='The generalized Natural Earth Suez Canal centerlines, including their separate mapped branches, over sampled terrain between the Mediterranean and Red seas. Relief is exaggerated 3 times; line width is a visibility symbol, not canal width. The source is generalized cartography, not a current engineering plan or full port-approach inventory. The independent 193.3 km ruler marks the catalog navigation-route length; neither map nor centerlines are stretched to it.'),
    'san-andreas': dict(item='San Andreas Fault', value=1210000, bounds=(-125,32.2,-114.8,41), zoom=7, shape=(161,129), gain=5, pitch=64, roll=-22,
        basis='https://www.usgs.gov/programs/earthquake-hazards/faults', palette='sand', faults=True, ocean=True, ruler='1,210 km',
        note='USGS Quaternary Fault and Fold Database traces whose fault_name contains San Andreas, with original section identities and gaps retained. Line geometry is simplified with a 300 m horizontal tolerance for this regional display; original vertices and fragments are pinned in the source. The bright trace is a widened cartographic symbol, not a chasm or measured fault-zone width. Relief is exaggerated 5 times. The source includes multiple mapped strands; their aggregate linework is not a single traversable route. The separate approximate 1,210 km ruler represents the catalog system length and is not used to rescale the coordinates.'),
    'sahara': dict(item='Sahara', value=4800000, bounds=(-17,15,34,34), zoom=5, shape=(145,321), gain=12, pitch=62,
        basis='https://modis.gsfc.nasa.gov/gallery/individual.php?db_date=2008-05-08', palette='sand', ocean=True,
        note='Northern Africa from Atlantic coastal terrain across the Atlas, Ahaggar and Tibesti to the Nile/Red Sea region, at geographic horizontal scale on a curved Earth. Relief is exaggerated 12 times. The rectangular viewing aperture is an authored regional crop, not a mapped climatic boundary of the Sahara; no desert-boundary polygon is invented. The 4,800 km catalog east-west span is an approximate geographic reference. Colors indicate elevation and ocean depth, not vegetation, dunes, sand cover or mapped lithology.'),
    'great-barrier-reef': dict(item='Great Barrier Reef', value=2300000, bounds=(142,-24.6,153.8,-10.5), zoom=6, shape=(257,193), gain=8, pitch=65, roll=-19,
        basis='https://www.gbrmpa.gov.au/about-us/spatial-data-information-services', palette='green', ocean=True, reefs=True,
        note='Actual Reef Authority reef polygons selected within the Queensland viewing aperture, in contrasting turquoise over sampled coastal terrain and NOAA ETOPO1 sea floor. These polygons are mapped reef footprints, not a live-coral census, park boundary or detailed 3D coral survey. Relief and bathymetry are exaggerated 8 times; the reef layer is a color overlay on that regional surface, not individually measured reef heights. Geographic horizontal coordinates and Earth curvature are retained. The 2,300 km catalog length refers to the broad reef system, not a straight end-to-end measurement of every polygon. Contains Great Barrier Reef Marine Park Authority 2023 data under CC BY 4.0; modified by selecting and rasterizing mapped reefs. No endorsement is implied.'),
}
# Source shading retains the complete pinned grid. Large regional surfaces only
# need every second source vertex at explorer scale; original metre axes remain.
for _name,_config in CONFIG.items():
    _config['mesh_step']=1 if _name in ['angel-falls','victoria-falls'] else 2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    return path.read_bytes()


def coordinates(c):
    rows, cols = c['shape']
    if 'bounds' in c:
        west, south, east, north = c['bounds']
        lon, lat = np.meshgrid(np.linspace(west,east,cols), np.linspace(north,south,rows))
    else:
        lon0, lat0 = c['center']; width, depth = c['span']
        x,z = np.meshgrid(np.linspace(-width/2,width/2,cols),np.linspace(-depth/2,depth/2,rows))
        lat = lat0-np.degrees(z/6378137)
        lon = lon0+np.degrees(x/(6378137*math.cos(math.radians(lat0))))
    return np.stack((lon,lat),axis=-1)


def bounds(c):
    ll=coordinates(c)
    return (float(ll[...,0].min()),float(ll[...,1].min()),float(ll[...,0].max()),float(ll[...,1].max()))


def sample_tiles(ll, zoom, cache):
    """Sample pixel centers, bilinearly across tile edges (including bathymetry)."""
    px=(ll[...,0]+180)/360*2**zoom*256-.5
    py=(1-np.arcsinh(np.tan(np.radians(ll[...,1])))/np.pi)/2*2**zoom*256-.5
    ix,iy=np.floor(px).astype(int),np.floor(py).astype(int)
    keys=set()
    for dx,dy in [(0,0),(1,0),(0,1),(1,1)]:
        keys.update(zip(((ix+dx)//256).ravel().tolist(),((iy+dy)//256).ravel().tolist()))
    def fetch(key):
        tx,ty=key
        url=f'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{zoom}/{tx}/{ty}.png'
        path=cache/f'{zoom}-{tx}-{ty}.png'; header_path=path.with_suffix('.headers.json')
        if not path.exists():
            for attempt in range(3):
                try:
                    with urlopen(url,timeout=45) as response:
                        path.write_bytes(response.read())
                        header_path.write_text(json.dumps({k:v for k,v in response.headers.items() if k.lower()=='x-imagery-sources'}))
                    break
                except OSError:
                    if attempt==2:raise
                    time.sleep(attempt+1)
        raw=path.read_bytes(); rgb=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB')).astype(float)
        h=rgb[...,0]*256+rgb[...,1]+rgb[...,2]/256-32768
        return key,h,dict(url=url,sha256=digest(path),headers=json.loads(header_path.read_text()) if header_path.exists() else {})
    tiles={}; records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for key,h,record in ex.map(fetch,sorted(keys)):
            tiles[key]=h;records.append(record)
    fx,fy=px-ix,py-iy; result=np.zeros(px.shape)
    for dx,dy,w in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
        xx,yy=ix+dx,iy+dy; v=np.empty(px.shape)
        for tx,ty in keys:
            mask=(xx//256==tx)&(yy//256==ty)
            v[mask]=tiles[tx,ty][yy[mask]%256,xx[mask]%256]
        result+=v*w
    return result,records


def prepare(names, cache):
    cache.mkdir(parents=True,exist_ok=True); SOURCE.mkdir(parents=True,exist_ok=True)
    vector_sources={}
    for kind in ['rivers','lakes','land']:
        suffix={'rivers':'rivers_lake_centerlines','lakes':'lakes','land':'land'}[kind]
        url=NE+f'ne_10m_{suffix}.geojson'
        raw=get(url,cache/f'{kind}.json'); vector_sources[kind]=(json.loads(raw),dict(url=url,sha256=hashlib.sha256(raw).hexdigest()))
    for name in names:
        c=CONFIG[name]; folder=SOURCE/name;folder.mkdir(parents=True,exist_ok=True)
        ll=coordinates(c)
        if c.get('direct_usgs'):
            heights,raster_record=sample_raster(ll,cache,name,'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer')
            tiles=[]
        else:heights,tiles=sample_tiles(ll,c['zoom'],cache)
        np.savez_compressed(folder/'terrain.npz',heights=heights.astype('<f4'),lonlat=ll.astype('<f8'))
        west,south,east,north=bounds(c); features=[]; records=[raster_record] if c.get('direct_usgs') else []
        for kind in ['rivers','lakes','land']:
            document,record=vector_sources[kind]
            for f in document['features']:
                n=f['properties'].get('name','')
                if kind=='rivers' and n not in c.get('rivers',[]):continue
                if kind=='lakes' and (not c.get('lake') or n!=c['lake']):continue
                if kind=='land' and not c.get('ocean'):continue
                # Keep unaltered source geometries; rasterization/clipping occurs offline.
                features.append(dict(type='Feature',properties={'kind':kind,'name':n},geometry=f['geometry']))
            if any(f['properties']['kind']==kind for f in features):records.append(record)
        if c.get('faults'):
            service='https://earthquake.usgs.gov/arcgis/rest/services/haz/Qfaults/MapServer/21'
            params=dict(
                where="fault_name LIKE '%San Andreas%'",outFields='fault_name,section_name,fault_id,section_id,linetype,age',
                outSR=4326,f='geojson',returnGeometry='true',orderByFields='OBJECTID',resultRecordCount=1000)
            selected,pages=arcgis_features(service,params,cache,'faults')
            for f in selected:f['properties']['kind']='faults';features.append(f)
            records.extend(pages)
        if c.get('reefs'):
            service='https://services-ap1.arcgis.com/8gXWSCxaJlFIfiTr/arcgis/rest/services/Great_Barrier_Reef_Features_20/FeatureServer/64'
            params=dict(where="FEAT_NAME = 'Reef'",geometry=','.join(map(str,bounds(c))),geometryType='esriGeometryEnvelope',inSR=4326,
                spatialRel='esriSpatialRelIntersects',outFields='OBJECTID,FEAT_NAME,GBR_NAME,LABEL_ID',outSR=4326,f='geojson',returnGeometry='true',
                orderByFields='OBJECTID',resultRecordCount=1000,geometryPrecision=6)
            selected,pages=arcgis_features(service,params,cache,'reefs')
            for f in selected:f['properties']['kind']='reefs';features.append(f)
            records.extend(pages)
            rights='https://www.arcgis.com/sharing/rest/content/items/816f4d747cd94d84acfd924b27f581d8?f=json'
            item=json.loads(get(rights,cache/'reef-item.json'))
            (folder/'reef-license.json').write_text(json.dumps({k:item[k] for k in ['id','title','owner','licenseInfo','accessInformation','url']},indent=2)+'\n')
        if c.get('ocean'):
            # Terrarium's high-zoom SRTM ocean is often zero. Read NOAA depth explicitly.
            ocean,record=sample_raster(ll,cache,name,'https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer')
            landmask=np.asarray(polygon_mask([f for f in features if f['properties']['kind']=='land'],bounds(c),(ll.shape[1],ll.shape[0])))>0
            heights=np.where(landmask,heights,ocean)
            np.savez_compressed(folder/'terrain.npz',heights=heights.astype('<f4'),lonlat=ll.astype('<f8'))
            records.append(record)
        # Global land polygons are large: retain clipped raster mask rather than vendoring the world.
        land=[f for f in features if f['properties']['kind']=='land']
        if land:
            polygon_mask(land,bounds(c),(1024,1024)).save(folder/'land-mask.png')
        features=[f for f in features if f['properties']['kind']!='land']
        raw=(json.dumps(dict(type='FeatureCollection',features=features),separators=(',',':'))+'\n').encode()
        (folder/'vectors.geojson.gz').write_bytes(gzip.compress(raw,mtime=0))
        (folder/'vectors.geojson').unlink(missing_ok=True)
        files=['terrain.npz','vectors.geojson.gz']+(['land-mask.png'] if land else [])+(['reef-license.json'] if c.get('reefs') else [])
        meta=dict(id=name,grid_shape=list(heights.shape),bounds_lonlat=bounds(c),source_zoom=c['zoom'],
            elevation_range_m=[float(heights.min()),float(heights.max())],vertical_gain=c['gain'],tiles=tiles,vector_sources=records,
            files={f:digest(folder/f) for f in files},
            processing='Bilinear pixel-center elevation sampling including negative depths; no summit/depth correction, smoothing or invented relief. Source vector fragments retained separately. Authored aperture.',attribution=ATTRIBUTION)
        (folder/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
        print(name,'prepared',len(tiles),'tiles',meta['elevation_range_m'],flush=True)


def arcgis_features(service,params,cache,prefix):
    features=[];records=[]
    for page in range(30):
        url=service+'/query?'+urlencode(dict(params,resultOffset=page*1000))
        raw=get(url,cache/f'{prefix}-page-{page}.json');d=json.loads(raw)
        if 'error' in d or not d.get('features'):raise ValueError(f'Incomplete {prefix} page {page}: {str(d)[:300]}')
        features.extend(d['features']);records.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest()))
        if not (d.get('exceededTransferLimit') or d.get('properties',{}).get('exceededTransferLimit')):
            return features,records
    raise ValueError(f'{prefix} exceeded paging limit')


def sample_raster(ll,cache,name,service):
    rows,cols=ll.shape[:2];dx=ll[0,1,0]-ll[0,0,0];dy=ll[0,0,1]-ll[1,0,1]
    bbox=[ll[0,0,0]-dx/2,ll[-1,0,1]-dy/2,ll[0,-1,0]+dx/2,ll[0,0,1]+dy/2]
    url=service+'/exportImage?'+urlencode(dict(
        bbox=','.join(map(str,bbox)),bboxSR=4326,imageSR=4326,size=f'{cols},{rows}',format='tiff',pixelType='F32',
        interpolation='RSP_BilinearInterpolation',renderingRule=json.dumps({'rasterFunction':'None'}),adjustAspectRatio='false',f='image'))
    key=hashlib.sha256(url.encode()).hexdigest()[:12]
    raw=get(url,cache/f'raster-{name}-{key}.tif');a=np.asarray(Image.open(io.BytesIO(raw))).astype(float)
    if a.shape!=(rows,cols) or not np.isfinite(a).all() or a.min() < -12000:raise ValueError('Unexpected elevation export')
    return a,dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),role=(
        'NOAA ETOPO1 sampled ocean elevations, native 1 arc-minute grid' if 'ETOPO1' in service else 'USGS 3DEP land elevation')+'; unrendered signed float TIFF')


def polygon_mask(features, window, size):
    west,south,east,north=window; im=Image.new('L',size);draw=ImageDraw.Draw(im)
    def points(ring):return [((p[0]-west)/(east-west)*(size[0]-1),(north-p[1])/(north-south)*(size[1]-1)) for p in ring]
    for f in features:
        g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        for poly in polys:
            if max(p[0] for p in poly[0])<west or min(p[0] for p in poly[0])>east:continue
            if max(p[1] for p in poly[0])<south or min(p[1] for p in poly[0])>north:continue
            draw.polygon(points(poly[0]),fill=255)
            for hole in poly[1:]:draw.polygon(points(hole),fill=0)
    return im


def frame(c,ll,h):
    if 'center' in c and 'span' in c:
        lon0,lat0=c['center']
        return np.stack((np.radians(ll[...,0]-lon0)*6378137*math.cos(math.radians(lat0)),h,
                         -np.radians(ll[...,1]-lat0)*6378137),axis=-1)
    west,south,east,north=bounds(c);center=((west+east)/2,(south+north)/2)
    return geographic_frame(ll,center,h/1000)*1000


def drape(ll, grid_ll, positions):
    """Barycentric sampling of the rendered triangles (not a finer hidden DEM)."""
    rows,cols=grid_ll.shape[:2]
    x=np.clip((ll[:,0]-grid_ll[0,0,0])/(grid_ll[0,-1,0]-grid_ll[0,0,0])*(cols-1),0,cols-1-1e-9)
    z=np.clip((ll[:,1]-grid_ll[0,0,1])/(grid_ll[-1,0,1]-grid_ll[0,0,1])*(rows-1),0,rows-1-1e-9)
    ix,iz=x.astype(int),z.astype(int);u,v=x-ix,z-iz
    a,b,c,d=positions[iz,ix],positions[iz,ix+1],positions[iz+1,ix],positions[iz+1,ix+1]
    return np.where((u+v<=1)[:,None],a*(1-u-v)[:,None]+b*u[:,None]+c*v[:,None],
                    b*(1-v)[:,None]+c*(1-u)[:,None]+d*(u+v-1)[:,None])


def simplify_line(points,tolerance,return_indices=False):
    """Douglas-Peucker retaining original vertices and every separate fragment."""
    if len(points)<=2:return np.arange(len(points)) if return_indices else points
    keep={0,len(points)-1};stack=[(0,len(points)-1)]
    while stack:
        start,end=stack.pop()
        if end-start<=1:continue
        delta=points[end]-points[start];length=delta@delta
        middle=points[start+1:end]
        t=np.clip(((middle-points[start])@delta)/max(length,1e-30),0,1)
        distance=np.linalg.norm(middle-(points[start]+t[:,None]*delta),axis=1)
        i=int(np.argmax(distance))
        if distance[i]>tolerance:
            at=start+1+i;keep.add(at);stack.extend([(start,at),(at,end)])
    return np.array(sorted(keep)) if return_indices else points[sorted(keep)]


def build(name):
    c=CONFIG[name];folder=SOURCE/name;meta=json.loads((folder/'provenance.json').read_text())
    for f,sha in meta['files'].items():
        if digest(folder/f)!=sha:raise ValueError(f'Pinned source hash mismatch: {name}/{f}')
    with np.load(folder/'terrain.npz') as data:h=data['heights'].astype(float);ll=data['lonlat']
    rows,cols=h.shape;source_shape=h.shape;p=frame(c,ll,h*c['gain']);window=bounds(c)
    vectors=json.loads(gzip.decompress((folder/'vectors.geojson.gz').read_bytes()))['features']
    glb=GLB('Universe Scales: real elevation/map data; authored geographic crop and elevation palette')
    # Elevation palette with subtle baked slope shading; colors do not claim land cover.
    low,high=([.18,.34,.23],[.68,.64,.48]) if c['palette']=='green' else ([.46,.31,.17],[.86,.73,.49])
    t=np.clip((h-max(h.min(),0))/max(np.percentile(h,98)-max(h.min(),0),1),0,1)[...,None]
    color=np.array(low)*(1-t)+np.array(high)*t
    du,dv=np.gradient(p,axis=1),np.gradient(p,axis=0);n=np.cross(dv,du);n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-20)
    # Bake high-frequency relief so the broad geographic scene remains legible when small.
    shade=np.clip(n@np.array([-.45,.78,.43]),0,1)
    color*=.72+.28*shade[...,None]
    if c.get('ocean'):
        land=np.asarray(Image.open(folder/'land-mask.png').resize((cols,rows),Image.Resampling.NEAREST))>0
        depth=np.clip(-h/5000,0,1)[...,None]
        ocean=np.array([.08,.39,.49])*(1-depth)+np.array([.025,.10,.22])*depth
        color[~land]=ocean[~land]
    lake=[f for f in vectors if f['properties']['kind']=='lakes']
    if lake:
        mask=np.asarray(polygon_mask(lake,window,(cols,rows)))>0;color[mask]=[.055,.31,.44]
    tex=Image.fromarray(np.uint8(np.clip(color,0,1)*255)).resize((1024,1024),Image.Resampling.BICUBIC)
    reefs=[f for f in vectors if f['properties']['kind']=='reefs']
    if reefs:
        # Preserve small measured footprints in texture space, not the coarser mesh grid.
        tex.paste((54,211,184),(0,0),polygon_mask(reefs,window,tex.size))
    # Use original sampled vertices at a lower mesh density, keeping the full
    # elevation shading/reef footprint texture. Do not interpolate new relief.
    step=c['mesh_step'];p=p[::step,::step];ll=ll[::step,::step];rows,cols=p.shape[:2]
    if c.get('ocean'):land=land[::step,::step]
    du,dv=np.gradient(p,axis=1),np.gradient(p,axis=0);n=np.cross(dv,du);n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-20)
    out=io.BytesIO();tex.save(out,format='JPEG',quality=94,subsampling=0)
    mat=glb.material('Authored elevation colors, not imagery or geology',rough=.98,double_sided=False,texture=glb.texture(out.getvalue(),'image/jpeg'))
    u,v=np.meshgrid(np.linspace(0,1,cols),np.linspace(0,1,rows))
    glb.mesh_node('Measured elevation surface',[glb.primitive(p.reshape(-1,3),grid_indices(rows,cols),mat,
        normals=n.reshape(-1,3),uvs=np.stack((u,v),axis=-1).reshape(-1,2))])
    bottom=float(p[...,1].min()-c['value']*.012)
    perimeter=np.concatenate((p[0],p[1:,-1],p[-1,-2::-1],p[-2:0:-1,0]))
    wall=glb.material('Arbitrary display cut',(.22,.17,.115,1),rough=1,double_sided=False)
    points=[];faces=[]
    for a,b in zip(perimeter,np.roll(perimeter,-1,axis=0)):
        k=len(points);points.extend([a,[a[0],bottom,a[2]],[b[0],bottom,b[2]],b]);faces.extend([(k,k+2,k+1),(k,k+3,k+2)])
    mesh(glb,'Opaque geographic crop sides',points,faces,wall)
    # The crop perimeter can be curved. Close it with its actual bottom ring.
    ring=perimeter.copy();ring[:,1]=bottom;center=ring.mean(axis=0)
    mesh(glb,'Flat display underside',np.concatenate(([center],ring)),[(0,i+1,(i+1)%len(ring)+1) for i in range(len(ring))],wall)
    if c.get('ocean') and name=='gibraltar':
        # Sea surface only where land is absent; no blue film over coastal hills.
        water=p.copy();water[...,1]=0
        idx=grid_indices(rows,cols).reshape(-1,3)
        idx=idx[(~land).ravel()[idx].all(axis=1)].ravel()
        watermat=glb.material('Sea-level surface',(.09,.48,.66,.34),rough=.3,blend=True,double_sided=True)
        glb.mesh_node('Sea level',[glb.primitive(water.reshape(-1,3),idx,watermat,normals=np.tile([0,1,0],(rows*cols,1)))])
    for kind in ['rivers','faults']:
        features=[f for f in vectors if f['properties']['kind']==kind]
        if not features:continue
        lines=clip_lines(lines_from_geojson(dict(features=features)),window)
        draped=[]
        # Densify original straight segments to stay on the rendered relief.
        for line in lines:
            if kind=='faults':
                metric=frame(c,line,np.zeros(len(line)))
                # Select original lon/lat vertices via simplified metric index positions.
                line=line[simplify_line(metric[:,[0,2]],300,return_indices=True)]
            dense=[]
            for a,b in zip(line[:-1],line[1:]):
                count=max(2,math.ceil(np.max(np.abs(b-a)/np.abs(ll[-1,-1]-ll[0,0]))*max(rows,cols)*3))
                dense.extend(np.linspace(a,b,count,endpoint=False))
            dense.append(line[-1]);q=drape(np.array(dense),ll,p);q[:,1]+=c['value']*.0007;draped.append(q)
        add_lines(glb,'Mapped fault traces' if kind=='faults' else 'Mapped waterway centerlines',draped,
            (1,.25,.065,1) if kind=='faults' else (.10,.77,.91,1),width=c['value']*.0018)
    if c.get('ruler'):
        add_ruler(glb,c['value'],bottom-c['value']*.025,float(p[...,2].max()+c['value']*.04),c['ruler'])
    model_id='terrain3d-'+name;path=ROOT/f'content/visualizations/models/{model_id}.glb';glb.write(path)
    note=c['note']+' Horizontal coordinates are not normalized to the catalog size. Colors are illustrative. The opaque sides and flat underside are arbitrary display cuts, not real cliffs or geological strata. '+ATTRIBUTION
    if c.get('ocean') and name!='gibraltar':
        note+=' Ocean depths are sampled explicitly from NOAA ETOPO1 (1 arc-minute), using Natural Earth coastlines to select ocean samples; coastlines and land/ocean source transitions are generalized.'
    entry=dict(id=model_id,source='https://registry.opendata.aws/terrain-tiles/',basis_url=c['basis'],basis_label='Geographic measurement and context',
        author=ATTRIBUTION,license='US-government public-domain elevation and Natural Earth public-domain vectors; Mapzen attribution',
        license_url='https://github.com/tilezen/joerd/blob/master/docs/attribution.md',license_files=[f'sources/{model_id}.md'],
        matches={'length':[c['item']]},geometry='mesh',representation='dem_terrain',volume_semantics='not_applicable',closed_volume_checked=False,
        presentation=dict(reference_size=c['value'],pitch=c['pitch'],yaw=c.get('yaw',0),roll=c.get('roll',0),layout_width_factor=1.3),
        note=note,processing=dict(script='scripts/build_terrain3d_models.py',units='metres',vertical_gain=c['gain'],mesh_grid_step=step,
            source_note=f'content/visualizations/models/sources/{model_id}.md',provenance=str((folder/'provenance.json').relative_to(ROOT)),source_files=meta['files']),
        src=str(path.relative_to(ROOT)),**inspect_glb(path.read_bytes()))
    if c.get('direct_usgs'):entry['source']='https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
    if reefs:
        entry['author']+=' Great Barrier Reef Marine Park Authority 2023.'
        entry['license']+='; Reef Authority reef data CC-BY-4.0'
        entry['processing']['reef_rights_snapshot']='content/visualizations/models/sources/terrain3d/great-barrier-reef/reef-license.json'
    HANDOFF.mkdir(parents=True,exist_ok=True);(HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry,indent=2)+'\n')
    refs=['https://registry.opendata.aws/terrain-tiles/','https://github.com/tilezen/joerd/blob/master/docs/data-sources.md',entry['license_url'],
          'https://www.naturalearthdata.com/about/terms-of-use/',c['basis']]+[r['url'] for r in meta['vector_sources']]
    (SOURCE.parent/f'{model_id}.md').write_text(f'# {c["item"]}: elevation and map geometry\n\n{note}\n\n'
        f'## Pinned source and processing\n\n`terrain3d/{name}/provenance.json` records every tile URL, SHA-256, provider header, grid bounds and elevation range, plus the original vector download hashes. '
        f'The compact `terrain.npz` stores {source_shape[0]} × {source_shape[1]} original sampled elevations and longitude/latitude. The mesh retains every {step} grid vertex along each axis ({rows} × {cols}), while the elevation-shading texture retains the full input grid. `vectors.geojson.gz` retains losslessly compressed source fragments independently. '
        'Global land is pinned as a derived crop mask, not distributed as a world dataset. Source grid spacing is a sampling choice, not a claim of DEM resolution. '
        'Small scenes use local east/up/south coordinates with spherical WGS84-radius distances; regional scenes use a spherical Earth of radius 6371.0088 km in a local tangent frame. '
        'Large-scene curvature is retained; no map projection rescales the footprint to fit the quantity. Geographic approximation differs slightly from ellipsoidal surveying. '
        f'Vertical gain: **{c["gain"]}×**. No extreme-point correction or procedural terrain is added.\n\n'
        'Normal offline rebuild: `./venv/bin/python scripts/build_terrain3d_models.py '+name+'`. '
        'Optional network source refresh: add `--prepare --cache /tmp/terrain3d`. Registration: '
        f'`python3 scripts/register_model.py handoff/terrain3d/{model_id}.entry.json content/visualizations/models/{model_id}.glb`.\n\n'
        '## Sources and rights\n\n'+ '\n'.join('- '+u for u in dict.fromkeys(refs))+'\n\n'
        'Source pages were opened during preparation on 2026-10-16. Mapzen attribution applies alongside provider rights; '
        'the Joerd software license alone is not a license for elevation data. USGS SRTM/GMTED/3DEP and NOAA ETOPO1 are U.S. government data; Natural Earth states its data are public domain. '
        'No aerial photography, proprietary map tiles, invented survey traces or external runtime dependencies are used.\n')
    print(model_id,entry['bytes'],entry['triangle_count'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('names',nargs='*',choices=list(CONFIG))
    parser.add_argument('--prepare',action='store_true');parser.add_argument('--cache',type=Path,default=Path('/tmp/terrain3d'))
    args=parser.parse_args();names=args.names or list(CONFIG)
    if args.prepare:prepare(names,args.cache)
    for name in names:build(name)
