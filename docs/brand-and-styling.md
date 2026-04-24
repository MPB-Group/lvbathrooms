# Brand & Styling — captured from live site

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
