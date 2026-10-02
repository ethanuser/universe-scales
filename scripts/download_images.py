#!/usr/bin/env python3
"""
Image Download Script for Universal Scales.

By default this script prefers article-linked images from Wikipedia / Wikimedia
and leaves an item missing if no decent match is found. Generated placeholders
are optional and disabled by default.
"""

import argparse
import json
import os
import re
import ssl
import time
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse
from pathlib import Path
import urllib.request
import urllib.error

try:
    import yaml
except ImportError:  # pragma: no cover - fallback path for minimal environments
    yaml = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environments without Pillow
    Image = None

USER_AGENT = "UniverseScalesImageDownloader/1.0 (educational dataset project)"
PLACEHOLDER_BG = (204, 204, 204)
PLACEHOLDER_BG_TOLERANCE = 8
PLACEHOLDER_DOMINANCE_RATIO = 0.94
PLACEHOLDER_MAX_COLORS = 300
REQUEST_RETRY_STATUSES = {429, 500, 502, 503, 504}
COMMONS_IMAGE_BAD_KEYWORDS = {
    "ambox",
    "disambig",
    "icon",
    "logo",
    "nuvola",
    "symbol",
    "wikidata-logo",
}
PAGE_IMAGE_BAD_KEYWORDS = {
    "avatar",
    "favicon",
    "icon",
    "logo",
    "placeholder",
    "sprite",
    "wordmark",
}
SEARCH_RESULT_BAD_DOMAINS = {
    "commons.wikimedia.org",
    "duckduckgo.com",
    "html.duckduckgo.com",
    "m.wikidata.org",
    "wikidata.org",
    "wikipedia.org",
}
SEARCH_SUFFIX_PATTERNS = {
    "area": [
        r"\bcross-sectional area\b",
        r"\bboundary area\b",
        r"\bsurface area\b",
        r"\bfootprint area\b",
        r"\bapparent area\b",
        r"\bprojected area\b",
        r"\barea\b",
    ],
    "volume": [r"\bvolume\b"],
    "mass": [r"\bmass\b"],
    "density": [r"\bdensity\b"],
    "current": [r"\bcurrent\b", r"\bcurrent draw\b"],
    "charge": [r"\bcharge\b"],
    "temperature": [r"\btemperature\b"],
    "entropy": [r"\bentropy\b", r"\bentropy change\b"],
    "force": [r"\bforce\b"],
    "pressure": [r"\bpressure\b"],
    "speed": [r"\bspeed\b"],
    "acceleration": [r"\bacceleration\b"],
    "jerk": [r"\bjerk\b"],
    "torque": [r"\btorque\b"],
    "moment of inertia": [r"\bmoment of inertia\b"],
    "angular velocity": [r"\bangular velocity\b"],
    "frequency": [r"\bfrequency\b"],
    "loudness": [r"\bsound level\b", r"\bloudness\b"],
    "sound intensity": [r"\bsound intensity\b"],
    "brightness": [r"\bbrightness\b", r"\bluminosity\b", r"\bluminous intensity\b"],
    "intensity": [r"\bintensity\b"],
}

MANUAL_IMAGE_FALLBACKS = {
    ("absorbed-dose", "Sterile insect technique dose"): [
        "https://upload.wikimedia.org/wikipedia/commons/8/8f/Sterile_Insect_Technique_%2805590009%29_%2848194516176%29.jpg",
    ],
    ("micromorts", "Giving birth in a high-income country"): [
        "https://upload.wikimedia.org/wikipedia/commons/1/15/Maternal_health_%284798750001%29.jpg",
    ],
}

