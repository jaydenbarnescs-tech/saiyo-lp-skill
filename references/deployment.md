# Deployment — saiyo-lp

How the skill deploys LPs to Vercel.

## The target

- **Project**: `nippo-sync` on Vercel
- **Team**: `team_InumbXmdUdRp3WpMs47TFd8s`
- **Project ID**: `prj_le2vOYHWk48qXpSiVzaMGIzDs2Dc`
- **Repo**: `jaydenbarnescs-tech/nippo-sync` (NOT `jaydenbarnes-cs` — that's wrong)
- **Branch**: `main` (auto-deploys on push)
- **Public URL**: `https://nippo-sync.vercel.app/lp/{slug}`

This is temporary — once 山口 pays, the plan is to move to 松尾's Vercel account. Don't bring that up proactively; wait for Jayden to mention it.

## The deploy flow

`scripts/deploy.py {slug}` does:

1. `cd /home/ubuntu/nippo-sync`
2. Check that `public/lp/{slug}/index.html` exists locally
3. Check that `next.config.ts` has the `/lp/:slug` rewrite rules (add them if missing, commit separately)
4. `git add public/lp/{slug}/`
5. `git commit -m "feat(lp): {slug} — {company name} 採用LP"`
6. `git push origin main`
7. Wait ~30s, then `curl -I https://nippo-sync.vercel.app/lp/{slug}` to verify 200
8. Return the live URL

## Git gotchas

- `.gitignore` may exclude certain paths. If `git add public/lp/{slug}/` fails to stage anything, use `git add -f public/lp/{slug}/`.
- Don't commit API keys or `.env` files. The deploy script never touches those.
- Don't push to branches other than `main`. Vercel only auto-deploys main.
- Don't force-push. Ever.

## Next.js rewrites

The `next.config.ts` needs these rewrites for clean URLs:

```typescript
async rewrites() {
  return [
    { source: '/lp/:slug', destination: '/lp/:slug/index.html' },
    { source: '/lp/:slug/:sub', destination: '/lp/:slug/:sub/index.html' },
    { source: '/lp/:slug/:sub/:detail', destination: '/lp/:slug/:sub/:detail/index.html' },
    // ...keep any existing rewrites like the yamaguchi-lp-example1 one
  ];
}
```

Add these if they're not already present. Don't remove existing rewrites.

## Verification

After push, always verify:

1. `curl -I https://nippo-sync.vercel.app/lp/{slug}` → expect 200
2. Visual check — tell the user the URL and ask them to load it and confirm it renders.

If the URL returns 404:
- Vercel may still be building — wait 30s more and retry
- Check `next.config.ts` rewrites are in place
- Check the file was actually committed: `git log -1 --stat`

## Quick mode never deploys

Quick mode builds locally under `public/lp/{slug}/` but does NOT call `deploy.py`. It shows the user the local file path and a preview URL like `file:///home/ubuntu/nippo-sync/public/lp/{slug}/index.html` (or they can open via `cat | less`). User must explicitly say "deploy it" before the skill runs the deploy flow.

## Review mode checkpoints

Even in review mode, the final deploy step requires explicit user confirmation. The checkpoint sequence is:

1. Design tokens approved → proceed to section generation
2. First section built → show HTML, proceed to other sections
3. All sections built → show full local preview, ask to deploy
4. User says deploy → run deploy.py

## Never touch other projects

The VM also hosts services for 松尾's projects. NEVER touch these:
- `mgc-connector-hub.service` (port 8443)
- `line-crm.service` (port 3002)
- `n8n-koko` (port 5679)
- `/home/ubuntu/mgc-connector-hub/`
- `/home/ubuntu/nippo-sync-koko/`
- `/home/ubuntu/line-harness-oss/`

`/home/ubuntu/nippo-sync/` is Jayden's and safe to write to.
