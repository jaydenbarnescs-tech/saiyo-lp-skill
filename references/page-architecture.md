# Page Architecture — saiyo-lp

URL routing convention and multi-page structure for the skill.

## URL pattern

**Index (always)**: `https://nippo-sync.vercel.app/lp/{slug}`

**Sub-pages (optional)**: `https://nippo-sync.vercel.app/lp/{slug}/{sub}`

The `{slug}` is a URL-safe identifier for the client (e.g. `yamaguchi`, `mirai-kogyo`, `tanaka-denki`). Always lowercase, hyphens not underscores, no Japanese characters. Pick the slug with the user during Step 1 intake.

## File layout on disk

Files live under `/home/ubuntu/nippo-sync/public/lp/{slug}/`:

```
public/lp/{slug}/
├── index.html              # The main LP (always)
├── about/                  # Optional about sub-page
│   └── index.html
├── interview/              # Optional interview sub-pages
│   ├── yamada/
│   │   └── index.html
│   ├── suzuki/
│   │   └── index.html
│   └── tanaka/
│       └── index.html
├── recruit/                # Optional opening detail sub-pages
│   ├── manufacturing/
│   │   └── index.html
│   └── sales/
│       └── index.html
└── entry/                  # Optional entry form sub-page
    └── index.html
```

This nesting matches the Next.js static file serving pattern. Every sub-page is `{sub}/index.html` so the URL stays clean.

## Next.js rewrite rules

For the clean URLs to work, `/home/ubuntu/nippo-sync/next.config.ts` must have rewrites that map:
- `/lp/:slug` → `/lp/:slug/index.html`
- `/lp/:slug/:sub` → `/lp/:slug/:sub/index.html`
- `/lp/:slug/:sub/:detail` → `/lp/:slug/:sub/:detail/index.html`

The skill's deploy script checks that these rewrites exist before pushing. If they don't, the skill adds them.

## Default = index only

When the user does not specify sub-pages, build ONLY `index.html`. Do not add sub-pages proactively. This is part of the "never assume" rule.

## Inter-page navigation

If sub-pages exist, the main LP's voice cards, opening cards, etc. should link to their sub-page counterparts instead of anchor links (`#voices` → `/lp/{slug}/interview/yamada`).

Each sub-page must include a "← 戻る" back link at the top and bottom that returns to `/lp/{slug}`.

## Header navigation

The header nav is populated from the selected top-level sections. Example default for a full build:

- 会社を知る → #about
- 強み → #strengths
- 数字で見る → #data
- 先輩の声 → #voices
- 採用職種 → #openings
- 応募する → #entry (or /lp/{slug}/entry if sub-page)

If the user adds sub-pages, optionally add them to the header nav as direct links. Ask per-build.

## Slug conventions

Good slugs: `yamaguchi`, `mirai-kogyo`, `tanaka-denki`, `osaka-lab`
Bad slugs: `Yamaguchi`, `yamaguchi_kensetsu`, `山口`, `yamaguchi.lp`, `lp1`

Check for slug conflicts before building — if `public/lp/{slug}/` already exists, ask the user whether to overwrite or pick a new slug.