# Simple YAML parser for basic YAML files
def parse_yaml_simple(file_path):
    """Simple YAML parser that handles basic YAML structure."""
    if yaml is not None:
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        if isinstance(loaded, dict):
            items = []
            for item in loaded.get('items', []) or []:
                if not isinstance(item, dict):
                    continue
                items.append({
                    'name': item.get('name', ''),
                    'source': item.get('source', ''),
                    'value': item.get('value', ''),
                    'description': item.get('description') or item.get('description_medium') or item.get('summary_short', ''),
                })
            return {
                'dimension': loaded.get('dimension', ''),
                'items': items,
            }

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fallback parser for environments without PyYAML.
    # It is intentionally narrow: enough to read this repo's generated YAML bundles.
    data = {}
    lines = content.split('\n')
    
    current_section = None
    items = []
    current_item = None
    
    for line in lines:
        raw_line = line.rstrip('\n')
        stripped = raw_line.strip()
        if not stripped or stripped.startswith('#'):
            continue
            
        if stripped.startswith('dimension:'):
            data['dimension'] = stripped.split(':', 1)[1].strip().strip('"\'')
        elif stripped.startswith('items:'):
            current_section = 'items'
        elif current_section == 'items':
            entry = stripped
            if entry.startswith('- '):
                if current_item:
                    items.append(current_item)
                current_item = {}
                entry = entry[2:].strip()

            if ':' not in entry or current_item is None:
                continue

            key, value = entry.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')

            if key in {'name', 'source', 'value', 'description', 'description_medium', 'summary_short'}:
                current_item[key] = value
    
    # Add the last item if it exists
    if current_item:
        items.append(current_item)
    
    data['items'] = items
    return data

