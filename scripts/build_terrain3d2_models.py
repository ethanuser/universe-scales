#!/usr/bin/env python3
"""Convert pinned public elevation, damage-survey, and stereo-height data to GLB.

Normal builds are offline. --prepare refreshes the source subsets; only that
step needs netCDF4 for the NASA file. No stands, undersides, extruded paths,
rulers, reconstructed overhangs, or invented plume volumes are generated.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
from PIL import Image, ImageDraw

from build_terrain3d_models import (bounds, coordinates, digest, frame, get,
                                    polygon_mask, sample_raster, sample_tiles)
from build_route_models import clip_lines, lines_from_geojson
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'content/visualizations/models/sources/terrain3d2'
HANDOFF = ROOT/'handoff/terrain3d2'
USGS = 'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
NOAA = 'https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer'
NPS = 'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/ANST_Facilities/FeatureServer/7'
DAT = 'https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/2'
NASA = 'https://science-data.larc.nasa.gov/LaRC-SD-Publications/2022-11-22-001-KMB/'
GRAVITY = 'https://topex.ucsd.edu/cgi-bin/get_data.cgi'
NAIP = 'https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer'
PGC_RIGHTS = 'https://www.pgc.umn.edu/guides/stereo-derived-elevation-models/pgc-dem-products-arcticdem-rema-and-earthdem/'
CONFIG = {
    'mount-thor': dict(item='Mount Thor Cliff', value=1200., center=(-65.32,66.538), span=(1400.,1000.), shape=(129,145), zoom=14, gain=1., pitch=5., yaw=65.,
        source='https://registry.opendata.aws/terrain-tiles/', basis='https://geonames.nrcan.gc.ca/search-place-names/unique?id=OAQLW&wbdisable=true',
        author='Mapzen/Tilezen; Polar Geospatial Center / ArcticDEM; Natural Resources Canada / CDEM. ArcticDEM support: NSF-OPP awards 1043681, 1559691, 1542736, 1810976 and 2129685.',
        license='ArcticDEM CC-BY-4.0 and Canadian Open Government Licence elevation; Mapzen attribution', rights='https://github.com/tilezen/joerd/blob/master/docs/attribution.md',
        note='Public Mapzen elevation tiles in a 1.4 km east-west by 1.0 km north-south aperture across the west face of Thor Peak. Tilezen documents ArcticDEM and Canadian elevation as sources at this latitude; per-tile provider headers are absent, so their precise local mix is not asserted. Horizontal distances and elevations retain metre units; vertical exaggeration is 1×. A single-valued DEM cannot represent the overhang and rounds the steep face. This is a cropped terrain surface, not a complete rock-face scan or a surveyed 1,200 m cliff-height measurement. No summit-height adjustment or gap filling is performed by this builder. A separate direct ArcticDEM service trial had major no-data holes and was rejected.'),
    'appalachian-trail': dict(item='Appalachian Trail', value=3536400., bounds=(-87.,30.,-64.,50.), shape=(257,257), zoom=7, gain=8., pitch=68., roll=-28.,
        source=NPS, basis='https://www.nps.gov/appa/planyourvisit/maps.htm',
        author='National Park Service Appalachian National Scenic Trail and Appalachian Trail Conservancy, 2023 treadway GPS data; Mapzen/Tilezen terrain, USGS SRTM/GMTED2010/3DEP and NOAA ETOPO1 bathymetry.',
        license='Public NPS GIS data (source liability and access notice retained); US-government elevation with Mapzen attribution', rights='https://www.nps.gov/aboutus/disclaimer.htm',
        note='All 30 original NPS A.T. Treadway features (June 2023 version, GPS surveys from 1998–2022 plus supplemental information) are drawn over eastern-US relief. Separate club sections, source bends and gaps are retained. The bright line is a widened map symbol rasterized onto the terrain, not the width of the footpath. Relief is exaggerated 8×; horizontal coordinates and Earth curvature retain geographic scale. The regional aperture supplies context and its edges do not measure trail length. The 3,536.4 km catalog quantity is accumulated walking distance, not map extent; the source is not claimed to be the 2024 alignment. This is not a navigation or property-access map.'),
    'el-reno': dict(item='El Reno Tornado', value=4184.2944, center=(-97.96,35.449), span=(5100.,5100.), shape=(145,145), gain=1., pitch=65.,
        source=DAT, basis='https://www.weather.gov/oun/events-20130531',
        author='NOAA National Weather Service Damage Assessment Toolkit, ElReno_Poly survey feature; USGS 3DEP terrain; USDA NAIP public-domain orthophotography via USGS The National Map.',
        license='US-government public-domain survey, elevation and NAIP imagery', rights='https://www.weather.gov/disclaimer',
        note='A 5.1 km square terrain aperture south of El Reno airport with the clipped original NWS Damage Assessment Toolkit polygon identified as ElReno_Poly (31 May 2013). Orange marks mapped damage-survey coverage on unexaggerated USGS 3DEP terrain. Public USDA NAIP aerial imagery supplies later geographic context, not a photograph of the tornado or its 2013 damage; the catalog tile at the aperture center is dated 29 May 2021. The full polygon is pinned, but its longer eastward track lies outside this deliberately local aperture. The polygon is not an instantaneous funnel, a measured wind-field surface, or an exact outline of the published maximum 2.6-mile tornado width. No vortex, funnel, moving centerline or artificial width boundary is constructed. The polygon source retains its historical EF3+ attribute; this does not revise the NWS event rating.'),
    'hunga-tonga': dict(item='Hunga Tonga Eruption Plume', value=58000., center=(-175.40,-20.64), span=(64000.,64000.), shape=(65,65), gain=1., pitch=10., yaw=0.,
        source=NASA, basis=NASA,
        author='Kristopher Bedka and Konstantin Khlopenkov, NASA Langley Research Center; GOES-17/Himawari-8 stereo retrievals, 15 January 2022; NOAA ETOPO1 ocean-floor elevations.',
        license='NASA dataset: No constraints on data access or use; NOAA public-domain bathymetry', rights=NASA+'data/A2022015.0430.stereo_CTH.nc',
        note='A direct mesh of measured cloud-top stereo heights in a 64 km aperture near the eruption, from NASA nominal 04:30 UTC retrievals (actual line observation times about 04:36–04:37 UTC) on 15 January 2022. Only native neighboring retrieval pixels with quality rating at least 1 are connected; missing or low-confidence pixels remain holes. All 449 retained observations are also shown as point markers at their measured positions; marker size is a visibility symbol, not a droplet size. The selected source reaches 58.357 km, without height correction or vertical exaggeration. The lower separate surface is historical NOAA ETOPO1 ocean bathymetry at geographic scale, not a post-eruption seafloor survey. Cloud-top brightness uses the co-recorded Himawari-8 infrared brightness temperature, not true-color imagery. This is the observed upper surface at one time, not a reconstructed plume volume, density, eruption column or full umbrella-cloud extent. No stem, skirts, sides or particles are invented.'),
    'chicxulub': dict(item='Chicxulub Crater', value=180000., center=(-89.55,21.3), span=(205000.,205000.), shape=(121,121), gain=1., pitch=63., yaw=0.,
        source=GRAVITY, basis='https://topex.ucsd.edu/marine_grav/mar_grav.html',
        author='Scripps Institution of Oceanography / UC San Diego, Sandwell et al. (2014), global gravity V33.1; EGM2008 contribution over land.',
        license='Public Scripps gravity grid; provider data-management plan states unrestricted distribution; citation retained', rights='https://topex.ucsd.edu/pub/sandwell/SF_geodesy_proposal.pdf',
        note='A direct conversion of the Scripps 1-minute global gravity-anomaly grid V33.1 around Chicxulub. Horizontal coordinates retain geographic metre scale. The vertical coordinate plots gravity anomaly at 500 display metres per mGal, relative to 0 mGal: it is not elevation, crater depth, geological relief or seismic topography. Colors also encode the recorded anomaly, with no radial template, ring, crater rim or inferred crater surface added. The 205 km authored aperture is geographic context for the approximately 180 km catalog diameter, not a measured crater boundary. Marine gravity and the EGM2008 land field have different information content; the landward crater signature is comparatively coarse.'),
}


def pin(name, arrays, records, extra=None):
    folder=SOURCE/name;folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'data.npz',**arrays)
    meta=dict(id=name,acquired='2026-10-18',sources=records,files={'data.npz':digest(folder/'data.npz')},
              processing='Data coordinates set every geometric vertex; no normalization to the catalog value, procedural geometry, added volume, rulers or interpolated gap filling.')
    if extra:meta.update(extra)
    (folder/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta


def save_vectors(name, doc):
    folder=SOURCE/name;folder.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(doc,separators=(',',':')).encode()
    (folder/'vectors.geojson.gz').write_bytes(gzip.compress(raw,mtime=0))
    return {'vectors.geojson.gz':digest(folder/'vectors.geojson.gz')}


def prepare(name,cache):
    c=CONFIG[name];ll=coordinates(c);records=[];vectors=None;extra={}
    if name=='hunga-tonga':
        # netCDF4 is preparation-only; the offline build reads plain numpy arrays.
        import netCDF4
        url=NASA+'data/A2022015.0430.stereo_CTH.nc';path=cache/'hunga-0430.nc';get(url,path)
        with netCDF4.Dataset(path) as d:
            lon,lat=np.meshgrid(d['longitude'][:],d['latitude'][:])
            cloud=d['cloud_top_height_retrieval'][0]
            quality=d['quality_rating'][0]
            bt=d['himawari8_brightness_temperature'][0]
            west,south,east,north=bounds(c)
            iy=np.where((lat[:,0]>=south)&(lat[:,0]<=north))[0]
            ix=np.where((lon[0]>=west)&(lon[0]<=east))[0]
            sl=np.ix_(iy,ix)
            # Retain native (ascending-latitude) samples. No resampling of plume heights.
            cloud=cloud[sl];quality=quality[sl];bt=bt[sl]
            valid=~np.ma.getmaskarray(cloud)&~np.ma.getmaskarray(quality)&(quality.filled(0)>=1)&(cloud.filled(0)>0)
            native_ll=np.stack((lon[sl],lat[sl]),axis=-1)
            metadata={k:getattr(d,k) for k in ['license','platform','spatial_resolution','time_coverage_start','time_coverage_end','date_created','product_version']}
            arrays=dict(cloud_m=cloud.filled(np.nan).astype('<f4')*1000,cloud_ll=native_ll.astype('<f8'),
                        quality=quality.filled(0).astype('<f4'),cloud_valid=np.asarray(valid),brightness_k=bt.filled(np.nan).astype('<f4'))
        h,rec=sample_raster(ll,cache,name,NOAA);records.extend([dict(url=url,sha256=digest(path),metadata=metadata),rec])
        arrays.update(heights=h.astype('<f4'),lonlat=ll)
        extra['retrieval_selection']=dict(bounds_lonlat=bounds(c),minimum_quality=1,native_shape=list(cloud.shape),
            retained_pixels=int(valid.sum()),height_range_m=[float(cloud[valid].min()*1000),float(cloud[valid].max()*1000)])
    elif name=='chicxulub':
        west,south,east,north=bounds(c)
        url=GRAVITY+'?'+urlencode(dict(north=north,south=south,west=west,east=east,mag=.1))
        path=cache/'chicxulub-gravity.xyz';raw=get(url,path);xyz=np.loadtxt(io.BytesIO(raw))
        xyz[:,0]=(xyz[:,0]+180)%360-180
        xs=np.unique(xyz[:,0]);ys=np.unique(xyz[:,1])[::-1]
        if len(xs)*len(ys)!=len(xyz):raise ValueError('Incomplete gravity grid')
        order=np.lexsort((xyz[:,0],-xyz[:,1]));xyz=xyz[order].reshape(len(ys),len(xs),3)
        arrays=dict(lonlat=xyz[...,:2],anomaly_mgal=xyz[...,2].astype('<f4'),heights=(xyz[...,2]*500).astype('<f4'))
        records.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),units='mGal',grid_version='V33.1',vertical_display_metres_per_mgal=500))
    else:
        if name=='mount-thor':h,tile_records=sample_tiles(ll,c['zoom'],cache);records.extend(tile_records)
        elif name=='el-reno':h,rec=sample_raster(ll,cache,name,USGS);records.append(rec)
        else:h,tile_records=sample_tiles(ll,c['zoom'],cache);records.extend(tile_records)
        arrays=dict(heights=h.astype('<f4'),lonlat=ll)
        if name=='mount-thor':arrays['valid']=(h>0)&np.isfinite(h)
        if name=='appalachian-trail':
            url=NPS+'/query?'+urlencode(dict(where='1=1',outFields='OBJECTID,Name,Trail_Club,Source,Version',outSR=4326,
                f='geojson',returnGeometry='true',orderByFields='OBJECTID',resultRecordCount=2000))
            raw=get(url,cache/'appa-gps.json');vectors=json.loads(raw)
            if len(vectors.get('features',[]))!=30 or vectors.get('exceededTransferLimit'):raise ValueError('Incomplete NPS treadway')
            records.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),feature_count=30))
            rights_url='https://www.arcgis.com/sharing/rest/content/items/2739a451a90c4a3283be4ccd6a6a12a9?f=json'
            item=json.loads(get(rights_url,cache/'appa-rights.json'))
            extra['rights_snapshot']={k:item[k] for k in ['id','title','licenseInfo','accessInformation']}
            extra['rights_snapshot']['url']=rights_url
        if name=='el-reno':
            url=DAT+'/query?'+urlencode(dict(where="event_id='ElReno_Poly'",outFields='objectid,efscale,event_id,stormdate,length,width',
                outSR=4326,f='geojson',returnGeometry='true'))
            raw=get(url,cache/'el-reno-original.json');vectors=json.loads(raw)
            if len(vectors.get('features',[]))!=1:raise ValueError('Expected one named El Reno polygon')
            records.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),feature_count=1))
            west,south,east,north=bounds(c)
            url=NAIP+'/exportImage?'+urlencode(dict(bbox=','.join(map(str,[west,south,east,north])),bboxSR=4326,imageSR=4326,
                size='1024,1024',format='jpg',bandIds='0,1,2',adjustAspectRatio='false',f='image'))
            raw=get(url,cache/'el-reno-naip-final.jpg')
            image=Image.open(io.BytesIO(raw)).convert('RGB')
            if image.size!=(1024,1024):raise ValueError('Unexpected NAIP image dimensions')
            arrays['aerial_rgb']=np.asarray(image)
            records.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),role='USGS NAIP-only natural-color aerial mosaic; current geographic context, not 2013 damage imagery'))
            url=NAIP+'/query?'+urlencode(dict(where='Category=1',geometry=','.join(map(str,c['center'])),geometryType='esriGeometryPoint',
                inSR=4326,spatialRel='esriSpatialRelIntersects',outFields='OBJECTID,Name,Year,acquisition_date,agency,raster_name',returnGeometry='false',f='json'))
            raw=get(url,cache/'el-reno-naip-catalog.json');catalog=json.loads(raw)
            if not catalog.get('features'):raise ValueError('NAIP catalog check returned no source tile')
            extra['imagery_catalog_check']=dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),
                source_attributes=[f['attributes'] for f in catalog['features']],scope='Center tile only; other mosaic tiles may have different dates.')
    meta=pin(name,arrays,records,extra)
    if name=='chicxulub' and (SOURCE/name/'rights-and-grid.json').exists():
        meta['files']['rights-and-grid.json']=digest(SOURCE/name/'rights-and-grid.json')
    if vectors:meta['files'].update(save_vectors(name,vectors))
    (SOURCE/name/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(name,'prepared',flush=True)


def normals(points,indices):
    """Area-weighted normals computed only from retained data triangles."""
    flat=points.reshape(-1,3);tri=indices.reshape(-1,3);n=np.zeros_like(flat)
    face=np.cross(flat[tri[:,1]]-flat[tri[:,0]],flat[tri[:,2]]-flat[tri[:,0]])
    for k in range(3):np.add.at(n,tri[:,k],face)
    length=np.linalg.norm(n,axis=1);n[length==0]=[0,1,0];length[length==0]=1
    return n/length[:,None]


def surface(glb,name,p,texture,valid=None):
    rows,cols=p.shape[:2];idx=grid_indices(rows,cols).reshape(-1,3)
    if valid is not None:idx=idx[valid.ravel()[idx].all(axis=1)]
    # Remove unused/missing data vertices entirely; no hidden origin vertices in bounds.
    used,reverse=np.unique(idx.ravel(),return_inverse=True);points=p.reshape(-1,3)
    u,v=np.meshgrid(np.linspace(0,1,cols),np.linspace(0,1,rows))
    out=io.BytesIO();texture.save(out,format='PNG')
    mat=glb.material(name,texture=glb.texture(out.getvalue(),'image/png'),rough=1,double_sided=True)
    n=normals(p,idx.ravel())
    glb.mesh_node(name,[glb.primitive(points[used],reverse,mat,normals=n[used],
        uvs=np.stack((u,v),axis=-1).reshape(-1,2)[used])])


def palette(h,kind):
    """Authored continuous scalar palettes, never imagery or invented features."""
    if kind=='chicxulub':
        stops=[(-20,(.05,.11,.30)),(0,(.12,.40,.61)),(15,(.28,.70,.68)),(30,(.94,.78,.37)),(55,(.85,.23,.13))]
        t=h/500
    elif kind=='hunga-tonga':
        stops=[(-6000,(.025,.09,.18)),(-2500,(.045,.23,.34)),(-500,(.09,.44,.51)),(0,(.36,.59,.48)),(2000,(.72,.76,.64))];t=h
    elif kind=='mount-thor':
        stops=[(150,(.19,.28,.27)),(600,(.39,.43,.41)),(1100,(.63,.60,.50)),(1500,(.78,.77,.70)),(1800,(.95,.96,.96))];t=h
    else:
        stops=[(-50,(.035,.14,.24)),(0,(.12,.30,.29)),(200,(.24,.43,.33)),(700,(.48,.55,.37)),(1500,(.73,.67,.47)),(3000,(.90,.87,.76))];t=h
    return np.stack([np.interp(t,[a for a,b in stops],[b[k] for a,b in stops]) for k in range(3)],axis=-1)


def texture(h,p,name,folder,ll):
    color=palette(h,name)
    # Fine shading uses only the sampled height field. No fractal/noise detail.
    du,dv=np.gradient(p,axis=1),np.gradient(p,axis=0)
    n=np.cross(dv,du);n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-20)
    shade=np.clip(n@np.array([-.5,.75,.43]),0,1)
    color*=.65+.35*shade[...,None]
    im=Image.fromarray(np.uint8(np.clip(color,0,1)*255)).resize((1024,1024),Image.Resampling.BICUBIC)
    if name=='el-reno':
        with np.load(folder/'data.npz') as a:im=Image.fromarray(a['aerial_rgb'])
    vf=folder/'vectors.geojson.gz'
    if vf.exists():
        doc=json.loads(gzip.decompress(vf.read_bytes()));draw=ImageDraw.Draw(im)
        window=(float(ll[...,0].min()),float(ll[...,1].min()),float(ll[...,0].max()),float(ll[...,1].max()))
        if name=='el-reno':
            mask=polygon_mask(doc['features'],window,im.size)
            # Survey coverage is an opaque map overlay, not added geometric thickness.
            im.paste((248,114,38),(0,0),mask.point(lambda p:round(p*.34)))
            west,south,east,north=window
            for f in doc['features']:
                for ring in f['geometry']['coordinates']:
                    draw.line([((q[0]-west)/(east-west)*1023,(north-q[1])/(north-south)*1023) for q in ring],fill=(255,178,67),width=3)
        else:
            west,south,east,north=window
            for line in clip_lines(lines_from_geojson(doc),window):
                xy=[((q[0]-west)/(east-west)*1023,(north-q[1])/(north-south)*1023) for q in line]
                draw.line(xy,fill=(250,198,73),width=4)
    return im


def build(name):
    c=CONFIG[name];folder=SOURCE/name;meta=json.loads((folder/'provenance.json').read_text())
    for f,sha in meta['files'].items():
        if digest(folder/f)!=sha:raise ValueError(f'Pinned source changed: {name}/{f}')
    with np.load(folder/'data.npz') as data:a={k:data[k] for k in data.files}
    h=a['heights'].astype(float);ll=a['lonlat'];p=frame(c,ll,h*c['gain'])
    glb=GLB('Universe Scales: direct public-data surface conversion, terrain3d2')
    tex=texture(h,p,name,folder,ll)
    if name=='appalachian-trail':
        # Retain actual sampled vertices; the texture keeps full source shading.
        surface(glb,'Recorded terrain elevations',p[::2,::2],tex)
    else:
        surface(glb,'Recorded gravity anomaly' if name=='chicxulub' else 'Recorded terrain elevations',p,tex,a.get('valid'))
    if name=='hunga-tonga':
        valid=a['cloud_valid'];height=np.where(valid,a['cloud_m'],0)
        cp=frame(c,a['cloud_ll'],height)
        bt=a['brightness_k'];grey=np.clip((290-np.nan_to_num(bt,nan=290))/100,.15,1)
        rgb=np.stack((grey*.95,grey*.97,grey),axis=-1)
        # Native latitude is ascending here; texture rows and UVs match those native rows.
        im=Image.fromarray(np.uint8(rgb*255)).resize((512,512),Image.Resampling.BILINEAR)
        surface(glb,'Retrieved plume top, Himawari-8 infrared brightness',cp,im,valid)
        # Every marker is an actual retained stereo retrieval. Points expose sparse
        # observations at the holes without inventing connecting cloud geometry.
        mat=glb.material('Measured stereo sample centers',(0.90,0.94,1.,1.),rough=1)
        primitive={'attributes':{'POSITION':glb._accessor(cp[valid].astype('<f4'),5126,'VEC3',34962,True)},'mode':0,'material':mat}
        glb.mesh_node('Stereo retrieval sample centers',[primitive])
        glb.doc['nodes'][-1]['extras']={'pointSize':{'max':4,'perPixel':.012}}
        peak=np.unravel_index(np.argmax(np.where(valid,a['cloud_m'],-np.inf)),valid.shape)
        glb.label_node('Highest retained retrieval',cp[peak],'58.36 km')
    model_id='terrain3d2-'+name;path=ROOT/f'content/visualizations/models/{model_id}.glb';glb.write(path)
    note=c['note']+' No crop walls, underside, stand, independent ruler or schematic geometry is included. '+c['author']
    entry=dict(id=model_id,source=c['source'],basis_url=c['basis'],basis_label='Source data and geographic context',author=c['author'],
        license=c['license'],license_url=c['rights'],license_files=[f'sources/{model_id}.md'],matches={'length':[c['item']]},
        geometry='mesh',representation='scientific_data_surface' if name in ['chicxulub','hunga-tonga'] else 'dem_terrain',
        volume_semantics='not_applicable',closed_volume_checked=False,
        presentation=dict(reference_size=c['value'],pitch=c.get('pitch',0),yaw=c.get('yaw',0),roll=c.get('roll',0),layout_width_factor=1.3),
        processing=dict(script='scripts/build_terrain3d2_models.py',units='metres',vertical_gain=c['gain'],
            provenance=str((folder/'provenance.json').relative_to(ROOT)),source_files=meta['files']),note=note,
        src=str(path.relative_to(ROOT)),**inspect_glb(path.read_bytes()))
    HANDOFF.mkdir(parents=True,exist_ok=True);(HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry,indent=2)+'\n')
    refs=[c['source'],c['basis'],c['rights']]+[r['url'] for r in meta['sources']]
    if name=='mount-thor':refs.extend([PGC_RIGHTS,'https://www.pgc.umn.edu/guides/user-services/acknowledgement-policy/',
        'https://github.com/tilezen/joerd/blob/master/docs/data-sources.md','https://open.canada.ca/en/open-government-licence-canada'])
    if name=='appalachian-trail':refs.extend(['https://registry.opendata.aws/terrain-tiles/','https://github.com/tilezen/joerd/blob/master/docs/attribution.md',meta['rights_snapshot']['url']])
    if name=='chicxulub':refs.append('https://topex.ucsd.edu/pub/global_grav_1min/README_V33.txt')
    if name=='el-reno':refs.append(NAIP)
    text=f'# {c["item"]}: direct public data conversion\n\n{note}\n\n'
    text+='## Source and processing\n\n'
    text+=f'Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/{name}/provenance.json`. '
    text+='`data.npz` retains the numerical source subset in native metric values and longitude/latitude. '
    text+='Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. '
    text+='All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. '
    text+='Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. '
    text+='Local scenes use the existing terrain builder\'s east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. '
    text+='These open surfaces make no enclosed-volume claim.\n\n'
    text+=f'Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py {name}`. '
    text+='Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). '
    text+=f'Register: `python3 scripts/register_model.py handoff/terrain3d2/{model_id}.entry.json content/visualizations/models/{model_id}.glb`.\n\n'
    text+='## Rights and citations\n\n'+ '\n'.join('- '+u for u in dict.fromkeys(refs))+'\n\n'
    text+='Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. '
    text+='CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.\n'
    (SOURCE.parent/f'{model_id}.md').write_text(text)
    print(model_id,entry['bytes'],entry['triangle_count'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('names',nargs='*',choices=list(CONFIG))
    parser.add_argument('--prepare',action='store_true');parser.add_argument('--cache',type=Path,default=Path('/tmp/terrain3d2'))
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    for name in args.names or list(CONFIG):
        if args.prepare:prepare(name,args.cache)
        build(name)
