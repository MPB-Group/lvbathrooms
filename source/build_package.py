#!/usr/bin/env python3
"""
Build the Bathrooms-by-LV rebuild preparation package from the exported
content bundle JSON.

Reads: source/lvbathrooms-content-bundle-*.json
Writes:
  content/pages/*.md        — one markdown file per page with frontmatter + body
  content/posts/*.md        — one markdown file per project/case study
  content/posts/_index.md   — projects index (metadata only)
  docs/asset-manifest.md    — all 195 media items, grouped
  docs/asset-manifest.json  — machine-readable version
  docs/seo-manifest.md      — every page & post's Yoast title + description
  docs/brand-and-styling.md — colours, type, layout notes
  docs/site-architecture.md — IA, nav, slugs, redirect plan
  docs/rebuild-plan.md      — step-by-step next actions
  docs/content-audit.md     — issues found (broken links, stock images, etc)
"""
from pathlib import Path
import json, re, html
from datetime import datetime

ROOT = Path('/home/claude/lvbathrooms')
SRC = ROOT / 'source' / 'lvbathrooms-content-bundle-2026-04-23.json'

with SRC.open() as f:
    BUNDLE = json.load(f)

PAGES = BUNDLE['pages']
POSTS = BUNDLE['posts']
MEDIA = BUNDLE['media']
CATEGORIES = {c['id']: c for c in BUNDLE['categories']}
TAGS = {t['id']: t for t in BUNDLE['tags']}
USERS = {u['id']: u for u in BUNDLE['users']}
MEDIA_BY_ID = {m['id']: m for m in MEDIA}

# ---------------------------------------------------------------------------
# Elementor harvester
# ---------------------------------------------------------------------------

# All text-bearing fields we know about, in preferred order
TEXT_FIELDS = [
    ('writing-effect-headline', 'before_text'),
    ('writing-effect-headline', 'written_text'),
    ('text-editor', 'editor'),
    ('advanced-text-block', 'content_description'),
    ('heading', 'title'),
    ('button', 'text'),
    ('icon-box', 'title_text'),
    ('icon-box', 'description_text'),
    ('counter', 'title'),
    ('counter', 'ending_number'),
    ('counter', 'starting_number'),
    ('counter', 'prefix'),
    ('counter', 'suffix'),
    ('testimonial', 'testimonial_content'),
    ('testimonial', 'testimonial_name'),
    ('testimonial', 'testimonial_job'),
    ('divider', 'text'),
    ('shortcode', 'shortcode'),
]


def harvest_element(node, collected):
    """Recursively walk an Elementor node tree, appending semantic items to `collected`."""
    if not isinstance(node, dict):
        return
    settings = node.get('settings') or {}
    el_type = node.get('elType', '')
    wt = node.get('widgetType', '')

    # Section / column: capture background image if present
    if el_type in ('section', 'column'):
        bg = settings.get('background_image')
        if isinstance(bg, dict) and bg.get('url'):
            collected.append({
                'type': 'bg_image',
                'el_type': el_type,
                'url': bg.get('url'),
                'image_id': bg.get('id'),
            })

    # Widget-specific extraction
    if wt == 'writing-effect-headline':
        collected.append({
            'type': 'hero_headline',
            'before_text': settings.get('before_text', ''),
            'written_text': settings.get('written_text', ''),
            'tag': settings.get('tag', 'h2'),
            'title_color': settings.get('title_color'),
            'words_color': settings.get('words_color'),
        })
    elif wt == 'text-editor':
        collected.append({'type': 'prose', 'html': settings.get('editor', '')})
    elif wt == 'advanced-text-block':
        collected.append({'type': 'prose', 'html': settings.get('content_description', '')})
    elif wt == 'heading':
        collected.append({'type': 'heading', 'text': settings.get('title', ''), 'tag': settings.get('header_size', 'h2')})
    elif wt == 'icon-box':
        collected.append({
            'type': 'icon_box',
            'title': settings.get('title_text', ''),
            'body': settings.get('description_text', ''),
            'icon': (settings.get('selected_icon') or {}).get('value'),
        })
    elif wt == 'counter':
        collected.append({
            'type': 'counter',
            'title': settings.get('title', ''),
            'value': settings.get('ending_number', ''),
            'prefix': settings.get('prefix', ''),
            'suffix': settings.get('suffix', ''),
        })
    elif wt == 'button':
        link = settings.get('link') or {}
        collected.append({
            'type': 'button',
            'text': settings.get('text', ''),
            'url': link.get('url', '') if isinstance(link, dict) else '',
        })
    elif wt == 'testimonial':
        ti = settings.get('testimonial_image') or {}
        collected.append({
            'type': 'testimonial',
            'body': settings.get('testimonial_content', ''),
            'name': settings.get('testimonial_name', ''),
            'location': settings.get('testimonial_job', ''),
            'image': ti.get('url', '') if isinstance(ti, dict) else '',
        })
    elif wt == 'image':
        img = settings.get('image') or {}
        if isinstance(img, dict) and img.get('url'):
            collected.append({
                'type': 'image',
                'url': img.get('url'),
                'image_id': img.get('id'),
                'caption': settings.get('caption', ''),
            })
    elif wt == 'icon-list':
        items = settings.get('icon_list') or []
        if isinstance(items, list):
            out_items = []
            for it in items:
                if isinstance(it, dict):
                    link = it.get('link') or {}
                    out_items.append({
                        'text': it.get('text', ''),
                        'url': link.get('url', '') if isinstance(link, dict) else '',
                        'icon': (it.get('selected_icon') or {}).get('value'),
                    })
            collected.append({'type': 'icon_list', 'items': out_items})
    elif wt == 'shortcode':
        collected.append({'type': 'shortcode', 'code': settings.get('shortcode', '')})
    elif wt == 'divider':
        collected.append({'type': 'divider'})
    elif wt == 'spacer':
        pass  # ignore
    elif wt:
        # Unknown widget — record it so we notice in the audit
        collected.append({'type': 'unknown_widget', 'widget_type': wt})

    # Recurse
    for child in node.get('elements') or []:
        harvest_element(child, collected)


