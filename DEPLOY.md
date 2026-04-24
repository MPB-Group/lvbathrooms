# Deployment — Cloudflare Pages

## One-time setup

### 1. Create the Cloudflare Pages project

1. Log in to your Cloudflare dashboard.
2. **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
3. Authorise GitHub and select the `MPB-Group/lvbathrooms` repo.
4. Set up the build:

   | Setting                  | Value                               |
   |--------------------------|-------------------------------------|
   | Production branch        | `main`                              |
   | Framework preset         | None                                |
   | Build command            | `cd site && npm install && npm run build` |
   | Build output directory   | `site/_site`                        |
   | Root directory (advanced)| *(leave blank)*                     |

5. Click **Save and Deploy**.  The first build takes ~90 seconds.

### 2. Set the Node version

In the Pages project dashboard: **Settings → Environment variables → Add**:

| Variable name   | Value   | Environment |
|-----------------|---------|-------------|
| `NODE_VERSION`  | `20`    | Both        |

Without this, Cloudflare uses an old default Node version that 11ty won't support.

### 3. Wire up the custom domain

Once the first deploy is green:

1. Project → **Custom domains** → **Set up a custom domain**
2. Enter `lvbathrooms.co.uk` (apex) — Cloudflare will prompt you to update DNS.
3. Optionally add `www.lvbathrooms.co.uk` and configure it to 301-redirect to the apex.
4. Cloudflare provisions an SSL certificate automatically.  Usually takes <1 minute.

At this point `lvbathrooms.co.uk` routes to the Pages project.

### 4. Cutover checklist

Before switching DNS from the current WordPress host to Cloudflare Pages:

- [ ] Preview URL looks right in desktop + mobile Chrome/Safari/Firefox
- [ ] All internal links resolve (no 404s)
- [ ] Favicon shows in the tab
- [ ] All project pages have gallery images
- [ ] Contact form (if added) is tested end-to-end
- [ ] Yoast meta titles & descriptions visible in Page Source
- [ ] Sitemap at `/sitemap.xml` (add before launch — planned v1.1)
- [ ] Google Search Console re-verified against the new host
- [ ] 301-redirect rules from old WP slugs to new `/projects/{slug}` routes set up in Cloudflare Page Rules or `_redirects` file

## Day-to-day

After the initial setup, deployment is automatic:

- Any push to `main` triggers a production build.
- Any push to a feature branch creates a preview URL like `https://{hash}.lvbathrooms.pages.dev`.
- Pull request previews are linked from the PR conversation on GitHub.

## Rolling back a bad deploy

Pages keeps every deploy.  Roll back by:

1. Project → **Deployments**.
2. Find the last-known-good deploy.
3. Click **…** → **Rollback to this deployment**.

Takes ~5 seconds.  The old WP site remains available (at the host's own IP or at a `legacy.` subdomain if configured) for 30 days post-cutover — see `docs/rebuild-plan.md`.
