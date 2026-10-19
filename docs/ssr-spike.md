# SSR spike: Cloudflare Pages + Functions vs GitHub Pages

Branch `web-ssr-spike` (from `web-96-wave2` abc3923), 2026-10-19. Question (user): should paperskyline.org move from
GitHub Pages to Cloudflare Pages and use Pages Functions for SSR, to help SEO for the city pages (#96)?

## Recommendation: hybrid, static pages + two small Functions

Keep the pre-built static HTML from `tools/cities.py` as the whole site. Host it on Cloudflare Pages for speed in
South-East Asia and per-branch previews. Use Functions only for the no-JS form POSTs (`/api/wish`, `/api/vote`).
**No full SSR:** it would send Googlebot the same bytes it gets today, at a cost per request and a slower first byte.
**No Accept-Language routing:** Google advises against it.

The move is worth doing for speed and previews, not for SEO. Before DNS moves, three things need a decision or a fix:
the `.html` canonicals (below), turning DNSSEC off, and the Direct Upload vs Git choice.

## 1. SEO: what Googlebot gets

**Same bytes.** Served by `wrangler pages dev` (Pages' own asset server) and by live GitHub Pages, all 11 sampled
files were byte-identical to the files on disk: `/`, `/cities/`, `/cities/{paris,tokyo,sydney}/`, `/world/`,
`/world/europe/france/`, `/sitemap.xml`, `/sitemap-cities.xml` and `/styles.css`. Since the HTML is already
complete, SSR cannot add anything a crawler reads, and pre-rendering *is* rendering. `tools/pages-verify.sh`
repeats the check against a deployed URL.

**Where the hosts differ (measured locally, `pages dev` vs paperskyline.org):**

| Request | GitHub Pages | Cloudflare Pages |
| :-- | :-- | :-- |
| `/privacy.html` (and the other 8 root `*.html`) | 200 | **308 → `/privacy`** |
| `/privacy` | 200 | 200 |
| `/cities/paris` | 301 → `/cities/paris/` | 308 → `/cities/paris/` |
| `/cities/paris/index.html`, `/index.html` | 200 | 308 → the folder |
| `/nope/` | 404 + `404.html` | 404 + `404.html` |
| `/play` (`_redirects`) | 404 | 302 → Play, with referrer |
| `/README.md`, `/tools/check.sh` | 200 | 200 (same tree is public) |
| `/CNAME` | 404 | 200 (harmless) |
| `Cache-Control` on HTML | `max-age=600` | `max-age=0, must-revalidate` + ETag |

**The one SEO issue:** Pages always strips `.html` and cannot be told not to. The same holds for Workers static
assets, unless `html_handling = "none"`, and that breaks `folder/index.html`. Today 9 root pages declare
`…/privacy.html` as canonical and list it in `sitemap-pages.xml`. On Cloudflare, a canonical URL that redirects
makes Search Console report "Page with redirect" and adds a hop to every footer link (42 + 28 links on the city and
world pages). City, world and home URLs are folders and are unaffected.
**Fix, host-neutral, before cutover (Web Engineer):** change the canonicals, `og:url`, sitemap rows and internal
links to the extensionless form (`/privacy`). GitHub Pages already serves `/privacy` with a 200, so the fix can ship
first on today's host. The Play Console privacy URL `privacy.html` keeps working through the 308, but should be
updated to `/privacy`.

**Wave 4 hreflang (zh-Hans, id) is static work.** Use separate URLs (`/zh-hans/cities/paris/`, `/id/cities/paris/`),
each page with reciprocal `<link rel="alternate" hreflang="en|zh-Hans|id|x-default">`, its own `<html lang>`,
canonical and `og:locale`. That is what Google recommends, and `cities.py` can emit it. Nothing about it needs a
server.

**`_headers` / `_redirects`** (in this branch; GitHub Pages' Jekyll ignores `_` files, so they are inert there):
`_headers` puts `X-Robots-Tag: noindex` on every `*.pages.dev` host, so previews and the project URL never compete
with paperskyline.org. Pages also adds it to preview URLs by itself. `_headers` also sets `nosniff`,
`Referrer-Policy` and a one-day browser cache on `img/` (Cloudflare advises against longer custom caching, since art
filenames are reused). `_redirects` holds one example, `/play`, a short Play link with the UTM referrer. Limits: 100
header rules, 2,000 static + 100 dynamic redirects.

## 2. What Functions add that static can't

| Need | Static on GitHub Pages | With Functions |
| :-- | :-- | :-- |
| No-JS wish / up-vote POST (#95/#97) | **Already possible:** a plain `<form action="https://paperskyline-stats…workers.dev/v1/wish">`, with the Worker answering in HTML or 303 to a static thanks page | Same-origin `/api/wish`, so CSP `form-action 'self'` and one domain. Prototype below |
| Live vote counts in city pages | Only by rebuilding the pages (nightly or on deploy) | HTMLRewriter injects the count. Prototype below. Every city view then costs a Function request and a D1 read, and gives no SEO gain |
| Accept-Language routing | Not possible | Possible, but **don't**: Googlebot sends no `Accept-Language` and crawls from the US, and Google says "avoid automatically redirecting" by guessed language |
| Per-branch preview URLs | No | Yes: `<branch>.paperskyline-site.pages.dev`, noindexed, with either Direct Upload or Git |

Functions only run on their routes: wrangler generates `_routes.json` from `functions/` (`/api/*`,
`/cities-live/*`), so every page and image stays a free static request.

## 3. Cost, limits, speed

**Free plan (Cloudflare docs):** static requests are free and unlimited. Functions share the Workers free quota of
**100,000 requests/day** (resets 00:00 UTC; over that, error 1027) at **10 ms CPU** each. The stats Worker
draws on the same quota. Builds: 500/month, 1 at a time, 20 min each, and **Direct Upload uses no builds**.
**20,000 files, 25 MiB per file**, 100 projects, unlimited previews.
**This site today:** 455 files and 28.7 MB, largest `video/reel-v4-web.mp4` at 8.3 MB, every image ≤ 300 KB
(`check.sh`). At ~300+ pages with three formats per image it stays well under 10% of the file cap.

**Time to first byte from this host (Vietnam, Cloudflare trace `loc=VN`), median of 7 new connections:**

| URL | Edge | TCP | TLS done | TTFB |
| :-- | :-- | --: | --: | --: |
| paperskyline.org/cities/paris/ (GitHub Pages) | Fastly NRT (Tokyo) | 0.099 | 0.242 | **0.875 s** |
| paperskyline.org/styles.css | Fastly NRT | 0.099 | 0.238 | **1.038 s** |
| paperskyline-stats…workers.dev (our Worker) | Cloudflare HKG | 0.043 | 0.089 | **0.214 s** |
| developers.cloudflare.com (Workers static assets) | Cloudflare HKG | 0.044 | 0.090 | **0.380 s** |

Cloudflare answered in about a quarter to a third of the time. The `*.pages.dev` row is still to be measured:
`tools/pages-verify.sh` prints it after the first deploy. **Indonesia and the Philippines (not measured here):**
Fastly lists Manila and Singapore, with Jakarta "coming soon". Cloudflare runs Jakarta, Manila and Cebu. Caveat: free
traffic is not always served from the nearest site. Vietnam went to HKG here, not to Cloudflare's Hanoi or HCMC sites.

## 4. Migration

**Apex needs Cloudflare nameservers.** Pages attaches an apex (`paperskyline.org`) only when the domain is a
Cloudflare zone. A plain CNAME at Squarespace works only for a subdomain, so moving nameservers is the only way to
keep the apex URLs. Today's DNS at Squarespace (`dig`, 2026-10-19):

| Record | Value | On Cloudflare |
| :-- | :-- | :-- |
| `A @` ×4 | 185.199.108–111.153 (GitHub), TTL 4 h | Replaced by the Pages custom domain (do not import) |
| `CNAME www` | trunghieulam.github.io | `CNAME www → paperskyline-site.pages.dev`, proxied, + a Redirect Rule www → apex 301 |
| `MX @` | 1 smtp.google.com | **Copy, DNS only.** The contact mailto depends on it |
| `TXT @` | google-site-verification=cmfD… | **Copy.** Search Console (#82) loses the domain without it |
| `DS` (at .org) | 44024 8 2 B6FC… | **DNSSEC is on: turn it off at Squarespace first** |

No SPF, DKIM or DMARC records exist. That is a separate email question, not a blocker.

**Steps (user, in order):**
1. Web Engineer: ship the extensionless canonicals (section 1) on GitHub Pages first.
2. Choose Direct Upload or Git (open decision 1), and deploy the production branch to `paperskyline-site`.
   Run `tools/pages-verify.sh https://paperskyline-site.pages.dev`.
3. Squarespace → Domains → paperskyline.org → DNSSEC: **off**. Wait at least 2 h (DS TTL is 1 h). Cloudflare warns
   that records won't resolve while an old DS is published.
4. Cloudflare dashboard → Add a domain → paperskyline.org (Free). Check the imported records against the table:
   keep MX and TXT, delete the GitHub `A` records and the `www` CNAME.
5. Squarespace → Nameservers → custom: the two `*.ns.cloudflare.com` names Cloudflare shows. Allow up to 24 h, until
   the zone shows Active.
6. Workers & Pages → paperskyline-site → Custom domains → add `paperskyline.org` (and `www`) **in the dashboard
   first**. A record made by hand before this step gives a 522. Cloudflare issues the certificate itself (no CAA
   records exist, so nothing blocks it). Turn on SSL/TLS → Always Use HTTPS, and add the www → apex Redirect Rule.
7. Verify: `tools/pages-verify.sh https://paperskyline.org`, `curl -I http://paperskyline.org/` → 301 https, mail
   still arrives, Search Console still verified.
8. Then turn DNSSEC on in Cloudflare and paste its DS record at Squarespace.
9. Keep GitHub Pages enabled for 2 weeks as the rollback. Then turn it off, keeping the `CNAME` file so a re-enable
   is one click.

**URLs:** every folder URL (all city, world and hub pages, `/`) stays exactly the same. Root `*.html` URLs gain one
308 unless step 1 lands first. `sitemap.xml`, `robots.txt` and `app-ads.txt` paths are unchanged.

**Rollback, from fastest to slowest:** (a) in Cloudflare DNS, remove the custom domain and put back the four GitHub
`A` records and `www → trunghieulam.github.io`, **DNS only**. It takes effect within minutes because the TTL is set
in Cloudflare, and GitHub Pages still serves the site since it was never turned off. GitHub may need "Enforce
HTTPS" re-ticked once its certificate renews. (b) Set Squarespace nameservers back to `nsa1–4.squarespacedns.com`.
The old records are still there unless deleted, and the change takes up to 24 h. For a short detour, Cloudflare
recommends a Redirect Rule rather than flipping DNS.

## 5. Prototype (this branch, local only)

`npx wrangler@4 pages dev . --port 8788` on the repo root, with:

- `functions/api/wish.js`: `GET` returns a plain form (spike only; production puts it on a static page). `POST`
  takes form data, NFC-normalizes and validates the name (letters and marks in any script, plus space, `.`, `'`,
  `-`, 2–60 chars), and checks a honeypot. It answers with an HTML page and no script. Tested: Jakarta → 200 thanks,
  `Hồ Chí Minh` and `北京` → 200, `paris` → 200 "already in the game" with a link, `<script>…` / empty → 400,
  honeypot filled → 400, JSON body → 415. Production would check names against GeoNames cities15000 and forward to
  the stats Worker through a service binding, so D1, the schema and the salted-IP rate limit keep one owner.
  **Privacy policy bump first:** the site would then store wishes.
- `functions/cities-live/[city].js`: fetches the static `/cities/<id>/` and injects
  `<p class="votes">128 players want more of Paris</p>` after the H1 from a stub. A diff against
  `cities/paris/index.html` shows only that line changed. It sends `x-robots-tag: noindex`, and an unknown city
  returns 404. The URL sits at the same depth so `../../` links resolve. In production it would be the
  `/cities/<id>/` route itself.
- `_headers`, `_redirects` as above. `functions/_page.js` is the shared shell plus stub data.
- `tools/pages-deploy.sh` deploys the committed tree (`git archive HEAD`, as GitHub Pages serves the branch root)
  with its Functions, creating the project on first run. `tools/pages-verify.sh <url>` runs the read-only checks:
  every page 200, byte-identical samples, headers, redirects, the wish flow and TTFB.

**Static pages unchanged:** `tools/cities.py` and every page are untouched. `tools/check.sh: OK (46 pages)`.
`pages-verify.sh http://localhost:8788` passes everything except the two pages.dev-only checks: there is no
pages.dev host locally, and `pages dev` serves `functions/` while `pages deploy` leaves it out (wrangler's upload
`IGNORE_LIST`).

**Not done:** the pages.dev deploy. The auto-mode classifier blocked even writing the deploy script, as a production
deploy, so the user runs it:

```bash
cd /Users/alex/Workspaces/Personal/paperskyline-website-ssr-spike && tools/pages-deploy.sh web-ssr-spike
tools/pages-verify.sh https://web-ssr-spike.paperskyline-site.pages.dev
```

The token needs **Account → Cloudflare Pages → Edit**. The stats Worker's token was made for Workers and D1, so
check it has this permission. If wrangler says "Authentication error [code: 10000]", the permission is missing.

## Open user decisions

1. **Direct Upload or Git integration.** A project created by `wrangler pages deploy` (Direct Upload) **can never
   switch to Git integration**. Git integration keeps today's "push to main = live" and gives a preview per branch
   automatically, but installs Cloudflare's GitHub app on the website repo. Direct Upload keeps deploys a
   deliberate step (`tools/pages-deploy.sh main`) with no repo access. Recommendation: Git integration for
   production. If so, run the spike as `PAGES_PROJECT=paperskyline-spike`, or delete `paperskyline-site` after the
   spike, and create the real project from the dashboard.
2. **Move nameservers to Cloudflare** (the only way to keep the apex on Pages), including DNSSEC off and back on.
3. **Fix the `.html` canonicals first** (Web Engineer, host-neutral), and update the Play Console privacy URL to
   `/privacy`.
4. **Wish/vote endpoint:** same-origin Pages Function via a service binding (recommended), or a direct form POST to
   the stats Worker (works today, no migration needed). Either way, the privacy policy bump comes first.
5. **Vote counts on city pages:** shown after voting plus a nightly rebuild (recommended), or a live Function on
   every city view.

Sources: Cloudflare Pages [limits](https://developers.cloudflare.com/pages/platform/limits/),
[serving pages](https://developers.cloudflare.com/pages/configuration/serving-pages/),
[Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/),
[custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/),
[direct upload](https://developers.cloudflare.com/pages/get-started/direct-upload/);
Workers [limits](https://developers.cloudflare.com/workers/platform/limits/),
[html_handling](https://developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/);
Google, [multi-regional sites](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites);
[Fastly network map](https://www.fastly.com/network-map/); Cloudflare blog, [Cebu](https://blog.cloudflare.com/cebu),
[Indonesia](https://blog.cloudflare.com/ja-jp/indonesia/).
