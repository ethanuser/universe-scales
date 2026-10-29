#!/usr/bin/env node
// Reproject existing licensed globe textures through their actual UVs. No new 3D asset.
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { loadPlaywright, executablePath } = require('./preview_glb.cjs');
const { sphereBounds, sphereDimensions } = require('../js/experiences/area-maps.js');
const ROOT = path.resolve(__dirname, '..');
const ids = ['nasa-earth', 'nasa-moon', 'nasa-jupiter', 'nasa-sun', 'nasa-mercury', 'nasa-venus',
    'nasa-mars-length', 'nasa-saturn-globe-length', 'nasa-uranus', 'nasa-neptune', 'nasa-pluto'];
const names = ['Earth', 'Moon', 'Jupiter', 'Sun', 'Mercury', 'Venus', 'Mars', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, 'content/visualizations/models.json'))).models;
const output = path.join(ROOT, 'content/visualizations/area-maps');
const sha = b => createHash('sha256').update(b).digest('hex');
const width = 1024, height = Math.round(width * sphereBounds[1] / sphereBounds[0]);
const pageHTML = `<!doctype html><body style="margin:0"><script type="importmap">{"imports":{"three":"/js/vendor/three/three.module.min.js"}}</script><script type="module">
import * as THREE from 'three';
import { GLTFLoader } from '/js/vendor/three/addons/loaders/GLTFLoader.js';
window.renderMap = async (src, longitude = 0) => {
 const gltf = await new GLTFLoader().loadAsync('/'+src);
 const scene = new THREE.Scene(); scene.add(gltf.scene);
 gltf.scene.updateMatrixWorld(true);
 const box = new THREE.Box3().setFromObject(gltf.scene), center = box.getCenter(new THREE.Vector3());
 const extent = box.getSize(new THREE.Vector3());
 // Convert the source globe's principal-axis ellipsoid into spherical latitude coordinates.
 // This does not alter the delivered GLB. The displayed map uses the catalog spherical-area convention.
 const wrapper = new THREE.Group(); scene.remove(gltf.scene); scene.add(wrapper); wrapper.add(gltf.scene);
 gltf.scene.position.sub(center); wrapper.scale.set(2/extent.x, 2/extent.y, 2/extent.z);
 gltf.scene.traverse(node => {
  if(!node.isMesh) return;
  const convert = m => new THREE.MeshBasicMaterial({map:m.map || m.emissiveMap,
   color:(m.map ? m.color : m.emissiveMap ? m.emissive : m.color),side:THREE.BackSide,toneMapped:false});
  node.material = Array.isArray(node.material) ? node.material.map(convert) : convert(node.material);
 });
 const renderer = new THREE.WebGLRenderer({alpha:true,antialias:false,preserveDrawingBuffer:true});
 renderer.setSize(${width},${height}); renderer.setPixelRatio(1);
 document.body.replaceChildren(renderer.domElement);
 const cube = new THREE.WebGLCubeRenderTarget(512, {type:THREE.UnsignedByteType,generateMipmaps:false});
 new THREE.CubeCamera(.001,10,cube).update(renderer,scene);
 const material = new THREE.ShaderMaterial({transparent:true, uniforms:{map:{value:cube.texture},longitude:{value:longitude}},
 vertexShader:'varying vec2 p;void main(){p=uv;gl_Position=vec4(position.xy,0.,1.);}',
 fragmentShader:\`precision highp float;uniform samplerCube map;uniform float longitude;varying vec2 p;
 void main(){vec2 q=(p*2.-1.)*vec2(${sphereBounds.join(',')});float t=q.y;
 for(int i=0;i<12;i++){float t2=t*t,t6=t2*t2*t2;float d=1.340264-3.*.081106*t2+t6*(7.*.000893+9.*.003796*t2);
 t-=(t*(1.340264-.081106*t2+t6*(.000893+.003796*t2))-q.y)/d;}
 float t2=t*t,t6=t2*t2*t2;float lon=.8660254037844386*q.x*(1.340264-3.*.081106*t2+t6*(7.*.000893+9.*.003796*t2))/cos(t);
 float s=sin(t)/.8660254037844386;if(abs(lon)>3.141592653589793||abs(s)>1.)discard;
 float lat=asin(s);lon+=longitude;vec3 dir=vec3(cos(lat)*sin(lon),sin(lat),cos(lat)*cos(lon));
 gl_FragColor=textureCube(map,dir);gl_FragColor.a=1.;
 #include <colorspace_fragment>
 }\`});
 const plane = new THREE.Mesh(new THREE.PlaneGeometry(2,2),material), flat = new THREE.Scene();flat.add(plane);
 renderer.setClearColor(0,0);renderer.render(flat,new THREE.Camera());
 const data=renderer.domElement.toDataURL('image/png');
 const ctx=document.createElement('canvas').getContext('2d');ctx.canvas.width=${width};ctx.canvas.height=${height};ctx.drawImage(renderer.domElement,0,0);
 const pixels=ctx.getImageData(0,0,${width},${height}).data;let opaque=0;
 for(let i=3;i<pixels.length;i+=4)if(pixels[i])opaque++;
 cube.dispose();renderer.dispose();return {data,opaque};
};</script>`;
(async () => {
 fs.mkdirSync(output,{recursive:true});
 const browser=await loadPlaywright().chromium.launch({executablePath:executablePath(),args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
  const page=await browser.newPage();
  await page.route('http://area-map.local/**',route=>{
   const pathname=new URL(route.request().url()).pathname;
   if(pathname==='/')return route.fulfill({contentType:'text/html',body:pageHTML});
   const file=path.resolve(ROOT,'.'+pathname);
   if(!file.startsWith(ROOT+path.sep)||!fs.existsSync(file))return route.fulfill({status:404});
   return route.fulfill({contentType:file.endsWith('.glb')?'model/gltf-binary':'text/javascript',body:fs.readFileSync(file)});
  });
  await page.goto('http://area-map.local/');await page.waitForFunction(()=>window.renderMap);
  const entries=[];
  for(let i=0;i<ids.length;i++){
   const model=registry.find(m=>m.id===ids[i]);if(!model)throw Error('Missing '+ids[i]);
   if(sha(fs.readFileSync(path.join(ROOT,model.src)))!==model.sha256)throw Error('Source hash mismatch '+ids[i]);
   const rendered=await page.evaluate(([src,longitude])=>window.renderMap(src,longitude),[model.src,names[i]==='Earth'?Math.PI:0]);
   const bytes=Buffer.from(rendered.data.split(',')[1],'base64'),slug=names[i].toLowerCase();
   fs.writeFileSync(path.join(output,slug+'.png'),bytes);
   const areaRatio=rendered.opaque/(width*height)*sphereDimensions[0]*sphereDimensions[1];
   if(Math.abs(areaRatio-1)>.005)throw Error('Projection coverage mismatch '+areaRatio);
   const atmosphere=['Jupiter','Saturn','Uranus','Neptune','Venus'].includes(names[i]);
   entries.push({id:'equal-earth-'+slug,name:names[i]+' surface area',src:'content/visualizations/area-maps/'+slug+'.png',
    projection:'Equal Earth',source:model.source,author:model.author,license:model.license,license_url:model.license_url,
    note:'The whole '+names[i]+' globe is unfolded with the Equal Earth projection. Equal-sized map patches represent equal surface areas under the listed spherical convention; the full colored footprint equals the listed area, not its bounding rectangle. '+
     (atmosphere?'The source shows atmospheric appearance, not a solid surface or current weather. ':names[i]==='Sun'?'The solar texture illustrates the photosphere, not a solid surface or a current observation. ':'')+
     (names[i]==='Pluto'?'New Horizons coverage has uneven resolution; parts of the globe are only weakly resolved. ':'')+
     'Existing NASA source UVs and imagery are retained without invented terrain. North follows the source globe; longitude is illustrative, not a navigation grid.',
    source_model_id:model.id,source_glb_sha256:model.sha256,sha256:sha(bytes),bytes:bytes.length,
    width:sphereDimensions[0],height:sphereDimensions[1],raster:[width,height],raster_area_ratio:areaRatio,
    additional_sources:[{label:'Projection method',url:'https://doi.org/10.1080/13658816.2018.1504949'}]});
   console.log(names[i],bytes.length,'bytes; area ratio',areaRatio.toFixed(6));
  }
  fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify({schema_version:1,entries},null,2)+'\n');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
