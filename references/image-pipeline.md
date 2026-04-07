# Image Pipeline — saiyo-lp

How images flow from the reference site (or client assets) into the final LP.

## The 4 image sources

1. **Client-provided** — real photos the client sent (team, workplace, products). Best quality, most trust. Always prefer these when available.
2. **Scraped from reference site** — images already on the reference URL. Good for inspiration, sometimes usable directly if the reference IS the client's own existing site.
3. **Nano Banana AI-customized** — scraped image + an AI edit (e.g. "change lighting to morning", "remove the logo watermark", "Japanese subjects instead of Western").
4. **Nano Banana AI-generated from scratch** — brand-new image from a text prompt. Good for placeholder team shots, workplace scenes, hero backgrounds when the client has nothing.

## The triage workflow (Step 4 in SKILL.md)

For EVERY image the scraper found, ask the user one of four choices:

1. **✅ use as-is** — download the image from the reference site through the proxy, upload it to the MGC proxy's `/img/` bucket to get a stable URL, embed it in the LP.
2. **🎨 customize with AI** — same download step, but then pass the image to Nano Banana with an edit instruction the user provides. Store the edited result, embed that URL.
3. **🔄 replace with AI** — ignore the scraped image entirely, generate a fresh one. Draft the prompt, show the user for approval, then generate.
4. **❌ skip** — this image is not used. The corresponding LP slot will need a different image (either a client-provided one or an AI-generated one — ask which).

Present the images in batches of 3-5 so the user can review efficiently. Include a short description of where in the LP each image will be used (hero? about? voices.1?).

## Nano Banana prompt templates

Use these as starting points. Always show the user the final prompt before generating.

### Hero background (wide environmental shot)
Aspect ratio: 16:9 or 21:9
Model: nb2 (flash2), resolution 2K
Prompt structure: "Wide environmental shot of [industry setting] at [time of day], [lighting description], [composition cue], Vanity Fair editorial style, [brand mood adjectives]."

Example: "Wide environmental shot of a modern precision machining factory floor at golden hour, warm directional sunlight streaming through tall windows onto rows of CNC equipment, shallow depth of field with workers in the middle distance, Vanity Fair editorial style, clean and aspirational."

### About / team meeting shot
Aspect ratio: 4:3 or 3:2
Prompt: "Candid overhead shot of a Japanese team meeting around a [material] table, 4-6 people in focused discussion, natural window light, muted neutral office background, Kinfolk magazine editorial style."

### Employee portrait (for voices section)
Aspect ratio: 3:4
Prompt: "Professional environmental portrait of a Japanese [gender] [age range] [department] employee, standing in a [workplace context], natural lighting, slight smile, GQ Japan editorial portrait style, shallow depth of field, wearing [uniform or business casual attire]."

Tip: specify Japanese features explicitly if AI defaults to Western faces. Use "Japanese" in the prompt at least twice.

### Job opening shot
Aspect ratio: 4:3
Prompt: "Documentary-style shot of [job activity] in action, focused hands-on-task composition, natural workplace lighting, Forbes Japan feature photography style, muted industrial color palette."

## Banned keywords for Nano Banana

Never use these — they trigger low-quality outputs:
- "4K", "8K", "ultra-detailed", "masterpiece", "photorealistic", "hyperrealistic"
- "beautiful", "stunning", "amazing" (too vague)
- "professional photo" (use magazine anchor instead)

Use instead:
- "Vanity Fair editorial", "National Geographic feature", "Kinfolk magazine", "GQ Japan", "Forbes Japan", "Wallpaper magazine"
- Specific camera cues: "shallow depth of field", "natural directional light", "documentary composition"
- Specific moods: "clean and aspirational", "muted industrial", "warm and human"

## Image hosting

All final images must live on the MGC proxy at `https://mgc-pass-proxy.duckdns.org/img/{filename}`. This is the stable host for AI-generated content.

- Nano Banana generations → the proxy returns a URL in this domain automatically
- Scraped images (use as-is) → download + re-upload via `googleslides_upload_image` or a manual curl to the proxy
- Client-provided images → upload via proxy, get back the public URL

Do NOT embed images from arbitrary third-party URLs — they may go down, change, or violate terms.

## Flagging images that need consent

If a scraped image shows identifiable people from the reference site (NOT the client), flag it and REFUSE to use as-is. Either:
- Replace with AI-generated
- Ask the client for their own photo of a similar scene
- Skip

Never put someone else's employees on the client's recruitment site.
