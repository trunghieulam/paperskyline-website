#!/usr/bin/env python3
"""One changelog to news/out/news.json (R2), news/out/whats-new-<version>.txt (Play), devlog.html,
devlog/<x-y>/ (one page per minor version, old devlog/<x-y-z>/ URLs refresh to it), feed.xml (Atom) and sitemap-devlog.xml.
Usage: tools/news.py [changelog.json]   (default: the game repo's docs/store/changelog.json, beside this site). Exits non-zero on any rule below."""
import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import lastmod  # noqa: E402
from art import CITIES, IDS, NAMES  # noqa: E402

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(SITE, '..', 'game-paper-flights', 'docs', 'store', 'changelog.json'))
OUT = os.path.join(SITE, 'news', 'out')
GAME = os.path.join(SITE, '..', 'game-paper-flights')
ORIGIN = 'https://paperskyline.org'
# The newest version on Play production: nothing after it is published here, whatever the changelog holds
LIVE = '2.0.5'
PLAY_LIMIT = 500
# The next release while it is on a test track: (version, lines), shown above the shipped ones
COMING = None
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']
DATEISH = re.compile(r'\b(20\d\d|' + '|'.join(MONTHS) + r'|tomorrow|next (week|month)|this (week|month))\b', re.I)


def fail(msg):
    sys.exit(f'news.py: {msg}')


def vkey(v):
    return tuple(int(x) for x in v.split('.'))


def load():
    data = json.load(open(SRC, encoding='utf-8'))
    if data.get('format') != 1:
        fail('changelog format must be 1')
    releases = data.get('releases', {})
    for v, d in releases.items():
        if not re.fullmatch(r'\d+\.\d+\.\d+', v) or (d is not None and not re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])', d)):
            fail(f'release {v}: version must be x.y.z and date YYYY-MM or null')
    seen = set()
    for e in data['entries']:
        i = e.get('id', '')
        if not re.fullmatch(r'[a-z0-9-]+', i) or i in seen:
            fail(f'entry id {i!r} missing, malformed or repeated')
        seen.add(i)
        if e.get('kind') not in ('new', 'fix', 'soon'):
            fail(f'{i}: kind must be new, fix or soon ("now" is decided in the game, from Play)')
        if not 0 < len(e.get('title', '')) <= 40 or not 0 < len(e.get('body', '')) <= 200:
            fail(f'{i}: title 1-40 and body 1-200 characters')
        i18n = e.get('i18n', {})
        if not isinstance(i18n, dict):
            fail(f'{i}: i18n must map a locale to its title and body')
        for lang, t in i18n.items():
            if lang == 'en' or not re.fullmatch(r'[a-z]{2}(-[A-Za-z]+)?', lang) or not isinstance(t, dict) or set(t) != {'title', 'body'}:
                fail(f'{i}: i18n {lang!r} must be a non-English locale with exactly a title and a body')
            if not 0 < len(t['title']) <= 40 or not 0 < len(t['body']) <= 200:
                fail(f'{i}: i18n {lang}: title 1-40 and body 1-200 characters')
        if len(e.get('play', '')) > 120:
            fail(f'{i}: play line over 120 characters')
        text = ' '.join(e.get(k, '') for k in ('title', 'body', 'play'))
        if e['kind'] != 'soon':
            if e.get('version') not in releases:
                fail(f'{i}: a {e["kind"]} entry needs a version listed in releases')
        else:
            if 'version' in e:
                fail(f'{i}: a soon entry has no version until it ships')
            if DATEISH.search(text):
                fail(f'{i}: coming-soon text promises a date ({DATEISH.search(text).group(0)!r})')
    return releases, data['entries']


def news_json(releases, entries):
    rows = []
    for e in entries:
        r = {k: e[k] for k in ('id', 'kind', 'title', 'body') if k in e}
        for k in ('image', 'availableIn', 'version', 'i18n'):
            if k in e:
                r[k] = e[k]
        if e['kind'] != 'soon':
            r['date'] = releases[e['version']]
        rows.append(r)
    return {'format': 1, 'entries': rows}


