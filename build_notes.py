#!/usr/bin/env python3
"""
Guild Atelier — Insights: static Notes generator.

Reads simple front-matter + markdown-ish text files from _notes_source/
and generates:
  - /notes/index.html        (the Insights landing page: Hero, From the
                               Workbench, Deeper Work, Closing CTA)
  - /notes/<slug>/index.html (one page per Note, Refined Atelier template)
  - /notes/feed.xml           (RSS feed of active/listed Notes)

Post source format (_notes_source/*.txt):

    title: Students Don't Practice Enough at Home
    date: 2026-06-20
    tag: Practice
    excerpt: A short one-line summary shown on the index row.
    slug: students-dont-practice-enough-at-home
    delisted: true          (optional, defaults to false)
    ---
    Body text goes here. Blank lines become paragraph breaks.

    Supports **bold**, _italic_, and [link text](https://example.com).
    Lines starting with "•" become a bulleted list.

A delisted post still gets its own page and keeps its URL working, but
is left out of the Insights index and the RSS feed. Use this instead of
deleting a post's source file when a Note no longer belongs in the
active public library.

No Ruby/Jekyll dependency — pure Python, runs anywhere.
"""

import re
import html
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE_DIR = ROOT / "_notes_source"
OUTPUT_DIR = ROOT / "notes"
CONTACT_EMAIL = "hello@guildatelier.com"
SITE_URL = "https://guild-atelier.com"

# ---------- Minimal markdown-ish inline formatting ----------
def inline_format(text):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\(([^\s\)]+)\)", r'<a href="\2">\1</a>', text)
    return text

# A block consisting of nothing but a single [label](url) link is
# rendered as a CTA button using the site's existing .ga-btn component,
# instead of a plain in-paragraph link. Reuses the same component as
# "Start a Conversation" elsewhere on the site — no new visual element.
STANDALONE_LINK_RE = re.compile(r"^\[(.+?)\]\(([^\s\)]+)\)$")

def body_to_html(body):
    blocks = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
    html_parts = []
    for block in blocks:
        standalone_link = STANDALONE_LINK_RE.match(block)
        if standalone_link:
            label, url = standalone_link.group(1), standalone_link.group(2)
            html_parts.append(
                f'  <p class="ga-note-cta"><a href="{html.escape(url)}" class="ga-btn ga-btn--solid" target="_blank" rel="noopener">{html.escape(label)}</a></p>'
            )
            continue
        lines = block.split("\n")
        bullet_lines = [l for l in lines if l.strip().startswith("•")]
        lead_lines = [l for l in lines if not l.strip().startswith("•")]
        if bullet_lines and all(
            l.strip().startswith("•") for l in lines[len(lead_lines):]
        ) and lead_lines == lines[:len(lead_lines)]:
            if lead_lines:
                html_parts.append(f"  <p>{inline_format(' '.join(lead_lines))}</p>")
            items = "\n".join(
                f"    <li>{inline_format(l.strip().lstrip('•').strip())}</li>"
                for l in bullet_lines
            )
            html_parts.append(f"  <ul>\n{items}\n  </ul>")
        else:
            html_parts.append(f"  <p>{inline_format(block)}</p>")
    return "\n".join(html_parts)

