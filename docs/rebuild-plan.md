# Rebuild Plan

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
