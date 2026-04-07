# Design System — saiyo-lp

This is the complete design system for the saiyo-lp skill. The yamaguchi LP (株式会社ミライ工業 placeholder) is the canonical reference implementation. When building in house mode, use these tokens verbatim. In vibe mode, swap the color + font tokens per reference-site scrape but keep the spacing scale, component structure, and paint-sweep effect identical.

## CSS Custom Properties (the :root block)

```css
:root {
  /* Colors — swap c1/c2/c3 in vibe mode */
  --c1: #1B2B5A;      /* primary navy */
  --c2: #E85D3A;      /* accent coral */
  --c3: #f59e0b;      /* secondary amber */
  --c2-dark: #c94a2b; /* coral hover state */
  --ct:  #1a1a2e;     /* primary text */
  --ct2: #5a5a72;     /* secondary text */
  --cbg: #FAFBFD;     /* page background */
  --cbg2: #F0F2F7;    /* alt section background */

  /* Fonts — swap --fen + --fjp in vibe mode, keep --fi */
  --fen: "Outfit", sans-serif;       /* EN display */
  --fjp: "Noto Sans JP", sans-serif; /* JP body */
  --fi:  "Inter", sans-serif;        /* UI labels */

  /* Layout */
  --mw: 1200px;   /* max content width */
  --hh: 72px;     /* header height */
  --rad: 12px;    /* border radius (rounded but not pill-y) */
  --sh: 0 8px 32px rgba(27,43,90,.07); /* default card shadow */
}
```

## Font loading (always include in <head>)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Noto+Sans+JP:wght@400;500;700;900&family=Outfit:wght@600;800;900&display=swap" rel="stylesheet">
```

Vibe mode may swap Outfit for any bold display font (Space Grotesk, Archivo, Syne, Bebas Neue, Anton, Noto Serif Display, etc.) and/or swap Noto Sans JP for Zen Kaku Gothic New, M PLUS 1p, Shippori Mincho, etc. Always keep Inter for UI labels.

## The anime-txt paint sweep — EXACT TAF recipe

This is the signature MGC LP effect. Reverse-engineered from https://www.taf-jp.com/recruitment/. Do not modify any of these numbers — they're the exact values TAF uses.

### HTML

```html
<span class="anime-txt">Recruitment</span>
```

Used exclusively on the hero title (and NOT on section headers — section headers use `.sec-en` static styling).

### CSS

```css
.anime-txt {
  font-family: var(--fen);
  font-weight: 900;
  font-size: clamp(3.5rem, 9vw, 7.5rem);
  letter-spacing: -0.025em;
  line-height: .95;
  background-image: url('https://mgc-pass-proxy.duckdns.org/img/text_back.png?v=3');
  background-size: 200% 100%;
  background-repeat: no-repeat;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: rgba(0,0,0,0);
  display: inline-block;
  transition: 1.1s background-position-x;
  transition-timing-function: linear;
  background-position-x: 300%;
  text-transform: uppercase;
}
.anime-txt.anime { background-position-x: 0%; }

/* Hero size override */
.hero-title-wrap .anime-txt {
  font-size: clamp(4rem, 11vw, 9.5rem);
  display: block;
  line-height: .92;
}
```

### JavaScript

```js
// Paint-sweep observer — exact TAF recipe
const ao = new IntersectionObserver(
  (entries) => entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('anime');
      ao.unobserve(e.target);
    }
  }),
  { root: null, rootMargin: "0% 0px -200px 0px", threshold: 0 }
);
document.querySelectorAll('.anime-txt').forEach(e => ao.observe(e));

// Hero fires automatically on load (above the fold)
setTimeout(() => {
  document.querySelectorAll('.hero .anime-txt').forEach(e => e.classList.add('anime'));
}, 400);
```

### Key rules about anime-txt

1. **Single fire** — observer unobserves the element once it's intersected. Never re-triggers.
2. **200% bg-size, not 300%** — image is stretched 2× the text width.
3. **1.1s linear** — not ease, not 1.4s. Exactly 1.1 seconds linear.
4. **300% → 0%** — image slides from off-screen right to left-aligned.
5. **rootMargin "0% 0px -200px 0px"** — fires when the text is 200px above viewport bottom. Not 0.3 threshold, not 0.5. Exactly this.
6. **Hero autoplays** via setTimeout 400ms because IntersectionObserver doesn't fire for elements already in view at page load.
7. **Only use on the hero title.** Section headers use `.sec-en` (static, no animation). Using anime-txt everywhere makes the page feel busy and breaks the hierarchy.

## Section header — static (.sec-en)

```css
.sec-head { margin-bottom: 70px; }
.sec-en {
  font-family: var(--fen);
  font-weight: 900;
  font-size: clamp(2.5rem, 5.5vw, 4.5rem);
  letter-spacing: -.02em;
  line-height: 1;
  color: var(--c1);
  display: block;
  margin-bottom: 14px;
  text-transform: uppercase;
}
.sec-head .jp-sub {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c1);
  letter-spacing: .08em;
  display: flex;
  align-items: center;
  gap: 14px;
}
.sec-head .jp-sub::before {
  content: "";
  width: 32px;
  height: 2px;
  background: var(--c2);
}
```

## Spacing scale

- Section vertical padding: `140px 0` desktop, `80px 0` mobile
- Section header margin-bottom: `70px` desktop, `50px` mobile
- Card padding: `36px 28px` or `24px 28px`
- Grid gaps: `24px` (tight), `28px`, `32px`, `60px` (about-grid)
- Wrap padding: `0 32px`

## The brush texture

Located at `assets/text_back.png` (3200×100 RGBA PNG). Originally generated via Gemini Nano Banana 2, padded left with 800px black so the final resting state (background-position-x: 0%) shows entirely dark. Published at `https://mgc-pass-proxy.duckdns.org/img/text_back.png?v=3`.

**This is an original AI-generated asset, not copied from TAF.** Safe to use and redistribute.

## Buttons

```css
.btn-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 40px;
  background: var(--c2);
  color: #fff;
  font-size: .95rem;
  font-weight: 700;
  border-radius: var(--rad);
  letter-spacing: .06em;
  transition: .25s;
  cursor: pointer;
  border: none;
}
.btn-main:hover {
  background: var(--c2-dark);
  transform: translateY(-2px);
}

.btn-ghost {
  display: inline-block;
  padding: 10px 28px;
  border: 1.5px solid var(--c1);
  color: var(--c1);
  border-radius: var(--rad);
  font-size: .88rem;
  font-weight: 600;
}
.btn-ghost:hover {
  background: var(--c1);
  color: #fff;
}
```

## Responsive breakpoint

Single breakpoint at `max-width: 900px`. No separate tablet styles. On mobile:

- Hide `.hdr-nav`, show `.hamburger`
- Grids collapse to 1 column
- Reduced padding on `.block` (80px 0)
- Voice cards: image on top instead of left
- Data pills: smaller (min-width 160px, val 2.2rem)

## Vibe mode color extraction

When scraping a reference site, use the extracted palette as follows:

1. Most frequent color (excluding white/black/greys) → `--c1`
2. Second most frequent accent → `--c2`
3. Third or derived complementary → `--c3`
4. Generate `--c2-dark` by darkening `--c2` by ~15% (HSL L − 15)
5. Keep text colors `--ct` (#1a1a2e) and `--ct2` (#5a5a72) unless the scraped site uses very distinctive text colors
6. Always show the extracted palette to the user for approval before building
