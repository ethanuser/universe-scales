#!/usr/bin/env python3
"""Set every `?v=` cache-busting query to the referenced file's content hash.

    python3 scripts/bump_versions.py          # rewrite stale versions
    python3 scripts/bump_versions.py --check  # exit 1 if any version is stale

Covers the HTML entry pages and ES-module imports under js/, adding missing
versions to local first-party imports. Vendored module URLs stay unchanged. Because a
changed module changes the import strings of the modules that import it, the
rewrite repeats until nothing changes. Identical URLs everywhere also mean a
module is never loaded twice under two different version strings.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = re.compile(r"""(?P<path>[\w./-]+\.(?:js|css))\?v=(?P<version>[\w.-]+)""")
UNVERSIONED_IMPORT = re.compile(
    r"""(?P<prefix>\b(?:from\s*|import\s*(?:\(\s*)?)[\"'])(?P<path>\.{1,2}/[\w./-]+\.js)(?P<suffix>[\"'])"""
)


def sources():
    yield from sorted(ROOT.glob("*.html"))
    yield from sorted(path for path in (ROOT / "js").rglob("*.js") if "vendor" not in path.parts)


def target(referrer, reference):
    base = ROOT if referrer.suffix == ".html" else referrer.parent
    path = (base / reference).resolve()
    return path if path.is_file() and ROOT in path.parents else None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def rewrite(check):
    stale = []
    for _ in range(12):
        changed = False
        for source in sources():
            text = source.read_text()

            def add_version(match):
                path = target(source, match["path"])
                if path is None or "vendor" in path.relative_to(ROOT).parts:
                    return match[0]
                stale.append(f"{source.relative_to(ROOT)}: {match['path']} missing version")
                return f"{match['prefix']}{match['path']}?v={digest(path)}{match['suffix']}"

            if source.suffix == ".js":
                text = UNVERSIONED_IMPORT.sub(add_version, text)

            def replace(match):
                path = target(source, match["path"])
                if path is None:
                    return match[0]
                version = digest(path)
                if version != match["version"]:
                    stale.append(f"{source.relative_to(ROOT)}: {match['path']} {match['version']} -> {version}")
                return f"{match['path']}?v={version}"

            updated = REFERENCE.sub(replace, text)
            if updated != source.read_text():
                changed = True
                if not check:
                    source.write_text(updated)
        if check or not changed:
            break
    return stale


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = rewrite(args.check)
    if args.check and stale:
        print("Stale cache-busting versions (run python3 scripts/bump_versions.py):\n  " + "\n  ".join(stale))
        sys.exit(1)
    print(f"{'Checked' if args.check else 'Updated'} versions; {len(set(stale))} reference(s) {'stale' if args.check else 'rewritten'}.")


if __name__ == "__main__":
    main()
