---
name: saiyo-lp
description: Use this skill whenever the user wants to build a 採用LP (Japanese recruitment landing page) for a client. Triggers on the keyword "採用LP" specifically. Guides Claude through a structured intake + reference scraping + image triage + build + deploy workflow, producing agency-quality custom sites hosted on nippo-sync.vercel.app/lp/{slug}. Supports both a consistent "house style" base (derived from the yamaguchi/MGC brand) and a "vibe per client" mode that synthesizes design from a reference site. Always checkpoints with the user before assuming anything.
---

# saiyo-lp — MGC Recruitment Landing Page Skill

## THE ONE RULE (read this first, always)

**NEVER ASSUME. When in doubt, ASK. Do not continue building until the user has confirmed the specific detail you're unsure about.**

This rule overrides every other instinct. If you think "I could just pick X as a reasonable default" — stop. Ask instead. The user (Jayden) has explicitly said this is the most important rule of this skill. Violating it will ship a site the client hates and waste everyone's time.

Concrete examples of when to ASK instead of assuming:

- Unsure which sections to include? → Ask.
- Unsure about brand colors? → Ask, or scrape from the reference site and confirm the extracted palette.
- Unsure whether to use a scraped image as-is or replace it? → Ask, per image.
- Unsure about sub-pages? → Ask. Default is NONE until the user says otherwise.
- Unsure about Japanese copy tone? → Ask for an example, or draft and get approval.
- Unsure about job titles, employee personas, data points? → Ask.
- Unsure about house vs vibe mode? → Ask.
- Unsure whether to deploy now? → Ask (quick mode never auto-deploys).

The only things you DON'T need to ask about are things that are explicitly locked-in in this SKILL.md (trigger keyword, URL pattern, deploy target, the paint sweep effect recipe). Everything else — ask.

---

## Trigger

Only activate this skill when the user says **"採用LP"**. Do not trigger on related but distinct phrases like "LP" (could be anything), "ランディングページ" (too broad), "recruitment site", "採用サイト" — unless the user explicitly says 採用LP. If in doubt, ask.

---

## What this skill produces

A production-ready Japanese recruitment landing page, hosted at:

- **Index**: `https://nippo-sync.vercel.app/lp/{slug}`
- **Sub-pages**: `https://nippo-sync.vercel.app/lp/{slug}/{sub}` (e.g. `/lp/yamaguchi/interview/yamada`, `/lp/yamaguchi/about`)

Quality target: agency-level custom design. We are competing with SHIRAHA, iRec, 採用係長 — we must beat them on visual quality while matching their speed. The MGC differentiator is the TAF-style paint-sweep hero effect, AI-generated or AI-customized imagery, and a custom-per-client feel that template tools can't match.

---

## The workflow (step by step)

Follow these steps in order. After each step that involves the user's input, STOP and wait for confirmation before moving on.

### Step 1 — Brief intake (ALWAYS)

Ask the user for the following. Don't guess any of these:

1. **Company name** (JP) and romaji/EN slug (for the URL)
2. **Industry** / what the company does
3. **Location** (for the map and footer)
4. **Reference site URL** (mandatory — always ask, even in house mode)
5. **What they want to emphasize** (craftsmanship? innovation? work-life balance? youth?)
6. **Openings** they're recruiting for (list of positions)
7. **Any assets the user already has** — logo, brand colors, employee photos, company description, existing website
8. **Target audience** (new grads? mid-career? specific industry background?)

Present this as a simple bulleted list of questions. Let the user answer in one message, then confirm you got it right before proceeding.

### Step 2 — Mode pick

Ask: **"House mode or vibe mode?"**

- **House mode**: use the yamaguchi base design (navy + coral, Outfit/Inter/Noto Sans JP stack, rounded-12px, the specific section layouts). Good for fast builds where the client doesn't care about strong differentiation. Still uses the reference site for imagery and copy tone.
- **Vibe mode**: synthesize a new design language from the reference site. Scrape its colors, fonts, layout patterns, imagery. Build a variant that reflects the client's industry. Takes ~20 extra minutes but each site feels distinct.

Ask the user which one, and if they say "I don't know", explain the trade-off and ask again.

### Step 3 — Reference scrape

Run `scripts/scrape_reference.py {url}` against the reference URL. This produces a JSON manifest at `/tmp/saiyo_ref_{slug}.json` containing:

- All `<img>` URLs with alt text (absolute URLs)
- CSS color palette (extracted from `<style>` tags and linked stylesheets, ranked by frequency)
- Google Fonts references
- H1/H2/H3 copy + first N paragraph snippets (for tone analysis)
- Section structure hints (how they organize their page)

If the user's in vibe mode, use the scraped palette + fonts + layout patterns as the basis for the new design language. In house mode, just use the images and copy snippets and ignore the visual design.

Show the user the scraped color palette and font stack before moving on. Confirm: "Look right? Any colors I should add or drop?"

### Step 4 — Image triage (ALWAYS per-image)

For each image in the scraped manifest, show the user the image URL and ask what to do:

- **use as-is** — embed the original URL directly into the LP
- **customize with AI** — pass the image URL to Nano Banana's image-editing mode with a specific tweak (e.g. "remove the logo watermark", "change the lighting to morning golden hour", "make the people Japanese"). Ask the user what change they want.
- **replace with AI** — generate a fresh image from scratch using Nano Banana with a prompt you draft and show them first for approval.
- **skip** — don't use this image at all.