def harvest_page(page):
    """Return a list of sections, each with a list of semantic items."""
    raw = page['meta'].get('_elementor_data')
    if not raw:
        return None
    try:
        tree = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None
    sections = []
    for section_node in tree:
        items = []
        harvest_element(section_node, items)
        sections.append(items)
    return sections


# ---------------------------------------------------------------------------
# HTML -> clean text/markdown
# ---------------------------------------------------------------------------

# Known spam-injection strings found in WordPress content — stripped on export.
# These look like they were inserted by a compromised plugin or left over from a
# template; they have nothing to do with Bathrooms by LV. See docs/content-audit.md.
SPAM_SUBSTRINGS = [
    'At present information about remedies changes regularly.',
    "Let's talk about <a",           # begins the "divers medicaments" link
    'divers medicaments',
    'smallbusinessconnection.com',
]


def strip_spam(s):
    """Remove any sentence (or HTML fragment up to the next '.') containing a spam marker."""
    if not s:
        return s
    # Split into sentences naively — enough for this use case
    # First, strip the specific link-bearing fragment as a whole
    s = re.sub(
        r'\s*At present information about remedies changes regularly\.\s*'
        r'Let\'s talk about\s*<a[^>]*>.*?</a>\s*you can get from Internet\.\s*',
        ' ', s, flags=re.IGNORECASE | re.DOTALL,
    )
    # Also catch the plain-text form (post-HTML strip), in case harvest order changes
    s = re.sub(
        r'\s*At present information about remedies changes regularly\.\s*'
        r"Let\'s talk about \[?divers medicaments\]?.*?you can get from Internet\.\s*",
        ' ', s, flags=re.IGNORECASE | re.DOTALL,
    )
    # Collapse any double spaces introduced
    s = re.sub(r'[ \t]+', ' ', s)
    return s


def html_to_markdown(s):
    """Very small HTML-to-markdown: preserves paragraphs, bold, italic, links."""
    if not s:
        return ''
    s = strip_spam(s)
    s = s.replace('<br />', '\n').replace('<br>', '\n').replace('<br/>', '\n')
    s = re.sub(r'</p>\s*<p[^>]*>', '\n\n', s)
    s = re.sub(r'<p[^>]*>', '', s)
    s = s.replace('</p>', '')
    s = re.sub(r'<strong>(.+?)</strong>', r'**\1**', s, flags=re.DOTALL)
    s = re.sub(r'<b>(.+?)</b>', r'**\1**', s, flags=re.DOTALL)
    s = re.sub(r'<em>(.+?)</em>', r'*\1*', s, flags=re.DOTALL)
    s = re.sub(r'<i>(.+?)</i>', r'*\1*', s, flags=re.DOTALL)
    s = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.+?)</a>', r'[\2](\1)', s, flags=re.DOTALL)
    s = re.sub(r'<span[^>]*>', '', s)
    s = s.replace('</span>', '')
    s = re.sub(r'<[^>]+>', '', s)  # strip anything else
    s = html.unescape(s)
    s = re.sub(r'\n{3,}', '\n\n', s).strip()
    return s


def yaml_escape(val):
    """Escape a string for YAML frontmatter."""
    if val is None:
        return '""'
    s = str(val).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"'


# ---------------------------------------------------------------------------
# Per-page content writers
# ---------------------------------------------------------------------------

def render_home(sections, page):
    """Build the home page markdown, section by section."""
    out = []
    out.append('# Home page — content reference')
    out.append('')
    out.append('Section-by-section breakdown of the existing homepage.  ')
    out.append('Each `## Section` maps to a visual region on the live site; use this as')
    out.append('the content source when building the new home template.')
    out.append('')
    out.append('---')
    out.append('')

    section_titles = [
        'Hero (animated headline)',          # 0
        'Intro prose band',                   # 1
        'Three room-type cards',              # 2
        'Project counters',                   # 3
        'Service card — Emergency Repairs',   # 4
        'Service card — Refurbishment',       # 5
        'Service card — Creation',            # 6
        'About us + van imagery',             # 7
        'Testimonials',                       # 8
        'Recent projects (auto, via shortcode)', # 9
        'Contact details + address',          # 10
    ]

    for i, items in enumerate(sections):
        title = section_titles[i] if i < len(section_titles) else f'Section {i}'
        out.append(f'## Section {i}: {title}')
        out.append('')
        for item in items:
            t = item['type']
            if t == 'hero_headline':
                out.append(f"**Animated headline** (tag `{item['tag']}`, title colour `{item['title_color']}`, rotating-words colour `{item['words_color']}`):")
                out.append('')
                out.append(f"> {html_to_markdown(item['before_text'])}")
                words = [w.strip() for w in re.split(r'[\n,]', item['written_text']) if w.strip()]
                out.append('')
                out.append('Rotating words:')
                for w in words:
                    out.append(f'- {w}')
                out.append('')
            elif t == 'prose':
                md = html_to_markdown(item['html'])
                if md:
                    out.append(md)
                    out.append('')
            elif t == 'heading':
                out.append(f"### {item['text']}")
                out.append('')
            elif t == 'icon_box':
                out.append(f"**{item['title']}**")
                out.append('')
                out.append(html_to_markdown(item['body']))
                out.append('')
            elif t == 'counter':
                out.append(f"- **{item['value']}+** {item['title']}")
            elif t == 'button':
                out.append(f"[Button] **{item['text']}** → `{item['url']}`")
                out.append('')
            elif t == 'testimonial':
                out.append(f"> {html_to_markdown(item['body'])}")
                attrib = f"— **{item['name']}**"
                if item.get('location'):
                    attrib += f", {item['location']}"
                out.append(attrib)
                if item.get('image'):
                    out.append(f"*(face image: `{item['image']}`)*")
                out.append('')
            elif t == 'image':
                out.append(f"![image]({item['url']})")
                if item.get('caption'):
                    out.append(f"*{item['caption']}*")
                out.append('')
            elif t == 'icon_list':
                for it in item['items']:
                    if it.get('url'):
                        out.append(f"- [{it['text']}]({it['url']})")
                    else:
                        out.append(f"- {it['text']}")
                out.append('')
            elif t == 'shortcode':
                out.append(f"`[shortcode]` `{item['code']}`")
                out.append('')
            elif t == 'bg_image':
                out.append(f"*({item['el_type']} background image: `{item['url']}`)*")
                out.append('')
            elif t == 'divider':
                pass  # skip
            elif t == 'unknown_widget':
                out.append(f"*(unhandled widget: `{item['widget_type']}`)*")
                out.append('')
        # spacer between sections
        if items:
            out.append('')
    return '\n'.join(out)


