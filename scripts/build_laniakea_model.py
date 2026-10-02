#!/usr/bin/env python3
"""Stage a reference-only flat panel of the published CF4 Laniakea visualization."""

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

from fetch_model_assets import inspect_glb, pack_glb
from geo_glb_common import GLB


DIAMETER_MPC = 160.0
DIAMETER_M = 4.937084130386187e24
SOURCE = "https://doi.org/10.1051/0004-6361/202346802"
BASIS = "https://www.nature.com/articles/nature13674"
FIGURE_URL = "https://arxiv.org/html/2305.02339v2/figures/visu_laniakea_names.jpeg"
FIGURE_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
DEFAULT_FIGURE = Path("/private/tmp/length-laniakea/aa2023-fig1.jpeg")
DEFAULT_OUTPUT = Path("/private/tmp/length-laniakea/laniakea-cf4-reference-preview.glb")
DEFAULT_METADATA = Path("/private/tmp/length-laniakea/laniakea-reference-preview.json")


def panel_texture(figure_bytes):
    """Re-encode the full authored projection without cropping or graphic edits."""
    with Image.open(io.BytesIO(figure_bytes)) as source:
        if source.format != "JPEG" or source.width != source.height:
            raise ValueError("Expected the square JPEG of the published Figure 1")
        source_dimensions = source.size
        image = source.convert("RGB")
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        encoded = io.BytesIO()
        image.save(encoded, format="JPEG", quality=88, optimize=True)
    return encoded.getvalue(), source_dimensions, image.size


def build_model(figure_bytes):
    glb = GLB("Universe Scales published CF4 Laniakea figure projection")
    texture_bytes, _, _ = panel_texture(figure_bytes)
    texture = glb.texture(texture_bytes, "image/jpeg")
    material = glb.material("Dupuy and Courtois 2023 Figure 1 (CC BY 4.0)", texture=texture)
    # This flat card preserves the source projection; its width is not a spatial axis.
    positions = [[-0.5, -0.5, 0], [0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0]]
    uvs = [[0, 1], [1, 1], [1, 0], [0, 0]]
    glb.mesh_node("Unmodified published projection, not reconstructed geometry", [
        glb.primitive(positions, [0, 1, 2, 0, 2, 3], material,
                      normals=[[0, 0, 1]] * 4, uvs=uvs)
    ])
    return pack_glb(glb.doc, bytes(glb.bin))


def build_metadata(data, staged_path, source_dimensions, texture_dimensions, source_sha256):
    """Create provenance metadata for a non-production visual reference."""
    stats = inspect_glb(data)
    return {
        "id": "laniakea-cf4-reference-preview",
        "representation": "reference_panel",
        "production_registry_eligible": False,
        "intended_use": "Source-faithful visual reference only; not a calibrated Length model or coverage asset",
        "source": SOURCE,
        "basis_url": BASIS,
        "basis_label": "2014 Laniakea definition and approximate diameter",
        "link_label": "A&A 2023 CF4 watershed paper",
        "author": "A. Dupuy and H. M. Courtois; source figure reproduced and re-encoded by Universe Scales",
        "license": "CC-BY-4.0; published Figure 1 reproduced as a downsampled, re-encoded texture",
        "license_url": FIGURE_LICENSE,
        "license_files": ["licenses/CC-BY-4.0.txt", "sources/laniakea-model.md"],
        "note": "Exact published projection from the ungrouped CF4 velocity-field reconstruction. The flat card is not 3D basin geometry, is not physically calibrated, and must not be used as Length-model coverage. No contour or volume was traced or invented. The grouped CF4 reconstruction merges Laniakea into Shapley. Laniakea is a velocity-defined basin, not a gravitationally bound system.",
        "processing": {
            "source_figure": "Figure 1: visu_laniakea_names.jpeg",
            "source_figure_url": FIGURE_URL,
            "source_figure_license": "CC BY 4.0",
            "staged_source_image": str(staged_path),
            "source_figure_sha256": source_sha256,
            "source_image_dimensions_px": list(source_dimensions),
            "texture_dimensions_px": list(texture_dimensions),
            "image_operations": ["Full-frame downsample to at most 1024x1024", "JPEG re-encode at quality 88; no crop or content edits"],
            "projection_semantics": "Exact 2D projection of the paper's 3D rendering; flat poster plane only",
            "published_reconstruction": "Ungrouped CF4; grouped CF4 does not isolate Laniakea",
            "model_plane_dimensions": "Unitless display card; its width and height do not represent spatial distances",
            "display_calibration": "Unitless panel framed to the Length item; no spatial calibration is implied",
            "published_diameter_context_m": DIAMETER_M,
            "operations": ["Embed credited published projection on one flat quad; do not reconstruct its 3D scene"],
        },
        "volume_semantics": "not_a_volume_measurement",
        "closed_volume_checked": False,
        "staged_asset_path": str(DEFAULT_OUTPUT),
        **stats,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    if not args.figure.is_file():
        raise FileNotFoundError(f"Download the CC BY source figure first: {FIGURE_URL}")
    output = build_model(args.figure.read_bytes())
    stats = inspect_glb(output)
    if len(output) > 1_500_000 or stats["triangle_count"] > 60_000:
        raise ValueError("Generated model exceeds the configured asset budget")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    figure_bytes = args.figure.read_bytes()
    with Image.open(io.BytesIO(figure_bytes)) as source_figure:
        source_dimensions = source_figure.size
    _, _, texture_dimensions = panel_texture(figure_bytes)
    metadata = build_metadata(
        output, str(args.figure), source_dimensions, texture_dimensions,
        hashlib.sha256(figure_bytes).hexdigest(),
    )
    metadata["staged_asset_path"] = str(args.output)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {args.output} ({len(output):,} bytes, {stats['triangle_count']:,} triangles)")
    print(f"Wrote reference-preview metadata {args.metadata} (not a registry entry)")


if __name__ == "__main__":
    main()
