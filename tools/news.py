#!/usr/bin/env python3
"""One changelog to news/out/news.json (R2), news/out/whats-new-<version>.txt (Play), devlog.html,
devlog/<version>/, feed.xml (Atom) and sitemap-devlog.xml.
Usage: tools/news.py [changelog.json]   (default: the game repo's docs/store/changelog.json, beside this site). Exits non-zero on any rule below."""
import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from art import CITIES, IDS, NAMES  # noqa: E402

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(SITE, '..', 'game-paper-flights', 'docs', 'store', 'changelog.json'))
OUT = os.path.join(SITE, 'news', 'out')
GAME = os.path.join(SITE, '..', 'game-paper-flights')
ORIGIN = 'https://paperskyline.org'
# The newest version on Play production: nothing after it is published here, whatever the changelog holds
LIVE = '1.9.3'
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


def template(title, desc, url, depth):
    """support.html's chrome with this page's head; depth re-roots its relative links."""
    src = open(os.path.join(SITE, 'support.html'), encoding='utf-8').read()
    old_desc = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    page = (src.replace('<title>Support | Paper Skyline</title>', f'<title>{title}</title>')
            .replace(old_desc, desc)
            .replace('https://paperskyline.org/support.html', url)
            .replace('content="Support | Paper Skyline"', f'content="{title}"')
            .replace('<a href="support.html" aria-current="page">Support</a>', '<a href="support.html">Support</a>')
            .replace('<link rel="canonical"', '<link rel="alternate" type="application/atom+xml" title="Paper Skyline devlog" href="/feed.xml">\n<link rel="canonical"'))
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


def release_page(v, items, newer, older):
    entries = ', '.join(e['title'] for e in items[:-1]) + (' and ' if len(items) > 1 else '') + items[-1]['title']
    title = f'Version {v} | Paper Skyline devlog'
    desc = html.escape(f"What's new in Paper Skyline {v}: {entries}.", quote=True)
    page = template(title, desc, f'{ORIGIN}/devlog/{slug(v)}/', 2)
    cards_ = '\n'.join(f'''        <article class="card">
          <span class="pill">{'Fix' if e.get('kind') == 'fix' else 'New'}</span>
          <h3>{html.escape(e['title'])}</h3>
          <p>{linked(e['body'], '../../')}</p>
        </article>''' for e in items)
    nav = [f'<a href="../{slug(x)}/">{label} {x}</a>' for x, label in ((newer, 'Newer:'), (older, 'Older:')) if x]
    body = f'''<main id="main">
  <div class="wrap page-head">
    <p><a href="../../devlog.html">Devlog</a></p>
    <h1>Version {v}</h1>
    <p class="lede">What's new in Paper Skyline {v}. The latest version is on <a href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer=utm_source%3Dsite%26utm_medium%3Ddevlog%26utm_campaign%3Dv{v.replace('.', '_')}">Google Play</a>.</p>
  </div>
  <section class="section alt" aria-label="Version {v}">
    <div class="wrap">
      <div class="plainly">
{cards_}
      </div>
      <p>{' &middot; '.join(nav)}</p>
    </div>
  </section>
</main>'''
    a = page.index('<main id="main">')
    b = page.index('</main>') + len('</main>')
    return page[:a] + body + page[b:]


def feed(releases, entries, versions):
    rows = []
    for v in versions:
        url = f'{ORIGIN}/devlog/{slug(v)}/'
        items = ''.join(f'<h3>{html.escape(e["title"])}</h3><p>{html.escape(e["body"])}</p>'
                        for e in entries if e.get('version') == v)
        rows.append(f'''  <entry>
    <title>Paper Skyline {v}</title>
    <id>{url}</id>
    <link rel="alternate" type="text/html" href="{url}"/>
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
    page = template('Devlog | Paper Skyline', "What's new in each version of Paper Skyline.", f'{ORIGIN}/devlog.html', 0)
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
    for v in shipped(releases, entries):
        items = [e for e in entries if e.get('version') == v]
        when = f' &middot; {month(releases[v])}' if releases[v] else ''
        vid = 'v' + v.replace('.', '-')
        parts.append(f'''
  <section class="section alt" aria-labelledby="{vid}">
    <div class="wrap">
      <h2 id="{vid}"><a href="devlog/{slug(v)}/">Version {v}</a>{when}</h2>
      <div class="plainly">
{cards(items, 'New')}
      </div>
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
    for i, v in enumerate(versions):
        d = os.path.join(SITE, 'devlog', slug(v))
        os.makedirs(d, exist_ok=True)
        items = [e for e in entries if e.get('version') == v]
        newer = versions[i - 1] if i else None
        older = versions[i + 1] if i + 1 < len(versions) else None
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(release_page(v, items, newer, older))
    with open(os.path.join(SITE, 'feed.xml'), 'w', encoding='utf-8') as f:
        f.write(feed(releases, entries, versions))
    with open(os.path.join(SITE, 'sitemap-devlog.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + ''.join(f'  <url><loc>{ORIGIN}/devlog/{slug(v)}/</loc></url>\n' for v in versions) + '</urlset>\n')
    print(f'news.json: {len(entries)} entries; devlog.html, {len(versions)} release pages, feed.xml and sitemap-devlog.xml written')


if __name__ == '__main__':
    main()
