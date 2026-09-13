# paperskyline.org — Website Design

**Date:** 2026-09-13 · **Status:** approved (brainstorm 2026-09-13; owner approved approach A+2 and asked for the
full build without further decision gates)
**Game:** `game-paper-flights` — Paper Skyline, Unity 6, unreleased.
**Model:** `uvstracker-app/uvstracker-website`, whose chassis this adopts wholesale.

## 1. Goal

A marketing-first site for Paper Skyline that is already carrying the legal pages the stores will ask for. The
landing page sells the game; privacy, terms and support are complete and honest but secondary.

The game is not published. The site therefore ships with the store-badge slot built and **unlinked** — one `href`
per badge is the whole of launch day.

## 2. Decisions taken in the brainstorm

| Question | Decision |
|---|---|
| Load-bearing job | Marketing first; legal complete but secondary. |
| Primary CTA | Store badges present and inert. No email capture, no devlog. |
| Visuals | Hand-written inline SVG in the game's palette. No screenshots, no build step, never blocked on the Unity build. |
| Page set | `index` + `privacy` + `terms` + `support` + `404`. No cities page, no how-to-play page. |
| Languages | English only. No `vi/` mirror. |
| Domain | `paperskyline.org`, apex canonical. |
| Aesthetic | Approach A (uvstracker chassis, paper skin) plus two moves from B: graph-paper ground everywhere, exactly one tilted card per section. |

## 3. Architecture

Hand-written static HTML and one stylesheet. Zero JavaScript (JSON-LD excepted). No framework, no build step, no
dependencies. GitHub Pages from `main` at root.

```
index.html  privacy.html  terms.html  support.html  404.html
styles.css            # tokens + every component, light/dark via prefers-color-scheme
brand/                # mark.svg and the export wrappers that render every icon
tools/                # check.sh, shots.sh — the verification harness
sitemap.xml  robots.txt  site.webmanifest  CNAME
```

Art is inline `<svg>` in the page, not files: the hero skyline, the three step glyphs, the blueprint plane. It is
the same decision the game itself made — Paper Skyline draws its world in code rather than shipping images — so the
site's art has the same provenance as the game's.

## 4. Design system

Tokens are the game's, taken from `2026-09-12-paper-skyline-design.md` §4 rather than invented:

- **Paper** `#f6efd9` · **Desk** `#ece4cf` · **Ink** `#2a2622` · **Marker red** `#c9463d` · **Coin gold** `#f4d47c`
  · **Amber** `#e6a24a` · **Blueprint** `#1f3a5f` · **Blueprint line** `#e8eef7`.
- Plane facets `#ffffff` / `#e6ebf1` / `#cbd4de` / `#b3bec9`, hairline edge `rgba(110,125,140,.55)`.
- **Type:** Caveat 700 for headlines and numbers, Patrick Hand for sentences and labels — the two faces the game is
  set in, both served by Google Fonts.
- **Cards and buttons:** 2–3 px ink border, hard offset shadow, no rounded corners, no gradients except sky.

**Dark mode is the Garage blueprint.** The game already owns a dark surface — `#1f3a5f` with `#e8eef7` line work,
16 px and 80 px grids — so `prefers-color-scheme: dark` swaps the paper ground for blueprint rather than inventing a
theme. Every colour is defined on bare `:root` first and only redefined inside the dark block.

**The two borrowed moves.** The graph-paper ground is a 40 px repeating-linear-gradient on `body`, present at every
width. Rotation is punctuation, not texture: exactly one element per section carries a `±1.5–3°` tilt, and no
rotated element sits within 1 rem of the viewport edge, so nothing clips on a phone.

## 5. Landing page content

1. **Hero** — the mark, "Paper Skyline", the pitch, inert store badges, and a full-bleed SVG of the folded dart mid-glide over a three-layer parallax skyline.
2. **How a flight goes** — three steps: draw back and release; skim, flap and boost; land and fold in upgrades. One ink glyph each.
3. **The workshop** — the blueprint band, dark in both themes: fifteen upgrade tracks, coins that reset with every city, a build choice rather than a checklist.
4. **The tour** — the cities, named in the order the campaign opens them, and the artifacts hidden in each.
5. **Drawn, not photographed** — every building, gull and shopfront is drawing code, which is why the game weighs nothing and never pixelates.
6. **Plainly** — a card row: saves live on the device, no account, landscape, iOS and Android.

### Claims the copy may not make

The site describes the game as it will ship, but three things are not settled and must stay out of the copy until
they are: **price** (the player-services spec is a draft, and rewarded ads are in it), **a city count** (levels 1–40
are authored of an approved hundred), and **a release date**. Named cities are safe — the ordering is approved.

## 6. Privacy policy — version 1

The policy describes the game as it exists today: no accounts, no advertising, no analytics, no network calls. Save
data (`paper-skyline-save`, `-unlocked`, `-artifacts`, `-bests`) is written to the device's local application
storage and never leaves it. Deleting the app deletes it.

`2026-09-13-player-services-design.md` is a **draft** that would add rewarded ads, accounts and leaderboards. The
policy goes to version 2 *before* any of that reaches a player, never after. The same rule the UV Tracker site
holds itself to: never let the policy describe a feature that isn't shipped, and never let a shipped feature go
undescribed.

## 7. Verification

`tools/check.sh` is the structural linter, adapted from uvstracker's:

- every page has `<html lang>`, viewport, description, `og:title`/`og:description`/`og:image`, `twitter:card`, canonical, icon, manifest
- zero executable `<script>` — JSON-LD only
- no `lorem`/`TODO`/`TBD`
- every `<img>` carries `alt`, `width`, `height`
- every internal link resolves to a file that exists
- **no store-badge `href`** while the game is unpublished — the check inverts on launch day
- every page links canonically to `https://paperskyline.org`
- `npx html-validate@8` over every page

`tools/shots.sh` renders any page at 500/768/1280 px in light and dark through headless Chrome, for a visual read.
500 px is the narrowest width headless Chrome lays out here, so mobile breakpoints are written at ≥ 500 px to stay
checkable.

## 8. Before publishing — open items

1. **Contact addresses are placeholders.** `hello@`, `privacy@` and `support@paperskyline.org` need forwarding set
   up at the registrar, or replacing with a real address. A policy with a dead contact address fails its purpose.
2. **Store badge hrefs** and the `installUrl` in the JSON-LD are empty pending the listings.
3. **Price, city count and release date** are absent by decision (§5). Add them when they are real.
4. **DNS** — the four GitHub Pages A records for the apex, and Enforce HTTPS once the certificate issues.
