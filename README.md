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
brand/                # the export wrappers that render every icon, and their output
tools/                # check.sh, shots.sh, brand.sh — the verification harness
docs/superpowers/specs/               # the design spec this was built from
sitemap.xml  robots.txt  site.webmanifest  CNAME
```

Every colour and both typefaces come from the game's own design spec, not from a web palette. Dark
mode is the Garage blueprint — `#1f3a5f` with `#e8eef7` line work — because that is the one dark
surface Paper Skyline already owns.

## The art is written, not loaded

There is not a single photograph or illustration file on this site. The skyline, the plane, the
coins, the blueprint elevation and every step glyph are inline `<svg>`: shapes and numbers in the
page. That is the same decision the game made — Paper Skyline draws its world in code — so the
site's art has the same provenance as the game's, and nothing here can go stale against a build.

The hero skyline is the one piece too repetitive to place by hand — two hundred windows across
three parallax layers. `tools/skyline.py` generates it from a fixed seed, so re-running it produces
byte-identical output; paste the result back over the `<svg class="skyline">` block in
`index.html`.

## Checks

Run before every commit:

```bash
tools/check.sh                        # every page: validity, links, zero-JS, unlinked badges, alt/width/height
tools/shots.sh index.html privacy.html  # 500/768/1280 px, light + dark, for a visual read
tools/brand.sh                        # re-render the icons and the social card
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

Every icon below is a headless-Chrome render of a wrapper page in `brand/export/`. `brand/mark.svg`
and `favicon.svg` are the hand-written sources. Re-render with `tools/brand.sh` after any change.

| File | Feeds |
| :--- | :--- |
| `brand/app-icon-1024.png` | The app icon source, and the JSON-LD `image` |
| `brand/og-image-1200x630.png` | `og:image` on every page |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` | Browser tab and iOS home screen |
