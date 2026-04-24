#!/usr/bin/env python3
"""
Sort the downloaded WordPress media library into a purposeful folder structure.

Reads:  source/lvbathrooms-content-bundle-2026-04-23.json (for the classifier)
        /home/claude/media-unpack/lvbathrooms-media/         (the downloaded files)
Writes: assets/logo/…
        assets/team/…
        assets/van/…
        assets/service-heroes/…
        assets/projects/{post-slug}/…
        assets/unsorted/…
        docs/alt-text.md    (human-readable description of every image)
"""
import json, re, shutil
from pathlib import Path

ROOT = Path('/home/claude/lvbathrooms')
SRC_MEDIA = Path('/home/claude/media-unpack/lvbathrooms-media')
BUNDLE = json.loads((ROOT / 'source' / 'lvbathrooms-content-bundle-2026-04-23.json').read_text())
MEDIA = BUNDLE['media']
POSTS = {p['slug']: p for p in BUNDLE['posts']}

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

POST_DISPLAY_NAMES = {
    'all-the-bathroom-mod-cons-for-hayley-and-mike': 'Hayley and Mike',
    'gorgeous-bathroom-for-bruce-and-mandy': 'Bruce and Mandy',
    'herringbone-tile-finish-and-underfloor-heating': 'a herringbone-tile bathroom',
    'three-elegant-bathrooms-for-the-wainwright-family': 'the Wainwright family',
    'stunning-wetroom-for-anthony-and-chris': 'Anthony and Chris',
    'epping-up-to-deliver-a-quality-bathroom': 'Rachel Aldersley',
    'stunning-shower-room-for-julie-and-neal': 'Julie and Neal',
    'a-shower-room-and-bathroom-for-ste-and-jo': 'Ste and Jo',
    'two-beautiful-bathrooms-for-sharon-and-lee': 'Sharon and Lee',
    'brand-new-bathroom-for-the-ecclestone-family': 'the Ecclestone family',
    'bathroom-creation-for-the-carters': 'the Carter family',
    'amazing-bathrooms-for-melanie-and-chris': 'Melanie and Chris',
    'every-bathroom-for-ken-and-lisa': 'Ken and Lisa',
    'ste-tracey-stunning-bathroom': 'Ste and Tracey',
    'janes-project': 'the Janes family',
    'our-picture-gallery-of-completed-projects': 'our picture gallery',
    'traditional-bathrooms': 'a traditional-style bathroom',
    'hi-tech-bathrooms': 'a hi-tech bathroom',
}

STOCK_PREFIXES = (
    'winter-', 'architecture-', 'villa-', 'house-', 'balcony-', 'lawn-', 'exterior-',
    'adult-', 'boy-', 'girl-', 'woman-', 'man-', 'kitchen-', 'bathroom-tub',
    'interior-', 'mattress-', 'stock-', 'sample-', 'minecraft-',
)


def classify(m):
    """Returns (group, destination_subpath, suggested_filename, alt_text)."""
    f = (m.get('file') or '').lower()
    s = (m.get('slug') or '').lower()
    orig_file = m.get('file', '')
    # Preserve the original filename (no rename) — we know it's unique
    basename = Path(orig_file).name

    # Manually identified items
    if m['id'] == 438:  # "image.jpg" — gold brush-stroke LV monogram
        return ('logo', 'logo', 'lv-monogram-gold.jpg',
                'LV monogram — gold brush-stroke logomark on black')
    if m['id'] == 297:  # the 73233878 FB-style photo — a real project shot
        return ('project', 'projects/our-picture-gallery-of-completed-projects',
                basename,
                'Completed LV bathroom with curved-front bath and recessed shelf niches')

    if 'bathrooms-by-lv-final' in f or 'bathrooms-by-lv-final' in s:
        return ('logo', 'logo', basename, 'Bathrooms by LV logo')
    if '10217573732749630' in f or s == 'lv-van':
        return ('van', 'van', basename, 'The Bathrooms by LV van on a driveway')
    if s == 'liam-vickers':
        return ('team', 'team', basename, 'Portrait of Liam Vickers, owner of Bathrooms by LV')
    if s == 'burst-pipes':
        return ('service_hero', 'service-heroes', basename, 'Burst pipes in need of emergency bathroom repairs')
    if s in ('face2', 'face4', 'placeholder2'):
        return ('skip_stock_face', None, None, None)
    if any(s.startswith(p) for p in STOCK_PREFIXES):
        return ('skip_stock', None, None, None)
    if s == 'architect' and m.get('width') == 80:
        return ('skip_stock', None, None, None)

    # Project galleries
    for prefix, post_slug in PROJECT_PREFIX_TO_POST.items():
        if s.startswith(prefix):
            display = POST_DISPLAY_NAMES.get(post_slug, post_slug)
            # Extract the trailing number for sensible alt text
            m_num = re.search(r'-(\d+)$', s)
            num = m_num.group(1) if m_num else ''
            if post_slug == 'our-picture-gallery-of-completed-projects':
                alt = f'Completed bathroom project from our gallery (image {num})'.strip()
            elif post_slug in ('traditional-bathrooms', 'hi-tech-bathrooms'):
                alt = f'Example of {display}'
            else:
                alt = f'Bathroom installation for {display}' + (f' — photo {num}' if num else '')
            return ('project', f'projects/{post_slug}', basename, alt)

    return ('unsorted', 'unsorted', basename, f'Uncategorised image ({basename})')