def whats_new(entries, version):
    lines = [f"• {e.get('play', e['title'])}" for e in entries if e.get('version') == version]
    text = '\n'.join(lines)
    if len(text) > PLAY_LIMIT:
        # A hand-written whats-new beside the changelog is what Play gets, so this one is only a draft
        if os.path.exists(os.path.join(os.path.dirname(SRC), 'google-play', f'whats-new-{version}.txt')):
            return None
        fail(f'Play text for {version} is {len(text)} characters, over {PLAY_LIMIT}')
    return text


def month(d):
    y, m = d.split('-')
    return f'{MONTHS[int(m) - 1]} {y}'


def cards(items, stamp):
    out = []
    for e in items:
        out.append(f'''        <article class="card">
          <span class="pill">{'Fix' if e.get('kind') == 'fix' else stamp}</span>
          <h3>{html.escape(e['title'])}</h3>
          <p>{html.escape(e['body'])}</p>
        </article>''')
    return '\n'.join(out)


def slug(v):
    return v.replace('.', '-')


def shipped(releases, entries):
    """Live versions with entries, newest first."""
    return [v for v in sorted(releases, key=vkey, reverse=True)
            if vkey(v) <= vkey(LIVE) and any(e.get('version') == v for e in entries)]


def posted(releases, v):
    """The feed date: the release month when the changelog has one, else when the version first reached game main."""
    if releases[v]:
        return releases[v] + '-01T00:00:00Z'
    out = subprocess.run(['git', '-C', GAME, 'log', 'origin/main', '--reverse', '--format=%cI', f'-S"{v}":', '--',
                          'docs/store/changelog.json'], capture_output=True, text=True, check=True).stdout.split()
    if not out:
        fail(f'{v}: no release date and no history in {GAME}')
    return out[0]


def template(title, desc, url, depth, trail):
    """support.html's chrome with this page's head and breadcrumb; depth re-roots its relative links."""
    src = open(os.path.join(SITE, 'support.html'), encoding='utf-8').read()
    old_desc = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    page = (src.replace('<title>Support | Paper Skyline</title>', f'<title>{title}</title>')
            .replace(old_desc, desc)
            .replace('https://paperskyline.org/support.html', url)
            .replace('content="Support | Paper Skyline"', f'content="{title}"')
            .replace('<a href="support.html" aria-current="page">Support</a>', '<a href="support.html">Support</a>')
            .replace('<a href="devlog.html">News</a>', '<a href="devlog.html" aria-current="page">News</a>', 1)
            .replace('utm_medium%3Dsupport%26', 'utm_medium%3Ddevlog%26').replace('ct=site-support&', 'ct=site-devlog&')
            .replace('<link rel="canonical"', '<link rel="alternate" type="application/atom+xml" title="Paper Skyline devlog" href="/feed.xml">\n<link rel="canonical"'))
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': n, 'item': u} for i, (n, u) in enumerate(trail, 1)]}
    page = re.sub(r'\{"@context": "https://schema.org", "@type": "BreadcrumbList".*', lambda m: json.dumps(crumbs, ensure_ascii=False), page, count=1)
    up = '../' * depth
    if up:
        page = re.sub(r'((?:href|src|srcset)=")(?!https?:|/|#|mailto:)', rf'\g<1>{up}', page)
    return page


def linked(text, up):
    """Escapes an entry's text and links the first mention of each shipped city to its page."""
    out = html.escape(text)
    for art_slug, _, _ in CITIES:
        page = IDS.get(art_slug, art_slug)
        name = NAMES.get(art_slug, art_slug.replace('-', ' ').title())
        if os.path.isdir(os.path.join(SITE, 'cities', page)):
            out = re.sub(rf'(?<![\w>])({re.escape(name)})(?![\w<])', rf'<a href="{up}cities/{page}/">\1</a>', out, count=1)
    return out


