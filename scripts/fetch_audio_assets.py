"""Discover Commons recordings; download only explicitly curated manifest entries."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import time
import tempfile
from urllib.parse import urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content/visualizations/assets.json"


def fetch(url):
    return subprocess.check_output([
        "curl", "-fLsS", "--max-time", "90", "--retry", "3", "--retry-delay", "10", url
    ])


def search(term, exact=False):
    params = dict(action="query", format="json", generator="search", gsrnamespace=6,
                  gsrlimit=6, gsrsearch=f'{term} filetype:audio -intitle:LL- -intitle:pronunciation',
                  prop="imageinfo", iiprop="url|extmetadata|size")
    if exact:
        params = dict(action="query", format="json", titles=term,
                      prop="imageinfo", iiprop="url|extmetadata|size")
    payload = json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + urlencode(params)))
    results = []
    for page in sorted(payload.get("query", {}).get("pages", {}).values(), key=lambda p:p.get("index", 0)):
        info = page.get("imageinfo", [{}])[0]
        meta = info.get("extmetadata", {})
        clean = lambda key: html.unescape(re.sub(r"<[^>]+>", "", str(meta.get(key, {}).get("value", ""))))
        url = urlsplit(info.get("url", ""))
        results.append(dict(file=page["title"], url=urlunsplit(url._replace(query="")),
                            source=info.get("descriptionurl"), author=clean("Artist"),
                            license=clean("LicenseShortName"), license_url=clean("LicenseUrl"),
                            description=clean("ImageDescription")[:2200], bytes=info.get("size")))
    return dict(query=term, candidates=results)


def audit():
    clips = json.loads(MANIFEST.read_text())["audio"]
    items = json.loads((ROOT / "exports/json/dimensions/sound-intensity.json").read_text())["items"]
    names = {item["name"] for item in items}
    problems = []
    for name, clip in clips.items():
        path = (ROOT / clip["src"]).resolve()
        if not path.is_relative_to(ROOT / "content/visualizations/audio"):
            problems.append(f"{name}: unsafe path")
            continue
        if name not in names:
            problems.append(f"{name}: no matching item")
        if not path.exists():
            problems.append(f"{name}: missing local file")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != clip.get("sha256"):
            problems.append(f"{name}: hash mismatch or absent hash")
        if not all(clip.get(key) for key in ("title", "author", "license", "source", "download_url")):
            problems.append(f"{name}: incomplete attribution")
    references = sorted(name for name in names if re.search(r"threshold|guideline|anechoic", name, re.I))
    report = dict(total_items=len(names), covered_items=len(names & clips.keys()),
                  unique_recordings=len({clip["src"] for clip in clips.values()}),
                  reference_items=references,
                  missing_recordings=sorted(names - clips.keys() - set(references)),
                  problems=problems)
    print(json.dumps(report, indent=2))
    if problems:
        raise SystemExit(1)


def download():
    manifest = json.loads(MANIFEST.read_text())
    downloaded = set()
    for clip in manifest["audio"].values():
        target = (ROOT / clip["src"]).resolve()
        if not target.is_relative_to(ROOT / "content/visualizations/audio"):
            raise ValueError(f"Unsafe asset path: {target}")
        if target in downloaded:
            continue
        downloaded.add(target)
        if target.exists():
            data = target.read_bytes()
        else:
            data = fetch(clip["download_url"])
            if clip.get("extract"):
                source_hash = hashlib.sha256(data).hexdigest()
                if clip.get("source_sha256") and clip["source_sha256"] != source_hash:
                    raise ValueError(f"Source hash mismatch: {target}")
                extract = clip["extract"]
                with tempfile.TemporaryDirectory() as temporary:
                    original = Path(temporary) / "original"
                    output = Path(temporary) / "excerpt.wav"
                    original.write_bytes(data)
                    subprocess.run([
                        "ffmpeg", "-v", "error", "-i", str(original),
                        "-ss", str(extract["start"]), "-t", str(extract["duration"]),
                        "-vn", "-map_metadata", "-1", "-fflags", "+bitexact",
                        "-flags:a", "+bitexact", "-ac", "1", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(output)
                    ], check=True)
                    data = output.read_bytes()
                print(json.dumps(dict(file=clip["src"], source_sha256=source_hash)))
        digest = hashlib.sha256(data).hexdigest()
        if clip.get("sha256") and clip["sha256"] != digest:
            raise ValueError(f"Hash mismatch: {target}")
        if not (data.startswith(b"OggS") or data.startswith(b"RIFF") or data.startswith(b"ID3")
                or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
            raise ValueError(f"Not a supported audio container: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        print(json.dumps(dict(file=clip["src"], sha256=digest, bytes=len(data))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", nargs="+")
    group.add_argument("--files", nargs="+", help="Resolve exact Commons file titles without search")
    group.add_argument("--download", action="store_true")
    group.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.search or args.files:
        for term in args.search or args.files:
            print(json.dumps(search(term, exact=bool(args.files)), ensure_ascii=False), flush=True)
            time.sleep(2)
    elif args.audit:
        audit()
    else:
        download()
