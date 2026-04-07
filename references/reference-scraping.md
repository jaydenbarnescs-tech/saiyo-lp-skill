# Reference Scraping — saiyo-lp

How to extract design tokens, images, and copy from a reference URL.

## The scraper

`scripts/scrape_reference.py {url} {slug}` extracts:

1. **Images** — all `<img src>` tags (absolute URLs), `<source srcset>` from picture elements, CSS `background-image:` url() references. Includes alt text and a guess at where in the page each one sits (hero? card? footer?).
2. **CSS color palette** — scans inline `<style>` tags and linked stylesheets for hex + rgb + hsl color values. Ranks by frequency. Excludes near-white and near-black. Returns top 8.
3. **Font stack** — extracts `font-family:` declarations + Google Fonts `<link>` references. Returns JP-capable fonts and display fonts separately.
4. **H1/H2/H3 copy** — text content of heading tags, useful for tone analysis.
5. **Section headers** — best-effort detection of repeated structural patterns (header + body paragraphs = section).
6. **Meta info** — `<title>`, meta description, og:image, og:site_name.

Output: JSON manifest at `/tmp/saiyo_ref_{slug}.json`.

## Output schema

```json
{
  "url": "https://example.com/recruit",
  "title": "採用情報 | 株式会社例",
  "description": "...",
  "colors": [
    {"hex": "#1B2B5A", "count": 47, "contexts": ["background", "color"]},
    {"hex": "#E85D3A", "count": 23, "contexts": ["background", "border"]}
  ],
  "fonts": {
    "display": ["Outfit", "Inter"],
    "jp": ["Noto Sans JP"],
    "google_fonts_url": "https://fonts.googleapis.com/css2?family=..."
  },
  "images": [
    {
      "url": "https://example.com/hero.jpg",
      "alt": "メインビジュアル",
      "width_guess": 1920,
      "context_guess": "hero",
      "mime": "image/jpeg"
    }
  ],
  "copy": {
    "h1": ["採用情報"],
    "h2": ["私たちについて", "働く環境"],
    "h3": ["..."],
    "paragraphs": ["...", "..."]
  },
  "meta": {
    "og_image": "https://example.com/og.jpg",
    "site_name": "株式会社例"
  }
}
```

## How Claude uses the manifest

1. **After scraping**, read the manifest JSON and show the user:
   - The extracted color palette as a visual (hex codes + swatches if possible)
   - The font stack
   - A count of images found
   - The page title and description
2. **Ask the user to confirm** the palette looks right. They may say "drop the pink, add a dark green" etc.
3. **In vibe mode**, the confirmed palette becomes the new `--c1`, `--c2`, `--c3` values. The confirmed fonts become `--fen` / `--fjp`.
4. **In both modes**, use the image list as the input to the image triage step (Step 4).
5. **Copy snippets** can be referenced when drafting placeholder copy — "the reference site uses [tone], do you want similar for this client?"

## Edge cases

- **Paywalled or bot-blocked sites**: scraper uses a normal Mozilla user agent. If it fails (403/503), tell the user and ask for an alternative reference or the client's own asset package.
- **JS-rendered sites** (React/Vue/Next without SSR): scraper uses requests + BeautifulSoup, so client-side rendered content won't be visible. In this case, fall back to fetching the og:image + title from meta tags, and ask the user to provide any other assets manually.
- **Very large pages**: limit to first 50 images, top 20 colors, first 20 headings. Enough signal without flooding context.
- **Non-HTTP URLs**: reject. Ask for a valid HTTP(S) URL.

## Never modify the scraper to fetch login-protected content

Don't pass cookies, don't fake auth headers. If the user provides a login-gated site, ask them to export the relevant page as HTML and upload that instead.
