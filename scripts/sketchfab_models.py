#!/usr/bin/env python3
"""Find and import small, credited Sketchfab models for the Length explorer.

Search needs no credentials. Import needs an API token in a file outside this
repository; the token and short-lived download URLs are never written to disk.
"""

import argparse
import base64
import html
import io
import json
import posixpath
import re
import shlex
import struct
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlencode, urlsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "content/visualizations/models"
REGISTRY = ROOT / "content/visualizations/models.json"
MANIFEST = ASSETS / "sketchfab-length.json"
API = "https://api.sketchfab.com/v3"
USER_AGENT = "UniverseScales-ModelImporter/1.0"
ALLOWED_LICENSES = {
    "by": ("CC-BY-4.0", "licenses/CC-BY-4.0.txt"),
    "cc0": ("CC0-1.0", "licenses/CC0-1.0.txt"),
}
DECODERS = {"KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_texture_basisu"}


def request_json(url, token=None):
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Token {token}"
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def request_bytes(url, limit):
    address = urlsplit(url)
    if address.scheme != "https" or not address.hostname or not (
        address.hostname.endswith(".sketchfab.com")
        or address.hostname == "sketchfab.com"
        or address.hostname.endswith(".amazonaws.com")
    ):
        raise ValueError("Unexpected model archive host")
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=90) as response:
            data = response.read(limit + 1)
    except HTTPError as error:
        raise ValueError(f"Authorized archive download failed (HTTP {error.code})") from error
    if len(data) > limit:
        raise ValueError(f"Source archive exceeds {limit:,} bytes")
    return data


def dataset_names():
    path = ROOT / "exports/json/dimensions/length.json"
    return {item["name"] for item in json.loads(path.read_text())["items"]}


def model_detail(uid):
    if not re.fullmatch(r"[0-9a-f]{32}", uid):
        raise ValueError(f"Invalid Sketchfab UID: {uid}")
    return request_json(f"{API}/models/{uid}")


def search(queries, limit, max_archive):
    for query in queries:
        params = urlencode({"type": "models", "q": query, "downloadable": "true", "count": 24})
        result = request_json(f"{API}/search?{params}")
        print(f"\n{query}:")
        count = 0
        for item in result.get("results", []):
            size = item.get("archives", {}).get("gltf", {}).get("size")
            label = item.get("license", {}).get("label", "")
            if not size or size > max_archive or label not in ("CC Attribution", "CC0 Public Domain", "CC0"):
                continue
            print(f"  {item['uid']}  {size / 1_000_000:.2f} MB  {label}  "
                  f"{item.get('faceCount', 0):,} faces  {item['name']}  "
                  f"by {item.get('user', {}).get('username', '?')}")
            count += 1
            if count >= limit:
                break
        if not count:
            print("  No small CC0/CC BY candidates in the first page")


