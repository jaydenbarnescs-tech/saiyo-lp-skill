# saiyo-lp-skill

> Claude Code skill for building agency-quality Japanese **採用LP** (recruitment landing pages) in ~30 minutes.

A reusable skill that turns a single-line brief ("make a 採用LP for 山口建設") into a fully-built, deployed recruitment site with AI-generated imagery, a TAF-style paint sweep hero effect, and flexible house-style or vibe-per-client modes.

Built for MGC Inc. (Kyoto) by [@jaydenbarnescs-tech](https://github.com/jaydenbarnescs-tech). Deploys to `nippo-sync.vercel.app/lp/{slug}`.

## What it does

When Claude sees the phrase "**採用LP**" in a conversation, this skill activates and runs a structured 9-step workflow:

1. **Brief intake** — asks for company name, industry, location, openings, target audience, and a reference URL
2. **Mode pick** — house style (consistent yamaguchi base) or vibe per client (synthesize from ref site)
3. **Reference scrape** — extracts colors, fonts, images, and copy from the reference URL via BeautifulSoup
4. **Image triage** — per-image decision: use as-is / customize with AI / replace with AI / skip
5. **Section selection** — propose a section list, user confirms
6. **Sub-pages decision** — always asks, default is none
7. **Build** — composes base.html + selected sections with placeholder replacement
8. **Walk-through or checkpoints** — quick mode (build, don't deploy) or review mode (checkpoint each step)
9. **Deploy** — git add/commit/push to nippo-sync, verify Vercel URL returns 200

## The #1 rule

**Never assume. When in doubt, ASK.** This is encoded as the first rule in `SKILL.md` and is the most important thing the skill does — it refuses to silently pick defaults for anything the user hasn't explicitly confirmed.

## The signature effect

A paint-sweep hero title, reverse-engineered from [TAF Japan's recruitment page](https://www.taf-jp.com/recruitment/). Exact recipe:

- 200% x 100% background-size with a brush texture PNG clipped to text
- 1.1s linear transition on `background-position-x`
- `300% → 0%` slide direction
- IntersectionObserver with `rootMargin: "0% 0px -200px 0px"`, `threshold: 0`, single fire
- Only applied to the hero word — never to section headers

The texture (`assets/text_back.png`) is an original AI-generated asset, not copied from TAF.

## Repo structure

```
saiyo-lp-skill/
├── SKILL.md                          # Workflow brain (read this first)
├── references/
│   ├── design-system.md              # CSS tokens + anime-txt recipe
│   ├── section-library.md            # Every available section
│   ├── page-architecture.md          # URL routing + sub-pages
│   ├── image-pipeline.md             # Scrape → triage → embed
│   ├── reference-scraping.md         # Scraper output schema
│   └── deployment.md                 # Git + Vercel deploy flow
├── templates/
│   ├── base.html                     # Skeleton with CSS + JS + placeholders
│   └── sections/                     # 24 section + fragment templates
├── assets/
│   └── text_back.png                 # 3200×100 brush sweep texture
└── scripts/
    ├── scrape_reference.py           # BeautifulSoup ref scraper
    ├── generate_lp.py                # Orchestrator (stdlib only)
    ├── deploy.py                     # Git add/commit/push/verify
    ├── example-yamaguchi.json        # Reference config
    └── README.md                     # Script usage
```

## Installation

### As a Claude Code / Claude.ai skill

```bash
# Option 1: clone into your skills directory
git clone https://github.com/jaydenbarnescs-tech/saiyo-lp-skill.git ~/.claude/skills/saiyo-lp

# Option 2: via skills CLI (if installed)
npx skills add https://github.com/jaydenbarnescs-tech/saiyo-lp-skill
```

Then in a new Claude conversation, say "**作って 採用LP for [company name]**" and the skill activates.

### As a standalone CLI

The scripts work without Claude too:

```bash
# Scrape a reference
python3 scripts/scrape_reference.py https://www.taf-jp.com/recruitment/ yamaguchi

# Generate from config
python3 scripts/generate_lp.py scripts/example-yamaguchi.json

# Deploy
python3 scripts/deploy.py yamaguchi --company "株式会社山口建設"
```

Dependencies: Python 3.8+, `beautifulsoup4`, `requests`. All scripts otherwise use stdlib only.

## Testing

The skill is smoke-tested by rebuilding the original yamaguchi LP through the pipeline:

```bash
python3 scripts/generate_lp.py scripts/example-yamaguchi.json
# Writes to /home/ubuntu/nippo-sync/public/lp/yamaguchi/index.html
# Verifies: 0 unreplaced placeholders, all sections present, same structural signature as manual build
```

## Configuration schema

A config JSON has three top-level keys: `brand`, `page`, `sections`. See `scripts/example-yamaguchi.json` for a full working example.

Sections are a list of `{ "type": "hero" | "about" | "strengths" | "data" | "voices" | "openings" | "welfare" | "message" | "faq" | "gallery" | "cta" | "map" | "footer", "data": { ... } }`. Repeating sections like `strengths` and `voices` take a `cards` or `items` array in their data block.

## License

MIT. Use freely. Attribution appreciated but not required.
