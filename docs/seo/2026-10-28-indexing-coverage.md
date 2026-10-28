# Indexing coverage, 2026-10-28

Search Console's coverage export (data to 2026-10-23, summary only) had 113 indexed and 59 not indexed: 5 noindex, 28 crawled but not indexed, 23 discovered but not indexed, 3 with redirects.
This note classifies every sitemap URL (209 before this change, 189 after), lists the fixes and gives the Search Console steps for next time.

## What the audit found

- **Noindex (5):** already fixed by 713a9af (live around 10-26, after the export).
- **Redirects (3):** none are in a sitemap. They are probably the http and www variants that GitHub Pages redirects, which is expected. From 10-26 the 34 old `devlog/<x-y-z>/` pages are refresh stubs with a canonical to their minor page, so expect them under "Page with redirect" or "Alternate page with proper canonical tag". That is expected and needs no action.
- **Thin hubs (20):** the world hub and the six continent hubs in en, zh-Hans and id had 22 to 229 words of their own, only cards and links. They were the only sitemap pages exempt from the 300-word rule, so they are the likeliest "crawled, not indexed" pages.
- **Keeper pages (42):** they were linked only from their city page and the sibling keeper, at depth 2. Their legend, in-game lines and "mine" quote were also printed in full on the city page.
- **No sitemap row had a lastmod**, except the 10 hand-entered rows in `sitemap-pages.xml`, and 4 of those were stale (support.html said 09-13).
- **Fine:** every sitemap URL has a self canonical, no sitemap page is JS-only or redirected, and the hreflang sets are reciprocal. City pages have 30+ inbound links each. Sentence-level duplication between city and country pages is low, limited to the shared "An Elite wakes first..." lede.
- **Discovered, not indexed (23):** on a domain this young, this mostly means "not crawled yet". Most rows are pages added from 10-19 on: city wave 1, then waves 2 and 3 on 10-20 and 10-23, and countries on 10-25.

## Fixes (branch w-indexing-coverage)

- **Hubs follow the word rule.** `world/` and the continent hubs are now `noindex,follow` and out of the sitemaps until they reach MIN_WORDS. `zh-Hans/world/` (531 Han characters) stays indexed. Verified text in `design/web-text/hub/world.<lang>.md` or `hub/<continent>.<lang>.md` lifts them, as `hub/cities` does for the cities index.
- **Keeper links:** each keeper name on the home page and on the cities hub now links to its page. A keeper page now has 4 inbound links, at depth 1.
- **Less duplication:** on the en city page, a keeper card keeps the legend and the "mine" quote, then links "Meet the Stryge." The game's wake, crack and break lines live only on the keeper page. All 21 en city pages stay above 300 words (lowest: Dubai, 312).
- **Accurate lastmod:** `tools/lastmod.py` dates each row from the last commit that changed the page's `<main>` text, so nav, footer and CSP restamps don't move it. `cities.py` and `news.py` run it.
- **check.sh** now fails a sitemap row whose page redirects, whose canonical is not the row's URL, or whose lastmod is missing or stale.

No structured-data change was needed: city, country, keeper and hub pages already carry WebPage, BreadcrumbList and an `about`.

## Search Console checklist

1. After this deploy, resubmit `https://paperskyline.org/sitemap.xml` under Sitemaps. Search Console reads the child sitemaps from it.
2. On the **"Excluded by 'noindex' tag"** row, click **Validate fix**.
3. **Request indexing** (at most 10 a day). Check each URL first with URL Inspection, and skip it if it says "URL is on Google".
   - Day 1: `/cities/dubai/`, `/cities/berlin/`, `/cities/athens/`, `/cities/ho-chi-minh-city/`, `/cities/amsterdam/`, `/cities/singapore/`, `/world/europe/germany/`, `/world/europe/greece/`, `/world/asia/united-arab-emirates/`, `/cities/`
   - Day 2: `/cities/paris/stryge/`, `/cities/new-york/statue-of-liberty/`, `/cities/tokyo/lucky-cat/`, `/cities/cairo/sphinx/`, `/cities/rome/capitoline-lion/`, `/cities/london/tower-raven/`, `/cities/paris/carousel-horse/`, `/cities/new-york/taxi/`, `/cities/beijing/palace-lion/`, `/cities/sydney/lyrebird/`
   - Day 3: `/devlog/2-0/`, `/devlog/1-9/`, then any en city or country page that URL Inspection shows is not on Google. Leave the other keeper pages and the zh-Hans and id pages to the sitemap.
