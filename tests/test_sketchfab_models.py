import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_model_assets import inspect_glb, read_glb
import sketchfab_models
from sketchfab_models import gltf_to_glb


def sample_archive(image_path="textures/preview.png", extensions=None):
    vertices = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    indices = struct.pack("<3H", 0, 1, 2)
    image = io.BytesIO()
    Image.new("RGB", (128, 96), "#3481ad").save(image, format="PNG")
    scene = {
        "asset": {"version": "2.0"},
        "buffers": [{"uri": "scene.bin", "byteLength": len(vertices + indices)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(vertices)},
            {"buffer": 0, "byteOffset": len(vertices), "byteLength": len(indices)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0, 0, 0], "max": [1, 1, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "images": [{"uri": image_path}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "extensionsRequired": extensions or [],
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("scene.gltf", json.dumps(scene))
        bundle.writestr("scene.bin", vertices + indices)
        bundle.writestr("textures/preview.png", image.getvalue())
    return archive.getvalue()


class SketchfabImportTests(unittest.TestCase):
    def test_review_pins_candidate_and_filters_unrelated_search_results(self):
        uid = "a" * 32
        candidate = {
            "uid": uid, "name": "Standing Cat", "user": {"username": "artist"},
            "license": {"label": "CC Attribution"}, "isDownloadable": True,
            "archives": {"gltf": {"size": 1_200_000}}, "faceCount": 10000,
            "thumbnails": {"images": [{"width": 720, "url": "https://media.sketchfab.com/cat.jpg"}]},
        }
        unrelated = {**candidate, "uid": "b" * 32, "name": "Diamond", "archives": {"gltf": {"size": 1000}}}
        detail = {**candidate, "license": {"slug": "by"}, "archives": None}
        with tempfile.TemporaryDirectory() as root_dir, \
             patch.object(sketchfab_models, "read_manifest", return_value=[{
                 "id": "sketchfab-cat", "name": "Cat Length", "uid": uid}]), \
             patch.object(sketchfab_models, "request_json", return_value={
                 "results": [unrelated, candidate]}), \
             patch.object(sketchfab_models, "model_detail", return_value=detail):
            output = Path(root_dir) / "review.html"
            sketchfab_models.review("sketchfab-cat", ["cat"], [], 10, 2_000_000, output)
            page = output.read_text()
        self.assertIn("Standing Cat", page)
        self.assertNotIn("Diamond", page)
        self.assertIn("select --id sketchfab-cat --uid", page)
        self.assertIn("SSL_CERT_FILE=/etc/ssl/cert.pem", page)
        self.assertIn("1.20 MB", page)

    def test_selection_requires_downloadable_cc_license_and_keeps_replacement(self):
        with tempfile.TemporaryDirectory() as root_dir:
            manifest = Path(root_dir) / "sketchfab-length.json"
            manifest.write_text(json.dumps({"schema_version": 1, "models": [{
                "id": "sketchfab-cat", "name": "Cat Length", "uid": "a" * 32,
                "author": "old", "license": "by", "replaces": "cat", "enabled": False,
                "deferred_reason": "Review pending"}]}))
            detail = {"isDownloadable": True, "user": {"username": "new-artist"},
                      "name": "Cat", "license": {"slug": "by"}}
            with patch.object(sketchfab_models, "MANIFEST", manifest), \
                 patch.object(sketchfab_models, "model_detail", return_value=detail):
                sketchfab_models.select_model("sketchfab-cat", "b" * 32)
            selected = json.loads(manifest.read_text())["models"][0]
            self.assertEqual(selected["uid"], "b" * 32)
            self.assertEqual(selected["author"], "new-artist")
            self.assertEqual(selected["replaces"], "cat")
            self.assertTrue(selected["enabled"])
            self.assertNotIn("deferred_reason", selected)

    def test_import_embeds_and_resizes_without_external_resources(self):
        result = gltf_to_glb(sample_archive(), 64)
        stats = inspect_glb(result)
        document, binary = read_glb(result)
        image = document["images"][0]
        view = document["bufferViews"][image["bufferView"]]
        with Image.open(io.BytesIO(binary[view["byteOffset"]:view["byteOffset"] + view["byteLength"]])) as saved:
            self.assertLessEqual(max(saved.size), 64)
        self.assertEqual(stats["triangle_count"], 1)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(image["mimeType"], "image/jpeg")

    def test_rejects_archive_path_traversal(self):
        with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
            gltf_to_glb(sample_archive("../../secret.png"), 64)

    def test_rejects_models_needing_missing_decoder(self):
        with self.assertRaisesRegex(ValueError, "unsupported decoder"):
            gltf_to_glb(sample_archive(extensions=["KHR_draco_mesh_compression"]), 64)

    def test_verifier_counts_nonindexed_triangles(self):
        source = sample_archive()
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            scene = json.loads(archive.read("scene.gltf"))
            scene["meshes"][0]["primitives"][0].pop("indices")
            repacked = io.BytesIO()
            with zipfile.ZipFile(repacked, "w") as bundle:
                for name in archive.namelist():
                    bundle.writestr(name, json.dumps(scene) if name == "scene.gltf" else archive.read(name))
        self.assertEqual(inspect_glb(gltf_to_glb(repacked.getvalue(), 64))["triangle_count"], 1)

    def test_import_discards_source_animations_for_static_explorer(self):
        source = sample_archive()
        with zipfile.ZipFile(io.BytesIO(source)) as archive:
            scene = json.loads(archive.read("scene.gltf"))
            scene["animations"] = [{"channels": [], "samplers": []}]
            repacked = io.BytesIO()
            with zipfile.ZipFile(repacked, "w") as bundle:
                for name in archive.namelist():
                    bundle.writestr(name, json.dumps(scene) if name == "scene.gltf" else archive.read(name))
        output = gltf_to_glb(repacked.getvalue(), 64)
        self.assertNotIn("animations", read_glb(output)[0])
        self.assertEqual(inspect_glb(output)["animations"], 0)

    def test_import_writes_model_and_attribution_without_token_or_url(self):
        entry = {"id": "sketchfab-water-test", "name": "Water Molecule", "uid": "a" * 32}
        detail = {
            "name": "Water Molecule", "user": {"username": "example-artist"},
            "license": {"slug": "by", "url": "https://creativecommons.org/licenses/by/4.0/"},
            "viewerUrl": "https://sketchfab.com/models/" + entry["uid"],
        }
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as secret_dir:
            root = Path(root_dir)
            registry = root / "content/visualizations/models.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"schema_version": 1, "models": [], "coverage_gaps": []}))
            token_file = Path(secret_dir) / "token"
            token_file.write_text("test-token")
            with patch.object(sketchfab_models, "ROOT", root), \
                 patch.object(sketchfab_models, "REGISTRY", registry), \
                 patch.object(sketchfab_models, "checked_detail", return_value=detail), \
                 patch.object(sketchfab_models, "request_json", return_value={
                     "gltf": {"url": "https://sketchfab-downloads.s3.amazonaws.com/test.zip", "size": 1000}}), \
                 patch.object(sketchfab_models, "request_bytes", return_value=sample_archive()):
                sketchfab_models.import_models([entry], token_file, 1_000_000, 2_000_000, 2_000_000, 64)
            saved = json.loads(registry.read_text())["models"][0]
            self.assertEqual(saved["author"], "example-artist on Sketchfab")
            self.assertEqual(saved["license"], "CC-BY-4.0")
            self.assertEqual(saved["matches"]["length"], ["Water Molecule"])
            self.assertEqual(saved["triangle_count"], 1)
            self.assertTrue((root / saved["src"]).is_file())
            self.assertNotIn("test-token", registry.read_text())

    def test_approved_import_replaces_only_named_old_match(self):
        entry = {"id": "sketchfab-cat-test", "name": "Cat Length",
                 "uid": "c" * 32, "replaces": "cat"}
        detail = {"name": "Cat", "user": {"username": "artist"},
                  "license": {"slug": "by", "url": "https://creativecommons.org/licenses/by/4.0/"},
                  "viewerUrl": "https://sketchfab.com/models/" + entry["uid"]}
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as secret_dir:
            root = Path(root_dir)
            registry = root / "content/visualizations/models.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"models": [
                {"id": "cat", "matches": {"length": ["Cat Length"]}},
                {"id": "earth", "matches": {"length": ["Earth Diameter"]}}]}))
            token = Path(secret_dir) / "token"
            token.write_text("test-token")
            with patch.object(sketchfab_models, "ROOT", root), \
                 patch.object(sketchfab_models, "REGISTRY", registry), \
                 patch.object(sketchfab_models, "checked_detail", return_value=detail), \
                 patch.object(sketchfab_models, "request_json", return_value={
                     "gltf": {"url": "https://sketchfab-downloads.s3.amazonaws.com/test.zip", "size": 1000}}), \
                 patch.object(sketchfab_models, "request_bytes", return_value=sample_archive()):
                sketchfab_models.import_models([entry], token, 1_000_000, 2_000_000, 2_000_000, 64)
            saved = json.loads(registry.read_text())["models"]
            self.assertEqual({model["id"] for model in saved}, {"earth", "sketchfab-cat-test"})
            self.assertEqual(saved[-1]["matches"]["length"], ["Cat Length"])

    def test_staged_volume_import_verifies_identity_and_glb_checksum(self):
        uid = "d" * 32
        entry = {"id": "sketchfab-bus-test", "name": "City bus envelope volume",
                 "uid": uid, "author": "artist", "license": "by"}
        output = gltf_to_glb(sample_archive(), 64)
        import hashlib
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as stage_dir:
            root, stage = Path(root_dir), Path(stage_dir)
            registry = root / "content/visualizations/models.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"models": [], "coverage_gaps": []}))
            metadata = {"uid": uid, "name": "A bus", "author": "artist", "license": "by",
                        "source": f"https://sketchfab.com/models/{uid}", "source_bytes": 500,
                        "source_sha256": "f" * 64, "texture_size": 64,
                        "sha256": hashlib.sha256(output).hexdigest()}
            (stage / f"{uid}.json").write_text(json.dumps(metadata))
            (stage / f"{uid}.glb").write_bytes(output)
            with patch.object(sketchfab_models, "ROOT", root), \
                 patch.object(sketchfab_models, "REGISTRY", registry), \
                 patch.object(sketchfab_models, "request_json", side_effect=AssertionError("network request")):
                sketchfab_models.import_models([entry], None, 1000, 1_000_000, 1_000_000, 64,
                                               staged_dir=stage, dimension="volume")
                saved = json.loads(registry.read_text())["models"][0]
                self.assertEqual(saved["matches"], {"volume": ["City bus envelope volume"]})
                self.assertEqual(saved["source_sha256"], metadata["source_sha256"])
                registry.write_text(json.dumps({"models": [], "coverage_gaps": []}))
                (stage / f"{uid}.glb").write_bytes(output + b"tampered")
                sketchfab_models.import_models([entry], None, 1000, 1_000_000, 1_000_000, 64,
                                               staged_dir=stage, dimension="volume")
                self.assertEqual(json.loads(registry.read_text())["models"], [])

    def test_stage_rejects_token_file_inside_repository(self):
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as stage_dir:
            root = Path(root_dir)
            token = root / "token"
            token.write_text("secret")
            with patch.object(sketchfab_models, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "outside the repository"):
                    sketchfab_models.stage_models([], token, False, Path(stage_dir), 1000, 1000, 128)


if __name__ == "__main__":
    unittest.main()