class ImageDownloader:
    def __init__(self, data_dir="data", images_dir="images", *, allow_placeholders=False):
        # Get the project root (parent of scripts directory)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # Make paths relative to project root
        self.data_dir = project_root / data_dir
        self.images_dir = project_root / images_dir
        self.thumbs_dir = self.images_dir / "thumbs"
        self.cache_dir = project_root / "dataset" / "cache"
        self.cache_file = self.cache_dir / "image_lookup_cache.json"
        self.allow_placeholders = allow_placeholders
        
        # Create images directory if it doesn't exist
        self.images_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ssl_context = ssl.create_default_context()
        self.insecure_ssl_context = ssl._create_unverified_context()
        self.insecure_hosts = set()
        self.last_request_time = {}
        self.json_cache = {}
        self.text_cache = {}
        self.lookup_cache = self.load_lookup_cache()
        self.page_image_cache = self.lookup_cache.setdefault("page_image_candidates", {})
        self.web_search_cache = self.lookup_cache.setdefault("web_search_urls", {})
        self.web_image_cache = self.lookup_cache.setdefault("web_search_image_candidates", {})
        self.wikipedia_title_cache = self.lookup_cache.setdefault("wikipedia_titles", {})
        self.wikipedia_image_cache = self.lookup_cache.setdefault("wikipedia_image_candidates", {})
        self.wikipedia_embedded_cache = self.lookup_cache.setdefault("wikipedia_embedded_candidates", {})
        self.commons_search_cache = self.lookup_cache.setdefault("commons_search_candidates", {})
        self.cache_dirty = False
        self.cache_write_counter = 0

    def load_lookup_cache(self):
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            return loaded if isinstance(loaded, dict) else {}
        except Exception as e:
            print(f"Warning: could not load image lookup cache: {e}")
            return {}

    def mark_lookup_cache_dirty(self):
        self.cache_dirty = True
        self.cache_write_counter += 1
        if self.cache_write_counter >= 25:
            self.save_lookup_cache()
            self.cache_write_counter = 0

    def save_lookup_cache(self):
        if not self.cache_dirty:
            return
        try:
            with open(self.cache_file, "w", encoding="utf-8") as handle:
                json.dump(self.lookup_cache, handle, indent=2, sort_keys=True)
            self.cache_dirty = False
        except Exception as e:
            print(f"Warning: could not save image lookup cache: {e}")

    def urlopen_with_ssl_fallback(self, req, timeout=30):
        """Open a URL with SSL fallback and backoff for rate-limited sources."""
        request_url = getattr(req, "full_url", str(req))
        host = urlparse(request_url).netloc
        contexts = [self.insecure_ssl_context] if host in self.insecure_hosts else [self.ssl_context]
        last_error = None
        for context in contexts:
            for attempt in range(4):
                try:
                    self.throttle_host(host)
                    return urllib.request.urlopen(req, timeout=timeout, context=context)
                except urllib.error.HTTPError as exc:
                    last_error = exc
                    if exc.code not in REQUEST_RETRY_STATUSES:
                        raise
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
                    delay = min(delay, 4.0)
                    print(f"HTTP {exc.code} for {getattr(req, 'full_url', req)}; retrying in {delay:.1f}s.")
                    time.sleep(delay)
                except Exception as exc:
                    last_error = exc
                    if context is self.ssl_context and self.is_ssl_certificate_error(exc):
                        self.insecure_hosts.add(host)
                        print(f"SSL verification failed for {request_url}; retrying without certificate checks.")
                        contexts.append(self.insecure_ssl_context)
                        break
                    raise
        if last_error:
            raise last_error

    def throttle_host(self, host):
        min_delay = 0.15
        if host == "upload.wikimedia.org":
            min_delay = 0.25
        previous = self.last_request_time.get(host)
        now = time.monotonic()
        if previous is not None:
            remaining = min_delay - (now - previous)
            if remaining > 0:
                time.sleep(remaining)
        self.last_request_time[host] = time.monotonic()

    def is_ssl_certificate_error(self, exc):
        """Detect certificate verification failures from urllib or ssl exceptions."""
        if isinstance(exc, ssl.SSLCertVerificationError):
            return True
        if isinstance(exc, urllib.error.URLError):
            reason = getattr(exc, "reason", None)
            if isinstance(reason, ssl.SSLCertVerificationError):
                return True
            if isinstance(reason, Exception) and "CERTIFICATE_VERIFY_FAILED" in str(reason):
                return True
        return "CERTIFICATE_VERIFY_FAILED" in str(exc)

    def normalize_wikipedia_title(self, wikipedia_url_or_title):
        parsed = urlparse(str(wikipedia_url_or_title))
        if parsed.scheme and "wikipedia.org" in parsed.netloc:
            return unquote(parsed.path.split("/")[-1])
        return str(wikipedia_url_or_title).strip().replace(" ", "_")

    def normalize_page_url(self, url):
        parsed = urlparse(str(url or "").strip())
        if not parsed.scheme:
            return f"https://{str(url).lstrip('/')}"
        return str(url)

    def build_api_url(self, base_url, params):
        return f"{base_url}?{urlencode(params)}"

    def build_request(self, url):
        req = urllib.request.Request(url)
        req.add_header("User-Agent", USER_AGENT)
        req.add_header("Accept-Language", "en-US,en;q=0.8")
        return req

    def fetch_json(self, url, timeout=10):
        if url in self.json_cache:
            return self.json_cache[url]
        with self.urlopen_with_ssl_fallback(self.build_request(url), timeout=timeout) as response:
            parsed = json.loads(response.read().decode())
            self.json_cache[url] = parsed
            return parsed

    def fetch_text(self, url, timeout=10):
        if url in self.text_cache:
            return self.text_cache[url]
        with self.urlopen_with_ssl_fallback(self.build_request(url), timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            self.text_cache[url] = text
            return text

    def looks_like_direct_image_url(self, url):
        parsed = urlparse(str(url or ""))
        path = parsed.path.lower()
        return path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"))

    def is_valid_existing_image(self, image_path):
        """Return True if an existing file looks like a readable image."""
        try:
            image_path = Path(image_path)
            if not image_path.exists() or image_path.stat().st_size == 0:
                return False
            if Image is None:
                return image_path.stat().st_size > 1024
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def is_promising_page_image_url(self, url):
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme not in {"http", "https"}:
            return False
        lowered = f"{parsed.netloc}{parsed.path}".lower()
        if any(keyword in lowered for keyword in PAGE_IMAGE_BAD_KEYWORDS):
            return False
        if lowered.endswith(".ico"):
            return False
        if not self.looks_like_direct_image_url(url):
            if "/images/" not in lowered and "/image/" not in lowered and "/media/" not in lowered:
                return False
        return True

    def dedupe_urls(self, urls):
        seen = set()
        deduped = []
        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            deduped.append(url)
        return deduped

    def extract_meta_image_candidates(self, html, page_url):
        candidates = []
        meta_patterns = (
            r'<meta[^>]+(?:property|name|itemprop)=["\'](?:og:image|og:image:url|twitter:image|twitter:image:src|image)["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\'](?:og:image|og:image:url|twitter:image|twitter:image:src|image)["\']',
            r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)["\']',
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']image_src["\']',
        )
        for pattern in meta_patterns:
            for match in re.finditer(pattern, html, re.IGNORECASE):
                candidates.append(urljoin(page_url, match.group(1)))
        for match in re.finditer(r'"image"\s*:\s*"([^"]+)"', html, re.IGNORECASE):
            value = match.group(1).replace("\\/", "/")
            if "/" in value or "." in value:
                candidates.append(urljoin(page_url, value))
        for match in re.finditer(r'"image"\s*:\s*\[\s*"([^"]+)"', html, re.IGNORECASE):
            value = match.group(1).replace("\\/", "/")
            if "/" in value or "." in value:
                candidates.append(urljoin(page_url, value))
        return candidates

    def extract_inline_image_candidates(self, html, page_url, limit=12):
        candidates = []
        img_patterns = (
            r'<img[^>]+(?:data-src|data-original|src)=["\']([^"\']+)["\']',
            r'<img[^>]+(?:srcset|data-srcset)=["\']([^"\']+)["\']',
        )
        for pattern in img_patterns:
            for match in re.finditer(pattern, html, re.IGNORECASE):
                raw = match.group(1).split(",")[0].strip().split(" ")[0]
                if not raw:
                    continue
                candidates.append(urljoin(page_url, raw))
                if len(candidates) >= limit:
                    return candidates
        return candidates

    def get_page_image_candidates(self, page_url):
        page_url = self.normalize_page_url(page_url)
        if page_url in self.page_image_cache:
            return self.page_image_cache[page_url]

        candidates = []
        try:
            if self.looks_like_direct_image_url(page_url):
                candidates = [page_url]
            else:
                html = self.fetch_text(page_url, timeout=12)
                candidates.extend(self.extract_meta_image_candidates(html, page_url))
                candidates.extend(self.extract_inline_image_candidates(html, page_url))
        except Exception as e:
            print(f"Error getting page image candidates for {page_url}: {e}")

        filtered = [
            candidate for candidate in self.dedupe_urls(candidates)
            if self.is_promising_page_image_url(candidate)
        ]
        self.page_image_cache[page_url] = filtered
        self.mark_lookup_cache_dirty()
        return filtered

    def extract_search_result_urls(self, html):
        candidates = []
        for match in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
            href = match.group(1)
            resolved = href
            if "uddg=" in href:
                parsed = urlparse(href)
                uddg = parse_qs(parsed.query).get("uddg", [])
                if uddg:
                    resolved = unquote(uddg[0])
            elif href.startswith("//"):
                resolved = f"https:{href}"

            parsed = urlparse(resolved)
            if parsed.scheme not in {"http", "https"}:
                continue
            netloc = parsed.netloc.lower()
            if any(netloc.endswith(domain) or netloc == domain for domain in SEARCH_RESULT_BAD_DOMAINS):
                continue
            candidates.append(resolved)
        return self.dedupe_urls(candidates)

    def search_web_page_urls(self, query, limit=5):
        query = str(query or "").strip()
        if not query:
            return []
        if query in self.web_search_cache:
            return self.web_search_cache[query]
        try:
            search_url = self.build_api_url("https://html.duckduckgo.com/html/", {"q": query})
            html = self.fetch_text(search_url, timeout=12)
            results = self.extract_search_result_urls(html)[:limit]
            self.web_search_cache[query] = results
            self.mark_lookup_cache_dirty()
            return results
        except Exception as e:
            print(f"Error searching web pages for {query}: {e}")
            self.web_search_cache[query] = []
            self.mark_lookup_cache_dirty()
            return []

    def search_web_page_image_candidates(self, query, limit=4):
        query = str(query or "").strip()
        if not query:
            return []
        if query in self.web_image_cache:
            return self.web_image_cache[query]
        candidates = []
        for page_url in self.search_web_page_urls(query, limit=limit):
            candidates.extend(self.get_page_image_candidates(page_url))
            if len(candidates) >= 10:
                break
        deduped = self.dedupe_urls(candidates)
        self.web_image_cache[query] = deduped
        self.mark_lookup_cache_dirty()
        return deduped

    def get_wikipedia_image_url(self, wikipedia_url):
        """Extract a Wikipedia page title and return multiple candidate image URLs."""
        return self.get_wikipedia_image_candidates(self.normalize_wikipedia_title(wikipedia_url))

    def get_wikipedia_image_candidates(self, page_title):
        """Collect likely article image candidates for a Wikipedia page title."""
        page_title = self.normalize_wikipedia_title(page_title)
        if page_title in self.wikipedia_image_cache:
            return self.wikipedia_image_cache[page_title]
        candidates = []

        try:
            data = self.fetch_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(page_title)}", timeout=10)
            if "thumbnail" in data and "source" in data["thumbnail"]:
                candidates.append(data["thumbnail"]["source"])
            if "originalimage" in data and "source" in data["originalimage"]:
                candidates.append(data["originalimage"]["source"])
        except Exception as e:
            print(f"Error getting Wikipedia summary image for {page_title}: {e}")

        try:
            api_url = (
                "https://en.wikipedia.org/w/api.php"
                f"?action=query&prop=pageimages&piprop=original|thumbnail&pithumbsize=1000"
                f"&titles={quote(page_title)}&redirects=1&format=json"
            )
            data = self.fetch_json(api_url, timeout=10)
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if "thumbnail" in page and "source" in page["thumbnail"]:
                    candidates.append(page["thumbnail"]["source"])
                if "original" in page and "source" in page["original"]:
                    candidates.append(page["original"]["source"])
        except Exception as e:
            print(f"Error getting Wikipedia pageimages for {page_title}: {e}")

        try:
            html = self.fetch_text(f"https://en.wikipedia.org/wiki/{quote(page_title)}", timeout=10)
            for pattern in (
                r'<meta\s+property="og:image"\s+content="([^"]+)"',
                r'<meta\s+content="([^"]+)"\s+property="og:image"',
            ):
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    candidates.append(match.group(1))
                    break
        except Exception as e:
            print(f"Error getting Wikipedia page HTML image for {page_title}: {e}")

        seen = set()
        deduped = []
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            deduped.append(candidate)
        self.wikipedia_image_cache[page_title] = deduped
        self.mark_lookup_cache_dirty()
        return deduped

    def is_promising_commons_title(self, title):
        lowered = str(title or "").lower()
        return not any(keyword in lowered for keyword in COMMONS_IMAGE_BAD_KEYWORDS)

    def extract_commons_candidates(self, data):
        ranked = []
        for page in data.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            if not self.is_promising_commons_title(title):
                continue
            for info in page.get("imageinfo", []):
                url = info.get("thumburl") or info.get("url")
                if not url:
                    continue
                mime = info.get("mime", "")
                width = info.get("thumbwidth") or info.get("width") or 0
                score = 0
                if mime in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                    score += 4
                elif mime == "image/svg+xml":
                    score += 2 if info.get("thumburl") else -2
                if width >= 800:
                    score += 2
                elif width >= 400:
                    score += 1
                ranked.append((score, url))
        ranked.sort(key=lambda entry: entry[0], reverse=True)
        deduped = []
        seen = set()
        for _, url in ranked:
            if url in seen:
                continue
            seen.add(url)
            deduped.append(url)
        return deduped

    def get_commons_candidates_for_titles(self, file_titles):
        file_titles = [title for title in file_titles if title and self.is_promising_commons_title(title)]
        if not file_titles:
            return []
        params = {
            "action": "query",
            "titles": "|".join(file_titles[:20]),
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1600,
            "format": "json",
        }
        try:
            data = self.fetch_json(self.build_api_url("https://commons.wikimedia.org/w/api.php", params), timeout=12)
            return self.extract_commons_candidates(data)
        except Exception as e:
            print(f"Error getting Commons imageinfo for {file_titles[:3]}...: {e}")
            return []

    def get_wikipedia_embedded_image_candidates(self, page_title):
        page_title = self.normalize_wikipedia_title(page_title)
        if page_title in self.wikipedia_embedded_cache:
            return self.wikipedia_embedded_cache[page_title]
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "images",
            "imlimit": 12,
            "format": "json",
            "redirects": 1,
        }
        try:
            data = self.fetch_json(self.build_api_url("https://en.wikipedia.org/w/api.php", params), timeout=10)
            file_titles = []
            for page in data.get("query", {}).get("pages", {}).values():
                for image in page.get("images", []):
                    title = image.get("title", "")
                    if title.startswith("File:"):
                        file_titles.append(title)
            candidates = self.get_commons_candidates_for_titles(file_titles)
            self.wikipedia_embedded_cache[page_title] = candidates
            self.mark_lookup_cache_dirty()
            return candidates
        except Exception as e:
            print(f"Error getting embedded Wikipedia images for {page_title}: {e}")
            self.wikipedia_embedded_cache[page_title] = []
            self.mark_lookup_cache_dirty()
            return []

    def search_wikimedia_commons_candidates(self, query, limit=8):
        query = str(query or "").strip()
        if not query:
            return []
        if query in self.commons_search_cache:
            return self.commons_search_cache[query]
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": min(int(limit), 12),
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1600,
            "format": "json",
        }
        try:
            data = self.fetch_json(self.build_api_url("https://commons.wikimedia.org/w/api.php", params), timeout=12)
            candidates = self.extract_commons_candidates(data)
            self.commons_search_cache[query] = candidates
            self.mark_lookup_cache_dirty()
            return candidates
        except Exception as e:
            print(f"Error searching Wikimedia Commons for {query}: {e}")
            self.commons_search_cache[query] = []
            self.mark_lookup_cache_dirty()
            return []

    def search_wikipedia_titles(self, query, limit=4):
        """Search Wikipedia for likely article titles to use as image sources."""
        query = str(query or "").strip()
        if not query:
            return []
        if query in self.wikipedia_title_cache:
            return self.wikipedia_title_cache[query]
        try:
            data = self.fetch_json(
                "https://en.wikipedia.org/w/api.php"
                f"?action=query&list=search&srsearch={quote(query)}&srlimit={int(limit)}&format=json",
                timeout=10,
            )
            titles = []
            for result in data.get("query", {}).get("search", []):
                title = str(result.get("title", "")).strip()
                if title:
                    titles.append(title)
            self.wikipedia_title_cache[query] = titles
            self.mark_lookup_cache_dirty()
            return titles
        except Exception as e:
            print(f"Error searching Wikipedia for {query}: {e}")
            self.wikipedia_title_cache[query] = []
            self.mark_lookup_cache_dirty()
            return []

    def generate_search_queries(self, item_name, dimension, source_url=""):
        queries = []
        normalized_name = str(item_name or "").strip()
        if normalized_name:
            queries.append(normalized_name)
            queries.append(re.sub(r"\s*\([^)]*\)", "", normalized_name).strip())
            queries.append(re.sub(r"\bat\b.*$", "", normalized_name, flags=re.IGNORECASE).strip())
            queries.append(self.strip_dimension_suffix(normalized_name, dimension))
        if source_url and "wikipedia.org" in source_url:
            queries.append(self.normalize_wikipedia_title(source_url).replace("_", " "))
        if normalized_name and dimension:
            queries.append(f"{normalized_name} {dimension}")
        deduped = []
        seen = set()
        for query in queries:
            cleaned = " ".join(query.split()).strip(" ,")
            if not cleaned or cleaned.lower() in seen:
                continue
            seen.add(cleaned.lower())
            deduped.append(cleaned)
        return deduped

    def strip_dimension_suffix(self, item_name, dimension):
        cleaned = re.sub(r"\s*\([^)]*\)", "", str(item_name or "")).strip()
        dimension_key = str(dimension or "").strip().lower()
        patterns = SEARCH_SUFFIX_PATTERNS.get(dimension_key, [])
        for pattern in patterns:
            cleaned = re.sub(rf"\s+{pattern}$", "", cleaned, flags=re.IGNORECASE).strip(" ,")
        return cleaned or str(item_name or "").strip()
    
    def generate_placeholder_image(self, filename, text):
        """Generate a local placeholder image file for cases where network fetches fail."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            filepath = self.images_dir / filename
            width, height = 400, 300
            image = Image.new("RGB", (width, height), (204, 204, 204))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()

            label = text.strip() if text else "Placeholder"
            if len(label) > 36:
                words = label.split()
                lines = []
                current = ""
                for word in words:
                    candidate = f"{current} {word}".strip()
                    if draw.textbbox((0, 0), candidate, font=font)[2] <= width - 40:
                        current = candidate
                    else:
                        if current:
                            lines.append(current)
                        current = word
                if current:
                    lines.append(current)
            else:
                lines = [label]

            text_block = "\n".join(lines[:3])
            bbox = draw.multiline_textbbox((0, 0), text_block, font=font, spacing=6, align="center")
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) / 2
            y = (height - text_height) / 2
            draw.multiline_text((x, y), text_block, fill=(102, 102, 102), font=font, spacing=6, align="center")
            image.save(filepath, format="JPEG", quality=90)
            print(f"Created placeholder: {filename}")
            return True
        except Exception as e:
            print(f"Error generating placeholder for {text}: {e}")
            return None

    def is_generated_placeholder(self, image_path):
        """Identify the simple gray generated placeholders from earlier runs."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                rgb = img.convert("RGB")
                if rgb.size != (400, 300):
                    return False
                colors = rgb.getcolors(maxcolors=1_000_000)
                if not colors or len(colors) > PLACEHOLDER_MAX_COLORS:
                    return False
                total = rgb.size[0] * rgb.size[1]
                dominant_count, dominant = max(colors, key=lambda entry: entry[0])
                if dominant_count / total < PLACEHOLDER_DOMINANCE_RATIO:
                    return False
                return all(abs(component - target) <= PLACEHOLDER_BG_TOLERANCE for component, target in zip(dominant, PLACEHOLDER_BG))
        except Exception:
            return False

    def purge_placeholder_artifacts(self, filename):
        removed = False
        image_path = self.images_dir / filename
        thumb_path = self.thumbs_dir / filename
        if image_path.exists():
            image_path.unlink()
            removed = True
        if thumb_path.exists():
            thumb_path.unlink()
        return removed
    
    def download_image(self, url, filename):
        """Download an image from URL and save it to the images directory."""
        try:
            with self.urlopen_with_ssl_fallback(self.build_request(url), timeout=30) as response:
                if response.status == 200:
                    filepath = self.images_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(response.read())
                    if not self.is_valid_existing_image(filepath):
                        try:
                            filepath.unlink()
                        except Exception:
                            pass
                        print(f"Rejected invalid image: {filename}")
                        return False
                    
                    print(f"Downloaded: {filename}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def sanitize_filename(self, dimension, name):
        """Convert dimension and item name to a safe filename."""
        # Remove special characters and replace spaces with underscores
        safe_dimension = re.sub(r'[^\w\s-]', '', dimension)
        safe_dimension = re.sub(r'[-\s]+', '_', safe_dimension)
        
        safe_name = re.sub(r'[^\w\s-]', '', name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        
        return f"{safe_dimension.lower()}_{safe_name.lower()}.jpg"

    def get_manual_image_fallbacks(self, dimension, item_name):
        return MANUAL_IMAGE_FALLBACKS.get((dimension, item_name), [])
    
    def find_missing_images(self, yaml_file):
        """Find all images that are missing for items in a YAML file."""
        print(f"\nChecking missing images in {yaml_file.name}...")
        
        data = parse_yaml_simple(yaml_file)
        
        if 'items' not in data or 'dimension' not in data:
            print(f"No items or dimension found in {yaml_file.name}")
            return []
        
        dimension = data['dimension']
        missing_images = []
        
        for item in data['items']:
            item_name = item['name']
            filename = self.sanitize_filename(dimension, item_name)
            image_path = self.images_dir / filename
            
            if image_path.exists() and self.is_generated_placeholder(image_path):
                missing_images.append({
                    'name': item_name,
                    'filename': filename,
                    'dimension': dimension,
                    'source': item.get('source', ''),
                    'placeholder': True,
                })
                continue

            if not image_path.exists():
                missing_images.append({
                    'name': item_name,
                    'filename': filename,
                    'dimension': dimension,
                    'source': item.get('source', '')
                })
            elif not self.is_valid_existing_image(image_path):
                missing_images.append({
                    'name': item_name,
                    'filename': filename,
                    'dimension': dimension,
                    'source': item.get('source', '')
                })
        
        print(f"Found {len(missing_images)} missing images for {dimension}")
        return missing_images
    
    def process_yaml_file(self, yaml_file):
        """Process a single YAML file and download images for its items."""
        print(f"\nProcessing {yaml_file.name}...")
        
        data = parse_yaml_simple(yaml_file)
        
        if 'items' not in data or 'dimension' not in data:
            print(f"No items or dimension found in {yaml_file.name}")
            return 0, 0
        
        dimension = data['dimension']
        downloaded_count = 0
        skipped_count = 0
        unresolved_count = 0
        
        for item in data['items']:
            item_name = item['name']
            
            # Create filename based on dimension and item name
            filename = self.sanitize_filename(dimension, item_name)
            image_path = self.images_dir / filename
            
            if image_path.exists():
                if self.is_generated_placeholder(image_path):
                    self.purge_placeholder_artifacts(filename)
                elif not self.is_valid_existing_image(image_path):
                    print(f"Corrupt image detected for {dimension}/{item_name}: {filename}; refetching")
                    try:
                        image_path.unlink()
                    except Exception:
                        pass
                    thumb_path = self.thumbs_dir / filename
                    if thumb_path.exists():
                        try:
                            thumb_path.unlink()
                        except Exception:
                            pass
                else:
                    print(f"Image already exists for {dimension}/{item_name}: {filename}")
                    skipped_count += 1
                    continue

            candidate_urls = []

            source_url = item.get('source', '')
            source_is_wikipedia = bool(source_url and 'wikipedia.org' in source_url)
            if source_url:
                if source_is_wikipedia:
                    candidate_urls.extend(self.get_wikipedia_image_url(source_url))
                    candidate_urls.extend(self.get_wikipedia_embedded_image_candidates(source_url))
                else:
                    candidate_urls.extend(self.get_page_image_candidates(source_url))

            for query in self.generate_search_queries(item_name, dimension, item.get('source', '')):
                candidate_urls.extend(self.search_web_page_image_candidates(query))
                if len(candidate_urls) < 8 and (not source_is_wikipedia or not candidate_urls):
                    for title in self.search_wikipedia_titles(query, limit=2):
                        candidate_urls.extend(self.get_wikipedia_image_candidates(title))
                        candidate_urls.extend(self.get_wikipedia_embedded_image_candidates(title))
                if len(candidate_urls) < 12:
                    candidate_urls.extend(self.search_wikimedia_commons_candidates(query))
                if len(candidate_urls) >= 12:
                    break

            deduped_urls = self.dedupe_urls(candidate_urls)

            downloaded = False
            for image_url in deduped_urls:
                if self.download_image(image_url, filename):
                    downloaded_count += 1
                    downloaded = True
                    time.sleep(0.35)
                    break

            if not downloaded:
                for image_url in self.get_manual_image_fallbacks(dimension, item_name):
                    if self.download_image(image_url, filename):
                        downloaded_count += 1
                        downloaded = True
                        time.sleep(0.35)
                        break

            if downloaded:
                print(f"Fetched image for {dimension}/{item_name}: {filename}")
                continue

            if self.allow_placeholders and self.generate_placeholder_image(filename, item_name):
                unresolved_count += 1
            else:
                unresolved_count += 1
                print(f"No fair-use image found for {dimension}/{item_name}")
        
        print(f"Summary for {dimension}: {downloaded_count} downloaded, {unresolved_count} unresolved, {skipped_count} already existed")
        return downloaded_count, skipped_count
    
    def run(self, *, dimension_filter=None):
        """Main function to process all YAML files."""
        try:
            print("Starting automatic image download process...")
            print("Images will be named as: dimension_item_name.jpg")
            
            # Find all YAML files in the configured data directory
            yaml_files = list(self.data_dir.glob("*.yaml"))
            if dimension_filter:
                normalized_filter = str(dimension_filter).strip().lower()
                yaml_files = [
                    yaml_file for yaml_file in yaml_files
                    if yaml_file.stem.lower() == normalized_filter
                    or yaml_file.name.lower() == normalized_filter
                ]
            
            if not yaml_files:
                print(f"No YAML files found in {self.data_dir}")
                return
            
            print(f"Found {len(yaml_files)} YAML files to process")
            
            total_downloaded = 0
            total_skipped = 0
            
            # First, show missing images summary
            print("\n" + "="*50)
            print("MISSING IMAGES SUMMARY")
            print("="*50)
            
            all_missing = []
            for yaml_file in yaml_files:
                missing = self.find_missing_images(yaml_file)
                all_missing.extend(missing)
            
            if all_missing:
                print(f"\nTotal missing images: {len(all_missing)}")
                for missing in all_missing:
                    print(f"  - {missing['dimension']}/{missing['name']} -> {missing['filename']}")
            else:
                print("\nAll images are present!")
            
            print("\n" + "="*50)
            print("DOWNLOADING MISSING IMAGES")
            print("="*50)
            
            for yaml_file in yaml_files:
                downloaded, skipped = self.process_yaml_file(yaml_file)
                total_downloaded += downloaded
                total_skipped += skipped
            
            print(f"\nImage download process completed!")
            print(f"Total images downloaded: {total_downloaded}")
            print(f"Total images already existed: {total_skipped}")
        finally:
            self.save_lookup_cache()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-placeholders", action="store_true", help="Generate local placeholder images when no source image can be found.")
    parser.add_argument("--dimension", help="Process only one exported YAML dimension, such as 'area' or 'mass'.")
    parser.add_argument("--data-dir", default="data", help="Directory containing YAML files to process (default: data).")
    args = parser.parse_args()

    downloader = ImageDownloader(data_dir=args.data_dir, allow_placeholders=args.allow_placeholders)
    downloader.run(dimension_filter=args.dimension)

if __name__ == "__main__":
    main()