4. **Export the per-reason URL lists** (in about two weeks):
   - Go to Indexing > Pages and set the top filter to "All submitted pages".
   - Under "Why pages aren't indexed", open each reason row and click **Export** (top right) > **Download CSV**. The reasons are Crawled - currently not indexed, Discovered - currently not indexed, Page with redirect, and Excluded by 'noindex' tag.
   - Back on Indexing > Pages, click **View data about indexed pages** and export that list too.
   - Send the zip to the coordinator. It goes to the game repo's `docs/validation/seo/`, not this repo: Pages publishes every file here.

## Every sitemap URL by likely cause

These are the 209 URLs from before the change. "(dropped)" marks a URL now noindex and out of its sitemap.

### ok (9)

`/cities/`, `/`, `/minigames/`, `/business.html`, `/devlog.html`, `/press/`, `/support.html`, `/privacy.html`, `/terms.html`

### ok: own text, self canonical, 30+ inbound links (15)

`/cities/paris/`, `/cities/new-york/`, `/cities/tokyo/`, `/cities/cairo/`, `/cities/rio-de-janeiro/`, `/cities/london/`, `/cities/sydney/`, `/cities/beijing/`, `/cities/rome/`, `/cities/san-francisco/`, `/cities/bangkok/`, `/cities/istanbul/`, `/cities/barcelona/`, `/cities/hong-kong/`, `/cities/toronto/`

### new 10-27; weak links (city page + sibling only) and lines duplicated on the city page, both fixed (42)

`/cities/paris/carousel-horse/`, `/cities/paris/stryge/`, `/cities/new-york/taxi/`, `/cities/new-york/statue-of-liberty/`, `/cities/tokyo/lucky-cat/`, `/cities/tokyo/kabuki-actor/`, `/cities/cairo/camel/`, `/cities/cairo/sphinx/`, `/cities/rio-de-janeiro/cable-car/`, `/cities/rio-de-janeiro/samba-dancer/`, `/cities/london/tower-raven/`, `/cities/london/guildhall-giant/`, `/cities/sydney/cockatoo/`, `/cities/sydney/lyrebird/`, `/cities/beijing/palace-lion/`, `/cities/beijing/xiezhi/`, `/cities/rome/capitoline-lion/`, `/cities/rome/freed-gladiator/`, `/cities/san-francisco/gripman/`, `/cities/san-francisco/monarch/`, `/cities/bangkok/fighting-fish/`, `/cities/bangkok/war-elephant/`, `/cities/istanbul/simit-gull/`, `/cities/istanbul/karagoz/`, `/cities/barcelona/gegant-queen/`, `/cities/barcelona/mosaic-salamander/`, `/cities/hong-kong/neon-master/`, `/cities/hong-kong/pearl-river-pirate/`, `/cities/toronto/goalie-moose/`, `/cities/toronto/raccoon-night-watchman/`, `/cities/ho-chi-minh-city/courier/`, `/cities/ho-chi-minh-city/cyclo-racer/`, `/cities/amsterdam/herring-heron/`, `/cities/amsterdam/windmill-giant/`, `/cities/singapore/great-hornbill/`, `/cities/singapore/harbour-elder/`, `/cities/dubai/oryx/`, `/cities/dubai/pearl-diver/`, `/cities/berlin/bear-dj/`, `/cities/berlin/traffic-light-man/`, `/cities/athens/bronze-griffin/`, `/cities/athens/serpent-of-erechtheion/`

### new (10-20 or 10-23); no fault found, request indexing (6)

`/cities/ho-chi-minh-city/`, `/cities/amsterdam/`, `/cities/singapore/`, `/cities/dubai/`, `/cities/berlin/`, `/cities/athens/`

### new 10-26 (one page per minor version replaced the per-patch pages) (8)

`/devlog/2-0/`, `/devlog/1-9/`, `/devlog/1-8/`, `/devlog/1-7/`, `/devlog/1-6/`, `/devlog/1-5/`, `/devlog/1-4/`, `/devlog/1-0/`

### ok: translated text with reciprocal hreflang; second-language pages rank last on a young site (87)