Default presumption: **use as-is** for hero/team/workplace shots, **replace with AI** for obviously-AI-placeholder images or broken links. But ALWAYS ask per image — never auto-decide.

See `references/image-pipeline.md` for the full image workflow including prompt templates.

### Step 5 — Section selection

Based on the reference site's structure and the client brief, propose a section list. Available sections are documented in `references/section-library.md`. Default candidates:

- hero (always)
- about / company
- strengths (3-6 cards)
- data (stats pills)
- voices (employee interviews, 1-N cards)
- openings (job postings, 1-N cards)
- welfare (benefits list)
- message (from the president/CEO)
- faq
- gallery (optional, for photo-heavy brands)
- cta (always)
- map + footer (always)

Propose your section list as a numbered list. Ask: "OK with these, or want to add/remove anything?" Wait for explicit confirmation.

### Step 6 — Sub-pages decision (ALWAYS ASK — default is NONE)

Ask: **"Any sub-pages?"**

Options you can offer:

- **None** (default — just the one-page LP)
- **Interview details** — expanded sub-page per employee in the voices section (`/lp/{slug}/interview/{name}`)
- **Opening details** — expanded sub-page per job opening with full responsibilities, requirements, interview process (`/lp/{slug}/recruit/{position}`)
- **About page** — full company history/mission sub-page (`/lp/{slug}/about`)
- **Entry form** — dedicated application form sub-page (`/lp/{slug}/entry`)
- **News/blog** — company news index (`/lp/{slug}/news`)

If the user says "I don't know", explain each option briefly and ask again. NEVER default to building sub-pages without explicit confirmation. Templates for sub-pages live in `templates/sections/interview-detail.html`, `templates/sections/opening-detail.html`, etc.

### Step 7 — Build

Once all the above is confirmed, run `scripts/generate_lp.py` with the collected config. This script:

1. Loads `templates/base.html`
2. For each selected section, loads `templates/sections/{name}.html`
3. Fills in all `{{PLACEHOLDERS}}` with the collected config
4. Concatenates sections in the requested order
5. Emits the final HTML to `/home/ubuntu/nippo-sync/public/lp/{slug}/index.html`
6. Emits any sub-pages to `/home/ubuntu/nippo-sync/public/lp/{slug}/{sub}/index.html`
7. Downloads/hot-links any externally-scraped images through the proxy upload pipeline
8. Triggers AI image generation for any "customize" or "replace" flagged images
9. Writes a build log to `/tmp/saiyo_build_{slug}.log`

If any step fails or is ambiguous, STOP and ask.

### Step 8 — Walk-through (QUICK mode) or Checkpoints (REVIEW mode)

Ask at the start of the build: **"Quick mode or review mode?"**

- **Quick mode**: after Step 7 completes, STOP. Do NOT auto-deploy. Show the user the local file paths and a preview command. Walk through the sections together. Wait for explicit "deploy it" from the user, then jump to Step 9.
- **Review mode**: checkpoint after EACH major step — after design tokens are picked, after the first section is built, after all sections are built. User approves each checkpoint before moving to the next.

### Step 9 — Deploy (ONLY when the user explicitly says to deploy)

Run `scripts/deploy.py {slug}`. This script:

1. `cd /home/ubuntu/nippo-sync`
2. `git add public/lp/{slug}/`
3. `git commit -m "feat(lp): {slug} — {company name} 採用LP"`
4. `git push origin main`
5. Waits ~30s for the Vercel deploy
6. Returns the live URLs for verification

Verify the URL is live before telling the user "done". Use `curl -I` to check.

---

## Key references (read these as needed)

- **`references/design-system.md`** — all CSS tokens, the anime-txt paint sweep recipe, font stacks, spacing scale
- **`references/section-library.md`** — every section's template, what it's for, required placeholders
- **`references/page-architecture.md`** — URL routing convention, sub-page structure, how multi-page flows work
- **`references/image-pipeline.md`** — how to scrape, customize, generate, and embed images
- **`references/reference-scraping.md`** — what the scraper extracts and how to use the manifest
- **`references/deployment.md`** — git push flow, Vercel rewrite rules, cache busting

---

## Critical constraints (NEVER violate these)

1. **NEVER touch Matsuo's services** — stay away from `mgc-connector-hub.service` (port 8443), `line-crm.service` (port 3002), `n8n-koko` (port 5679), `/home/ubuntu/mgc-connector-hub/`, `/home/ubuntu/nippo-sync-koko/`, `/home/ubuntu/line-harness-oss/`. The `nippo-sync` directory at `/home/ubuntu/nippo-sync/` is OK to write to.
2. **Use `git add -f`** if `.gitignore` blocks a path you need to commit.
3. **The TAF effect is an EXACT recipe** — see `references/design-system.md` section "anime-txt". Don't deviate. Match: 200% 100% bg-size, 1.1s linear transition, 300%→0%, rootMargin "0% 0px -200px 0px", threshold 0, single fire.
4. **The brush texture in `assets/text_back.png` is ORIGINAL AI-generated work** — not copied from TAF. It's safe to use and redistribute.
5. **Hero anime-txt fires automatically on load** (via setTimeout 400ms) because it's above the fold. All other anime-txt elements fire on scroll intersection.
6. **Never hardcode client names in the template files** — always use `{{PLACEHOLDER}}` variables.
7. **Never commit real PII** — if the user provides real employee names/photos, confirm they have consent before pushing to a public Vercel URL.

---

## When you're unsure

Say: "Before I continue, I want to confirm: [specific thing]. Which would you prefer: (a) X, (b) Y, (c) something else?" — and wait.