def render_simple_page(sections, page):
    """Render non-home pages. All of contact/services are simpler — just flatten the items."""
    out = []
    title = page['title']
    out.append(f"# {title}")
    out.append('')
    if sections is None:
        # Fall back to content_raw
        md = html_to_markdown(page.get('content_raw', ''))
        out.append(md)
        return '\n'.join(out)
    for items in sections:
        for item in items:
            t = item['type']
            if t == 'hero_headline':
                words = ', '.join(w.strip() for w in re.split(r'[\n,]', item['written_text']) if w.strip())
                out.append(f"{html_to_markdown(item['before_text'])} {words}")
                out.append('')
            elif t == 'prose':
                md = html_to_markdown(item['html'])
                if md:
                    out.append(md)
                    out.append('')
            elif t == 'heading':
                out.append(f"## {item['text']}")
                out.append('')
            elif t == 'icon_box':
                out.append(f"### {item['title']}")
                out.append('')
                out.append(html_to_markdown(item['body']))
                out.append('')
            elif t == 'testimonial':
                out.append(f"> {html_to_markdown(item['body'])}")
                attrib = f"— **{item['name']}**"
                if item.get('location'):
                    attrib += f", {item['location']}"
                out.append(attrib)
                if item.get('image'):
                    out.append(f"*(face image: `{item['image']}`)*")
                out.append('')
            elif t == 'button':
                out.append(f"[Button] **{item['text']}** → `{item['url']}`")
                out.append('')
            elif t == 'image':
                out.append(f"![image]({item['url']})")
                out.append('')
            elif t == 'icon_list':
                for it in item['items']:
                    if it.get('url'):
                        out.append(f"- [{it['text']}]({it['url']})")
                    else:
                        out.append(f"- {it['text']}")
                out.append('')
            elif t == 'bg_image':
                out.append(f"*(section background image: `{item['url']}`)*")
                out.append('')
    return '\n'.join(out)


def page_frontmatter(page):
    y = page.get('yoast') or {}
    fm = {
        'title': page['title'],
        'slug': page['slug'],
        'wp_page_id': page['id'],
        'status': page['status'],
        'original_url': page['link'],
        'date': page['date'],
        'modified': page.get('modified'),
        'seo_title': y.get('title'),
        'seo_description': y.get('description'),
        'og_image': y.get('og_image'),
        'featured_media': page.get('featured_media'),
    }
    lines = ['---']
    for k, v in fm.items():
        if v is None or v == '':
            continue
        lines.append(f'{k}: {yaml_escape(v)}')
    lines.append('---')
    return '\n'.join(lines)


def post_frontmatter(post):
    y = post.get('yoast') or {}
    fm = {
        'title': post['title'],
        'slug': post['slug'],
        'wp_post_id': post['id'],
        'date': post['date'],
        'modified': post.get('modified'),
        'status': post['status'],
        'original_url': post['link'],
        'seo_title': y.get('title'),
        'seo_description': y.get('description'),
        'og_image': y.get('og_image'),
        'featured_media_id': post.get('featured_media'),
        'categories': [CATEGORIES[c]['slug'] for c in post.get('categories', []) if c in CATEGORIES],
        'tags': [TAGS[t]['slug'] for t in post.get('tags', []) if t in TAGS],
        'author': USERS.get(post.get('author'), {}).get('slug'),
    }
    # Resolve featured media URL
    fm_id = post.get('featured_media')
    if fm_id and fm_id in MEDIA_BY_ID:
        fm['featured_image'] = MEDIA_BY_ID[fm_id]['source_url']

    lines = ['---']
    for k, v in fm.items():
        if v is None or v == '' or v == []:
            continue
        if isinstance(v, list):
            lines.append(f'{k}:')
            for item in v:
                lines.append(f'  - {yaml_escape(item)}')
        else:
            lines.append(f'{k}: {yaml_escape(v)}')
    lines.append('---')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Write page files
# ---------------------------------------------------------------------------

def slug_for_page(page):
    # Canonical slug map (fix the "bathrooms" slug of the home page)
    if page['id'] == 31:
        return 'home'
    if page['slug'] == 'privacy-policy':
        return 'privacy-policy'
    return page['slug']


pages_dir = ROOT / 'content' / 'pages'
pages_dir.mkdir(parents=True, exist_ok=True)

for page in PAGES:
    sections = harvest_page(page)
    out_name = slug_for_page(page) + '.md'
    out_path = pages_dir / out_name
    parts = [page_frontmatter(page), '']
    if page['id'] == 31:
        parts.append(render_home(sections, page))
    elif sections:
        parts.append(render_simple_page(sections, page))
    else:
        # Blog index / Privacy Policy etc.
        parts.append(f"# {page['title']}")
        parts.append('')
        parts.append(html_to_markdown(page.get('content_raw') or ''))
    out_path.write_text('\n'.join(parts))
    print(f'  wrote {out_path.relative_to(ROOT)}  ({len("".join(parts))} chars)')


