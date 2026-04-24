# Site Architecture

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
