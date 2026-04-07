#!/usr/bin/env python3
"""
generate_lp.py — saiyo-lp skill orchestrator.

Takes a JSON config and composes a full LP by loading base.html + section
templates + fragment templates, applying placeholder replacements, and writing
the output to /home/ubuntu/nippo-sync/public/lp/{slug}/index.html.

Also handles sub-pages (interview, opening-detail, about, entry).

Usage:
    python3 generate_lp.py <config.json>

Config schema: see the saiyo-lp SKILL.md and example configs in scripts/examples/.

No external dependencies — stdlib only (json, pathlib, re, sys, datetime).
"""

import json
import re
import sys
import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"
SECTIONS = TEMPLATES / "sections"
DEPLOY_ROOT = Path("/home/ubuntu/nippo-sync/public/lp")

# Repeating section types: (section_template, fragment_template, data_key)
REPEATING = {
    "strengths": ("strengths.html", "strengths-card.html", "cards", "STRENGTH_CARDS"),
    "data":      ("data.html",      "data-pill.html",      "pills", "DATA_PILLS"),
    "voices":    ("voices.html",    "voice-card.html",     "cards", "VOICE_CARDS"),
    "openings":  ("openings.html",  "opening-card.html",   "cards", "OPENING_CARDS"),
    "welfare":   ("welfare.html",   "welfare-item.html",   "items", "WELFARE_ITEMS"),
    "faq":       ("faq.html",       "faq-item.html",       "items", "FAQ_ITEMS"),
    "gallery":   ("gallery.html",   "gallery-item.html",   "items", "GALLERY_ITEMS"),
}

# Simple section types: (template_file,)
SIMPLE = {
    "hero":    "hero.html",
    "about":   "about.html",
    "message": "message.html",
    "cta":     "cta.html",
    "map":     "map.html",
    "footer":  "footer.html",
}

# Default header nav map by section id
DEFAULT_NAV = {
    "about":    ("会社を知る", "#about"),
    "strengths":("強み",       "#strengths"),
    "data":     ("数字で見る", "#data"),
    "voices":   ("先輩の声",   "#voices"),
    "openings": ("採用職種",   "#openings"),
    "welfare":  ("待遇",       "#welfare"),
    "message":  ("メッセージ", "#message"),
    "faq":      ("FAQ",        "#faq"),
    "gallery":  ("ギャラリー", "#gallery"),
}


def load_template(name):
    path = SECTIONS / name if not name.endswith(".html") else SECTIONS / name
    if not name.endswith(".html"):
        path = SECTIONS / f"{name}.html"
    return path.read_text(encoding="utf-8")


def load_base():
    return (TEMPLATES / "base.html").read_text(encoding="utf-8")


def fill(template: str, data: dict) -> str:
    """Replace {{KEY}} placeholders with values from data dict.

    Keys in the template are uppercase by convention. Values are strings.
    Missing keys are left alone (for the generator to catch in a lint pass).
    """
    def repl(match):
        key = match.group(1).strip()
        if key in data:
            return str(data[key])
        # Try lowercase
        if key.lower() in data:
            return str(data[key.lower()])
        return match.group(0)  # leave unreplaced

    return re.sub(r"\{\{\s*([A-Z0-9_]+)\s*\}\}", repl, template)


def build_repeating_section(section_type: str, data: dict) -> str:
    """Build a repeating section like strengths/voices/openings."""
    section_tpl_name, fragment_tpl_name, items_key, placeholder = REPEATING[section_type]
    section_tpl = load_template(section_tpl_name)
    fragment_tpl = load_template(fragment_tpl_name)

    items = data.get(items_key, [])
    fragments = []
    for i, item in enumerate(items, start=1):
        # Build placeholder dict for this fragment
        fragment_data = {}
        for k, v in item.items():
            fragment_data[k.upper()] = v
        # Special: strengths cards need a zero-padded number
        if section_type == "strengths":
            fragment_data.setdefault("NUM", f"{i:02d}")
        rendered = fill(fragment_tpl, fragment_data)
        fragments.append(rendered)

    # Now fill the section wrapper
    wrapper_data = {k.upper(): v for k, v in data.items() if k != items_key}
    wrapper_data[placeholder] = "\n".join(fragments)
    # Make subtitle field names consistent (each section has its own subtitle var)
    subtitle_key = f"{section_type.upper()}_SUBTITLE"
    if "SUBTITLE" in wrapper_data:
        wrapper_data[subtitle_key] = wrapper_data["SUBTITLE"]
    return fill(section_tpl, wrapper_data)