# ---------------------------------------------------------------------------
# Write post files
# ---------------------------------------------------------------------------

posts_dir = ROOT / 'content' / 'posts'
posts_dir.mkdir(parents=True, exist_ok=True)

# Clean up old content/projects dir from skeleton
old_projects = ROOT / 'content' / 'projects'
if old_projects.exists():
    import shutil
    shutil.rmtree(old_projects)

# Sort posts by date ascending (so filenames sort nicely)
for post in sorted(POSTS, key=lambda p: p['date']):
    date_prefix = post['date'][:10]
    fname = f"{date_prefix}_{post['slug']}.md"
    body_html = post.get('content_raw') or ''
    # Extract inline image URLs for convenience
    image_urls = re.findall(r'<img[^>]+src="([^"]+)"', body_html)
    body_md = html_to_markdown(body_html)
    frontmatter = post_frontmatter(post)
    parts = [frontmatter, '', f"# {post['title']}", '', body_md]
    if image_urls:
        parts.extend(['', '## Images referenced in this post', ''])
        for url in image_urls:
            parts.append(f'- {url}')
    (posts_dir / fname).write_text('\n'.join(parts))
    print(f'  wrote content/posts/{fname}')


# ---------------------------------------------------------------------------
# docs/asset-manifest.{md,json}
# ---------------------------------------------------------------------------

docs_dir = ROOT / 'docs'
docs_dir.mkdir(parents=True, exist_ok=True)

# Group media logically
# Map filename prefixes to which post slug they belong to
PROJECT_PREFIX_TO_POST = {
    'hayley-and-mike':          'all-the-bathroom-mod-cons-for-hayley-and-mike',
    'bruce-and-mandy':          'gorgeous-bathroom-for-bruce-and-mandy',
    'herringbone-tile':         'herringbone-tile-finish-and-underfloor-heating',
    'wainwright':               'three-elegant-bathrooms-for-the-wainwright-family',
    'anthony-and-chris':        'stunning-wetroom-for-anthony-and-chris',
    'rachel':                   'epping-up-to-deliver-a-quality-bathroom',
    'stunning-shower-room':     'stunning-shower-room-for-julie-and-neal',
    'shower-room-and-bathroom': 'a-shower-room-and-bathroom-for-ste-and-jo',
    'sharon-and-lee':           'two-beautiful-bathrooms-for-sharon-and-lee',
    'ecclestone':               'brand-new-bathroom-for-the-ecclestone-family',
    'carter-project':           'bathroom-creation-for-the-carters',
    'melanie-and-chris':        'amazing-bathrooms-for-melanie-and-chris',
    'ken-and-lisa':             'every-bathroom-for-ken-and-lisa',
    'ste-and-tracey':           'ste-tracey-stunning-bathroom',
    'janes':                    'janes-project',
    'img_':                     'our-picture-gallery-of-completed-projects',
    '766cb17f':                 'traditional-bathrooms',
    '74378818':                 'hi-tech-bathrooms',
}

# Filename prefixes that are clearly Pixabay / theme-demo stock, not real LV project photos
STOCK_PREFIXES = (
    'winter-', 'architecture-', 'villa-', 'house-', 'balcony-', 'lawn-', 'exterior-',
    'adult-', 'boy-', 'girl-', 'woman-', 'man-', 'kitchen-', 'bathroom-tub',
    'interior-', 'mattress-', 'stock-', 'sample-',
)


def classify(m):
    f = (m.get('file') or '').lower()
    t = (m.get('title') or '').lower()
    s = (m.get('slug') or '').lower()

    # Logo: any file with "bathrooms-by-lv-final" in the name
    if 'bathrooms-by-lv-final' in f or 'bathrooms-by-lv-final' in s:
        return ('logo', None)

    # Van / team
    if '10217573732749630' in f or s == 'lv-van':
        return ('van', None)

    # Liam's headshot
    if s == 'liam-vickers':
        return ('team', None)

    # Service page hero
    if s == 'burst-pipes':
        return ('service_hero', None)

    # Testimonial stock faces + Elementor placeholder
    if s in ('face2', 'face4', 'placeholder2'):
        return ('testimonial_face', None)

    # Stock demo imagery (Pixabay-style from theme demo) — expanded
    if any(s.startswith(p) for p in STOCK_PREFIXES):
        return ('stock_demo', None)
    if s == 'architect' and m.get('width') == 80:  # small 80x80 theme icon
        return ('stock_demo', None)

    # Project galleries — try to match filename prefix to a known project
    for prefix, post_slug in PROJECT_PREFIX_TO_POST.items():
        if s.startswith(prefix):
            return ('project', post_slug)

    # Unclassified — keep for manual review
    return ('other', None)


groups = {'logo': [], 'team': [], 'van': [], 'service_hero': [],
          'testimonial_face': [], 'stock_demo': [],
          'project': [], 'other': []}
project_by_post = {}   # post_slug -> [media items]
for m in MEDIA:
    grp, post_slug = classify(m)
    groups[grp].append(m)
    if grp == 'project' and post_slug:
        project_by_post.setdefault(post_slug, []).append(m)

manifest_md = ['# Asset Manifest', '',
               f'Total: **{len(MEDIA)}** items exported from WordPress Media Library on '
               f'{BUNDLE["exported_at"][:10]}.',
               '',
               'Each item lists: `[WP id]` `slug` — `source_url` `(dimensions)`.',
               '',
               '> **Alt text audit**: All 195 items have empty `alt_text` in the WP database.',
               '> This is a quick SEO/accessibility win for the rebuild — Claude can generate',
               '> alt text for every image from its filename and project context.',
               '',
               '---', '']