# ---------- Parse a single post source file ----------
def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    if "---" not in raw:
        raise ValueError(f"{path.name}: missing '---' separator between front-matter and body")
    front, body = raw.split("---", 1)
    meta = {}
    for line in front.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
    required = ["title", "date", "tag", "excerpt", "slug"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise ValueError(f"{path.name}: missing fields {missing}")
    meta["delisted"] = meta.get("delisted", "false").strip().lower() == "true"
    # Optional, backward-compatible overrides. Any post that omits these
    # behaves exactly as before: the index card and social tags fall
    # back to the same excerpt every post already provides.
    meta["card_desc"] = meta.get("card_desc", "").strip() or meta["excerpt"]
    meta["og_description"] = meta.get("og_description", "").strip() or meta["excerpt"]
    meta["image"] = meta.get("image", "").strip()
    meta["body_html"] = body_to_html(body)
    meta["date_obj"] = datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
    meta["date_display"] = meta["date_obj"].strftime("%B %-d, %Y")
    return meta

# ---------- Templates (Refined Atelier) ----------

# Individual Note article — lives at /notes/<slug>/index.html, so shared
# assets are two levels up. Self-contained per the same pattern used by
# cross-cultural.css / hospitality.css / communication-education.css:
# it loads ../../css/homepage.css for tokens/reset/header/footer/closing,
# and ../notes.css for Insights-specific pieces (page hero, workbench,
# and this article template).
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Guild Atelier</title>
<meta name="description" content="{excerpt}">

<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16x16.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,500;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<link rel="stylesheet" href="../../css/homepage.css">
<link rel="stylesheet" href="../notes.css">
<link rel="alternate" type="application/rss+xml" title="Insights | Guild Atelier" href="../feed.xml">
</head>
<body class="ga-page">

<header class="ga-header">
  <div class="ga-header-inner">
    <a href="../../" class="ga-brand">
      <img src="../../images/guild-rings-mark.png" alt="Guild Atelier" class="ga-mark">
      <span class="ga-brand-name">Guild Atelier</span>
    </a>
    <nav class="ga-nav">
      <div class="ga-nav-links">
        <a href="../../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
        <a href="../../hospitality/">Hospitality</a>
        <a href="../../communication-education/">Communication &amp; Education</a>
        <a href="../" class="ga-nav-current" aria-current="page">Insights</a>
        <a href="../../#background">About</a>
      </div>
      <a href="../../#contact" class="ga-nav-cta">Start a Conversation</a>
      <button id="lang-toggle" class="ga-lang-toggle" aria-label="Switch language">
        <span class="ga-lang-option ga-lang-en">EN</span>
        <span class="ga-lang-divider">/</span>
        <span class="ga-lang-option ga-lang-vi">VI</span>
      </button>
      <button type="button" class="ga-menu-toggle" id="ga-menu-toggle" aria-expanded="false" aria-controls="ga-mobile-nav" aria-label="Open menu">
        <span></span><span></span><span></span>
      </button>
    </nav>
  </div>
  <div id="ga-mobile-nav" class="ga-mobile-nav" hidden>
    <a href="../../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
    <a href="../../hospitality/">Hospitality</a>
    <a href="../../communication-education/">Communication &amp; Education</a>
    <a href="../" class="ga-nav-current" aria-current="page">Insights</a>
    <a href="../../#background">About</a>
    <a href="../../#contact" class="ga-btn">Start a Conversation</a>
  </div>
</header>

<main>
  <article class="ga-note-post">
    <div class="ga-container--essay">
      <div class="ga-note-head">
        <p class="ga-eyebrow">{tag}</p>
        <h1>{title}</h1>
        <p class="ga-note-meta">{date_display}</p>
      </div>
      <div class="ga-note-body">
{body_html}
      </div>
      <div class="ga-note-footer">
        <a href="../" class="ga-link">&larr; Back to Insights</a>
      </div>
    </div>
  </article>
</main>

<footer class="ga-footer">
  <img src="../../images/guild-rings-mark.png" alt="Guild Atelier" class="ga-mark">
  <p class="ga-footer-tagline">Guild Atelier: Crafted Communication</p>
  <nav class="ga-footer-nav">
    <a href="../../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
    <a href="../../hospitality/">Hospitality</a>
    <a href="../../communication-education/">Communication &amp; Education</a>
    <a href="../">Insights</a>
    <a href="../../#background">About</a>
    <a href="../../#contact">Contact</a>
  </nav>
  <p class="ga-footer-email"><a href="mailto:{contact_email}">{contact_email}</a></p>
</footer>

<script src="../../js/lang-toggle.js"></script>
<script>
(function () {{
  var toggle = document.getElementById('ga-menu-toggle');
  var panel = document.getElementById('ga-mobile-nav');
  if (!toggle || !panel) return;

  function closeMenu() {{
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
  }}
  function openMenu() {{
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
  }}

  toggle.addEventListener('click', function () {{
    var isOpen = toggle.getAttribute('aria-expanded') === 'true';
    if (isOpen) {{ closeMenu(); }} else {{ openMenu(); }}
  }});

  panel.addEventListener('click', function (e) {{
    if (e.target.tagName === 'A') closeMenu();
  }});

  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape') closeMenu();
  }});
}})();
</script>
</body>
</html>
"""

INDEX_ROW_TEMPLATE = """      <a href="{slug}/" class="ga-insight-row">
        <span class="ga-insight-tag">{tag}</span>
        <h4>{title}</h4>
        <span class="ga-insight-desc">{excerpt}</span>
        <span class="ga-insight-more">Read the note &rarr;</span>
      </a>"""

# The Insights landing page — lives at /notes/index.html. Hero, Deeper
# Work, and Closing CTA are fixed editorial copy; only the "From the
# Workbench" rows are generated from source files. Architecture is
# intentionally locked to these four sections — see Insights revision
# notes before adding to it.
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Insights | Guild Atelier</title>
<meta name="description" content="Working ideas from Guild Atelier on culture, communication, organizations, service, and the systems behind them.">

<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16x16.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,500;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<link rel="stylesheet" href="../css/homepage.css">
<link rel="stylesheet" href="notes.css">
<link rel="alternate" type="application/rss+xml" title="Insights | Guild Atelier" href="feed.xml">
</head>
<body class="ga-page">

<header class="ga-header">
  <div class="ga-header-inner">
    <a href="../" class="ga-brand">
      <img src="../images/guild-rings-mark.png" alt="Guild Atelier" class="ga-mark">
      <span class="ga-brand-name">Guild Atelier</span>
    </a>
    <nav class="ga-nav">
      <div class="ga-nav-links">
        <a href="../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
        <a href="../hospitality/">Hospitality</a>
        <a href="../communication-education/">Communication &amp; Education</a>
        <a href="./" class="ga-nav-current" aria-current="page">Insights</a>
        <a href="../#background">About</a>
      </div>
      <a href="../#contact" class="ga-nav-cta">Start a Conversation</a>
      <button id="lang-toggle" class="ga-lang-toggle" aria-label="Switch language">
        <span class="ga-lang-option ga-lang-en">EN</span>
        <span class="ga-lang-divider">/</span>
        <span class="ga-lang-option ga-lang-vi">VI</span>
      </button>
      <button type="button" class="ga-menu-toggle" id="ga-menu-toggle" aria-expanded="false" aria-controls="ga-mobile-nav" aria-label="Open menu">
        <span></span><span></span><span></span>
      </button>
    </nav>
  </div>
  <div id="ga-mobile-nav" class="ga-mobile-nav" hidden>
    <a href="../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
    <a href="../hospitality/">Hospitality</a>
    <a href="../communication-education/">Communication &amp; Education</a>
    <a href="./" class="ga-nav-current" aria-current="page">Insights</a>
    <a href="../#background">About</a>
    <a href="../#contact" class="ga-btn">Start a Conversation</a>
  </div>
</header>

<main>

  <!-- 1. HERO -->
  <section class="ga-hero ga-page-hero" id="top">
    <div class="ga-hero-inner ga-page-hero-inner">
      <p class="ga-eyebrow">Insights</p>
      <h1 class="ga-hero-title ga-page-hero-title">Notes from the workbench.</h1>
      <div class="ga-hero-body ga-page-hero-body">
        <p>Working ideas about culture, communication, organizations, service, and the systems behind them.</p>
      </div>
    </div>
  </section>

  <!-- 2. FROM THE WORKBENCH -->
  <section class="ga-insights ga-workbench" id="workbench">
    <div class="ga-container">
      <div class="ga-insights-inner ga-workbench-inner">
        <h2>From the Workbench</h2>
        <div class="ga-insights-list">
{rows}
        </div>
      </div>
    </div>
  </section>

  <!-- 3. DEEPER WORK -->
  <section class="ga-trap" id="deeper-work">
    <div class="ga-trap-inner">
      <p class="ga-trap-quote">Some problems need a longer look.</p>
      <div class="ga-trap-body">
        <p>Guild Atelier is developing a deeper body of work around a recurring question: why do organizations keep producing outcomes that nobody inside them actually intended?</p>
        <p>That work looks beyond individual mistakes to the relationships between people, processes, information, authority, feedback, and the conditions under which the work actually happens.</p>
        <p>Longer Notes, Executive Briefs, and White Papers will appear here as that thinking develops.</p>
      </div>
    </div>
  </section>

  <!-- 4. CLOSING CTA -->
  <section class="ga-closing" id="contact">
    <div class="ga-closing-inner">
      <img src="../images/guild-rings-mark.png" alt="" class="ga-mark" aria-hidden="true">
      <h2>Start with a conversation</h2>
      <p>If something here describes a problem you're seeing in your own organization, tell us about it.</p>
      <a href="mailto:{contact_email}" class="ga-btn ga-btn--solid">Start a Conversation</a>
    </div>
  </section>

</main>

<footer class="ga-footer">
  <img src="../images/guild-rings-mark.png" alt="Guild Atelier" class="ga-mark">
  <p class="ga-footer-tagline">Guild Atelier: Crafted Communication</p>
  <nav class="ga-footer-nav">
    <a href="../cross-cultural-executive-consulting/">Cross-Cultural Consulting</a>
    <a href="../hospitality/">Hospitality</a>
    <a href="../communication-education/">Communication &amp; Education</a>
    <a href="./">Insights</a>
    <a href="../#background">About</a>
    <a href="#contact">Contact</a>
  </nav>
  <p class="ga-footer-email"><a href="mailto:{contact_email}">{contact_email}</a></p>
</footer>

<script src="../js/lang-toggle.js"></script>
<script>
(function () {{
  var toggle = document.getElementById('ga-menu-toggle');
  var panel = document.getElementById('ga-mobile-nav');
  if (!toggle || !panel) return;

  function closeMenu() {{
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
  }}
  function openMenu() {{
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
  }}

  toggle.addEventListener('click', function () {{
    var isOpen = toggle.getAttribute('aria-expanded') === 'true';
    if (isOpen) {{ closeMenu(); }} else {{ openMenu(); }}
  }});

  panel.addEventListener('click', function (e) {{
    if (e.target.tagName === 'A') closeMenu();
  }});

  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape') closeMenu();
  }});
}})();
</script>
</body>
</html>
"""

