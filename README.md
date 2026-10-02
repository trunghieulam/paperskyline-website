# paperskyline.org

The public website for **Paper Skyline** — the landing page, plus privacy, terms and support.

Hand-written static HTML and one stylesheet, zero JavaScript. No framework, no build step, no
dependencies. It is meant to load instantly, stay legible for years, and never break because a
toolchain moved on.

## Why it exists

Paper Skyline is on Google Play; the site says what it is and links there. It also carries the
privacy policy and terms the store listings point at.

## Structure

```
index.html  privacy.html  terms.html  support.html  404.html
styles.css            # tokens + every component, light/dark via prefers-color-scheme
img/                  # the game's paintings and keepers, exported by tools/art.py
brand/                # the app icon and the social card
tools/                # art.py, check.sh, shots.sh
docs/superpowers/specs/               # the design spec this was built from
sitemap.xml  robots.txt  site.webmanifest  CNAME
```

Every colour and both typefaces come from the game's own design spec, not from a web palette. Dark
mode is the Garage blueprint — `#1f3a5f` with `#e8eef7` line work — because that is the one dark
surface Paper Skyline already owns.

## The art is the game's own

The hero and the social card are cropped from the 1.3 Paris phone capture, and the keepers section
shows all twenty keepers of the ten cities. `tools/art.py` reads them from the game repo and writes
`img/` and `brand/`, so re-run it after the game's art changes rather than editing images by hand. Each image is exported at the size its slot needs, as AVIF and WebP, with a JPEG
(paintings) or PNG (cut-out keepers) fallback for browsers that take neither.

"In the game" shows the eight 1.3 Play phone captures from the game repo's
`docs/store/google-play/screenshots-1.3/phone/`, at 800 and 1600 px; `SHOTS` in `tools/art.py` picks
them, and the frames are 2:1 to match, so nothing is cropped. `brand/google-play-badge.png` is
Google's official badge, used unmodified.

The step glyphs and the blueprint elevation are still inline `<svg>`.

## Copy

No em dash (—) in any page's copy, titles or meta: write a period, comma or colon, and `|` in page titles. `tools/check.sh` fails on one.

## Checks

Run before every commit:

```bash
tools/check.sh                        # every page: validity, links, zero-JS, unlinked badges, alt/width/height
tools/shots.sh index.html privacy.html  # 500/768/1280 px, light + dark, for a visual read
tools/art.py                          # re-export the paintings, keepers, social card and icons
```

500 px is the narrowest width this machine's headless Chrome will lay out, so mobile breakpoints
are written at ≥ 500 px to stay checkable here.

Headless Chrome has no `prefers-color-scheme` switch. `shots.sh` copies the site to `tools/.tmp/`
and rewrites the dark media query to `@media all` for the dark run — the page itself is untouched.

## Local preview

No server needed — open `index.html` in a browser. To serve it properly:

```bash
python3 -m http.server 8000
```

## Deploying

GitHub Pages, from the default branch root:

1. Repo → **Settings → Pages** → Source: *Deploy from a branch* → `main` / `/ (root)`.
2. `CNAME` already declares `paperskyline.org`, so Pages picks the custom domain up.
3. At the registrar, point the apex at GitHub Pages:
   - `A` records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - and a `CNAME` for `www` → `trunghieulam.github.io`
4. Back in Settings → Pages, tick **Enforce HTTPS** once the certificate is issued.

## Before publishing — things that still need a decision

1. **Contact.** Every page's mailto is the owner's address (user, 2026-09-28); it must receive mail
   before publishing, since store reviewers do check.
2. **Store links.** Google Play is linked (package `paperskyline.org`); `check.sh` fails any
   `store-link` that points elsewhere. The App Store badge stays an unlinked `<span class="badge">`
   until the iPhone version ships, and `check.sh` fails it if it becomes a link.
3. **Developer and law.** The developer is "THLab (Trung Hieu Lam)", and the terms are governed by
   Vietnamese law (user, 2026-09-28).
4. **Two claims are absent on purpose**: price and a release date. The city count (ten) is stated.

## Keeping the policy honest

Privacy policy version 3 adds the opt-in AdMob rewarded ad on Android (F17): child-directed,
non-personalised, UMP consent in the EEA and UK, no advertising ID. Version 4 (branch web-stats-v4, G5)
describes Paper Skyline 1.1: made for adults 18 and over (V-D37), anonymous gameplay statistics to our
Cloudflare Worker, in-game feedback and `feedback.html`, a no-JS mailto form for adults. Version 2 described Paper Skyline 1.0: progress and settings saved on the device, no ads, analytics or purchases, no Unity cloud service enabled, and one-time HTTPS downloads of New York,
Tokyo, Cairo and Rio from Cloudflare R2 with no identifiers sent. It is the Play Console privacy URL,
so keep `privacy.html` at that path. Any change to the game's data flow bumps the policy **first**.

## Brand exports

`tools/art.py` makes every icon from the game's painted app icon ("Dusk over Paris") and composes
the social card from the Paris preflight painting and the five Bosses.

| File | Feeds |
| :--- | :--- |
| `brand/app-icon-1024.jpg` | The JSON-LD `image` and `logo`, and the manifest |
| `brand/og-image-1200x630.jpg` | `og:image` on every page |
| `favicon-32.png`, `apple-touch-icon.png` | Browser tab and iOS home screen |
| `img/mark-96.*` | The header and footer mark |
