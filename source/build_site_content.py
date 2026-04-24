#!/usr/bin/env python3
"""
Generate the 11ty content files in site/src/ from the prep-package markdown
in content/.  Rewrites image URLs (from live WP URLs to local /images/ paths)
and adds the right `layout:` frontmatter for 11ty to pick up.
"""
from pathlib import Path
import json, re, shutil

ROOT = Path('/home/claude/lvbathrooms')
SRC_CONTENT = ROOT / 'content'            # prep-package markdown
DEST = ROOT / 'site' / 'src'               # 11ty input root
BUNDLE = json.loads((ROOT / 'source' / 'lvbathrooms-content-bundle-2026-04-23.json').read_text())

# Build a lookup: live URL -> local /images/ path, using the alt-text manifest
# which already maps each WP asset to its sorted location.
ALT_JSON = json.loads((ROOT / 'docs' / 'alt-text.json').read_text())
# The manifest key is a path like "assets/projects/{slug}/filename.jpeg" — turn
# that into a /images/ URL and also build a reverse map from the original WP
# source_url to /images/ path so we can rewrite post bodies.
url_to_local = {}
for rel, meta in ALT_JSON.items():
    wp_id = meta.get('wp_id')
    if not wp_id:
        continue
    # Find the WP media item with this id and map its source_url
    for m in BUNDLE['media']:
        if m['id'] == wp_id:
            local = '/' + rel.replace('assets/', 'images/')
            url_to_local[m['source_url']] = local
            # Also map the thumbnail URL variants (WP generates sizes)
            # Most posts link to sized variants like "-1024x768.jpeg"
            base = m['source_url'].rsplit('.', 1)
            if len(base) == 2:
                stem, ext = base
                # Strip any existing -WIDTHxHEIGHT from the end of stem
                stem_clean = re.sub(r'-\d+x\d+$', '', stem)
                # All possible sized permalink patterns map to the same local file
                for size in ['150x150', '300x225', '768x576', '1024x768',
                             '768x1024', '473x1024', '1024x1024', '1536x1152',
                             '2048x1536', '480x640']:
                    url_to_local[f'{stem_clean}-{size}.{ext}'] = local
            break


def rewrite_image_urls(s):
    """Replace any live lvbathrooms WP URL with its local /images/ path."""
    if not s:
        return s
    # Replace exact matches first
    for url, local in url_to_local.items():
        if url in s:
            s = s.replace(url, local)
    # Also rewrite http:// variants (Elementor sometimes stored them without https)
    s = s.replace('http://lvbathrooms.co.uk/wp-content/uploads/',
                  'https://lvbathrooms.co.uk/wp-content/uploads/')
    # Any remaining /wp-content/uploads/ URL that we couldn't map: flag it by leaving
    # the URL but commenting above so it's visible in review
    return s


def strip_frontmatter(md):
    """Return (frontmatter_dict, body) from a markdown file containing YAML frontmatter."""
    import yaml
    if not md.startswith('---'):
        return {}, md
    end = md.find('\n---', 3)
    if end == -1:
        return {}, md
    fm_block = md[3:end].strip()
    body = md[end + 4:].lstrip('\n')
    fm = yaml.safe_load(fm_block) or {}
    return fm, body


def yaml_dump(d):
    """Minimal YAML dumper — handles our simple frontmatter shape."""
    import yaml
    return yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=200)


# ---------------------------------------------------------------------------
# Content pages
# ---------------------------------------------------------------------------

# Custom page configs — how each source page maps to a site/src/ file
PAGE_CONFIGS = {
    'home':              {'out': 'index.md',            'layout': 'layouts/home.njk',
                          'permalink': '/'},
    'emergency-repairs': {'out': 'emergency-repairs.md','layout': 'layouts/page.njk',
                          'permalink': '/emergency-repairs/'},
    'refurbishment':     {'out': 'refurbishment.md',    'layout': 'layouts/page.njk',
                          'permalink': '/refurbishment/'},
    'bathroom-creation': {'out': 'bathroom-creation.md','layout': 'layouts/page.njk',
                          'permalink': '/bathroom-creation/'},
    'contact':           {'out': 'contact.md',          'layout': 'layouts/page.njk',
                          'permalink': '/contact/'},
    'privacy-policy':    {'out': 'privacy-policy.md',   'layout': 'layouts/page.njk',
                          'permalink': '/privacy-policy/'},
}

