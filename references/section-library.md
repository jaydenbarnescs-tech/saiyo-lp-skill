# Section Library — saiyo-lp

Every section is a template in `templates/sections/{name}.html` with placeholders. Always ask the user which sections they want before building.

## Core sections (almost always included)

### `hero.html` — Hero with paint sweep
Full-viewport hero with background image, overlay, eyebrow label, paint-sweep English word, JP subtitle, primary CTA.

Placeholders: HERO_IMAGE_URL, HERO_EYEBROW, HERO_EN_WORD, HERO_JP_HEADLINE, HERO_SUB_COPY, HERO_CTA_LABEL, HERO_CTA_HREF

Notes: Paint sweep fires ONLY here. Don't duplicate anime-txt elsewhere. Always required.

### `about.html` — Company intro (2-column)
Left-image / right-copy layout.

Placeholders: ABOUT_IMAGE_URL, ABOUT_IMAGE_ALT, ABOUT_HEADLINE, ABOUT_PARAGRAPH_1, ABOUT_PARAGRAPH_2, ABOUT_CTA_LABEL, ABOUT_CTA_HREF

### `cta.html` — Final call-to-action
Dark navy gradient band with centered copy and button.

Placeholders: CTA_HEADLINE, CTA_SUB, CTA_BUTTON_LABEL, CTA_BUTTON_HREF

### `map.html` — Google Maps embed
Placeholders: MAP_EMBED_URL

### `footer.html` — Footer
Placeholders: COMPANY_NAME_JP, COMPANY_TAGLINE, COMPANY_ADDRESS_LINE_1, COMPANY_ADDRESS_LINE_2, COMPANY_PHONE, COMPANY_FOUNDED, COMPANY_REPRESENTATIVE, COMPANY_BUSINESS, COMPANY_NAME_EN, YEAR

## Content sections

### `strengths.html` — 3-column numbered cards
Numbered cards with big semi-transparent number, headline, paragraph.

Placeholders: STRENGTHS_SUBTITLE, STRENGTH_N_TITLE, STRENGTH_N_DESC for N=1..3 (extensible to 4 or 6)

### `data.html` — Stat pills row
Horizontal pill badges with count-up animation.

Placeholders: DATA_SUBTITLE, DATA_N_VALUE, DATA_N_LABEL, DATA_N_UNIT for N=1..6

Values must be numeric integers. Good stats: 創業年数, 社員数, 平均年齢, 有給取得率, 年間休日.

### `voices.html` — Employee interviews
Horizontal cards: portrait (left), name/dept/quote (right).

Placeholders per card: VOICE_N_IMAGE, VOICE_N_IMAGE_ALT, VOICE_N_DEPT_EN, VOICE_N_NAME_JP, VOICE_N_META, VOICE_N_QUOTE

Typically 2-4 cards. More = move to grid or sub-page. Real photos preferred — ask client.

### `openings.html` — Job listings (grid)
2-column grid of job cards.

Placeholders per card: OPEN_N_IMAGE, OPEN_N_IMAGE_ALT, OPEN_N_BADGE, OPEN_N_TITLE, OPEN_N_DESC, OPEN_N_HREF

Link to /lp/{slug}/recruit/{slug} if sub-pages enabled, else #entry.

### `welfare.html` — Benefits list
2-column grid of dl/dt/dd items.

Placeholders: WELFARE_SUBTITLE, WELFARE_N_TERM, WELFARE_N_DESC for N=1..8

Standard items: 給与, 賞与, 休日, 保険, 手当, 制度, 勤務時間, 勤務地

## Optional sections

### `message.html` — President/CEO message
Placeholders: MESSAGE_PORTRAIT_URL, MESSAGE_QUOTE_JP, MESSAGE_NAME, MESSAGE_TITLE

### `faq.html` — FAQ accordion
Placeholders: FAQ_N_Q, FAQ_N_A for N=1..8

### `gallery.html` — Photo gallery
6-8 photos in bento grid: GALLERY_N_IMAGE, GALLERY_N_ALT

## Sub-page templates (only if sub-pages enabled)

- `interview-detail.html` → /lp/{slug}/interview/{name} — full Q&A
- `opening-detail.html` → /lp/{slug}/recruit/{position} — full job spec
- `about-detail.html` → /lp/{slug}/about — history, mission, leadership
- `entry.html` → /lp/{slug}/entry — application form

## Header + mobile nav

`header.html` and `mob-nav.html` are NOT sections — they're in `base.html` and always present. Nav items auto-populate from selected sections.
