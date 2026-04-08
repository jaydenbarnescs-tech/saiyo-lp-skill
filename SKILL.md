---
name: saiyo-lp
description: >
  Use this skill whenever the user wants to build a 採用LP (Japanese recruitment landing page) for a client. Triggers on the keyword "採用LP" specifically. Guides Claude through a structured intake + reference scraping + image triage + build + deploy workflow, producing agency-quality custom sites hosted on nippo-sync.vercel.app/lp/{slug}. Every LP is born as a full SaaS product: dynamic content from Supabase, per-LP admin dashboard with Google OAuth, auto Google Sheets sync, email notifications on new applications, and a built-in content editor so clients can edit their own LP text and images without touching code. Supports both a consistent "house style" base (derived from the yamaguchi/MGC brand) and a "vibe per client" mode that synthesizes design from a reference site. Always checkpoints with the user before assuming anything.
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

The only things you DON'T need to ask about are things that are explicitly locked-in in this SKILL.md (trigger keyword, URL pattern, deploy target, the paint sweep effect recipe, the Phase 1-5 infrastructure described below). Everything else — ask.

---

## Trigger

Only activate this skill when the user says **"採用LP"**. Do not trigger on related but distinct phrases like "LP" (could be anything), "ランディングページ" (too broad), "recruitment site", "採用サイト" — unless the user explicitly says 採用LP. If in doubt, ask.

---

## What this skill produces

A production-ready Japanese recruitment landing page, hosted at:

- **Index**: `https://nippo-sync.vercel.app/lp/{slug}`
- **Entry form**: `https://nippo-sync.vercel.app/lp/{slug}/entry`
- **Admin dashboard**: `https://nippo-sync.vercel.app/lp/{slug}/admin`
- **Sub-pages** (optional): `https://nippo-sync.vercel.app/lp/{slug}/{sub}`

Quality target: agency-level custom design. We are competing with SHIRAHA, iRec, 採用係長 — we must beat them on visual quality while matching their speed. The MGC differentiator is the TAF-style paint-sweep hero effect, AI-generated or AI-customized imagery, and a custom-per-client feel that template tools can't match.

**Every LP is born as a full SaaS product, not a static page.** When you finish building, the client gets:

1. **A branded recruitment site** with the content you authored
2. **An entry form** that collects applications into Supabase
3. **A private admin dashboard** they access via Google sign-in, with two tabs:
   - **応募管理** — list of applicants, status management, CSV export, member invites
   - **LP編集** — in-browser form editor for all LP text and image URLs, saves directly to production (no git, no code)
4. **A private Google Sheet** auto-created in their Drive, auto-synced on every new application
5. **Email notifications** to all admins on every new application (branded sender, reply-to applicant for one-click response)
6. **The ability to invite colleagues** as co-admins via email — invitees get an invite email and automatic access to the shared sheet

The client never needs to ask Jayden to change a headline, swap an image, or add a job opening after launch. They log in and edit.

---

## The full product lifecycle

### Build phase (Steps 1–7)
Intake → mode pick → reference scrape → image triage → sections → sub-pages → generate HTML + seed `lp_content` row.

### Deploy phase (Steps 8–9)
Review → git push → Vercel deploys → verify URLs live.

### Handoff phase (Step 10)
Send client the admin URL. Client signs in with Google → becomes owner → Sheet auto-created in their Drive.

### Post-launch: applications flow
```
applicant fills /lp/{slug}/entry
   ↓
POST /api/lp-entry
   ↓ (all awaited, not fire-and-forget)
   1. Insert row in lp_entries
   2. Slack DM to Jayden (via proxy /saiyo-entry-notify → n8n)
   3. Email all active admins (via proxy /saiyo-entry-email → n8n SMTP)
      - From: "{company} 採用通知" <jayden.barnes.cs@gmail.com>
      - Reply-To: applicant's email (hit Reply → opens compose to applicant)
   4. Append row to the admin's Google Sheet (via stored OAuth refresh token)
   ↓
Response to applicant: "ご応募ありがとうございます"
```

