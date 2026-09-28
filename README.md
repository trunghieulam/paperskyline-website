# paperskyline.org

The public website for **Paper Skyline** — the landing page, plus privacy, terms and support.

Hand-written static HTML and one stylesheet, zero JavaScript. No framework, no build step, no
dependencies. It is meant to load instantly, stay legible for years, and never break because a
toolchain moved on.

## Why it exists

The game is unreleased, so the site's first job is to say what Paper Skyline is. Its second job is
to be carrying a reachable privacy policy and terms on the day the store listings are submitted —
both Apple and Google ask for the URL, and neither waits while you write one.

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

The hero, the city strip and the social card are the game's shipped paintings: the Paris preflight
card, the five city backgrounds and the porcelain keepers. `tools/art.py` reads them from the game
repo and writes `img/` and `brand/`, so re-run it after the game's art changes rather than editing
images by hand. Each image is exported at the size its slot needs, as AVIF and WebP, with a JPEG
(paintings) or PNG (cut-out keepers) fallback for browsers that take neither.

The screenshot slots in "In the game" are placeholders until the store captures land in the game
repo's `docs/store/google-play/screenshots/`. Each slot swaps its `.shot-pending` span for a
`<picture>`; the frame is 16:9 and `object-fit` crops a wider capture to it.

The step glyphs and the blueprint elevation are still inline `<svg>`.

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

1. **The contact addresses are placeholders.** The pages reference `privacy@`, `support@` and
   `hello@paperskyline.org`. Set up forwarding at the registrar or change them to a real address.
   A privacy policy with a dead contact address fails its purpose, and store reviewers do check.
2. **The store badges are deliberately unlinked.** They are `<span class="badge">`, dashed and
   dimmed, and `check.sh` **fails the build if one becomes a link** — invert that rule in
   `tools/check.sh` on launch day, add the two `href`s, and add `installUrl` plus `offers` to the
   JSON-LD in `index.html`.
3. **Governing law is unnamed.** `terms.html` says "the country in which LLOG is established"
   rather than naming one. Name it before publishing.
4. **Three claims are absent on purpose** — price, a city count, and a release date. The
   player-services spec that would add rewarded ads is still a draft, levels 1–40 are authored of
   an approved hundred, and there is no date. Add each one when it is real, not before.

## Keeping the policy honest

The policy makes concrete promises the game currently keeps: nothing is collected, no network call
is made, no Unity cloud service is enabled, and the four save keys never leave the device. The
moment rewarded ads, accounts or leaderboards ship, the policy goes to version 2 **first**, since
it would otherwise be inaccurate in exactly the way regulators care about.

## Brand exports

`tools/art.py` makes every icon from the game's painted app icon ("Dusk over Paris") and composes
the social card from the Paris preflight painting and the five Bosses.

| File | Feeds |
| :--- | :--- |
| `brand/app-icon-1024.jpg` | The JSON-LD `image` and `logo`, and the manifest |
| `brand/og-image-1200x630.jpg` | `og:image` on every page |
| `favicon-32.png`, `apple-touch-icon.png` | Browser tab and iOS home screen |
| `img/mark-96.*` | The header and footer mark |
