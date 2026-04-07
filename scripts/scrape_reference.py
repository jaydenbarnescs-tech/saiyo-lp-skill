#!/usr/bin/env python3
"""
scrape_reference.py — saiyo-lp reference site scraper.

Fetches a reference URL and extracts:
  - All images (img src, picture srcset, CSS background-image urls) as absolute
  - CSS color palette (from inline styles + linked stylesheets), ranked by frequency
  - Google Fonts references
  - H1/H2/H3 headings
  - Paragraph snippets (tone analysis)
  - Meta info (title, description, og:image)

Output: JSON manifest at /tmp/saiyo_ref_{slug}.json

Usage:
    python3 scrape_reference.py <url> <slug>
"""

import json
import re
import sys
from collections import Counter
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEX_RE = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
RGB_RE = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)")
HSL_RE = re.compile(r"hsla?\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%(?:\s*,\s*[\d.]+)?\s*\)")
FONT_FAMILY_RE = re.compile(r'font-family\s*:\s*([^;}]+)')
BG_IMAGE_RE = re.compile(r'background-image\s*:\s*url\(["\']?([^"\')]+)["\']?\)', re.IGNORECASE)


def fetch(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    r.raise_for_status()
    # Try to use UTF-8 if the server doesn't specify
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def absolutize(base_url: str, url: str) -> str:
    if url.startswith("data:"):
        return url
    return urljoin(base_url, url)


def is_near_white_or_black(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return True
    # Near white: all channels > 240
    if r > 240 and g > 240 and b > 240:
        return True
    # Near black: all channels < 20
    if r < 20 and g < 20 and b < 20:
        return True
    # Grey: channels within 10 of each other and mid-range
    if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
        return True
    return False


def normalize_hex(hex_color: str) -> str:
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return f"#{h}"


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def hsl_to_rgb(h: int, s: int, l: int) -> tuple:
    s /= 100
    l /= 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if 0 <= h < 60:
        rp, gp, bp = c, x, 0
    elif 60 <= h < 120:
        rp, gp, bp = x, c, 0
    elif 120 <= h < 180:
        rp, gp, bp = 0, c, x
    elif 180 <= h < 240:
        rp, gp, bp = 0, x, c
    elif 240 <= h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    return (round((rp + m) * 255), round((gp + m) * 255), round((bp + m) * 255))


def extract_colors(css_text: str) -> list:
    """Extract hex/rgb/hsl colors from CSS text. Returns hex strings."""
    colors = []

    for match in HEX_RE.finditer(css_text):
        colors.append(normalize_hex(match.group(0)))

    for match in RGB_RE.finditer(css_text):
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        colors.append(rgb_to_hex(r, g, b))

    for match in HSL_RE.finditer(css_text):
        h, s, l = int(match.group(1)), int(match.group(2)), int(match.group(3))
        r, g, b = hsl_to_rgb(h, s, l)
        colors.append(rgb_to_hex(r, g, b))

    return colors


def extract_fonts(css_text: str) -> list:
    """Extract font-family values from CSS text."""
    fonts = []
    for match in FONT_FAMILY_RE.finditer(css_text):
        value = match.group(1).strip()
        # First family in the stack
        first = value.split(",")[0].strip().strip('"').strip("'")
        if first and not first.startswith("var(") and first not in ("inherit", "initial"):
            fonts.append(first)
    return fonts


def get_stylesheets(soup: BeautifulSoup, base_url: str) -> list:
    """Return list of (url_or_inline, text) for all stylesheets."""
    results = []

    # Inline <style> blocks
    for style in soup.find_all("style"):
        if style.string:
            results.append(("inline", style.string))

    # Linked stylesheets
    for link in soup.find_all("link", rel=lambda x: x and "stylesheet" in x):
        href = link.get("href")
        if not href:
            continue
        abs_url = absolutize(base_url, href)
        # Skip google fonts CSS — we'll catch them separately
        if "fonts.googleapis.com" in abs_url:
            results.append(("google-fonts", abs_url))
            continue
        try:
            r = requests.get(abs_url, headers={"User-Agent": USER_AGENT}, timeout=10)
            if r.ok:
                results.append((abs_url, r.text))
        except Exception:
            continue

    return results


def guess_image_context(img_tag, position: int, total: int) -> str:
    """Best-effort guess at where the image sits in the page."""
    parent = img_tag.parent
    classes = " ".join(img_tag.get("class", []) + (parent.get("class", []) if parent else []))
    classes_lower = classes.lower()

    if "hero" in classes_lower or "mv" in classes_lower or "kv" in classes_lower:
        return "hero"
    if "logo" in classes_lower:
        return "logo"
    if "avatar" in classes_lower or "portrait" in classes_lower or "member" in classes_lower or "staff" in classes_lower:
        return "portrait"
    if "thumb" in classes_lower:
        return "thumbnail"
    if position < 2:
        return "hero"
    if position < total * 0.3:
        return "above-fold"
    return "content"


def scrape(url: str, slug: str) -> dict:
    print(f"Fetching {url}...")
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    # Meta
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    og_image = ""
    og_img_tag = soup.find("meta", property="og:image")
    if og_img_tag and og_img_tag.get("content"):
        og_image = absolutize(url, og_img_tag["content"])

    og_site = ""
    og_site_tag = soup.find("meta", property="og:site_name")
    if og_site_tag and og_site_tag.get("content"):
        og_site = og_site_tag["content"]

    # Images from <img> tags
    img_tags = soup.find_all("img")
    images = []
    for i, img in enumerate(img_tags):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        abs_url = absolutize(url, src)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            continue
        alt = img.get("alt", "").strip()
        context = guess_image_context(img, i, len(img_tags))
        # Guess mime from extension
        ext = parsed.path.split(".")[-1].lower() if "." in parsed.path else ""
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                    "webp": "image/webp", "gif": "image/gif", "svg": "image/svg+xml"}
        mime = mime_map.get(ext, "image/jpeg")
        images.append({
            "url": abs_url,
            "alt": alt,
            "context_guess": context,
            "mime": mime,
        })

    # Dedupe by URL
    seen = set()
    deduped_images = []
    for im in images:
        if im["url"] not in seen:
            seen.add(im["url"])
            deduped_images.append(im)

    # Limit to first 50
    deduped_images = deduped_images[:50]

    # CSS colors + fonts
    all_colors = []
    all_fonts = []
    google_fonts_urls = []

    for source, text in get_stylesheets(soup, url):
        if source == "google-fonts":
            google_fonts_urls.append(text)
            continue
        all_colors.extend(extract_colors(text))
        all_fonts.extend(extract_fonts(text))

    # Also scan inline style attributes
    for el in soup.find_all(style=True):
        style_attr = el.get("style", "")
        all_colors.extend(extract_colors(style_attr))

    # Rank colors
    color_counter = Counter(c for c in all_colors if not is_near_white_or_black(c))
    top_colors = [{"hex": c, "count": n} for c, n in color_counter.most_common(12)]

    # Rank fonts
    font_counter = Counter(all_fonts)
    all_font_names = [f for f, _ in font_counter.most_common(20)]

    # Classify fonts into display vs JP
    display_fonts = []
    jp_fonts = []
    for f in all_font_names:
        if any(kw in f for kw in ["Noto Sans JP", "Noto Serif JP", "Shippori", "Zen Kaku", "Zen Old", "M PLUS", "Kosugi", "Sawarabi", "Hina Mincho"]):
            jp_fonts.append(f)
        elif any(kw in f for kw in ["sans-serif", "serif", "monospace"]):
            continue  # generic
        else:
            display_fonts.append(f)

    # Headings
    headings = {"h1": [], "h2": [], "h3": []}
    for level in ("h1", "h2", "h3"):
        for h in soup.find_all(level)[:10]:
            text = h.get_text(strip=True)
            if text and len(text) < 200:
                headings[level].append(text)

    # Paragraphs (first 10)
    paragraphs = []
    for p in soup.find_all("p")[:20]:
        text = p.get_text(strip=True)
        if 20 <= len(text) <= 500:
            paragraphs.append(text)
        if len(paragraphs) >= 10:
            break

    manifest = {
        "url": url,
        "slug": slug,
        "title": title,
        "description": meta_desc,
        "colors": top_colors,
        "fonts": {
            "display": display_fonts[:5],
            "jp": jp_fonts[:5],
            "google_fonts_urls": google_fonts_urls,
        },
        "images": deduped_images,
        "copy": {
            "h1": headings["h1"],
            "h2": headings["h2"],
            "h3": headings["h3"],
            "paragraphs": paragraphs,
        },
        "meta": {
            "og_image": og_image,
            "site_name": og_site,
        },
    }

    return manifest


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scrape_reference.py <url> <slug>")
        sys.exit(1)

    url = sys.argv[1]
    slug = sys.argv[2]

    if not url.startswith(("http://", "https://")):
        print("ERROR: URL must start with http:// or https://")
        sys.exit(1)

    try:
        manifest = scrape(url, slug)
    except requests.RequestException as e:
        print(f"ERROR fetching {url}: {e}")
        sys.exit(1)

    out_path = f"/tmp/saiyo_ref_{slug}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Scraped {url}")
    print(f"  Title: {manifest['title']}")
    print(f"  Colors: {len(manifest['colors'])} (top 5: {[c['hex'] for c in manifest['colors'][:5]]})")
    print(f"  Fonts: display={manifest['fonts']['display'][:3]}, jp={manifest['fonts']['jp'][:3]}")
    print(f"  Images: {len(manifest['images'])}")
    print(f"  Headings: h1={len(manifest['copy']['h1'])}, h2={len(manifest['copy']['h2'])}, h3={len(manifest['copy']['h3'])}")
    print(f"\n  Manifest written to: {out_path}")


if __name__ == "__main__":
    main()
