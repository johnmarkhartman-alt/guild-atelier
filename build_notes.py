#!/usr/bin/env python3
"""
Guild Atelier — Notes from the Bench: static blog generator.

Reads simple front-matter + markdown-ish text files from _notes_source/
and generates:
  - /notes/index.html        (auto-updating list of all posts)
  - /notes/<slug>/index.html (one page per post)
  - /notes/feed.xml           (basic RSS feed)

Post source format (_notes_source/*.txt):

    title: Students Don't Practice Enough at Home
    date: 2026-06-20
    tag: Practice
    excerpt: A short one-line summary shown on the index card.
    slug: students-dont-practice-enough-at-home
    ---
    Body text goes here. Blank lines become paragraph breaks.

    Supports **bold**, _italic_, and [link text](https://example.com).

No Ruby/Jekyll dependency — pure Python, runs anywhere.
"""

import re
import html
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE_DIR = ROOT / "_notes_source"
OUTPUT_DIR = ROOT / "notes"
REPLY_EMAIL = "guild-atelier@gmail.com"
SITE_URL = "https://guild-atelier.com"

# ---------- Minimal markdown-ish inline formatting ----------
def inline_format(text):
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((https?://[^\)]+)\)", r'<a href="\2">\1</a>', text)
    return text

def body_to_html(body):
    blocks = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
    html_parts = []
    for block in blocks:
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
    meta["body_html"] = body_to_html(body)
    meta["date_obj"] = datetime.datetime.strptime(meta["date"], "%Y-%m-%d")
    meta["date_display"] = meta["date_obj"].strftime("%B %-d, %Y")
    return meta

# ---------- Templates ----------
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Notes from the Bench — Guild Atelier</title>
<meta name="description" content="{excerpt}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../css/styles.css">
<link rel="stylesheet" href="../notes.css">
<link rel="alternate" type="application/rss+xml" title="Notes from the Bench" href="../feed.xml">
</head>
<body>
<div class="grain"></div>

<header class="site-header">
  <div class="header-inner">
    <a href="../../" class="brand-mark">
      <img src="../../images/guild-mark.jpeg" alt="Guild Atelier" class="mark-img">
      <span class="brand-name">Guild Atelier</span>
    </a>
    <nav class="site-nav">
      <a href="../../#crafts">The Crafts</a>
      <a href="../../#workshop">In the Workshop</a>
      <a href="../">Notes</a>
      <a href="../../#contact" class="nav-cta">Begin an Inquiry</a>
    </nav>
  </div>
</header>

<main>
  <article class="note-post">
    <div class="note-post-head">
      <span class="note-tag">{tag}</span>
      <h1>{title}</h1>
      <p class="note-meta">{date_display}</p>
    </div>
    <div class="note-post-body">
{body_html}
    </div>
    <div class="note-post-footer">
      <a href="mailto:{reply_email}?subject=Re: {title}" class="btn-primary">Reply by Email</a>
      <a href="../" class="back-link">← Back to Notes</a>
    </div>
  </article>
</main>

<footer class="site-footer">
  <img src="../../images/guild-mark.jpeg" alt="Guild Atelier" class="footer-mark">
  <p>&copy; 2026 Guild Atelier. Crafted Communication.</p>
</footer>
</body>
</html>
"""

INDEX_CARD_TEMPLATE = """      <a href="{slug}/" class="note-card">
        <span class="note-tag">{tag}</span>
        <h4>{title}</h4>
        <span class="note-date">{date_display}</span>
        <span class="note-read-more">Read note →</span>
      </a>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Notes from the Bench — Guild Atelier</title>
<meta name="description" content="Recent observations from teaching, coaching, and product development.">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../css/styles.css">
<link rel="stylesheet" href="notes.css">
<link rel="alternate" type="application/rss+xml" title="Notes from the Bench" href="feed.xml">
</head>
<body>
<div class="grain"></div>

<header class="site-header">
  <div class="header-inner">
    <a href="../" class="brand-mark">
      <img src="../images/guild-mark.jpeg" alt="Guild Atelier" class="mark-img">
      <span class="brand-name">Guild Atelier</span>
    </a>
    <nav class="site-nav">
      <a href="../#crafts">The Crafts</a>
      <a href="../#workshop">In the Workshop</a>
      <a href="./">Notes</a>
      <a href="../#contact" class="nav-cta">Begin an Inquiry</a>
    </nav>
  </div>
</header>

<main>
  <section class="notes-index">
    <div class="section-head">
      <p class="eyebrow">Notes from the Bench</p>
      <h1>Recent Observations</h1>
      <p class="section-lede">Recent observations from teaching, coaching, and product development.</p>
    </div>

    <div class="notes-grid">
{cards}
    </div>
  </section>
</main>

<footer class="site-footer">
  <img src="../images/guild-mark.jpeg" alt="Guild Atelier" class="footer-mark">
  <p>&copy; 2026 Guild Atelier. Crafted Communication.</p>
</footer>
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
  <title>Notes from the Bench — Guild Atelier</title>
  <link>{site_url}/notes/</link>
  <description>Recent observations from teaching, coaching, and product development.</description>
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

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Build each post page
    for post in posts:
        post_dir = OUTPUT_DIR / post["slug"]
        post_dir.mkdir(exist_ok=True)
        html_out = POST_TEMPLATE.format(
            title=html.escape(post["title"]),
            excerpt=html.escape(post["excerpt"]),
            tag=html.escape(post["tag"]),
            date_display=post["date_display"],
            body_html=post["body_html"],
            reply_email=REPLY_EMAIL,
        )
        (post_dir / "index.html").write_text(html_out, encoding="utf-8")
        print(f"Built: notes/{post['slug']}/index.html")

    # Build index page
    cards = "\n".join(
        INDEX_CARD_TEMPLATE.format(
            slug=p["slug"], tag=html.escape(p["tag"]),
            title=html.escape(p["title"]), date_display=p["date_display"],
        ) for p in posts
    )
    (OUTPUT_DIR / "index.html").write_text(INDEX_TEMPLATE.format(cards=cards), encoding="utf-8")
    print("Built: notes/index.html")

    # Build RSS feed
    items = "\n".join(
        RSS_ITEM_TEMPLATE.format(
            title=html.escape(p["title"]), slug=p["slug"],
            site_url=SITE_URL, excerpt=html.escape(p["excerpt"]),
            rss_date=p["date_obj"].strftime("%a, %d %b %Y 00:00:00 +0000"),
        ) for p in posts
    )
    (OUTPUT_DIR / "feed.xml").write_text(RSS_TEMPLATE.format(site_url=SITE_URL, items=items), encoding="utf-8")
    print("Built: notes/feed.xml")

    print(f"\nDone — {len(posts)} post(s) built.")

if __name__ == "__main__":
    main()
