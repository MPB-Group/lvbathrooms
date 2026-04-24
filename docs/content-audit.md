# Content Audit — issues found during export

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

## ✅ Typos fixed in the rebuild (was: 🟡 on live site)

The items below were flagged during migration.  In the rebuild, `quatation` → `quotation`
has been fixed on the contact page; the homepage copy (`you've`, `Instagram`, `Pinterest`,
`Dickie`, site tagline without stray apostrophe) was rewritten from scratch when we
authored the new homepage template, so those read correctly in the deployed site.

The live WordPress site is untouched — the typos will disappear when DNS cuts over.

Original list:


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