section_titles = {
    'logo':             'Logo & brand marks',
    'van':              'Van / team photos',
    'testimonial_face': 'Testimonial face images  ⚠ stock demo images, to review',
    'stock_demo':       'Stock / theme-demo imagery (not LV project photos — DO NOT migrate)',
    'project':          'Project imagery (grouped by case study)',
    'other':            'Unclassified',
}

for key, label in section_titles.items():
    manifest_md.append(f'## {label}')
    manifest_md.append(f'*{len(groups[key])} items*')
    manifest_md.append('')
    if key == 'project':
        # Group the project imagery by post slug
        for post_slug, items in sorted(project_by_post.items()):
            manifest_md.append(f'### `/{post_slug}` — {len(items)} images')
            manifest_md.append('')
            for m in sorted(items, key=lambda x: x['id']):
                dim = f'{m.get("width")}×{m.get("height")}' if m.get('width') else '—'
                manifest_md.append(f"- [{m['id']}] `{m['slug']}` — {m['source_url']}  ({dim})")
            manifest_md.append('')
    else:
        for m in sorted(groups[key], key=lambda x: (x.get('date', ''), x['id'])):
            dim = f'{m.get("width")}×{m.get("height")}' if m.get('width') else '—'
            manifest_md.append(f"- [{m['id']}] `{m['slug']}` — {m['source_url']}  ({dim}, {m['mime_type']})")
        manifest_md.append('')

(docs_dir / 'asset-manifest.md').write_text('\n'.join(manifest_md))
print('  wrote docs/asset-manifest.md')

# Machine-readable versions — split into keep-for-rebuild vs discard
keep_urls = [m['source_url'] for m in MEDIA
             if classify(m)[0] not in ('stock_demo', 'testimonial_face')]
discard_urls = [m['source_url'] for m in MEDIA
                if classify(m)[0] in ('stock_demo', 'testimonial_face')]
(docs_dir / 'media-urls-keep.txt').write_text('\n'.join(keep_urls) + '\n')
(docs_dir / 'media-urls-discard.txt').write_text('\n'.join(discard_urls) + '\n')
print(f'  wrote docs/media-urls-keep.txt  ({len(keep_urls)} items — for wget -i)')
print(f'  wrote docs/media-urls-discard.txt  ({len(discard_urls)} stock items — not needed)')

# Full JSON manifest including the grouping decision and per-project mapping
manifest_json = {
    'exported_at': BUNDLE['exported_at'],
    'total': len(MEDIA),
    'groups': {k: [{'id': m['id'], 'slug': m['slug'], 'url': m['source_url'],
                    'width': m.get('width'), 'height': m.get('height'),
                    'mime': m['mime_type'], 'file': m.get('file'),
                    'alt': m.get('alt_text'), 'title': m.get('title'),
                    'caption': m.get('caption')}
                   for m in v] for k, v in groups.items()},
    'project_images_by_post_slug': {
        post_slug: [m['source_url'] for m in sorted(items, key=lambda x: x['id'])]
        for post_slug, items in project_by_post.items()
    },
}
(docs_dir / 'asset-manifest.json').write_text(json.dumps(manifest_json, indent=2))
print('  wrote docs/asset-manifest.json')


# ---------------------------------------------------------------------------
# docs/seo-manifest.md
# ---------------------------------------------------------------------------

seo_md = ['# SEO Manifest', '',
          'Existing Yoast SEO titles, descriptions and canonical URLs captured from the',
          'live WordPress site.  **Preserve these verbatim in the rebuild** so that',
          'established search-engine rankings carry over unchanged.',
          '',
          '---', '', '## Pages', '']

for p in sorted(PAGES, key=lambda x: x['id']):
    y = p.get('yoast') or {}
    seo_md.extend([
        f"### {p['title']}",
        f'- **Slug**: `/{p["slug"]}`',
        f'- **Original URL**: {p["link"]}',
        f'- **SEO title**: {y.get("title") or "_(none)_"}',
        f'- **Meta description**: {y.get("description") or "_(none)_"}',
        f'- **Canonical**: {y.get("canonical") or "—"}',
        f'- **OG image**: {y.get("og_image") or "—"}',
        f'- **Robots**: {y.get("robots") or "—"}',
        '',
    ])

seo_md.extend(['## Posts (case studies)', ''])
for p in sorted(POSTS, key=lambda x: x['date'], reverse=True):
    y = p.get('yoast') or {}
    seo_md.extend([
        f"### {p['title']}",
        f'- **Slug**: `/{p["slug"]}`',
        f'- **Original URL**: {p["link"]}',
        f'- **Date**: {p["date"][:10]}',
        f'- **SEO title**: {y.get("title") or "_(none)_"}',
        f'- **Meta description**: {y.get("description") or "_(none)_"}',
        f'- **OG image**: {y.get("og_image") or "—"}',
        '',
    ])

(docs_dir / 'seo-manifest.md').write_text('\n'.join(seo_md))
print('  wrote docs/seo-manifest.md')


# ---------------------------------------------------------------------------
# docs/brand-and-styling.md
# ---------------------------------------------------------------------------