pages_src = SRC_CONTENT / 'pages'
for stem, cfg in PAGE_CONFIGS.items():
    src_file = pages_src / f'{stem}.md'
    if not src_file.exists():
        print(f'  skip {stem} — source not found')
        continue
    fm, body = strip_frontmatter(src_file.read_text())

    # Build 11ty frontmatter
    out_fm = {
        'layout': cfg['layout'],
        'permalink': cfg['permalink'],
        'title': fm.get('title', stem.replace('-', ' ').title()),
    }
    if fm.get('seo_title'):
        out_fm['seo_title'] = fm['seo_title']
    if fm.get('seo_description'):
        out_fm['seo_description'] = fm['seo_description']
    if fm.get('og_image'):
        # Rewrite to local
        og = fm['og_image']
        out_fm['og_image'] = url_to_local.get(og, og)

    # For home page, we don't want the content from home.md — the layout template
    # renders everything from site.js data. Just keep the frontmatter.
    if stem == 'home':
        out_text = '---\n' + yaml_dump(out_fm) + '---\n'
    else:
        body = rewrite_image_urls(body)
        # Strip the first H1 heading (the layout renders it in the hero)
        lines = body.splitlines()
        i = 0
        while i < len(lines) and not lines[i].strip().startswith('# '):
            i += 1
        if i < len(lines):
            # Drop the H1 line and any blank lines immediately after
            del lines[i]
            while i < len(lines) and not lines[i].strip():
                del lines[i]
        body = '\n'.join(lines)

        # Strip our prep-package section markers like "## Section 0: Hero (animated headline)"
        # from the non-home pages — they're prep-only metadata
        body = re.sub(r'^## Section \d+:[^\n]*\n\n?', '', body, flags=re.MULTILINE)
        # And the prep preamble lines like "Section-by-section breakdown..."
        body = re.sub(r'^Section-by-section breakdown.*?---\n', '', body, flags=re.DOTALL)

        out_text = '---\n' + yaml_dump(out_fm) + '---\n\n' + body

    out_path = DEST / cfg['out']
    out_path.write_text(out_text)
    print(f'  wrote {out_path.relative_to(ROOT)}')


# ---------------------------------------------------------------------------
# Projects (case studies)
# ---------------------------------------------------------------------------

posts_src = SRC_CONTENT / 'posts'
projects_dest = DEST / 'projects'
projects_dest.mkdir(parents=True, exist_ok=True)

# For each prep-package post, emit an 11ty project page
count = 0
for src_file in sorted(posts_src.glob('*.md')):
    fm, body = strip_frontmatter(src_file.read_text())
    slug = fm.get('slug')
    if not slug:
        print(f'  skip {src_file.name} — no slug')
        continue

    # Output frontmatter
    out_fm = {
        'layout': 'layouts/post.njk',
        'permalink': f'/projects/{slug}/',
        'title': fm.get('title', slug),
        'date': fm['date'][:10] if fm.get('date') else None,
    }
    if fm.get('seo_title'):
        out_fm['seo_title'] = fm['seo_title']
    if fm.get('seo_description'):
        out_fm['seo_description'] = fm['seo_description']
    # og_image: rewrite to local /images/ path
    og = fm.get('og_image') or fm.get('featured_image')
    if og:
        out_fm['og_image'] = url_to_local.get(og, og)
    if fm.get('tags'):
        out_fm['tags'] = fm['tags']

    # Gallery directory: does /images/projects/{slug}/ have files?
    gallery_dir = ROOT / 'site' / 'public' / 'images' / 'projects' / slug
    if gallery_dir.exists() and any(gallery_dir.iterdir()):
        out_fm['gallery_dir'] = slug

    # Strip the first H1 and the "## Images referenced in this post" section + list
    body = rewrite_image_urls(body)
    lines = body.splitlines()
    # Drop H1
    i = 0
    while i < len(lines) and not lines[i].strip().startswith('# '):
        i += 1
    if i < len(lines):
        del lines[i]
        while i < len(lines) and not lines[i].strip():
            del lines[i]
    # Drop the "## Images referenced in this post" section and everything after
    for j, line in enumerate(lines):
        if line.strip() == '## Images referenced in this post':
            lines = lines[:j]
            break
    body = '\n'.join(lines).rstrip() + '\n'

    out_name = f'{slug}.md'
    out_path = projects_dest / out_name
    out_text = '---\n' + yaml_dump(out_fm) + '---\n\n' + body
    out_path.write_text(out_text)
    count += 1
    print(f'  wrote src/projects/{out_name}')

print(f'\n{count} project pages written')


# ---------------------------------------------------------------------------
# Projects index page
# ---------------------------------------------------------------------------

projects_index = DEST / 'projects' / 'index.njk'
index_content = """---
layout: layouts/base.njk
permalink: /projects/
title: "Projects"
seo_title: "Our Projects - Bathrooms by LV"
seo_description: "A gallery of completed bathroom, en-suite and cloakroom projects by Bathrooms by LV in Warrington and the North West."
---
<article class="page">
  <header class="page-hero">
    <h1>Projects</h1>
    <p class="page-hero__subtitle">A selection of completed bathrooms, en-suites and cloakrooms from recent years.</p>
  </header>

  <div class="page-body">
    <ul class="recent-projects__grid" style="padding-left:0; list-style:none;">
    {% for post in collections.projects %}
      <li>
        <a href="{{ post.url }}" class="project-card">
          {% if post.data.og_image %}
          <img src="{{ post.data.og_image }}" alt="" loading="lazy">
          {% endif %}
          <h3>{{ post.data.title }}</h3>
          <p class="project-card__date">{{ post.date | monthYear }}</p>
        </a>
      </li>
    {% endfor %}
    </ul>
  </div>
</article>
"""
projects_index.write_text(index_content)
print(f'wrote src/projects/index.njk')