RSS_ITEM_TEMPLATE = """  <item>
    <title>{title}</title>
    <link>{site_url}/notes/{slug}/</link>
    <guid>{site_url}/notes/{slug}/</guid>
    <pubDate>{rss_date}</pubDate>
    <description>{excerpt}</description>
  </item>"""

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Insights | Guild Atelier</title>
  <link>{site_url}/notes/</link>
  <description>Working ideas from Guild Atelier on culture, communication, organizations, service, and the systems behind them.</description>
{items}
</channel>
</rss>
"""

def main():
    if not SOURCE_DIR.exists():
        print(f"No source directory at {SOURCE_DIR}, nothing to build.")
        return

    posts = []
    for path in sorted(SOURCE_DIR.glob("*.txt")):
        try:
            posts.append(parse_post(path))
        except ValueError as e:
            print(f"SKIPPED — {e}")

    if not posts:
        print("No valid posts found.")
        return

    posts.sort(key=lambda p: p["date_obj"], reverse=True)
    listed_posts = [p for p in posts if not p["delisted"]]

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Build every post's page, listed or not — delisting only affects
    # the index and feed, never the page itself or its URL.
    for post in posts:
        post_dir = OUTPUT_DIR / post["slug"]
        post_dir.mkdir(exist_ok=True)
        desc_meta = f'<meta name="description" content="{html.escape(post["excerpt"])}">'
        html_out = POST_TEMPLATE.format(
            title=html.escape(post["title"]),
            excerpt=html.escape(post["excerpt"]),
            tag=html.escape(post["tag"]),
            date_display=post["date_display"],
            body_html=post["body_html"],
            contact_email=CONTACT_EMAIL,
        )
        # Social-sharing meta is only spliced in for posts that supply an
        # `image`. This keeps every other post's generated HTML byte-for-
        # byte identical to before — nothing here touches the shared
        # template or its default output.
        if post["image"]:
            page_url = f"{SITE_URL}/notes/{post['slug']}/"
            image_url = f"{SITE_URL}/notes/{post['slug']}/{post['image']}"
            social_meta = "\n".join([
                '<meta property="og:type" content="article">',
                f'<meta property="og:title" content="{html.escape(post["title"])}">',
                f'<meta property="og:description" content="{html.escape(post["og_description"])}">',
                f'<meta property="og:url" content="{page_url}">',
                f'<meta property="og:image" content="{image_url}">',
                '<meta name="twitter:card" content="summary_large_image">',
                f'<meta name="twitter:title" content="{html.escape(post["title"])}">',
                f'<meta name="twitter:description" content="{html.escape(post["og_description"])}">',
                f'<meta name="twitter:image" content="{image_url}">',
            ])
            html_out = html_out.replace(desc_meta, f"{desc_meta}\n{social_meta}", 1)
        (post_dir / "index.html").write_text(html_out, encoding="utf-8")
        status = "delisted" if post["delisted"] else "listed"
        print(f"Built: notes/{post['slug']}/index.html ({status})")

    # Build the Insights landing page — only listed posts appear.
    rows = "\n".join(
        INDEX_ROW_TEMPLATE.format(
            slug=p["slug"], tag=html.escape(p["tag"]),
            title=html.escape(p["title"]), excerpt=html.escape(p["card_desc"]),
        ) for p in listed_posts
    )
    (OUTPUT_DIR / "index.html").write_text(
        INDEX_TEMPLATE.format(rows=rows, contact_email=CONTACT_EMAIL), encoding="utf-8"
    )
    print("Built: notes/index.html")

    # Build RSS feed — only listed posts appear.
    items = "\n".join(
        RSS_ITEM_TEMPLATE.format(
            title=html.escape(p["title"]), slug=p["slug"],
            site_url=SITE_URL, excerpt=html.escape(p["excerpt"]),
            rss_date=p["date_obj"].strftime("%a, %d %b %Y 00:00:00 +0000"),
        ) for p in listed_posts
    )
    (OUTPUT_DIR / "feed.xml").write_text(
        RSS_TEMPLATE.format(site_url=SITE_URL, items=items), encoding="utf-8"
    )
    print("Built: notes/feed.xml")

    print(f"\nDone — {len(posts)} post(s) built, {len(listed_posts)} listed, {len(posts) - len(listed_posts)} delisted.")

if __name__ == "__main__":
    main()