def build_simple_section(section_type: str, data: dict) -> str:
    """Build a non-repeating section like hero/about/cta."""
    tpl = load_template(SIMPLE[section_type])
    section_data = {k.upper(): v for k, v in data.items()}
    return fill(tpl, section_data)


def build_section(section: dict) -> str:
    stype = section["type"]
    sdata = section.get("data", {})
    if stype in REPEATING:
        return build_repeating_section(stype, sdata)
    elif stype in SIMPLE:
        return build_simple_section(stype, sdata)
    else:
        raise ValueError(f"Unknown section type: {stype}")


def build_header_nav(sections: list, include_entry: bool = True) -> tuple:
    """Build the header nav HTML from the section list."""
    nav_items = []
    mobile_items = []
    for s in sections:
        stype = s["type"]
        if stype in DEFAULT_NAV:
            label, href = DEFAULT_NAV[stype]
            nav_items.append(f'<a href="{href}">{label}</a>')
            mobile_items.append(f'<a href="{href}">{label}</a>')
    if include_entry:
        nav_items.append('<a href="#entry" class="hdr-cta">応募する</a>')
        mobile_items.append('<a href="#entry">応募する</a>')
    return ("\n    ".join(nav_items), "\n  ".join(mobile_items))


def generate_index(config: dict) -> str:
    """Generate the index HTML from a config dict."""
    base = load_base()
    sections = config.get("sections", [])

    # Build all sections
    section_htmls = [build_section(s) for s in sections]
    sections_inject = "\n\n".join(section_htmls)

    # Build header nav
    header_nav, mobile_nav = build_header_nav(sections)

    # Global placeholder dict
    brand = config.get("brand", {})
    page = config.get("page", {})
    colors = brand.get("colors", {})
    fonts = brand.get("fonts", {})

    global_data = {
        "PAGE_TITLE":          page.get("title", "採用情報"),
        "META_DESCRIPTION":    page.get("meta_description", ""),
        "GOOGLE_FONTS_URL":    brand.get("google_fonts_url",
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Noto+Sans+JP:wght@400;500;700;900&family=Outfit:wght@600;800;900&display=swap"),
        "COLOR_C1":            colors.get("c1", "#1B2B5A"),
        "COLOR_C2":            colors.get("c2", "#E85D3A"),
        "COLOR_C3":            colors.get("c3", "#f59e0b"),
        "COLOR_C2_DARK":       colors.get("c2_dark", "#c94a2b"),
        "FONT_EN":             fonts.get("en", '"Outfit",sans-serif'),
        "FONT_JP":             fonts.get("jp", '"Noto Sans JP",sans-serif'),
        "LOGO_LETTER":         brand.get("logo_letter", "M"),
        "COMPANY_NAME_JP":     brand.get("company_name_jp", ""),
        "HEADER_NAV_ITEMS":    header_nav,
        "MOBILE_NAV_ITEMS":    mobile_nav,
        "SECTIONS_INJECT":     sections_inject,
    }

    # Also pull HERO_IMAGE_URL from the hero section (base.html needs it in CSS)
    for s in sections:
        if s["type"] == "hero":
            global_data["HERO_IMAGE_URL"] = s.get("data", {}).get("hero_image_url", "")
            break

    return fill(base, global_data)


def generate_sub_page(sub: dict, config: dict) -> str:
    """Generate a sub-page HTML. A sub-page reuses base.html but with a single
    sub-page section injected and simplified nav.
    """
    base = load_base()

    # Sub-page uses its own section template, treated as simple
    sub_type = sub["type"]  # interview-detail, opening-detail, about-detail, entry
    tpl_name = f"{sub_type}.html"
    sub_tpl = load_template(tpl_name)
    sub_data_full = sub.get("data", {})

    # For interview-detail with Q&A blocks, pre-build the Q&A blocks HTML
    if sub_type == "interview-detail" and "qa_pairs" in sub_data_full:
        qa_tpl = load_template("interview-qa-block.html")
        blocks = []
        for pair in sub_data_full["qa_pairs"]:
            blocks.append(fill(qa_tpl, {"Q": pair.get("q", ""), "A": pair.get("a", "")}))
        sub_data_full["qa_blocks"] = "\n".join(blocks)

    # For opening-detail with list fields, build <li> items
    if sub_type == "opening-detail":
        for key in ("responsibilities", "requirements", "process"):
            if key in sub_data_full and isinstance(sub_data_full[key], list):
                items = "\n".join(f"      <li>{x}</li>" for x in sub_data_full[key])
                sub_data_full[f"{key}_list"] = items
                sub_data_full[f"{key}_steps"] = items  # alias

    # For entry sub-page, build position <option> tags
    if sub_type == "entry" and "positions" in sub_data_full:
        options = "\n".join(f'          <option value="{p}">{p}</option>' for p in sub_data_full["positions"])
        sub_data_full["position_options"] = options

    section_data = {k.upper(): v for k, v in sub_data_full.items()}
    section_data["PARENT_URL"] = f"/lp/{config['slug']}"
    sub_html = fill(sub_tpl, section_data)

    # Build simplified nav for sub-page
    brand = config.get("brand", {})
    page = config.get("page", {})
    colors = brand.get("colors", {})
    fonts = brand.get("fonts", {})

    nav_items = [
        f'<a href="/lp/{config["slug"]}">採用トップ</a>',
        '<a href="#entry" class="hdr-cta">応募する</a>',
    ]
    mobile_items = [
        f'<a href="/lp/{config["slug"]}">採用トップ</a>',
        '<a href="#entry">応募する</a>',
    ]

    global_data = {
        "PAGE_TITLE":          f"{sub.get('title', sub_type)}｜{brand.get('company_name_jp', '')}",
        "META_DESCRIPTION":    page.get("meta_description", ""),
        "GOOGLE_FONTS_URL":    brand.get("google_fonts_url",
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Noto+Sans+JP:wght@400;500;700;900&family=Outfit:wght@600;800;900&display=swap"),
        "COLOR_C1":            colors.get("c1", "#1B2B5A"),
        "COLOR_C2":            colors.get("c2", "#E85D3A"),
        "COLOR_C3":            colors.get("c3", "#f59e0b"),
        "COLOR_C2_DARK":       colors.get("c2_dark", "#c94a2b"),
        "FONT_EN":             fonts.get("en", '"Outfit",sans-serif'),
        "FONT_JP":             fonts.get("jp", '"Noto Sans JP",sans-serif'),
        "LOGO_LETTER":         brand.get("logo_letter", "M"),
        "COMPANY_NAME_JP":     brand.get("company_name_jp", ""),
        "HEADER_NAV_ITEMS":    "\n    ".join(nav_items),
        "MOBILE_NAV_ITEMS":    "\n  ".join(mobile_items),
        "SECTIONS_INJECT":     sub_html,
        "HERO_IMAGE_URL":      sub_data_full.get("hero_image_url", ""),
    }

    return fill(base, global_data)


def write_output(config: dict):
    slug = config["slug"]
    out_dir = DEPLOY_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Main index
    index_html = generate_index(config)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")
    print(f"✓ Wrote {out_dir / 'index.html'} ({len(index_html)} bytes)")

    # Sub-pages
    for sub in config.get("sub_pages", []):
        sub_slug = sub.get("slug", sub["type"])
        sub_path_parts = sub.get("path", [sub_slug])
        sub_dir = out_dir
        for part in sub_path_parts:
            sub_dir = sub_dir / part
        sub_dir.mkdir(parents=True, exist_ok=True)
        sub_html = generate_sub_page(sub, config)
        (sub_dir / "index.html").write_text(sub_html, encoding="utf-8")
        print(f"✓ Wrote {sub_dir / 'index.html'} ({len(sub_html)} bytes)")


def lint(html: str) -> list:
    """Return a list of unreplaced {{PLACEHOLDER}} patterns found in the output."""
    unfilled = re.findall(r"\{\{\s*[A-Z0-9_]+\s*\}\}", html)
    return unfilled


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_lp.py <config.json>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    config = json.loads(config_path.read_text(encoding="utf-8"))

    if "slug" not in config:
        print("ERROR: config must have a 'slug' field")
        sys.exit(1)

    print(f"Building LP for slug='{config['slug']}'...")
    write_output(config)

    # Lint the output
    index_html = (DEPLOY_ROOT / config["slug"] / "index.html").read_text(encoding="utf-8")
    unfilled = lint(index_html)
    if unfilled:
        print(f"⚠  {len(unfilled)} unreplaced placeholders found:")
        for u in sorted(set(unfilled)):
            print(f"   {u}")
    else:
        print("✓ No unreplaced placeholders")

    print(f"\nLocal file: {DEPLOY_ROOT / config['slug'] / 'index.html'}")
    print(f"After deploy: https://nippo-sync.vercel.app/lp/{config['slug']}")


if __name__ == "__main__":
    main()
