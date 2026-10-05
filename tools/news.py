#!/usr/bin/env python3
"""One changelog to news/out/news.json (R2), news/out/whats-new-<version>.txt (Play) and devlog.html.
Usage: tools/news.py [changelog.json]   (default: the game repo's docs/store/changelog.json, beside this site). Exits non-zero on any rule below."""
import html
import json
import os
import re
import sys

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                      os.path.join(SITE, '..', 'game-paper-flights', 'docs', 'store', 'changelog.json'))
OUT = os.path.join(SITE, 'news', 'out')
PLAY_LIMIT = 500
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December']
# Child audience (devlog spike §4): no pressure, and "Coming soon" never promises a date.
PRESSURE = re.compile(r'hurry|limited[- ]time|last chance|only today|countdown|don\'t miss|ends in|before it\'s gone',
                      re.I)
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
        if e.get('kind') not in ('new', 'soon'):
            fail(f'{i}: kind must be new or soon ("now" is decided in the game, from Play)')
        if not 0 < len(e.get('title', '')) <= 40 or not 0 < len(e.get('body', '')) <= 200:
            fail(f'{i}: title 1-40 and body 1-200 characters')
        if len(e.get('play', '')) > 120:
            fail(f'{i}: play line over 120 characters')
        text = ' '.join(e.get(k, '') for k in ('title', 'body', 'play'))
        if PRESSURE.search(text):
            fail(f'{i}: pressure wording ({PRESSURE.search(text).group(0)!r})')
        if e['kind'] == 'new':
            if e.get('version') not in releases:
                fail(f'{i}: a new entry needs a version listed in releases')
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
        for k in ('image', 'availableIn', 'version'):
            if k in e:
                r[k] = e[k]
        if e['kind'] == 'new':
            r['date'] = releases[e['version']]
        rows.append(r)
    return {'format': 1, 'entries': rows}


def whats_new(entries, version):
    lines = [f"• {e.get('play', e['title'])}" for e in entries if e.get('version') == version]
    text = '\n'.join(lines)
    if len(text) > PLAY_LIMIT:
        fail(f'Play text for {version} is {len(text)} characters, over {PLAY_LIMIT}')
    return text


def month(d):
    y, m = d.split('-')
    return f'{MONTHS[int(m) - 1]} {y}'


def cards(items, stamp):
    out = []
    for e in items:
        out.append(f'''        <article class="card">
          <span class="pill">{stamp}</span>
          <h3>{html.escape(e['title'])}</h3>
          <p>{html.escape(e['body'])}</p>
        </article>''')
    return '\n'.join(out)


def devlog(releases, entries):
    src = open(os.path.join(SITE, 'support.html'), encoding='utf-8').read()
    desc = "What's new in each version of Paper Skyline."
    old_desc = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    page = (src.replace('<title>Support | Paper Skyline</title>', '<title>Devlog | Paper Skyline</title>')
            .replace(old_desc, desc)
            .replace('https://paperskyline.org/support.html', 'https://paperskyline.org/devlog.html')
            .replace('content="Support | Paper Skyline"', 'content="Devlog | Paper Skyline"')
            .replace('<a href="support.html" aria-current="page">Support</a>', '<a href="support.html">Support</a>'))
    # Only shipped versions go on the public page; soon entries stay in news.json for the game.
    soon = []
    parts = ['''<main id="main">
  <div class="wrap page-head">
    <h1>Devlog</h1>
    <p class="lede">What's new in each version of Paper Skyline.</p>
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
    for v in sorted(releases, key=vkey, reverse=True):
        items = [e for e in entries if e.get('version') == v]
        if not items:
            continue
        when = f' &middot; {month(releases[v])}' if releases[v] else ''
        vid = 'v' + v.replace('.', '-')
        parts.append(f'''
  <section class="section alt" aria-labelledby="{vid}">
    <div class="wrap">
      <h2 id="{vid}">Version {v}{when}</h2>
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
        with open(os.path.join(OUT, f'whats-new-{v}.txt'), 'w', encoding='utf-8') as f:
            f.write(text + '\n')
        print(f'whats-new-{v}.txt: {len(text)}/{PLAY_LIMIT} characters')
    with open(os.path.join(SITE, 'devlog.html'), 'w', encoding='utf-8') as f:
        f.write(devlog(releases, entries))
    print(f'news.json: {len(entries)} entries; devlog.html written')


if __name__ == '__main__':
    main()