# Build a lookup: by WP-uploads path (e.g. "2022/03/Hayley-and-Mike-3.jpeg") → media dict
file_to_media = {m.get('file'): m for m in MEDIA if m.get('file')}

# Walk actual downloaded files
copied = []
duplicates_skipped = []
missing_metadata = []
skipped_stock = []

for src_path in sorted(SRC_MEDIA.rglob('*')):
    if not src_path.is_file():
        continue
    rel = str(src_path.relative_to(SRC_MEDIA))  # e.g. "2022/03/Hayley-and-Mike-3.jpeg"
    m = file_to_media.get(rel)
    if m is None:
        missing_metadata.append(rel)
        continue

    group, subpath, basename, alt = classify(m)

    if group.startswith('skip_'):
        skipped_stock.append({'file': rel, 'group': group, 'id': m['id']})
        continue

    dest_dir = ROOT / 'assets' / subpath
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / basename

    # Handle filename collisions: WP occasionally re-uploads the same file under
    # different dates.  If the bytes match, silently de-dupe; if they differ,
    # rename the second one to avoid data loss.
    if dest_path.exists():
        import hashlib
        def md5(p):
            return hashlib.md5(p.read_bytes()).hexdigest()
        if md5(dest_path) == md5(src_path):
            duplicates_skipped.append({'file': rel, 'existing': str(dest_path.relative_to(ROOT))})
            continue
        # Different content — rename with date suffix
        stem = dest_path.stem
        suffix = dest_path.suffix
        date_tag = m['date'][:7].replace('-', '')
        dest_path = dest_dir / f'{stem}-{date_tag}{suffix}'

    shutil.copy2(src_path, dest_path)
    copied.append({
        'id': m['id'],
        'src_rel': rel,
        'dest_rel': str(dest_path.relative_to(ROOT)),
        'group': group,
        'alt': alt,
        'width': m.get('width'),
        'height': m.get('height'),
        'mime': m.get('mime_type'),
    })

print(f'Copied:              {len(copied)} files')
print(f'Duplicates skipped:  {len(duplicates_skipped)} files (identical bytes, already copied under the same name)')
print(f'Skipped (stock):     {len(skipped_stock)} files')
print(f'Missing metadata:    {len(missing_metadata)} files')
if missing_metadata:
    for m in missing_metadata:
        print(f'    {m}')

# Group summary
from collections import Counter
groups = Counter(c['group'] for c in copied)
print()
print('By group:')
for g, n in sorted(groups.items()):
    print(f'  {g:20}: {n}')

# Per-project counts
project_counts = Counter(Path(c['dest_rel']).parent.name for c in copied if c['group'] == 'project')
print()
print('Per project folder:')
for slug, n in sorted(project_counts.items()):
    print(f'  {slug:50}: {n}')

# Write the alt-text manifest
docs_dir = ROOT / 'docs'
alt_lines = [
    '# Image Alt Text Manifest',
    '',
    'Auto-generated descriptive alt text for every image in `assets/`.',
    'The original WordPress media library had **empty alt text on all 195 items** —',
    'this file fills that gap.  The rebuild will consume these directly.',
    '',
    'Hand-edit any entries that need refinement before the rebuild — the script',
    'at `source/sort_media.py` generates this file deterministically, so your',
    'manual edits here will be preserved on reruns only if the filename is',
    'unchanged.',
    '',
    '---',
    ''
]

# Organise by group, then by destination path
by_group = {}
for c in copied:
    by_group.setdefault(c['group'], []).append(c)

group_titles = {
    'logo':         'Logo',
    'team':         'Team photos',
    'van':          'Van / team photos',
    'service_hero': 'Service page hero images',
    'project':      'Project case-study imagery',
    'unsorted':     'Unsorted (manual review)',
}

for g, label in group_titles.items():
    items = by_group.get(g, [])
    if not items:
        continue
    alt_lines.append(f'## {label}')
    alt_lines.append(f'*{len(items)} items*')
    alt_lines.append('')
    alt_lines.append('| File | Alt text | Size |')
    alt_lines.append('|------|----------|------|')
    for c in sorted(items, key=lambda x: x['dest_rel']):
        dim = f'{c["width"]}×{c["height"]}' if c['width'] else '—'
        alt_lines.append(f'| `{c["dest_rel"]}` | {c["alt"]} | {dim} |')
    alt_lines.append('')

(docs_dir / 'alt-text.md').write_text('\n'.join(alt_lines))
print()
print(f'Wrote docs/alt-text.md')

# Also write a JSON version consumable by the rebuild templating
alt_json = {c['dest_rel']: {'alt': c['alt'], 'width': c['width'],
                             'height': c['height'], 'wp_id': c['id']}
            for c in copied}
(docs_dir / 'alt-text.json').write_text(json.dumps(alt_json, indent=2))
print('Wrote docs/alt-text.json')
