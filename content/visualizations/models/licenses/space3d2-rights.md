# Space3d2 source rights (checked 16 October 2026)

- Ryugu: [ISAS Data Policy, section 6](https://www.isas.jaxa.jp/en/researchers/data-policy/)
  permits commercial and noncommercial copying, forwarding and modification with
  ISAS/JAXA attribution, added third-party credits where requested, and disclosure
  of modifications. These are Government of Japan Standard Terms of Use 2.0,
  declared compatible with CC BY 4.0. This is the actual source license basis,
  rather than a claim that the Science article or every JAXA image is CC BY.
  [Watanabe archive README](https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/README.html)
  identifies the public SfM models and requests acknowledgment of contributors.
  Credit ISAS/JAXA, Watanabe et al. (2019), Hayabusa2 shape-model team. We retain
  source coordinates, rotate to Y-up, calculate normals and package as glTF.
- Hyperion: [NASA Open Data Portal, Saturn Small Moon Shape Models V1.0](https://data.nasa.gov/dataset/saturn-small-moon-shape-models-v1-0)
  explicitly declares the dataset **us-pd**. The asset is the Cassini/Thomas
  `hyperion_30k_plt.tab` shape converted to OBJ by the PDS Small Bodies Node.
  Credit Peter C. Thomas, NASA/JPL/Cassini ISS and NASA PDS SBN.
- Dimorphos: [NASA NAIF DART archive](https://naif.jpl.nasa.gov/pub/naif/pds/pds4/dart/dart_spice/)
  distributes DART's final pre-impact v004 global shape as a public NASA mission
  scientific data product; credit NASA/Johns Hopkins APL DART team and PDS/NAIF.
  [NAIF rules](https://naif.jpl.nasa.gov/naif/rules.html) provide unrestricted use
  of SPICE data and request acknowledgment. No model is taken from an ESA artwork.
- Great Red Spot: [NASA Photojournal PIA23606](https://science.nasa.gov/photojournal/the-great-red-spot/)
  explicitly credits **Image data: NASA/JPL-Caltech/SwRI/MSSS, Image processing
  by Kevin M. Gill, © CC BY**. The page does not specify the license version; the
  registry consequently does not invent one. We crop and drape the image on an
  idealized surface, with source credit retained in the entry and source note.
- Hexagon: [NASA PIA17652](https://science.nasa.gov/resource/saturns-streaming-hexagon-storm/)
  credits NASA/JPL-Caltech/SSI/Hampton University. NASA media usage rules apply;
  retain the complete credit, and do not describe the false-color composite as
  natural color. The delivered model is an adapted cloud-top image, not a new
  measured 3D storm reconstruction.
- Saturn: the existing NASA VTAD model and original NASA media licenses are
  retained. JPL orbital elements are public NASA scientific facts; all diagrams
  add explicit NASA/JPL Solar System Dynamics credit.

The new untextured stellar/Eris geometry and Roche math implementation are original
CC0 contributions. Papers are cited for facts; their figures are not redistributed.