brand_md = """# Brand & Styling — captured from live site

Source: computed styles from `https://lvbathrooms.co.uk/` (Futurio theme + Elementor 4.0.3),
supplemented by widget settings harvested from the Elementor page data.

## Colour palette

| Role                                    | Hex       | Notes                                              |
|-----------------------------------------|-----------|----------------------------------------------------|
| **Primary accent (CTA buttons)**        | `#FF003F` | Raspberry-red; used on all buttons, hover `#FFF`   |
| **Headline red** (H1, rotating words)   | `#DD3333` | Warmer red; H1 and animated headline rotating text |
| Hero overlay text                       | `#FFFFFF` | On black hero                                      |
| Hero subtitle                           | `#CCCCCC` | Light grey on dark hero                            |
| Body text                               | `#686868` | Neutral grey                                       |
| Nav links                               | `#00AFF2` | ⚠ Odd cyan; likely a Futurio default. Recommend reviewing in rebuild. |
| Off-white section background            | `#F9F9F9` | Subtle alternation                                 |
| Secondary section background            | `#F4F4F4` |                                                    |
| Dark hero / footer BG                   | `#1E1E1E` | Near-black                                         |
| True black hero background              | `#000000` | Used for the animated-headline hero                |
| Logo colour (from kit custom colours)   | `#4054B2` | Saved but not used prominently                     |

## Typography

Single typeface throughout: **Oswald** (Google Fonts).  The kit also loads Roboto and
Roboto Slab but they are barely used in the visible UI.

| Element                      | Family | Size | Weight | Other                       |
|------------------------------|--------|------|--------|------------------------------|
| H1                           | Oswald | 30 px | 700    | Colour `#DD3333`             |
| Hero H2 (animated headline)  | Oswald | 62 px | 900    | White, uppercase             |
| Project title H2             | Oswald | 26 px | 700    | Colour `#686868`             |
| Body copy                    | Oswald | 17 px | 300-400| Line-height 27.2 px          |
| Nav links                    | Oswald | 18 px | —      | Uppercase                    |
| Buttons                      | Oswald | 14 px | 700    | Uppercase, padding `20px 50px`, radius `6px` |
| Counter labels               | Oswald | 17 px | 300    |                              |

## Layout features to preserve

- **Animated rotating-text hero** — key signature element.  Five alternating words cycle behind a fixed "We make beautiful" prefix: Bathrooms, Wet Rooms, Powder Rooms, Toilets, Lavatories, Water Closets, Privy's.
- **Three-column "room type" cards** in section 2 with decorative horn icons (Bathroom / Cloakroom / en suite).
- **Counter band** — "Bathrooms 500+ · Cloakrooms 250+ · En Suites 750+".
- **Three service cards** (Emergency Repairs · Refurbishment · Creation), each with a short pitch and a Find Out More button.
- **About section** with the van photo + team copy.
- **Testimonial block** — two reviewer quotes with a face avatar.
- **Recent projects strip** (originally populated by `[futurio-posts]` shortcode — must be replicated as a real component).
- **Contact block** at the bottom with the architectural overlay background image.

## Known styling issues worth fixing in rebuild

1. The site displays as 40 stylesheets (WordPress + Bootstrap 3.3.7 + Elementor 4.0.3 + Futurio Extra + Yoast + Jetpack + Site Kit).  A static rebuild can serve a single minified CSS bundle well under 50 KB.
2. Bootstrap 3.3.7 is EOL since 2019; remove entirely in the rebuild.
3. Nav link colour `#00AFF2` looks unintentional against this palette.  Propose switching to the accent red or keeping white on dark.
4. All 195 media items have empty alt text in WordPress.
"""
(docs_dir / 'brand-and-styling.md').write_text(brand_md)
print('  wrote docs/brand-and-styling.md')


# ---------------------------------------------------------------------------
# docs/site-architecture.md
# ---------------------------------------------------------------------------

arch_md = """# Site Architecture

## URL structure (exactly preserved from live site)

| Current URL                                       | WP ID | New path              | Notes                           |
|---------------------------------------------------|-------|-----------------------|---------------------------------|
| `/`                                               | 31    | `/`                   | Home (renamed from `bathrooms` slug) |
| `/emergency-repairs`                              | 309   | `/emergency-repairs`  |                                 |
| `/refurbishment`                                  | 104   | `/refurbishment`      |                                 |
| `/bathroom-creation`                              | 311   | `/bathroom-creation`  |                                 |
| `/contact`                                        | 72    | `/contact`            |                                 |
| `/blog`                                           | 56    | `/projects`           | Rename recommended — the live site already labels the nav item "Projects" |
| `/privacy-policy`                                 | 3     | `/privacy-policy`     | Currently in DRAFT — needs content before launch |
| `/{post-slug}` (18 posts at root level)           | —     | `/projects/{post-slug}` | Scope case studies under `/projects/` — see REDIRECTS below |

## Navigation

Primary nav, in order, exactly as on live site:
1. Home
2. Projects (links to the blog index)
3. Services (anchor link to `#services-start` on the home page)
4. Contact

The "Services" dropdown on the live site is actually a same-page anchor — the three service pages (Emergency Repairs / Refurbishment / Bathroom Creation) are linked only from the home page's three service cards, not from the global nav.  The rebuild can either keep that or promote Services to a proper dropdown.

## Categories & tags

| Taxonomy   | Item              | Count | Notes                                   |
|------------|-------------------|-------|-----------------------------------------|
| Category   | Blog              | 16    | Most case studies                       |
| Category   | Projects          | 2     | Just `hi-tech-bathrooms` + `traditional-bathrooms` — probably should be merged into Blog/Projects |
| Category   | News              | 0     | Delete in rebuild                       |
| Category   | Uncategorized     | 0     | Delete                                  |
| Tag        | Bathrooms         | 9     | Keep                                    |
| Tag        | En-suites         | 9     | Keep                                    |
| Tag        | ensuites          | 0     | Zombie — delete                         |
| Tag        | tag1 … tag5       | 0     | Demo-leftover zombies — delete          |

Recommendation: single category `Projects`, two tags `bathrooms` + `en-suites`.  The "Blog" vs "Projects" split on the live site has no user-facing purpose.

## Redirects to set up (to preserve inbound links + SEO)

If we scope case studies under `/projects/{slug}`, add permanent (301) redirects from:
```
/{post-slug}             →  /projects/{post-slug}
/blog                    →  /projects
/blog/page/2             →  /projects?page=2  (or /projects/page/2 depending on routing)
/blog/page/3             →  /projects?page=3
/author/liam_v           →  /projects
/category/blog           →  /projects
/category/projects       →  /projects
/tag/bathrooms           →  /projects?tag=bathrooms
/tag/en-suites           →  /projects?tag=en-suites
```

Keeping the post slugs identical means no other permalink work is required.

## Sitemap

Yoast currently generates sitemaps at `/sitemap_index.xml` and per-type sitemaps below it.  Rebuild should generate an equivalent `/sitemap.xml` at launch.
"""
(docs_dir / 'site-architecture.md').write_text(arch_md)
print('  wrote docs/site-architecture.md')


