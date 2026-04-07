# Scripts — saiyo-lp

Three Python scripts compose the runtime of the skill:

## `scrape_reference.py`

Scrapes a reference URL and writes a JSON manifest to `/tmp/saiyo_ref_{slug}.json`.

```bash
python3 scrape_reference.py https://example.com/recruit yamaguchi
```

Outputs:
- Title, description, og:image
- Ranked color palette (top 12)
- Font stack (display + JP)
- All image URLs with alt text and context guesses
- H1/H2/H3 headings and paragraph snippets

Dependencies: `requests`, `beautifulsoup4`

## `generate_lp.py`

Takes a JSON config and composes a full LP, writing to `/home/ubuntu/nippo-sync/public/lp/{slug}/index.html` and any sub-pages.

```bash
python3 generate_lp.py /path/to/config.json
```

Config schema: see `scripts/example-config.json`.

Sections loaded from `templates/sections/`. Base HTML loaded from `templates/base.html`. Placeholder replacement is simple `{{KEY}}` regex.

Dependencies: stdlib only.

## `deploy.py`

Commits and pushes the generated LP to `nippo-sync` main branch, then verifies the Vercel URL is live.

```bash
python3 deploy.py yamaguchi --company "株式会社山口建設"
```

Always prompts for confirmation unless `--yes` is passed. Verifies by polling the Vercel URL until it returns 200 (60s timeout).

Dependencies: stdlib only + a working git remote on `/home/ubuntu/nippo-sync/`.

## Typical workflow

```bash
# Step 1: scrape reference
python3 scrape_reference.py https://www.taf-jp.com/recruitment/ yamaguchi

# Step 2 (manual): review /tmp/saiyo_ref_yamaguchi.json, decide per-image
#                  triage, draft a config.json based on the manifest

# Step 3: generate
python3 generate_lp.py /tmp/yamaguchi-config.json

# Step 4 (manual): review /home/ubuntu/nippo-sync/public/lp/yamaguchi/index.html
#                  in a browser, check it looks right

# Step 5: deploy
python3 deploy.py yamaguchi --company "株式会社山口建設"
```

In quick mode, steps 1-4 happen but step 5 waits for explicit user confirmation. In review mode, Claude pauses after each of steps 1, 2, 3, 4 for user approval.