def review(model_id, queries, uids, limit, max_archive, output):
    entries = read_manifest()
    selection = next((entry for entry in entries if entry["id"] == model_id), None)
    if not selection:
        raise ValueError(f"Unknown curated model ID: {model_id}")
    candidates = {}
    for query in queries:
        params = urlencode({"type": "models", "q": query, "downloadable": "true", "count": 24})
        for item in request_json(f"{API}/search?{params}").get("results", []):
            candidates[item["uid"]] = item
    pinned = {selection["uid"], *uids}
    for uid in pinned:
        detail = model_detail(uid)
        previous = candidates.get(uid, {})
        candidates[uid] = {**previous, **{key: value for key, value in detail.items() if value is not None}}
    eligible = []
    subject = selection["name"].lower().replace(" length", "").split()[0]
    for item in candidates.values():
        archive = (item.get("archives") or {}).get("gltf") or {}
        size = archive.get("size")
        license_info = item.get("license") or {}
        license_slug = license_info.get("slug") or {
            "CC Attribution": "by", "CC0 Public Domain": "cc0", "CC0": "cc0"
        }.get(license_info.get("label"))
        if ((not size and item["uid"] not in pinned) or (size and size > max_archive)
                or license_slug not in ALLOWED_LICENSES
                or (subject not in item["name"].lower() and item["uid"] not in pinned)):
            continue
        thumbnail = (item.get("thumbnails") or {}).get("images") or []
        preview = min(thumbnail, key=lambda image: abs(image.get("width", 0) - 720)) if thumbnail else None
        eligible.append({"uid": item["uid"], "name": item["name"],
                         "author": item.get("user", {}).get("username", "?"),
                         "license": license_slug.upper(), "bytes": size,
                         "likes": item.get("likeCount", 0),
                         "faces": item.get("faceCount", 0), "image": preview["url"] if preview else "",
                         "url": item.get("viewerUrl") or f"https://sketchfab.com/models/{item['uid']}",
                         "embed": item.get("embedUrl") or f"https://sketchfab.com/models/{item['uid']}/embed"})
    eligible.sort(key=lambda item: (item["uid"] != selection["uid"], -item["likes"], item["bytes"] or 0))
    eligible = eligible[:limit]
    if not eligible:
        raise ValueError("No downloadable CC BY/CC0 models under the archive limit")
    cards = "\n".join(
        '<button class="card" type="button" data-uid="{uid}"><img src="{image}" alt="" loading="lazy">'
        '<strong>{name}</strong><span>by {author} · {license}</span>'
        '<small>{mb} archive · {faces:,} faces</small></button>'.format(
            uid=html.escape(item["uid"]), image=html.escape(item["image"], quote=True),
            name=html.escape(item["name"]), author=html.escape(item["author"]),
            license=html.escape(item["license"]),
            mb=f'{item["bytes"] / 1_000_000:.2f} MB' if item["bytes"] else 'size unlisted',
            faces=item["faces"] or 0) for item in eligible)
    payload = json.dumps({item["uid"]: item for item in eligible}).replace("<", "\\u003c")
    approval_prefix = (f"SSL_CERT_FILE=/etc/ssl/cert.pem {shlex.quote(sys.executable)} "
                       f"{shlex.quote(str(Path(__file__).resolve()))} select --id "
                       f"{shlex.quote(model_id)} --uid ")
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Model review · {html.escape(selection["name"])}</title>
<style>
:root{{font-family:Georgia,serif;color:#162536;background:#eaf0f4}}
*{{box-sizing:border-box}}body{{margin:0}}header{{padding:24px 32px;background:#122332;color:#f8f7ef}}
h1{{margin:0;font-size:30px}}header p{{margin:8px 0 0;color:#cbd9df}}
main{{display:grid;grid-template-columns:minmax(300px,1fr) minmax(340px,1.2fr);gap:20px;padding:20px;max-width:1550px;margin:auto}}
.choices{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;align-content:start}}
.card{{text-align:left;background:#fff;border:2px solid transparent;border-radius:6px;padding:9px;cursor:pointer;color:inherit;font:inherit}}
.card:hover,.card:focus-visible{{border-color:#20799b}}.card.selected{{border-color:#117ca2;background:#eefaff}}
.card img{{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;background:#d5dce0}}
.card strong,.card span,.card small{{display:block;margin-top:7px}}.card span,.card small{{font:13px/1.4 sans-serif;color:#4b5e68}}
.detail{{position:sticky;top:20px;align-self:start;background:white;padding:18px;border-radius:6px}}
iframe{{width:100%;aspect-ratio:16/10;border:0;background:#e2e8ed}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;padding:12px;background:#122332;color:#f8f7ef}}
a{{color:#006e96}}.hint{{font:14px/1.5 sans-serif;color:#526775}}
.copy{{border:1px solid #0f7296;background:#0f7296;color:white;border-radius:4px;padding:9px 14px;cursor:pointer;font:600 14px sans-serif}}
.copy:hover,.copy:focus-visible{{background:#09516d}}
@media(max-width:850px){{main{{display:block}}.detail{{position:static;margin-top:20px}}}}
</style>
<header><h1>{html.escape(selection["name"])} · model review</h1><p>Compare before downloading. Thumbnail and live preview are served by Sketchfab.</p></header>
<main><section class="choices">{cards}</section><section class="detail">
<iframe id="preview" title="3D model preview" allow="autoplay; fullscreen; xr-spatial-tracking" allowfullscreen loading="lazy"></iframe>
<h2 id="title"></h2><p id="facts"></p><p><a id="source" target="_blank" rel="noopener noreferrer">Open source and license details</a></p>
<p class="hint">Inspect all sides and confirm that the mesh represents the listed measurement. Choosing a model does not download it. Approve it in a terminal with:</p>
<pre id="command"></pre><button class="copy" id="copy" type="button">Copy approval command</button>
<p class="hint">Paste that command into a terminal. Then run the importer using your token file outside the repository. Review the result locally before publishing.</p>
</section></main><script>
const models={payload};const approvalPrefix={json.dumps(approval_prefix)};
document.querySelector('.choices').addEventListener('click',event=>{{
 const card=event.target.closest('[data-uid]');if(!card)return;
 document.querySelectorAll('.card').forEach(node=>node.classList.toggle('selected',node===card));
 const item=models[card.dataset.uid];
 document.querySelector('#preview').src=item.embed;
 document.querySelector('#title').textContent=item.name;
 document.querySelector('#facts').textContent=`${{item.author}} · ${{item.license}} · ${{item.bytes ? (item.bytes/1e6).toFixed(2)+' MB' : 'size unlisted'}} archive · ${{item.faces.toLocaleString()}} faces`;
 const source=document.querySelector('#source');source.href=item.url;
 document.querySelector('#command').textContent=approvalPrefix+item.uid;
}});
document.querySelector('.card')?.click();
document.querySelector('#copy').addEventListener('click',async()=>{{
 const value=document.querySelector('#command').textContent;
 try{{await navigator.clipboard.writeText(value);document.querySelector('#copy').textContent='Copied';}}
 catch{{document.querySelector('#copy').textContent='Select and copy the command above';}}
}});
</script></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document)
    print(f"Review {len(eligible)} candidates for {selection['name']}: {output}")


def select_model(model_id, uid):
    from fetch_model_assets import write_json

    entries = read_manifest()
    entry = next((item for item in entries if item["id"] == model_id), None)
    if not entry:
        raise ValueError(f"Unknown curated model ID: {model_id}")
    detail = model_detail(uid)
    license_info = detail.get("license") or {}
    if not detail.get("isDownloadable") or license_info.get("slug") not in ALLOWED_LICENSES:
        raise ValueError("Selected model is not downloadable under CC BY or CC0")
    entry.update(uid=uid, author=detail["user"]["username"], license=license_info["slug"],
                 note="Curator-selected illustrative model; verify that the modeled extent matches the listed measurement.",
                 enabled=True)
    entry.pop("deferred_reason", None)
    write_json(MANIFEST, {"schema_version": 1, "models": entries})
    print(f"Approved {entry['name']}: {detail['name']} by {entry['author']}. Run import --only {model_id} with your token file.")


def read_manifest():
    entries = json.loads(MANIFEST.read_text())["models"]
    names = dataset_names()
    used = set()
    identifiers = set()
    for entry in entries:
        if entry["name"] not in names:
            raise ValueError(f"Not an exact Length item: {entry['name']}")
        if entry["name"] in used:
            raise ValueError(f"Duplicate Length match: {entry['name']}")
        if not re.fullmatch(r"[a-z0-9-]+", entry["id"]):
            raise ValueError(f"Unsafe model ID: {entry['id']}")
        if entry["id"] in identifiers:
            raise ValueError(f"Duplicate model ID: {entry['id']}")
        used.add(entry["name"])
        identifiers.add(entry["id"])
    return entries


def checked_detail(entry):
    detail = model_detail(entry["uid"])
    if not detail.get("isDownloadable"):
        raise ValueError(f"Not downloadable: {entry['id']}")
    license_info = detail.get("license") or {}
    if license_info.get("slug") not in ALLOWED_LICENSES:
        raise ValueError(f"Unsupported license for {entry['id']}: {license_info.get('label')}")
    if entry.get("license") and license_info["slug"] != entry["license"]:
        raise ValueError(f"License changed for {entry['id']}: {license_info['slug']}")
    if entry.get("author") and detail.get("user", {}).get("username") != entry["author"]:
        raise ValueError(f"Author changed for {entry['id']}")
    return detail


def archive_member(archive, name):
    if name.startswith("data:"):
        return base64.b64decode(name.split(",", 1)[1])
    member = posixpath.normpath(unquote(name))
    if member.startswith("../") or member.startswith("/") or member == "..":
        raise ValueError(f"Unsafe archive path: {name}")
    return archive.read(member)


def pack_glb(document, binary):
    encoded = json.dumps(document, ensure_ascii=True, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    payload = bytearray(binary)
    payload.extend(b"\0" * (-len(payload) % 4))
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(encoded) + len(payload))
            + struct.pack("<I4s", len(encoded), b"JSON") + encoded
            + struct.pack("<I4s", len(payload), b"BIN\0") + payload)


def gltf_to_glb(source_zip, texture_size):
    from PIL import Image

    with zipfile.ZipFile(io.BytesIO(source_zip)) as archive:
        if sum(info.file_size for info in archive.infolist()) > 100_000_000:
            raise ValueError("Sketchfab archive expands beyond 100 MB")
        scene_paths = [name for name in archive.namelist() if name.endswith(".gltf")]
        if len(scene_paths) != 1:
            raise ValueError("Expected one glTF scene in the Sketchfab archive")
        scene_path = scene_paths[0]
        prefix = posixpath.dirname(scene_path)
        document = json.loads(archive.read(scene_path))
        if document.get("asset", {}).get("version") != "2.0":
            raise ValueError("Expected glTF 2.0")
        extensions = set(document.get("extensionsUsed", []) + document.get("extensionsRequired", []))
        if extensions & DECODERS:
            raise ValueError(f"Model needs an unsupported decoder: {sorted(extensions & DECODERS)}")

        def resource(uri):
            if uri.startswith("data:"):
                return archive_member(archive, uri)
            return archive_member(archive, posixpath.join(prefix, uri))

        binary = bytearray()
        offsets = []
        for buffer in document.get("buffers", []):
            binary.extend(b"\0" * (-len(binary) % 4))
            offsets.append(len(binary))
            data = resource(buffer["uri"])
            if len(data) < buffer["byteLength"]:
                raise ValueError("Truncated glTF buffer")
            binary.extend(data)
        for view in document.get("bufferViews", []):
            view["byteOffset"] = offsets[view["buffer"]] + view.get("byteOffset", 0)
            view["buffer"] = 0

        for image in document.get("images", []):
            if "uri" in image:
                payload = resource(image.pop("uri"))
            else:
                view = document["bufferViews"][image["bufferView"]]
                start = view["byteOffset"]
                payload = bytes(binary[start:start + view["byteLength"]])
            with Image.open(io.BytesIO(payload)) as original:
                original.load()
                original.thumbnail((texture_size, texture_size), Image.Resampling.LANCZOS)
                transparent = "A" in original.getbands() or "transparency" in original.info
                output = io.BytesIO()
                if transparent:
                    original.convert("RGBA").save(output, format="PNG", optimize=True)
                    image["mimeType"] = "image/png"
                else:
                    original.convert("RGB").save(output, format="JPEG", quality=84, optimize=True)
                    image["mimeType"] = "image/jpeg"
            binary.extend(b"\0" * (-len(binary) % 4))
            image["bufferView"] = len(document["bufferViews"])
            document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary),
                                             "byteLength": len(output.getvalue())})
            binary.extend(output.getvalue())

    document["buffers"] = [{"byteLength": len(binary)}]
    document.pop("animations", None)
    return pack_glb(document, binary)


def repair_static_models(only):
    from fetch_model_assets import inspect_glb, read_glb, write_json

    registry = json.loads(REGISTRY.read_text())
    changed = 0
    for model in registry["models"]:
        if not model.get("sketchfab_uid") or (only and model["id"] not in only):
            continue
        destination = ROOT / model["src"]
        document, binary = read_glb(destination.read_bytes())
        if not document.pop("animations", None):
            continue
        output = pack_glb(document, binary[:document["buffers"][0]["byteLength"]])
        stats = inspect_glb(output)
        model.update(stats)
        model["processing"]["operations"].append("Remove animations for static Length presentation")
        destination.write_bytes(output)
        print(f"Static {model['id']}: {len(output) / 1_000_000:.2f} MB")
        changed += 1
    if changed:
        write_json(REGISTRY, registry)
    print(f"Repacked {changed} model(s)")


def import_models(entries, token_file, max_archive, max_glb, max_total, texture_size):
    token_path = token_file.expanduser().resolve()
    if token_path.is_relative_to(ROOT):
        raise ValueError("Keep the API token outside the repository")
    token = token_path.read_text().strip()
    if not token:
        raise ValueError("API token file is empty")
    from fetch_model_assets import check_matches, inspect_glb, sha, write_json

    registry = json.loads(REGISTRY.read_text())
    existing = {name for model in registry["models"] for name in model.get("matches", {}).get("length", [])}
    pending = []
    for entry in entries:
        if entry.get("enabled") is False:
            print(f"Deferred {entry['name']}: {entry['deferred_reason']}")
            continue
        if any(model["id"] == entry["id"] for model in registry["models"]):
            print(f"Already imported: {entry['name']}")
            continue
        replacement = entry.get("replaces")
        if entry["name"] in existing and not replacement:
            print(f"Already covered: {entry['name']}")
            continue
        if replacement and not any(model["id"] == replacement for model in registry["models"]):
            raise ValueError(f"Replacement not found: {replacement}")
        detail = checked_detail(entry)
        answer = request_json(f"{API}/models/{entry['uid']}/download", token)
        gltf = answer.get("gltf") or {}
        if not gltf.get("url") or gltf.get("size", max_archive + 1) > max_archive:
            print(f"Skip {entry['name']}: source archive exceeds {max_archive / 1_000_000:g} MB")
            continue
        source = request_bytes(gltf["url"], max_archive)
        try:
            selected_texture_size = texture_size
            output = gltf_to_glb(source, selected_texture_size)
            while len(output) > max_glb and selected_texture_size > 128:
                selected_texture_size = max(128, selected_texture_size // 2)
                output = gltf_to_glb(source, selected_texture_size)
            if len(output) > max_glb:
                print(f"Skip {entry['name']}: GLB is {len(output) / 1_000_000:.2f} MB")
                continue
            if sum(len(data) for _, data in pending) + len(output) > max_total:
                print(f"Skip {entry['name']}: batch exceeds {max_total / 1_000_000:g} MB")
                continue
            stats = inspect_glb(output)
        except (OSError, ValueError, KeyError, struct.error, zipfile.BadZipFile) as error:
            print(f"Skip {entry['name']}: {error}")
            continue
        license_info = detail["license"]
        license_name, license_file = ALLOWED_LICENSES[license_info["slug"]]
        username = detail["user"]["username"]
        source_page = detail.get("viewerUrl") or f"https://sketchfab.com/models/{entry['uid']}"
        model = {
            "id": entry["id"], "source": source_page, "author": f"{username} on Sketchfab",
            "license": license_name, "license_url": license_info["url"].replace("http://", "https://"),
            "license_files": [license_file], "matches": {"length": [entry["name"]]},
            "geometry": "mesh", "note": entry.get("note", "Illustrative model; longest mesh axis represents the listed length."),
            "src": f"content/visualizations/models/{entry['id']}.glb", **stats,
            "sketchfab_uid": entry["uid"], "source_sha256": sha(source), "source_bytes": len(source),
            "processing": {"operations": ["Embed glTF buffers and images into GLB",
                                          f"Resize textures to at most {selected_texture_size}px",
                                          "Remove animations for static Length presentation"],
                           "source_model_name": detail["name"], "source_author": username},
            "volume_semantics": "cubic_linear_equivalent_approximation", "closed_volume_checked": False,
        }
        pending.append((model, output))
        print(f"Ready {entry['name']}: {len(output) / 1_000_000:.2f} MB, {stats['triangle_count']:,} triangles")
    replaced = {entry["replaces"] for entry in entries if entry.get("replaces")
                and any(model["id"] == entry["id"] for model, _ in pending)}
    if replaced:
        registry["models"] = [model for model in registry["models"] if model["id"] not in replaced]
    check_matches(registry["models"] + [model for model, _ in pending])
    for model, data in pending:
        destination = ROOT / model["src"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        registry["models"].append(model)
    covered = {name for model in registry["models"] for name in model.get("matches", {}).get("length", [])}
    for gap in registry.get("coverage_gaps", []):
        if "length" in gap.get("matches", {}):
            gap["matches"]["length"] = [name for name in gap["matches"]["length"] if name not in covered]
    registry["coverage_gaps"] = [gap for gap in registry.get("coverage_gaps", [])
                                 if not gap.get("matches") or any(gap["matches"].values())]
    registry.setdefault("build", {})["sketchfab_script"] = "scripts/sketchfab_models.py"
    if pending:
        write_json(REGISTRY, registry)
    print(f"Imported {len(pending)} model(s)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    finder = subcommands.add_parser("search", help="Search public downloadable models")
    finder.add_argument("query", nargs="+", help="One quoted search phrase per argument")
    finder.add_argument("--limit", type=int, default=8)
    finder.add_argument("--max-archive-mb", type=float, default=5)
    reviewer = subcommands.add_parser("review", help="Generate a visual, no-download model shortlist")
    reviewer.add_argument("--id", required=True, help="Curated manifest entry ID")
    reviewer.add_argument("--query", action="append", default=[], help="Sketchfab search phrase; repeat as needed")
    reviewer.add_argument("--uid", action="append", default=[], help="Include a specific model UID")
    reviewer.add_argument("--limit", type=int, default=16)
    reviewer.add_argument("--max-archive-mb", type=float, default=8)
    reviewer.add_argument("--output", type=Path, default=Path("/private/tmp/universe-scales-review/models.html"))
    selector = subcommands.add_parser("select", help="Approve one reviewed model in the curated manifest")
    selector.add_argument("--id", required=True)
    selector.add_argument("--uid", required=True)
    audit = subcommands.add_parser("audit", help="Check curated model identity and licenses")
    audit.add_argument("--only", nargs="*")
    importer = subcommands.add_parser("import", help="Download curated models using a personal API token")
    importer.add_argument("--token-file", type=Path, required=True)
    importer.add_argument("--only", nargs="*")
    importer.add_argument("--max-archive-mb", type=float, default=15)
    importer.add_argument("--max-glb-mb", type=float, default=2)
    importer.add_argument("--max-total-mb", type=float, default=20)
    importer.add_argument("--texture-size", type=int, default=512)
    repair = subcommands.add_parser("repair-static", help="Remove unused animations from imported GLBs")
    repair.add_argument("--only", nargs="*")
    args = parser.parse_args()
    try:
        if args.command == "search":
            search(args.query, args.limit, int(args.max_archive_mb * 1_000_000))
        elif args.command == "review":
            review(args.id, args.query, args.uid, args.limit,
                   int(args.max_archive_mb * 1_000_000), args.output.expanduser())
        elif args.command == "select":
            select_model(args.id, args.uid)
        elif args.command == "repair-static":
            repair_static_models(args.only)
        else:
            entries = read_manifest()
            if args.only:
                entries = [entry for entry in entries if entry["id"] in args.only]
            if args.command == "audit":
                for entry in entries:
                    detail = checked_detail(entry)
                    print(f"OK {entry['name']}: {detail['name']} by {detail['user']['username']} "
                          f"({detail['license']['slug']})"
                          + (f"; deferred: {entry['deferred_reason']}" if entry.get("enabled") is False else ""))
            else:
                import_models(entries, args.token_file, int(args.max_archive_mb * 1_000_000),
                              int(args.max_glb_mb * 1_000_000), int(args.max_total_mb * 1_000_000),
                              args.texture_size)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Sketchfab import failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