# ---------------------------------------------------------------------------
# docs/content-audit.md — issues we've discovered
# ---------------------------------------------------------------------------

audit_md = """# Content Audit — issues found during export

## ✅ Already fixed in this package

### Spam paragraph removed
The homepage contained this paragraph, clearly a spam injection (either from a
compromised WordPress plugin or left over from a template):

> "At present information about remedies changes regularly. Let's talk about [divers medicaments](https://www.smallbusinessconnection.com/falsified-drugs-flood-north-american-markets) you can get from Internet."

**Status**: stripped from `content/pages/home.md` during the build.  The live WordPress
site still contains it — it'll disappear when we cut DNS over to the rebuild.  If
you'd like it removed from the live site before then, it's inside the "About us" prose
block on the homepage in the Elementor editor.

---

## 🔴 Broken links on live homepage

Two of the three "Find out more" buttons in the Services section point at URLs that return 404:

| Button              | Current link                                       | Actual page                          |
|---------------------|----------------------------------------------------|--------------------------------------|
| Emergency Repairs   | `/bathroom-emergency-repairs-maintenance`          | **`/emergency-repairs`** (id 309)    |
| Refurbishment       | `/custom-featured-image-height`                    | **`/refurbishment`** (id 104)        |
| Creation            | `/bathroom-creation`                               | `/bathroom-creation` — OK            |

These will be correctly linked in the rebuild.  Per Mike's instruction, the live WP site is not being modified.

## 🟠 Stock demo images still in use

The site was built from a Futurio theme demo and several placeholder images were never swapped for real content:

| Location                 | Current source                                                                                                          | Action                               |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| Testimonial 1 face       | `https://futuriodemos.com/architect-demo/.../face2.png`                                                                 | Ask LV for a real photo, or remove   |
| Testimonial 2 face       | `https://futuriodemos.com/architect-demo/.../face4.png`                                                                 | Same                                 |
| Contact section background | `https://futuriodemos.com/architect-demo/.../architecture-1048092_1280.jpg` (cross-domain architectural stock)        | Replace with a real project photo    |
| Bathroom Creation page testimonial placeholder | `/wp-content/plugins/elementor/assets/images/placeholder.png`                                       | Remove or replace                    |

## 🟠 Paragraph that reads as spammy/AI content

The "About us" prose on the home page contains this line that feels out of place and links to an external low-quality site:

> "At present information about remedies changes regularly. Let's talk about [divers medicaments](https://www.smallbusinessconnection.com/falsified-drugs-flood-north-american-markets) you can get from Internet."

**Recommendation: remove in the rebuild.** It looks like either an SEO spam injection from a compromised plugin, or content left over from a template. It has no business being on a bathroom-fitting site.

## 🟠 Privacy Policy is in draft status

Page ID 3 (`/privacy-policy`) is in `status: draft` — meaning it returns 404 on the live site.  A published Privacy Policy is a GDPR/UK-DPA requirement for any site collecting contact-form data.  Recommend drafting and publishing one as part of the rebuild.

## 🟡 Empty alt text on every image

All 195 media items have `alt_text=""` in the WP database.  This hurts SEO and accessibility.  Easy win: generate descriptive alt text during the rebuild (Claude can do this in bulk based on filenames + project context).

## 🟡 Typos on live site

- "Luxury bathroom**'**s at affordable prices" — stray apostrophe in the site tagline (should be plural "bathrooms", not possessive).
- Homepage intro: "anything that you**'**e seen whilst perusing instagram, pintrest" — "you've" and "Pinterest" both misspelled.
- Homepage intro: "Bathroom**'**s" (repeated possessive issue).
- Contact form free-quote page title: "for a free **quatation**" — should be "quotation".
- Blog post Sep 2021: slug `/epping-up-to-deliver-a-quality-bathroom` is missing a leading **St** — should be `stepping-up-...`.  Live URL works but it's not ideal.
- Various project posts have stray capitalisation (e.g. "**dickie**" should be "Dickie" in the Mariah & Dickie testimonial attribution).

## 🟡 Zombie tags and categories

Tags `ensuites`, `tag1`, `tag2`, `tag3`, `tag4`, `tag5` have zero posts and are leftover from the theme demo.  Categories `News` and `Uncategorized` have zero posts.  Prune in rebuild.

## 🟡 Performance / tech debt

The live site loads 40 stylesheets and uses Bootstrap 3.3.7 (end-of-lifed 2019).  A plain static rebuild will be significantly faster and more secure.
"""
(docs_dir / 'content-audit.md').write_text(audit_md)
print('  wrote docs/content-audit.md')


# ---------------------------------------------------------------------------
# docs/rebuild-plan.md
# ---------------------------------------------------------------------------