### Post-launch: client self-edits content
```
admin visits /lp/{slug}/admin → signs in with Google
   ↓
Clicks ✏️ LP編集 tab
   ↓
Edits any of 12 sections (meta, header, hero, about, strengths, data,
    voices, openings, welfare, cta, map, footer) via form fields
   ↓
Clicks 保存 → PUT /api/lp/{slug}/admin/content
   ↓
lp_content row updated
   ↓
/lp/{slug} route handler reads the new content on next request — live instantly
```

### Post-launch: inviting colleagues
```
owner clicks 管理者を招待 in dashboard
   ↓
POST /api/lp/{slug}/admin/invites
   1. Insert lp_admins row with invite_status='pending'
   2. Share the Google Sheet with the invitee via Drive API (using owner's token)
   3. Send invite email via Resend
   ↓
Invitee clicks the email link → /lp/{slug}/admin → signs in
   ↓
Callback recognises them → flips invite_status → 'active'
   ↓
They have full dashboard access + sheet access + notification emails
```

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
9. **Who will be the first admin** — the Google account email of the client contact who will sign in first and claim ownership (they get the auto-created Google Sheet in their Drive)

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

**IMPORTANT**: The editable schema for every LP is defined in `nippo-sync/src/lib/lp-content-types.ts`. The section list you pick should map 1:1 to fields in that schema. Currently the schema covers: meta, header, hero, about, strengths, data, voices, openings, welfare, cta, map_embed_src, footer. Anything outside this list either requires schema extension first OR has to be hardcoded into the static HTML (which the client won't be able to edit).

Propose your section list as a numbered list. Ask: "OK with these, or want to add/remove anything?" Wait for explicit confirmation.

### Step 6 — Sub-pages decision (ALWAYS ASK — default is NONE)

Ask: **"Any sub-pages?"**

Options you can offer:

- **None** (default — just the one-page LP + the auto-included /entry and /admin sub-pages which are ALWAYS present)
- **Interview details** — expanded sub-page per employee in the voices section (`/lp/{slug}/interview/{name}`)
- **Opening details** — expanded sub-page per job opening with full responsibilities, requirements, interview process (`/lp/{slug}/recruit/{position}`)
- **About page** — full company history/mission sub-page (`/lp/{slug}/about`)
- **News/blog** — company news index (`/lp/{slug}/news`)

Note: `/lp/{slug}/entry` (application form) and `/lp/{slug}/admin` (admin dashboard) are ALWAYS created automatically — they're part of the core product, not optional sub-pages. Don't ask about them.

If the user says "I don't know", explain each option briefly and ask again. NEVER default to building sub-pages without explicit confirmation.

### Step 7 — Build (generates HTML + seeds lp_content row)

Once all the above is confirmed, run `scripts/generate_lp.py` with the collected config. This script must produce **two outputs** from the same source config:

1. **An LpContent JSON blob** matching the schema in `nippo-sync/src/lib/lp-content-types.ts`. Write it to `/tmp/saiyo_content_{slug}.json`. This is the source of truth — the admin dashboard edits this same shape.

2. **A static HTML fallback file** at `/home/ubuntu/nippo-sync/public/lp/{slug}/_legacy-index.html.bak` (yes, `.bak` — it's renamed out of the way so the dynamic route wins). This is a safety net in case the DB is ever unreachable — the route handler at `src/app/lp/[slug]/route.ts` reads it from disk if the `lp_content` row is missing.

The script also:

- Downloads/hot-links any externally-scraped images through the proxy upload pipeline
- Triggers AI image generation for any "customize" or "replace" flagged images — uploaded URLs go into the JSON blob
- Writes a build log to `/tmp/saiyo_build_{slug}.log`

If any step fails or is ambiguous, STOP and ask.

### Step 8 — Walk-through (QUICK mode) or Checkpoints (REVIEW mode)

Ask at the start of the build: **"Quick mode or review mode?"**

- **Quick mode**: after Step 7 completes, STOP. Do NOT auto-deploy. Show the user the local JSON file path and a local preview command. Walk through the content together (or suggest they preview by temporarily seeding a dev DB). Wait for explicit "deploy it" from the user, then jump to Step 9.
- **Review mode**: checkpoint after EACH major step — after design tokens are picked, after the first section is built, after all sections are built. User approves each checkpoint before moving to the next.

### Step 9 — Deploy (ONLY when the user explicitly says to deploy)

Deployment has **two parts** — both must succeed for the LP to be fully live:

**Part A — Push the static fallback file to git:**
1. `cd /home/ubuntu/nippo-sync`
2. `git add public/lp/{slug}/`
3. `git commit -m "feat(lp): {slug} — {company name} 採用LP"`
4. `git push origin main`
5. Wait ~30s for the Vercel deploy

**Part B — Seed the lp_content row in Supabase:**
```bash
curl -s -X POST "https://nippo-sync.vercel.app/api/admin/lp-content-upsert?slug={slug}" \
  -H "x-migration-secret: $(cat /tmp/mig_secret.txt)" \
  -H "Content-Type: application/json" \
  --data @/tmp/saiyo_content_{slug}.json
```

Expected response: `{"ok":true,"slug":"{slug}","message":"Content upserted"}`

**Verify:**
```bash
curl -sI "https://nippo-sync.vercel.app/lp/{slug}" | head -2
# HTTP/2 200
curl -s "https://nippo-sync.vercel.app/lp/{slug}" | grep -c "{company name}"
# should be > 0
```

If either part fails, STOP and tell Jayden. Never tell the user "done" until both the public LP URL is serving the new content AND the admin dashboard URL returns 200.

### Step 10 — Handoff to client (NEW)

Once deploy succeeds, send the client:

1. **The public LP URL**: `https://nippo-sync.vercel.app/lp/{slug}`
2. **The entry form**: `https://nippo-sync.vercel.app/lp/{slug}/entry` (linked from the LP's CTA buttons)
3. **The admin dashboard**: `https://nippo-sync.vercel.app/lp/{slug}/admin`

Explain to Jayden to tell the client:
- "Sign in with your company Google account at the admin URL. You'll be the owner."
- "A Google Sheet will auto-create in your Drive with today's date of applications."
- "New applications will be emailed to you, Slacked to Jayden, and appended to the sheet in real-time."
- "To edit any text or image on your LP, click the ✏️ LP編集 tab in the admin dashboard — no code needed."
- "To add co-workers as admins, use the 管理者を招待 button. They'll get an invite email and automatic access to the sheet."

The first Google sign-in claims ownership. Warn Jayden to make sure the right person signs in first — it matters because the Sheet ends up in THEIR Drive.

---

## Architecture reference

All permanent infrastructure facts. Update this section whenever the underlying system changes.

### Supabase tables (project `vrsvfphylajgrnjiewxk`, Tokyo region)

| Table | Purpose | Key columns |
|---|---|---|
| `lp_entries` | Form submissions from `/lp/{slug}/entry` | lp_slug, name, email, phone, position, message, company_jp, status, created_at |
| `lp_admins` | Per-LP admin list, OAuth tokens, roles | lp_slug, email, role (owner/member), invite_status (pending/active), google_refresh_token, google_access_token, google_token_expiry, last_signed_in_at, signin_count |
| `lp_sheet_configs` | Per-LP Google Sheet metadata + sync state | lp_slug, sheet_id, sheet_url, sheet_title, owner_email, last_synced_at, last_sync_status, last_sync_error |
| `lp_content` | Per-LP editable content (JSONB) | lp_slug (pk), content (jsonb), published, updated_at, updated_by |

### API endpoints (nippo-sync, Next.js app router)

| Route | Method | Purpose | Auth |
|---|---|---|---|
| `/api/lp-entry` | POST | Receive form submission, insert + fan out (Slack + email + Sheet) | honeypot + IP rate limit |
| `/api/lp/[slug]/admin/entries` | GET/PATCH | List/update applications | signed-cookie session |
| `/api/lp/[slug]/admin/invites` | GET/POST/DELETE | List/invite/revoke admins | signed-cookie session (owner for POST/DELETE) |
| `/api/lp/[slug]/admin/sync` | POST | Manual sheet re-sync | signed-cookie session |
| `/api/lp/[slug]/admin/signout` | POST | Clear session cookie | signed-cookie session |
| `/api/lp/[slug]/admin/content` | GET/PUT | Load/save LpContent JSONB | signed-cookie session |
| `/api/sheets/connect/[slug]/authorize` | GET | Start Google OAuth flow (claim-or-signin) | none (redirects to Google) |
| `/api/sheets/connect/callback` | GET | OAuth callback, creates session cookie, auto-creates sheet for first-time owners | HMAC state |
| `/api/admin/lp-content-upsert` | POST | One-shot content upsert (skill uses this at deploy time) | x-migration-secret header |
| `/lp/[slug]` | GET (route handler) | Dynamic LP renderer, reads from lp_content or falls back to static HTML | public |
| `/lp/[slug]/entry` | page | Public entry form | public |
| `/lp/[slug]/admin` | page | Admin dashboard (shows ConnectScreen if not signed in, AdminDashboard if signed in) | session-aware |

### Proxy endpoints (on `mgc-pass-proxy.duckdns.org`, served by proxy-core :3010)

| Route | Forwards to | Purpose |
|---|---|---|
| `/saiyo-entry-notify` | n8n `/webhook/send-slack-msg` | Slack DM to Jayden on new application |
| `/saiyo-entry-email` | n8n `/webhook/saiyo-entry-email` | SMTP email to all active admins on new application |

### n8n workflow + SMTP credential

- **Workflow**: `3NRaiENBIOiGhnkw` — "saiyo-lp Notification Email (Phase 4)" — ACTIVE
- **Webhook path**: `saiyo-entry-email`
- **SMTP credential**: `ZoHdEjix1iBa53vZ` (Gmail Workspace SMTP, authenticated as `jayden.barnes.cs@gmail.com`)
- **Display-name override**: `"{company} 採用通知" <jayden.barnes.cs@gmail.com>` — the email part matches auth (Gmail won't rewrite it), recipients see the company brand in inbox preview
- **Reply-To**: the applicant's email → admins hit Reply in their inbox → compose opens pre-addressed to the applicant

### Google OAuth

- **Google Cloud project**: separate from solar-semiotics-491215-e9 (the Influencer Finder project had HTTP redirect URIs blocking consent-screen publishing, so saiyo-lp got its own clean project)
- **OAuth Client ID**: `302503787770-m01scg835se6v3d59eophvni3tor6iap.apps.googleusercontent.com`
- **Consent screen**: **published in production** with non-sensitive scopes only — `drive.file`, `userinfo.email`, `openid`. No Google verification required, no 100-user cap.
- **Legal pages**: `/privacy` and `/terms` on nippo-sync.vercel.app (required for publishing the consent screen)
- **Why no `spreadsheets` scope**: `drive.file` is sufficient because the app is always the creator of the sheet (via `spreadsheets.create`). `drive.file` grants full read/write on app-created files, which covers everything the auto-sync and sharing flows need. Dropping the sensitive scope removes verification requirements.

### Content editor schema

The shape of `lp_content.content` (JSONB) is defined in:
```
nippo-sync/src/lib/lp-content-types.ts
```

Sections: `meta`, `header`, `hero`, `about`, `strengths[]`, `data[]`, `voices[]`, `openings[]`, `welfare[]`, `cta`, `map_embed_src`, `footer`, optional `theme` (primary/accent colors).

The HTML renderer lives at:
```
nippo-sync/src/lib/lp-render.ts
```

XSS-safe via `esc()` and `escBr()` helpers. All CSS preserved from the original yamaguchi template. Generates the full LP HTML from an LpContent object.

The editor UI lives at:
```
nippo-sync/src/app/lp/[slug]/admin/LpContentEditor.tsx
```

Accordion sections, single sticky 保存 button, プレビュー opens `/lp/{slug}` in new tab, dirty state with beforeunload warning, arrays get +追加/削除 buttons, image fields show preview thumbnails from the URL.

### Email: Resend vs n8n SMTP

| Use case | Sender | Why |
|---|---|---|
| **Invite emails** (owner invites a new admin) | Resend `onboarding@resend.dev` with branded display name | The invitee might not have a Gmail account; Resend handles delivery reliably. Trial mode works because the inviter IS the Resend account owner (which is the to-address when inviting yourself; for inviting others, Resend's trial restriction requires a verified domain OR a trial-mode override env var). |
| **New-entry notification emails** (new applicant → all admins) | n8n Gmail SMTP, `"{company} 採用通知" <jayden.barnes.cs@gmail.com>` | Resend's free trial mode ONLY allows sending TO the account-owner email — if the To: list includes anyone else, the ENTIRE send fails with 403. n8n Gmail SMTP has no such restriction. |

Do NOT mix these up. The code paths are separate (`src/lib/email.ts` handles Resend for invites; `/api/lp-entry` POSTs to the proxy for notifications).

---

## Gotchas & Hard-Won Lessons

Every one of these cost an hour+ to discover. Read them before making the same mistake.

### 1. Vercel serverless kills fire-and-forget async

**Symptom**: Code works locally but silently never runs in production. Logs show the API returned successfully but the side effect (sheet sync, email) never happened.

**Cause**: `(async () => { ... })()` IIFEs that aren't awaited get killed the moment the lambda returns its response. The inner `await` never completes because the process is already being torn down.

**Fix**: Always `await` async work inline. Adds ~500ms–1s latency but actually runs. Precedents in git history:
- `b261c5b` — sheet sync was fire-and-forget, wasn't running for real submissions
- `d3ef7e1` — notification email had same bug, found during Phase 4 debugging

**Rule**: In any Vercel Next.js API route, NEVER use `;(async () => {...})().catch(() => {})`. Either `await` it or use `waitUntil` from `@vercel/functions`.

### 2. Gmail SMTP rewrites the From header

**Symptom**: You set `fromEmail: "noreply@mgc-global01.com"` in the n8n Send Email node, but emails arrive showing From `jayden.barnes.cs@gmail.com`. The email Jayden set is demoted to Reply-To.

**Cause**: `smtp.gmail.com` with app-password auth forces the envelope From to match the authenticated user. It's a Gmail anti-spoofing policy, not a bug.

**Fix**: Use a display-name override where the email part matches the auth:
```
"株式会社ミライ工業 採用通知" <jayden.barnes.cs@gmail.com>
```
Recipients see the company brand in the inbox preview. The personal Gmail is only visible when they expand the From field. This is the approach saiyo-lp uses.

**Alternative**: Configure "Send mail as" in Gmail Settings → Accounts and Import, authorize the other email address, then Gmail allows native sending from it.

### 3. drive.file OAuth scope is per-user-per-app

**Symptom**: Owner claimed the LP, the Google Sheet was created fine, it showed up in their Drive. A few days later they revoked the app in their Google account permissions. Now the sheet still exists in their Drive, but the app can't touch it (Drive API returns 404 on any operation, even though the file is right there).

**Cause**: `drive.file` grants per-user-per-app file authorizations. When the user revokes the app, ALL file authorizations are wiped — the files remain but the app has zero grants on them. Re-signing in gives the app a fresh grant, but the old files are still orphaned from the app's perspective.

**Recovery**: Delete the `lp_admins` + `lp_sheet_configs` rows for that slug, have the owner sign in again — the claim flow creates a fresh sheet that the new grant can access. Entries in `lp_entries` are unaffected.

**One-shot recovery endpoint**: `/api/admin/reset-lp-claim?slug={slug}` (gated by migration secret). Used during Phase 3 debugging.

**Long-term**: auto-detect 404 on the owner's sheet and auto-rebuild. Not yet implemented as of Phase 5.

### 4. Resend free tier trial-mode restriction

**Symptom**: You send an email from `onboarding@resend.dev` to a list of 2 admins. Resend returns HTTP 403 `validation_error`: "You can only send testing emails to your own email address". The ENTIRE send fails — not just the second recipient.

**Cause**: Resend's free trial mode with the default `onboarding@resend.dev` sender only allows TO = the Resend account-owner's email. Any other recipient in the To: list triggers the 403 for the whole request.

**Workarounds**:
- **A** — Verify a custom domain at resend.com/domains (requires DNS access — SPF, DKIM, MX, return-path records)
- **B** — Override the To: list to always use the account-owner email via env var `RESEND_TRIAL_MODE_RECIPIENT` (lossy — all admins get redirected to one mailbox)
- **C** — Bypass Resend entirely for multi-recipient sends — route through n8n + Gmail SMTP instead (what saiyo-lp's Phase 4 does for notification emails)

Resend stays for invite emails in saiyo-lp because invites go TO the account-owner by definition (the owner invites others; the email is addressed to the specific invitee but the trial scope still applies).

### 5. Next.js static files take precedence over dynamic app routes

**Symptom**: You add `/app/lp/[slug]/route.ts` expecting it to dynamically render LPs. Visiting `/lp/yamaguchi` still serves the old content. You check the file, it's right. You redeploy, same result. The dynamic route handler appears never to fire.

**Cause**: If `/public/lp/{slug}/index.html` exists, Vercel's static file handler serves it BEFORE app router's dynamic handler even gets a chance. Same for `/public/lp/{slug}/entry/index.html` overriding any `/app/lp/[slug]/entry/page.tsx`.

**Fix**: Rename the static file to something non-routable (e.g. `_legacy-index.html.bak`) so the dynamic route wins. Keep it in the repo as a safety fallback — the route handler can read it from disk as a fallback for when the DB row is missing (this is what `/app/lp/[slug]/route.ts` does now).

**Precedent**: commit `4645fca` — yamaguchi's static `/public/lp/yamaguchi/index.html` was intercepting the Phase 5 dynamic route until the file was renamed.

**Corollary**: when generating a new LP from this skill, always name the static fallback `_legacy-index.html.bak` from the start. Never name it `index.html` in the public directory — that will silently override your route handler.

### 6. Drive.file can share files with other users (via Drive API permissions)

**Symptom**: Owner claimed the sheet, sheet was private to the owner. When an invitee was added as an admin, they couldn't see the sheet even though the dashboard said they had access.

**Cause**: `drive.file` is per-user — the invitee's OAuth token sees NOTHING, because the sheet wasn't created on behalf of them. The invitee needs explicit share.

**Fix**: When an admin is invited, use the OWNER's drive.file token to call the Drive API `permissions` endpoint and explicitly share the sheet with the invitee's email as a writer. drive.file is sufficient for this because the file was created by the app on behalf of the owner — drive.file grants read/write/share/delete on app-created files.

**Precedent**: commit `895747e` — Phase 3 invite flow was creating the lp_admins row but not sharing the sheet. Invitees could sign in but couldn't see the sheet from the dashboard link.

**Implementation**: `src/lib/sheets.ts` has `shareSheetWithEmail` and `unshareSheetWithEmail` helpers that wrap the Drive API `/files/{id}/permissions` endpoint.

### 7. OAuth consent screen: one sensitive scope taints the whole thing

**Symptom**: Every sign-in shows an "unverified app" warning with a big scary "proceed to unsafe site" bypass. Only 100 users allowed. Can't publish to production without Google verification (weeks of work, demo videos, privacy review).

**Cause**: Using `https://www.googleapis.com/auth/spreadsheets` (or any other sensitive scope) requires Google verification. ONE sensitive scope in the scope list kicks you into the verification track.

**Fix**: Use only non-sensitive scopes. For saiyo-lp that means `drive.file` (not `spreadsheets`), `userinfo.email`, `openid`. `drive.file` is enough because the app is always the creator of any file it touches — you can do `spreadsheets.create`, then `spreadsheets.values.append`, `spreadsheets.batchUpdate`, etc. on app-created files with just `drive.file`.

**Precedent**: commit `d933495` — dropped `spreadsheets` from the scopes, republished consent screen with no verification required.

---

## Key references (read these as needed)

- **`references/design-system.md`** — all CSS tokens, the anime-txt paint sweep recipe, font stacks, spacing scale
- **`references/section-library.md`** — every section's template, what it's for, required placeholders (should match `lp-content-types.ts`)
- **`references/page-architecture.md`** — URL routing convention, sub-page structure, how multi-page flows work
- **`references/image-pipeline.md`** — how to scrape, customize, generate, and embed images
- **`references/reference-scraping.md`** — what the scraper extracts and how to use the manifest
- **`references/deployment.md`** — git push flow, Vercel rewrite rules, cache busting, `lp_content` upsert step

---

## Critical constraints (NEVER violate these)

1. **NEVER touch Matsuo's services** — stay away from `mgc-connector-hub.service` (port 8443), `line-crm.service` (port 3002), `n8n-koko` (port 5679), `/home/ubuntu/mgc-connector-hub/`, `/home/ubuntu/nippo-sync-koko/`, `/home/ubuntu/line-harness-oss/`. The `nippo-sync` directory at `/home/ubuntu/nippo-sync/` is OK to write to.
2. **Use `git add -f`** if `.gitignore` blocks a path you need to commit.
3. **The TAF effect is an EXACT recipe** — see `references/design-system.md` section "anime-txt". Don't deviate. Match: 200% 100% bg-size, 1.1s linear transition, 300%→0%, rootMargin "0% 0px -200px 0px", threshold 0, single fire.
4. **The brush texture in `assets/text_back.png` is ORIGINAL AI-generated work** — not copied from TAF. It's safe to use and redistribute.
5. **Hero anime-txt fires automatically on load** (via setTimeout 400ms) because it's above the fold. All other anime-txt elements fire on scroll intersection.
6. **Never hardcode client names in the template files** — always use `{{PLACEHOLDER}}` variables OR `{content.x}` references for the dynamic renderer.
7. **Never commit real PII** — if the user provides real employee names/photos, confirm they have consent before pushing to a public Vercel URL.
8. **Never name the static fallback `index.html`** in `/public/lp/{slug}/` — it will silently override the dynamic route. Name it `_legacy-index.html.bak`.
9. **Never use the `spreadsheets` OAuth scope** — always use `drive.file` only, along with `userinfo.email` and `openid`. Adding `spreadsheets` kicks you into Google's sensitive scope verification track and disables consent screen publishing.
10. **Never use a fire-and-forget IIFE for async side effects** in any `/api/*` route. Always `await`. The Vercel lambda kills unawaited async the moment it returns.
11. **Never send multi-recipient notification emails via Resend free tier** — the trial mode will reject the whole send. Use n8n SMTP for notifications, keep Resend for invites only.
12. **Never seed content without also pushing the static fallback** — Step 9 has two parts (git push + lp_content upsert). Both must succeed or the LP has no safety net.
13. **Never tell the user "done" after deploy without verifying** — always `curl -sI /lp/{slug}` and check for HTTP 200, then `curl -s /lp/{slug} | grep "{client marker}"` to confirm content is actually rendering.

---

## When you're unsure

Say: "Before I continue, I want to confirm: [specific thing]. Which would you prefer: (a) X, (b) Y, (c) something else?" — and wait.
