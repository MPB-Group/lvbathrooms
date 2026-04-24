# Bathrooms by LV — website source

Static site built with [Eleventy](https://www.11ty.dev/).  No framework, no runtime, just HTML + CSS + a tiny bit of JS.

Live site: https://lvbathrooms.co.uk
Repo: https://github.com/MPB-Group/lvbathrooms

---

## Local development

Requires **Node.js 18+** and **npm**.

```bash
git clone https://github.com/MPB-Group/lvbathrooms.git
cd lvbathrooms/site
npm install
npm run dev
```

The dev server runs at http://localhost:8080 and live-reloads on changes.

### Useful scripts

| Command          | What it does                                                   |
|------------------|----------------------------------------------------------------|
| `npm run dev`    | Start dev server on `:8080` with live reload                   |
| `npm run build`  | Build production site to `_site/`                              |
| `npm run clean`  | Delete `_site/`                                                |
| `npm run debug`  | Build with verbose Eleventy debug logging                      |

---

## Directory structure

```
site/
├── .eleventy.js              Eleventy config (collections, shortcodes, filters)
├── package.json
├── public/                   Static files copied verbatim to the site root
│   └── images/               All 178 images, sorted by purpose
│       ├── logo/
│       ├── team/
│       ├── van/
│       ├── service-heroes/
│       └── projects/{slug}/  One folder per case study
└── src/                      Eleventy input
    ├── _data/
    │   └── site.js           Global site config: nav, services, testimonials…
    ├── _includes/
    │   ├── layouts/
    │   │   ├── base.njk      HTML shell: head, nav, footer
    │   │   ├── home.njk      Homepage (hero, sections, CTAs)
    │   │   ├── page.njk      Standard inner page
    │   │   └── post.njk      Project case study
    │   └── partials/
    │       ├── nav.njk
    │       └── footer.njk
    ├── assets/
    │   ├── css/site.css      One hand-written stylesheet
    │   └── js/hero.js        Rotating-word hero + mobile nav + counter rollup
    ├── index.md              Home page (uses home.njk)
    ├── contact.md
    ├── emergency-repairs.md
    ├── refurbishment.md
    ├── bathroom-creation.md
    ├── privacy-policy.md
    └── projects/
        ├── index.njk         Projects index — lists all case studies
        └── {slug}.md         18 case-study files, one per project
```

---

## Editing content

### Changing text on an existing page

Find the corresponding `.md` file in `src/` (for the top-level pages) or `src/projects/` (for case studies).  Edit the markdown, commit, push — Cloudflare Pages rebuilds and publishes automatically.

Every page has YAML frontmatter at the top with its SEO title, meta description, and OG image.  Keep those in sync when the page content changes meaningfully.

### Homepage copy

Much of the homepage (nav items, testimonials, service card taglines, counter values, contact details) lives in **`src/_data/site.js`** rather than `src/index.md` — that's so the same values can be used in multiple layouts (e.g. the footer mirrors the nav).

The homepage's section copy (hero headline, intro paragraphs, room cards, about section) lives in **`src/_includes/layouts/home.njk`**.

### Adding a new project case study

1. Create a new folder of photos at `public/images/projects/{your-slug}/`.  Filenames like `Project-1.jpeg`, `Project-2.jpeg` work fine — they'll be alphabetised by the gallery shortcode.
2. Create a new markdown file at `src/projects/{your-slug}.md`:

   ```markdown
   ---
   layout: layouts/post.njk
   permalink: /projects/{your-slug}/
   title: "A short project title"
   date: 2026-04-24
   seo_title: "A short project title - Bathrooms by LV"
   seo_description: "One or two sentences that'll show as the Google snippet."
   og_image: /images/projects/{your-slug}/Project-1.jpeg
   gallery_dir: {your-slug}
   tags:
     - bathrooms
   ---

   Your project write-up in plain markdown.  A paragraph or two works
   well — the image gallery renders automatically below the body.
   ```

3. Commit + push.  The project auto-appears at `/projects/{your-slug}/` and on the projects index page.

### Adding a new service page

1. Create `src/new-service.md`:

   ```markdown
   ---
   layout: layouts/page.njk
   permalink: /new-service/
   title: "New Service Name"
   seo_title: "New Service Name - Bathrooms by LV"
   seo_description: "What this service is, in 150 characters or less."
   ---

   Your page content here.
   ```

2. If the service should appear as a card on the homepage, add it to the `services` array in `src/_data/site.js`.
3. Commit + push.

---

## Deploy — Cloudflare Pages

The site is hosted on [Cloudflare Pages](https://pages.cloudflare.com/) with a `main`-branch deploy hook.  Configuration is either:

- **In the Cloudflare dashboard**: project → Settings → Builds & deployments
  - Framework preset: *None*
  - Build command: `cd site && npm install && npm run build`
  - Build output directory: `site/_site`
  - Root directory: (leave blank — repo root)
  - Node version: `18` or higher (set via `NODE_VERSION` env var)

- **Via `wrangler.toml`** at the repo root (already committed — no extra setup needed).

Each push to `main` triggers a production deploy.  Each PR gets its own preview URL.

### DNS

The production domain `lvbathrooms.co.uk` is a CNAME to the Cloudflare Pages project.  The `www.` subdomain is configured as a 301 redirect to the apex domain.

---

## Architecture notes

- **No JavaScript framework.**  Everything is static HTML at build time.  The only runtime JS is ~60 lines in `src/assets/js/hero.js` for the rotating hero word, mobile nav toggle, and counter rollup.  That file is optional — the site works fully without it.
- **Single stylesheet.**  ~5 KB gzipped, hand-written, uses CSS custom properties for the palette.
- **Fonts.**  Oswald via Google Fonts with `font-display: swap`.  Preconnect hints are in the `<head>` for a fast first paint.
- **Images.**  All 178 images are served from `/images/` as-is.  No build-time image optimisation in v1 — can be added later with [@11ty/eleventy-img](https://www.11ty.dev/docs/plugins/image/) if LCP metrics indicate a need.
- **SEO.**  Every page has a Yoast-style `<title>` and meta description carried over from the original WordPress site.  OG tags are set from the same frontmatter.  A `sitemap.xml` and `robots.txt` should be added before launch (v1.1).

---

## Troubleshooting

**"Cannot find module '@11ty/eleventy'"** — run `npm install` inside `site/`.

**Build fails with "filter not found: X"** — we're using Eleventy's Nunjucks engine.  Only built-in Nunjucks filters + the ones registered in `.eleventy.js` are available.  If you need a new filter, add it there.

**Changes don't appear in dev** — the dev server sometimes misses new files.  Ctrl-C and re-run `npm run dev`.

**Images 404** — check the path matches a file under `public/images/`.  Paths in markdown/Nunjucks should start with `/images/`.

---

## Content preservation

The rebuild inherits content from the previous WordPress site unchanged in SEO-visible places (page titles, meta descriptions, URL structure).  See the top-level `../README.md` and `../docs/` for the full migration notes.