# The launch versions were a handful of lines each, too thin for a page apiece
FOLD = {'1.1': '1.0', '1.2': '1.0', '1.3': '1.0'}


def lower(s):
    return s[0].lower() + s[1:]


def minor(v):
    m = '.'.join(v.split('.')[:2])
    return FOLD.get(m, m)


def label(vs):
    ms = sorted({'.'.join(v.split('.')[:2]) for v in vs}, key=vkey)
    return f'Version {ms[0]}' if len(ms) == 1 else f'Versions {ms[0]} to {ms[-1]}'


def groups(versions):
    """Shipped versions by minor, both newest first: patches fold into one page each, so none is thin."""
    out = {}
    for v in versions:
        out.setdefault(minor(v), []).append(v)
    return list(out.items())


def months(releases, vs):
    ms = sorted({releases[v] for v in vs if releases[v]})
    return ' to '.join(month(d) for d in (ms[:1] + ms[-1:] if len(ms) > 1 else ms))


def span(vs):
    return vs[0] if len(vs) == 1 else f'{vs[-1]} to {vs[0]}'


def swap_main(page, body):
    a = page.index('<main id="main">')
    b = page.index('</main>') + len('</main>')
    return page[:a] + body + page[b:]


def minor_page(releases, entries, m, vs, newer, older):
    titles = [e['title'] for v in vs for e in entries if e.get('version') == v]
    shown = []
    for t in titles:
        if len(', '.join(shown + [t])) > 130:
            break
        shown.append(t)
    rest = ', '.join(shown) + (' and more' if len(shown) < len(titles) else '')
    title = f'{label(vs)} | Paper Skyline devlog'
    desc = html.escape(f"What's new in Paper Skyline {span(vs)}: {rest}.", quote=True)
    page = template(title, desc, f'{ORIGIN}/devlog/{slug(m)}/', 2,
                    [('Home', f'{ORIGIN}/'), ('News', f'{ORIGIN}/devlog.html'), (label(vs), f'{ORIGIN}/devlog/{slug(m)}/')])
    sections = []
    for v in vs:
        when = f' &middot; {month(releases[v])}' if releases[v] else ''
        cards_ = '\n'.join(f'''        <article class="card">
          <span class="pill">{'Fix' if e.get('kind') == 'fix' else 'New'}</span>
          <h3>{html.escape(e['title'])}</h3>
          <p>{linked(e['body'], '../../')}</p>
        </article>''' for e in entries if e.get('version') == v)
        sections.append(f'''  <section class="section alt" aria-labelledby="v{slug(v)}">
    <div class="wrap">
      <h2 id="v{slug(v)}">Version {v}{when}</h2>
      <div class="plainly">
{cards_}
      </div>
    </div>
  </section>''')
    nav = [f'<a href="../{slug(x[0])}/">{side} {label(x[1])}</a>' for x, side in ((newer, 'Newer:'), (older, 'Older:')) if x]
    every = 'the only update' if len(vs) == 1 else 'every update, newest first'
    body = f'''<main id="main">
  <div class="wrap page-head">
    <p><a href="../../devlog.html">Devlog</a></p>
    <h1>{label(vs)}</h1>
    <p class="lede">What's new in Paper Skyline {span(vs)}, {every}. The latest version is on <a href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer=utm_source%3Dsite%26utm_medium%3Ddevlog%26utm_campaign%3Dv{m.replace('.', '_')}">Google Play</a>.</p>
  </div>
{chr(10).join(sections)}
  <section class="section" aria-label="More versions">
    <div class="wrap">
      <p>{' &middot; '.join(nav)}</p>
    </div>
  </section>
</main>'''
    return swap_main(page, body)