rebuild_md = """# Rebuild Plan

Target: a static, GitHub-hosted, Claude-maintainable version of Bathrooms by LV at
`github.com/MPB-Group/lvbathrooms` (mirroring the MPB-Events repo pattern).

## Principles

1. **Preserve the brand**: the Oswald-everywhere typography, the red-on-black hero, the raspberry CTA, the van photo and van-in-the-drive visual language are what makes this feel like *LV's* site, not a generic bathroom fitter.  The rebuild keeps them.
2. **Preserve SEO**: identical URL structure, identical Yoast titles and meta descriptions, 301 redirects where slugs move under `/projects/`.
3. **Fix the obvious bugs** (broken homepage buttons, stock demo faces, spammy out-of-place sentence, typos) in the same commit that ships the rebuild.
4. **Move content to markdown** so every future edit is a commit, reviewable in GitHub, and editable by Claude.
5. **Keep it simple**: no WordPress, no Elementor, no Bootstrap, no 40 stylesheets.

## Stack (recommended)

- **11ty (Eleventy)** — generates static HTML from the markdown files in `content/pages/` and `content/posts/`.  Familiar to anyone who can read HTML, zero JS framework required, renders fast.
- **Vanilla CSS** with custom properties for the palette (no Tailwind, no framework — keep CSS specific and readable).  One stylesheet, under ~15 KB gzipped.
- **No JS framework**.  Maybe one tiny script for the rotating-word hero animation (~30 lines of vanilla JS).
- **GitHub Pages** or **Cloudflare Pages** for hosting.  Cloudflare Pages is preferred — free custom domain, automatic HTTPS, global CDN, Pull-Request previews.

The MPB-Events repo uses a slightly more basic plain-HTML approach.  For Bathrooms by LV, 11ty earns its keep because there are 18 case-study posts (and counting) that benefit from a real collection + templating system rather than hand-written HTML files.  If you'd prefer to match MPB-Events exactly, say the word — everything below still works, we just hand-generate the HTML from the same markdown sources.

## Step-by-step

### 1. Create the GitHub repo *(your action)*
- New repo at `MPB-Group/lvbathrooms`, private initially.
- Grant Claude access via a fine-grained personal access token scoped to this repo only.  **Do not paste the token into chat** — create it, store it in 1Password, and when we get to the push step, paste it into a browser prompt dialog that clears after use (same approach we used for MPB-Events).

### 2. Download the media library to your Mac *(your action — see commands below)*
The sandbox can't pull images from `lvbathrooms.co.uk`, but your Mac can.  On your Mac:

```bash
cd ~/Downloads
mkdir lvbathrooms-media && cd lvbathrooms-media
# Use the URL list generated in docs/media-urls.txt
wget --content-disposition -i /path/to/media-urls.txt
# Or with curl:
# xargs -n1 curl -O < /path/to/media-urls.txt
```

195 files, roughly 80-150 MB total.  When complete, zip or attach the folder back and I'll process it into the repo structure.

### 3. WXR backup download *(optional, 2 minutes)*
Still from the WordPress admin, `Tools → Export → Download Export File`.  That XML is a point-in-time backup of the whole site — keep a copy somewhere safe even if we never need to import it.

### 4. Generate the rebuild skeleton *(Claude's action, next session)*
Once the media files are in the sandbox, Claude will:

- Scaffold an 11ty project in the repo root (`_includes/`, `_data/`, `src/`, `eleventy.config.js`).
- Copy media files to `src/assets/images/` in an organised tree (`logo/`, `general/`, `projects/{slug}/`).
- Generate one template per page type: `home.njk`, `page.njk`, `project.njk`, `projects-index.njk`, `contact.njk`.
- Write a single stylesheet at `src/assets/styles/site.css` using the captured palette + Oswald + layout tokens from `brand-and-styling.md`.
- Copy the page markdown from `content/pages/` and post markdown from `content/posts/` into 11ty's collection structure.
- Fill in alt text for every image from filenames + project context.
- Fix the broken button links, remove the spammy sentence, correct typos.
- Ship a Privacy Policy boilerplate for Mike to review.
- Wire up the Cloudflare Pages deployment config (`wrangler.toml` or Pages build settings via GH Actions).

### 5. Review + preview *(your action)*
Claude opens a PR on the repo.  Cloudflare Pages auto-builds a preview URL.  You review, request changes, merge when happy.

### 6. DNS cutover *(your action)*
Point `lvbathrooms.co.uk` DNS at Cloudflare Pages.  Old WP host can be decommissioned once traffic is stable — or kept as a backup for a month before cancelling the subscription.

## Post-launch: how future changes work

- **New project case study**: add a new `.md` file to `content/posts/` + drop the photos into `src/assets/images/projects/{slug}/`.  Ask Claude to write the copy + alt text.  PR → merge → live in ~2 minutes.
- **Copy tweak on any page**: tell Claude what to change, Claude opens a PR, you merge.
- **New service page / new testimonial / price changes**: same workflow.
- **SEO updates**: meta titles and descriptions live in the markdown frontmatter, same PR workflow.

## What I have NOT captured from WordPress and may need later

| Thing                          | Where it lives in WP                                          | Do we need it? |
|--------------------------------|---------------------------------------------------------------|-----------------|
| Comments                       | WP DB (13 comment instances in the blog posts)                | No — site isn't really using them |
| Contact form submissions       | WP DB (Jetpack Contact Forms Responses)                       | No — that's historical correspondence, not site content |
| Google Search Console data     | Site Kit plugin                                               | Re-connect after launch from the new site |
| Google Analytics history       | Jetpack / Site Kit                                            | Re-connect to GA4; previous data stays in GA |

## What happens to the live WordPress site?

Recommended sequence:
1. Keep it running, untouched, during the rebuild.
2. When the new site is approved on a preview URL, do DNS cutover during a low-traffic window (e.g. Sunday evening).
3. Leave the old WP install live but hidden (move to a `legacy.` subdomain or an IP-only URL) for 30 days so anything missed can be pulled over.
4. After 30 days of stable traffic, cancel the WP hosting.
"""
(docs_dir / 'rebuild-plan.md').write_text(rebuild_md)
print('  wrote docs/rebuild-plan.md')


# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------

print()
print('=' * 60)
print('PACKAGE BUILD COMPLETE')
print('=' * 60)
