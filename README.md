# Bathrooms by LV — site rebuild package

This repository contains everything needed to rebuild and maintain
[lvbathrooms.co.uk](https://lvbathrooms.co.uk) as a static, GitHub-managed site.

It replaces a WordPress install (Futurio theme + Elementor 4.0.3) with a plain
Eleventy-built static site, while preserving all existing content, URLs, and
SEO metadata.

---

## Quick start

```bash
cd site
npm install
npm run dev   # dev server at http://localhost:8080
```

See [`site/README.md`](site/README.md) for full dev/editing docs and
[`DEPLOY.md`](DEPLOY.md) for the Cloudflare Pages setup.

---

## Repo layout

```
lvbathrooms/
├── README.md                 ← you are here
├── DEPLOY.md                 Cloudflare Pages setup + go-live checklist
├── wrangler.toml             Cloudflare Pages config (machine-readable)
│
├── site/                     ▶ the actual 11ty site (deploy this)
│   ├── README.md             dev + editing docs
│   ├── package.json
│   ├── .eleventy.js
│   ├── src/                  content, layouts, partials, data
│   └── public/               images + static files (copied verbatim on build)
│
├── docs/                     migration docs & planning
│   ├── rebuild-plan.md
│   ├── content-audit.md
│   ├── site-architecture.md
│   ├── brand-and-styling.md
│   ├── seo-manifest.md
│   ├── asset-manifest.md
│   ├── asset-manifest.json
│   ├── alt-text.md
│   ├── alt-text.json
│   ├── media-urls-keep.txt
│   └── media-urls-discard.txt
│
├── content/                  WP content extracted as markdown (reference)
│   ├── pages/                7 page files with YAML frontmatter
│   └── posts/                18 project files
│
└── source/                   raw inputs & generator scripts (reproducibility)
    ├── lvbathrooms-content-bundle-2026-04-23.json    full WP export
    ├── build_package.py       generates docs/ + content/ from bundle
    ├── sort_media.py          generates site/public/images/ + alt-text from media folder
    └── build_site_content.py  generates site/src/ from content/
```

`site/` is the actual product — what gets deployed.  `docs/`, `content/`, and
`source/` are reference materials kept in the repo so the migration is
reproducible and auditable.  They could be removed after launch without
affecting the live site, but they're cheap to keep (a few hundred KB of text).

The production images live at `site/public/images/` — 178 files, ~49 MB —
served from `/images/…` on the deployed site.

---

## What changed from the WordPress site

SEO-visible content is preserved exactly:

- ✅ Same URL structure for pages and services
- ✅ Same Yoast SEO titles & descriptions on every page
- ✅ All 18 case studies migrated with their dates, titles, tags, and photo galleries
- ✅ All 178 real project/brand/team images migrated
- ✅ 301 redirects configured for any URL that moves (see `site/public/_redirects`)

Cleanups / improvements:

- 🧹 **Spam paragraph removed** — a "divers medicaments" link had been injected into the homepage About section
- 🧹 **Two broken homepage buttons fixed** — they pointed to non-existent service-page slugs
- 🧹 **Demo theme images dropped** — 14 leftover Pixabay-style stock photos from the original theme
- 🧹 **All 178 images now have descriptive alt text** — the WP media library had empty `alt` on every item
- 🧹 **Zombie tags/categories** (`tag1`–`tag5`, `ensuites`, `News`, `Uncategorized`) not migrated
- 🧹 **Typos to fix at launch** — flagged in [`docs/content-audit.md`](docs/content-audit.md) for Liam's review before going live
- 🚀 **Performance**: dropped from 40 stylesheets + Bootstrap 3.3.7 + Elementor runtime to one hand-written stylesheet (~5 KB gzipped) and a single ~60-line vanilla JS file

See [`docs/content-audit.md`](docs/content-audit.md) for the full list.

---

## Editing & adding content

After launch, every content change is a git commit:

- **Edit existing copy**: find the `.md` file in `site/src/` or `site/src/projects/`, edit, push.
- **New case study**: drop photos in `site/public/images/projects/{slug}/`, add `site/src/projects/{slug}.md` with YAML frontmatter, push.  New project auto-appears in the nav and on the projects index.
- **New service page**: add `site/src/{slug}.md` and a card in `site/src/_data/site.js`.

Each push triggers an automatic Cloudflare Pages rebuild — typically live in
under 90 seconds.  Pull requests get their own preview URLs.

See [`site/README.md`](site/README.md) for the full editing workflow.

---

## Reproducibility

The prep artefacts in `docs/`, `content/`, and `assets/` can all be
regenerated from the raw WordPress export (`source/lvbathrooms-content-bundle-*.json`)
plus the downloaded media folder:

```bash
# Regenerate prep docs + content markdown:
python3 source/build_package.py

# Regenerate sorted assets + alt-text manifest
# (needs /home/claude/media-unpack/lvbathrooms-media/ or similar):
python3 source/sort_media.py

# Regenerate the 11ty site input from content/ + assets/:
python3 source/build_site_content.py
```

If any script needs tweaking — classifier rules, copy sanitisers, IA changes —
edit the script and re-run.  The scripts are idempotent.

---

## Status

- [x] WordPress content exported
- [x] Media library downloaded and sorted
- [x] Brand, IA, SEO documented
- [x] Eleventy site scaffolded
- [x] All content migrated
- [x] Build passes cleanly (25 HTML pages, 1.1s)
- [x] Sitemap, robots.txt, 301 redirects configured
- [ ] Pushed to GitHub (`MPB-Group/lvbathrooms`)
- [ ] Cloudflare Pages project created — see [`DEPLOY.md`](DEPLOY.md)
- [ ] Liam approves preview URL
- [ ] DNS cutover
- [ ] 30-day monitoring period
- [ ] WP host decommissioned