def moved_page(v, m, name):
    """The old per-version URL: an instant refresh to its section, canonical to the minor page."""
    to = f'../{slug(m)}/#v{slug(v)}'
    page = template(f'Version {v} | Paper Skyline devlog', f'Paper Skyline {v} is now part of the {name} devlog.',
                    f'{ORIGIN}/devlog/{slug(m)}/', 2,
                    [('Home', f'{ORIGIN}/'), ('News', f'{ORIGIN}/devlog.html'), (name, f'{ORIGIN}/devlog/{slug(m)}/')])
    page = page.replace('<link rel="canonical"', f'<meta http-equiv="refresh" content="0; url={to}">\n<link rel="canonical"', 1)
    return swap_main(page, f'''<main id="main">
  <div class="wrap page-head">
    <p><a href="../../devlog.html">Devlog</a></p>
    <h1>Version {v}</h1>
    <p class="lede">Version {v} is now on the <a href="{to}">{name} page</a>.</p>
  </div>
</main>''')


def feed(releases, entries, versions):
    rows = []
    for v in versions:
        # The id stays the old per-version URL so readers don't see every entry again
        url = f'{ORIGIN}/devlog/{slug(v)}/'
        link = f'{ORIGIN}/devlog/{slug(minor(v))}/#v{slug(v)}'
        items = ''.join(f'<h3>{html.escape(e["title"])}</h3><p>{html.escape(e["body"])}</p>'
                        for e in entries if e.get('version') == v)
        rows.append(f'''  <entry>
    <title>Paper Skyline {v}</title>
    <id>{url}</id>
    <link rel="alternate" type="text/html" href="{link}"/>
    <updated>{posted(releases, v)}</updated>
    <content type="html">{html.escape(items)}</content>
  </entry>''')
    return f'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Paper Skyline devlog</title>
  <subtitle>What's new in each version of Paper Skyline.</subtitle>
  <id>{ORIGIN}/devlog.html</id>
  <link rel="self" type="application/atom+xml" href="{ORIGIN}/feed.xml"/>
  <link rel="alternate" type="text/html" href="{ORIGIN}/devlog.html"/>
  <updated>{max(posted(releases, v) for v in versions)}</updated>
  <author><name>THLab</name><uri>{ORIGIN}/</uri></author>
  <icon>{ORIGIN}/favicon-32.png</icon>
{chr(10).join(rows)}
</feed>
'''


def devlog(releases, entries):
    page = template('Devlog | Paper Skyline', "What's new in each version of Paper Skyline.", f'{ORIGIN}/devlog.html', 0,
                    [('Home', f'{ORIGIN}/'), ('News', f'{ORIGIN}/devlog.html')])
    # Only shipped versions go on the public page; soon entries stay in news.json for the game.
    soon = []
    parts = ['''<main id="main">
  <div class="wrap page-head">
    <h1>Devlog</h1>
    <p class="lede">What's new in each version of Paper Skyline. The latest one is on <a href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer=utm_source%3Dsite%26utm_medium%3Ddevlog%26utm_campaign%3Dlede">Google Play</a>.</p>
  </div>''']
    if soon:
        parts.append(f'''
  <section class="section" aria-labelledby="soon-title">
    <div class="wrap">
      <h2 id="soon-title">Coming soon</h2>
      <p>No dates: each one arrives when it's ready, and the game tells you when it does.</p>
      <div class="plainly">
{cards(soon, 'Coming soon')}
      </div>
    </div>
  </section>''')
    parts.append('''
  <section class="section" aria-labelledby="ahead-title">
    <div class="wrap">
      <h2 id="ahead-title">The road ahead &middot; 6 October 2026</h2>
      <p>Where the plane goes next. Not in the app yet, and no dates.</p>
      <div class="plainly">
        <article class="card">
          <span class="pill">Vision</span>
          <h3>Across the whole story of civilisation</h3>
          <p>Throw your paper plane across the cities and enjoy the wonders of our world. You won&#39;t only fly through today&#39;s skies, but across the whole story of human civilisation. Fly back in time to watch the Pyramids rise, or to London in the Victorian age. Fly ahead to a future where people voyage to the farthest stars. Then cross into fictional worlds and their cities to meet the characters you love. It&#39;s all waiting for you.</p>
        </article>
      </div>
    </div>
  </section>''')
    if COMING and COMING[0] not in releases:
        lines = '\n'.join(f'          <li>{html.escape(t)}</li>' for t in COMING[1])
        parts.append(f'''
  <section class="section" aria-labelledby="coming-title">
    <div class="wrap">
      <h2 id="coming-title">Coming next: version {COMING[0]}</h2>
      <p>In testing now, and on Google Play once it passes.</p>
      <div class="card changes-card">
        <ul class="changes">
{lines}
        </ul>
      </div>
    </div>
  </section>''')
    # Titles only: each version's text lives once, on its minor page
    for m, vs in groups(shipped(releases, entries)):
        when = months(releases, vs)
        lines = '\n'.join(f'          <li>{html.escape(e["title"])}</li>' for v in vs for e in entries if e.get('version') == v)
        parts.append(f'''
  <section class="section alt" aria-labelledby="v{slug(m)}">
    <div class="wrap">
      <h2 id="v{slug(m)}"><a href="devlog/{slug(m)}/">{label(vs)}</a>{' &middot; ' + when if when else ''}</h2>
      <p>{'Version' if len(vs) == 1 else 'Versions'} {span(vs)}.</p>
      <div class="card changes-card">
        <ul class="changes">
{lines}
        </ul>
      </div>
      <p><a href="devlog/{slug(m)}/">Everything in {lower(label(vs))}</a></p>
    </div>
  </section>''')
    parts.append('</main>')
    a = page.index('<main id="main">')
    b = page.index('</main>') + len('</main>')
    return page[:a] + '\n'.join(parts) + page[b:]


def main():
    releases, entries = load()
    notes = {v: whats_new(entries, v) for v in releases}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'news.json'), 'w', encoding='utf-8') as f:
        json.dump(news_json(releases, entries), f, ensure_ascii=False, indent=1)
        f.write('\n')
    for v, text in notes.items():
        if text is None:
            print(f'whats-new-{v}.txt: skipped, over {PLAY_LIMIT}; the game repo has a hand-written one')
            continue
        with open(os.path.join(OUT, f'whats-new-{v}.txt'), 'w', encoding='utf-8') as f:
            f.write(text + '\n')
        print(f'whats-new-{v}.txt: {len(text)}/{PLAY_LIMIT} characters')
    with open(os.path.join(SITE, 'devlog.html'), 'w', encoding='utf-8') as f:
        f.write(devlog(releases, entries))
    versions = shipped(releases, entries)
    minors = groups(versions)
    for i, (m, vs) in enumerate(minors):
        newer = minors[i - 1] if i else None
        older = minors[i + 1] if i + 1 < len(minors) else None
        pages = {m: minor_page(releases, entries, m, vs, newer, older)} | {v: moved_page(v, m, lower(label(vs))) for v in vs}
        for k, text in pages.items():
            d = os.path.join(SITE, 'devlog', slug(k))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(text)
    with open(os.path.join(SITE, 'feed.xml'), 'w', encoding='utf-8') as f:
        f.write(feed(releases, entries, versions))
    with open(os.path.join(SITE, 'sitemap-devlog.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + ''.join(f'  <url><loc>{ORIGIN}/devlog/{slug(m)}/</loc></url>\n' for m, _ in minors) + '</urlset>\n')
    lastmod.run()
    print(f'news.json: {len(entries)} entries; devlog.html, {len(minors)} version pages, {len(versions)} redirects, feed.xml and sitemap-devlog.xml written')


if __name__ == '__main__':
    main()