`/zh-Hans/world/` (531 Han characters, stays indexed), `/id/`, `/id/cities/`, `/id/cities/paris/`, `/id/cities/new-york/`, `/id/cities/tokyo/`, `/id/cities/cairo/`, `/id/cities/rio-de-janeiro/`, `/id/cities/london/`, `/id/cities/sydney/`, `/id/cities/beijing/`, `/id/cities/rome/`, `/id/cities/san-francisco/`, `/id/cities/bangkok/`, `/id/cities/istanbul/`, `/id/cities/barcelona/`, `/id/cities/hong-kong/`, `/id/cities/toronto/`, `/id/cities/ho-chi-minh-city/`, `/id/cities/amsterdam/`, `/id/cities/singapore/`, `/id/cities/dubai/`, `/id/cities/berlin/`, `/id/cities/athens/`, `/id/world/europe/france/`, `/id/world/north-america/united-states/`, `/id/world/asia/japan/`, `/id/world/africa/egypt/`, `/id/world/south-america/brazil/`, `/id/world/europe/united-kingdom/`, `/id/world/oceania/australia/`, `/id/world/asia/china/`, `/id/world/europe/italy/`, `/id/world/asia/thailand/`, `/id/world/asia/turkiye/`, `/id/world/europe/spain/`, `/id/world/asia/hong-kong/`, `/id/world/north-america/canada/`, `/id/world/asia/vietnam/`, `/id/world/europe/netherlands/`, `/id/world/asia/singapore/`, `/id/world/asia/united-arab-emirates/`, `/id/world/europe/germany/`, `/id/world/europe/greece/`, `/zh-Hans/`, `/zh-Hans/cities/`, `/zh-Hans/cities/paris/`, `/zh-Hans/cities/new-york/`, `/zh-Hans/cities/tokyo/`, `/zh-Hans/cities/cairo/`, `/zh-Hans/cities/rio-de-janeiro/`, `/zh-Hans/cities/london/`, `/zh-Hans/cities/sydney/`, `/zh-Hans/cities/beijing/`, `/zh-Hans/cities/rome/`, `/zh-Hans/cities/san-francisco/`, `/zh-Hans/cities/bangkok/`, `/zh-Hans/cities/istanbul/`, `/zh-Hans/cities/barcelona/`, `/zh-Hans/cities/hong-kong/`, `/zh-Hans/cities/toronto/`, `/zh-Hans/cities/ho-chi-minh-city/`, `/zh-Hans/cities/amsterdam/`, `/zh-Hans/cities/singapore/`, `/zh-Hans/cities/dubai/`, `/zh-Hans/cities/berlin/`, `/zh-Hans/cities/athens/`, `/zh-Hans/world/europe/france/`, `/zh-Hans/world/north-america/united-states/`, `/zh-Hans/world/asia/japan/`, `/zh-Hans/world/africa/egypt/`, `/zh-Hans/world/south-america/brazil/`, `/zh-Hans/world/europe/united-kingdom/`, `/zh-Hans/world/oceania/australia/`, `/zh-Hans/world/asia/china/`, `/zh-Hans/world/europe/italy/`, `/zh-Hans/world/asia/thailand/`, `/zh-Hans/world/asia/turkiye/`, `/zh-Hans/world/europe/spain/`, `/zh-Hans/world/asia/hong-kong/`, `/zh-Hans/world/north-america/canada/`, `/zh-Hans/world/asia/vietnam/`, `/zh-Hans/world/europe/netherlands/`, `/zh-Hans/world/asia/singapore/`, `/zh-Hans/world/asia/united-arab-emirates/`, `/zh-Hans/world/europe/germany/`, `/zh-Hans/world/europe/greece/`

### thin hub (cards and links only), now noindex,follow and out of the sitemap (20)

`/id/world/ (dropped)`, `/id/world/europe/ (dropped)`, `/id/world/asia/ (dropped)`, `/id/world/africa/ (dropped)`, `/id/world/north-america/ (dropped)`, `/id/world/south-america/ (dropped)`, `/id/world/oceania/ (dropped)`, `/world/ (dropped)`, `/world/europe/ (dropped)`, `/world/asia/ (dropped)`, `/world/africa/ (dropped)`, `/world/north-america/ (dropped)`, `/world/south-america/ (dropped)`, `/world/oceania/ (dropped)`, `/zh-Hans/world/europe/ (dropped)`, `/zh-Hans/world/asia/ (dropped)`, `/zh-Hans/world/africa/ (dropped)`, `/zh-Hans/world/north-america/ (dropped)`, `/zh-Hans/world/south-america/ (dropped)`, `/zh-Hans/world/oceania/ (dropped)`

### thin utility or promo page; expected to stay unindexed, acceptable (2)

`/dragon.html`, `/feedback.html`

### ok: own text, self canonical (17)

`/world/europe/france/`, `/world/north-america/united-states/`, `/world/asia/japan/`, `/world/africa/egypt/`, `/world/south-america/brazil/`, `/world/europe/united-kingdom/`, `/world/oceania/australia/`, `/world/asia/china/`, `/world/europe/italy/`, `/world/asia/thailand/`, `/world/asia/turkiye/`, `/world/europe/spain/`, `/world/asia/hong-kong/`, `/world/north-america/canada/`, `/world/asia/vietnam/`, `/world/europe/netherlands/`, `/world/asia/singapore/`

### indexable only since 10-25, too new to judge (3)

`/world/asia/united-arab-emirates/`, `/world/europe/germany/`, `/world/europe/greece/`
