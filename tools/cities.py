#!/usr/bin/env python3
"""Writes cities/<id>/, world/<continent>/<country>/ and their hubs and sitemaps from the game's own data.
Usage: tools/cities.py [path to game-paper-flights]   (default: ../game-paper-flights next to this repo)
Facts come from the city graph (kg.py, built into tools/.tmp/) and the Atlas text; nothing is written here by hand.
"""
import html
import json
import os
import re
import subprocess
import sys
import unicodedata

from art import CITIES, NAMES

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, '..', 'game-paper-flights'))
ORIGIN = 'https://paperskyline.org'
# The #96 rule: index a page only with this many words of its own verified text, plus its own image
MIN_WORDS = 300
IDS = {'rio': 'rio-de-janeiro'}
CONTINENTS = {'europe': 'Europe', 'asia': 'Asia', 'africa': 'Africa', 'north-america': 'North America',
              'south-america': 'South America', 'oceania': 'Oceania'}
LOOK_KINDS = {'trail': 'trail', 'paper': 'paper', 'ink': 'ink', 'colour': 'colour', 'fold': 'fold', 'style': 'style'}


def kg(sql):
    db = os.path.join(SITE, 'tools', '.tmp', 'kg.sqlite')
    os.makedirs(os.path.dirname(db), exist_ok=True)
    out = subprocess.run(['python3', 'design-studio/tools/kg/kg.py', '--db', db, 'sql', sql, '--json', '--limit', '0'],
                         cwd=GAME, capture_output=True, text=True, check=True).stdout
    data = json.loads(out[out.index('{'):])
    return [dict(zip(data['columns'], r)) for r in data['rows']]


def esc(s):
    return html.escape(s, quote=True)


def words(*parts):
    return sum(len(re.findall(r"[\w'’-]+", re.sub(r'<[^>]+>', ' ', p))) for p in parts)


def load():
    atlas = json.load(open(os.path.join(GAME, 'Assets/Resources/Atlas/atlas-stories.json'), encoding='utf-8'))
    cities = []
    for n, (slug, _, _) in enumerate(CITIES, 1):
        cid = IDS.get(slug, slug)
        level = json.loads(kg(f"SELECT props FROM nodes WHERE key='level:{cid}'")[0]['props'])
        beats = {r['key'].split('/', 1)[1]: json.loads(r['props'])['en']
                 for r in kg(f"SELECT key, props FROM nodes WHERE key LIKE 'story_beat:{cid}/%'")}
        bg = json.loads(kg(f"SELECT props FROM nodes WHERE key='background:{cid}'")[0]['props'])
        place = json.loads(kg(f"SELECT props FROM nodes WHERE key='place:{level['place']}'")[0]['props'])
        relics = {json.loads(r['props'])['keeper']: (r['label'], json.loads(r['props'])['reason'])
                  for r in kg(f"SELECT label, props FROM nodes WHERE kind='relic' "
                              f"AND json_extract(props,'$.city')='{cid}' AND json_extract(props,'$.shipped')=1")}
        keepers = {json.loads(r['props'])['role']: r['dst'].split(':', 1)[1]
                   for r in kg(f"SELECT dst, props FROM edges WHERE src='level:{cid}' AND kind='has_keeper'")}
        parents = [r['dst'].split(':', 1)[1] for r in kg(f"SELECT dst FROM edges WHERE src='level:{cid}' AND kind='parent'")]
        children = [r['src'].split(':', 1)[1] for r in kg(f"SELECT src FROM edges WHERE dst='level:{cid}' AND kind='parent'")]
        looks = kg(f"SELECT n.label, n.props FROM edges e JOIN nodes n ON n.key=e.dst "
                   f"WHERE e.src='level:{cid}' AND e.kind='grants_look'")
        a = atlas['cities'][cid]
        cities.append(dict(n=n, id=cid, slug=slug, name=NAMES.get(slug, level['name']), level=level, beats=beats,
                           landmark_col=bg.get('landmarkColumn', .5), coords=place.get('coords'), relics=relics, keepers=keepers,
                           parents=parents, children=children, looks=looks, atlas=a,
                           code=a['country'], cont=level['continent'],
                           country=atlas['countries'][a['country']]['name']))
    return cities, atlas


# Country names that take "the" in a sentence
THE = {'US', 'GB', 'NL'}


def the(name):
    """A keeper or country name in mid-sentence: 'The Stryge' becomes 'the Stryge'."""
    return 'the ' + name[4:] if name.startswith('The ') else name


def country_in(code, name):
    return f'the {name}' if code in THE else name


def joined(xs):
    return ', '.join(xs[:-1]) + (' and ' if len(xs) > 1 else '') + xs[-1]


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip('-')


def country_path(x):
    return f'world/{x["cont"]}/{slugify(x["country"])}/'


def head(c, title, desc, path, image, index, ld=None):
    ld = f'<script type="application/ld+json">\n{json.dumps(ld, ensure_ascii=False, indent=1)}\n</script>\n' if ld else ''
    robots = '' if index else '<meta name="robots" content="noindex,follow">\n'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{ORIGIN}{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Paper Skyline">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:image" content="{ORIGIN}/{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#fff3e3">
<link rel="icon" href="{c}favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{c}apple-touch-icon.png">
<link rel="manifest" href="{c}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@800&amp;family=Be+Vietnam+Pro:wght@400;600;700&amp;display=swap">
<link rel="stylesheet" href="{c}styles.css">
{ld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{c}">
      <picture><source type="image/avif" srcset="{c}img/mark-96.avif"><source type="image/webp" srcset="{c}img/mark-96.webp"><img src="{c}img/mark-96.png" width="96" height="96" alt=""></picture>
      Paper Skyline
    </a>
    <nav class="site-nav" aria-label="Site">
      <a href="{c}">Home</a>
      <a href="{c}business.html">Business</a>
      <a href="{c}support.html">Support</a>
      <a href="{c}privacy.html">Privacy</a>
      <a href="{c}terms.html">Terms</a>
    </nav>
  </div>
</header>
'''


def foot(c):
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div>
      <a class="brand" href="{c}">
        <picture><source type="image/avif" srcset="{c}img/mark-96.avif"><source type="image/webp" srcset="{c}img/mark-96.webp"><img src="{c}img/mark-96.png" width="96" height="96" alt=""></picture>
        Paper Skyline
      </a>
      <p>One sheet of paper, one city at a time.</p>
      <p>&copy; 2026 THLab &middot; paperskyline.org</p>
      <p class="fine">Google Play and the Google Play logo are trademarks of Google LLC.</p>
    </div>
    <nav class="site-nav" aria-label="Footer">
      <a href="{c}">Home</a>
      <a href="{c}business.html">For businesses</a>
      <a href="{c}support.html">Support</a>
      <a href="{c}privacy.html">Privacy policy</a>
      <a href="{c}terms.html">Terms of use</a>
    </nav>
  </div>
</footer>
</body>
</html>
'''


def pic(c, name, ext, alt, w, h, extra=''):
    return (f'<picture><source type="image/avif" srcset="{c}img/{name}.avif">'
            f'<source type="image/webp" srcset="{c}img/{name}.webp">'
            f'<img src="{c}img/{name}.{ext}" width="{w}" height="{h}" alt="{esc(alt)}"{extra}></picture>')


def play(c, medium, campaign):
    return ('<a class="store-link" href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer='
            f'utm_source%3Dsite%26utm_medium%3D{medium}%26utm_campaign%3D{campaign.replace("-", "_")}">\n'
            f'          <img src="{c}brand/google-play-badge.png" width="646" height="250" alt="Get it on Google Play">\n'
            '        </a>')


def names(ids, by_id):
    xs = [f'<a href="../{i}/">{esc(by_id[i]["name"])}</a>' for i in ids if i in by_id]
    return ', '.join(xs[:-1]) + (' and ' if len(xs) > 1 else '') + xs[-1] if xs else ''


def keeper_size(slug, role):
    from PIL import Image
    return Image.open(os.path.join(SITE, 'img', f'keeper-{slug}-{role}.png')).size


def keeper_card(x, role):
    b = x['beats']
    name, sub = b[f'{role}.name'], b[f'{role}.subtitle']
    w, h = keeper_size(x['slug'], role)
    relic = x['relics'].get(x['keepers'][role])
    relic_html = (f'\n          <p class="relic"><b>Guards a relic: the {esc(relic[0])}.</b> {esc(relic[1])}</p>'
                  if relic else '')
    return f'''        <li class="keeper-card">
          <div class="keepers">
            {pic('../../', f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
            {pic('../../', f'keeper-{x["slug"]}-{role}', 'png', f'{name}, {sub.split(" · ")[0].lower()}', w, h, ' loading="lazy" decoding="async"')}
          </div>
          <span class="eyebrow">{"The Elite" if role == "elite" else "The Boss"}</span>
          <h3>{esc(name)}</h3>
          <p class="sub">{esc(sub)}</p>
          <p>{esc(b[f"{role}.legend"])}</p>
          <p>{esc(b[f"{role}.wake"])} {esc(b[f"{role}.crack"])} {esc(b[f"{role}.break"])}</p>
          <blockquote class="mine"><p>&ldquo;{esc(b[f"{role}.mine"])}&rdquo;</p></blockquote>{relic_html}
        </li>'''


GAME_LD = {'@type': ['VideoGame', 'MobileApplication'], '@id': f'{ORIGIN}/#game', 'name': 'Paper Skyline',
           'applicationCategory': 'GameApplication', 'operatingSystem': 'Android', 'gamePlatform': 'Android',
           'installUrl': 'https://play.google.com/store/apps/details?id=paperskyline.org', 'url': f'{ORIGIN}/'}


def city_ld(x, title, desc):
    url = f'{ORIGIN}/cities/{x["id"]}/'
    place = {'@type': 'City', 'name': x['name'], 'containedInPlace': {'@type': 'Country', 'name': x['country']}}
    if x['coords']:
        place['geo'] = {'@type': 'GeoCoordinates', 'latitude': x['coords']['lat'], 'longitude': x['coords']['lon']}
    crumbs = [('Home', f'{ORIGIN}/'), (CONTINENTS[x['cont']], f'{ORIGIN}/world/{x["cont"]}/'),
              (x['country'], f'{ORIGIN}/{country_path(x)}'), (x['name'], url)]
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': title, 'description': desc, 'inLanguage': 'en',
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': f'{ORIGIN}/img/og-{x["slug"]}.jpg',
                                'width': 1200, 'height': 630},
         'about': place, 'mentions': {'@id': f'{ORIGIN}/#game'}, 'breadcrumb': {'@id': f'{url}#breadcrumb'}},
        {'@type': 'BreadcrumbList', '@id': f'{url}#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs, 1)]},
        GAME_LD]}


def city_page(x, by_id, total):
    a, b, lv = x['atlas'], x['beats'], x['level']
    wish = re.sub(r'^Wish #\{n\}:\s*', '', b['preflight.wish'])
    wish = wish[0].upper() + wish[1:]
    elite, boss = b['elite.name'], b['boss.name']
    hero = 'hero-paris' if x['slug'] == 'paris' else f'city-{x["slug"]}'
    srcset = lambda e: ', '.join(f'../../img/{hero}-{w}.{e} {w}w' for w in (640, 1024, 1600))
    route = []
    if x['parents']:
        route.append(f'The plane reaches {esc(x["name"])} from {names(x["parents"], by_id)}.')
    else:
        route.append(f'Every journey starts in {esc(x["name"])}.')
    nxt = [i for i in x['children'] if i in by_id]
    if nxt:
        route.append(f'Clear it and the map opens the way to {names(nxt, by_id)}.')
    for look in x['looks']:
        p = json.loads(look['props'])
        route.append(f'Its own plane look is {esc(look["label"])}, a {LOOK_KINDS.get(p.get("lookKind"), "plane")} '
                     f'look.')
    journal = ''.join(f'\n          <li>{esc(b[k])}</li>' for k in ('journal[0]', 'journal[1]') if k in b)
    body = [wish, b['preflight.goal'], a['historyTitle'], a['history'], a['historyIdLine'], a['landmarkTitle'],
            a['landmark'], b['clear'], *(b[k] for k in ('journal[0]', 'journal[1]') if k in b)]
    for role in ('elite', 'boss'):
        body += [b[f'{role}.{k}'] for k in ('name', 'subtitle', 'legend', 'wake', 'crack', 'break', 'mine')]
    body += [f'{r[0]} {r[1]}' for r in x['relics'].values()]
    n_words = words(*body)
    index = n_words >= MIN_WORDS
    title = f'{x["name"]} paper plane game | Paper Skyline'
    desc = (f'Fly a paper plane over {x["name"] if x["name"] == x["country"] else x["name"] + ", " + x["country"]}, '
            f'painted in ink and watercolour. '
            f'Meet its keepers, {the(elite)} and {the(boss)}, and the history behind them.')
    others = ''.join(f'\n        <li><a href="../{o["id"]}/">{esc(o["name"])}</a></li>'
                     for o in by_id.values() if o['id'] != x['id'])
    page = head('../../', title, desc, f'/cities/{x["id"]}/', f'img/og-{x["slug"]}.jpg', index, city_ld(x, title, desc)) + f'''
<main id="main">
  <nav class="wrap crumbs" aria-label="Breadcrumb">
    <a href="../../">Home</a> <span aria-hidden="true">/</span> <a href="../../world/{x["cont"]}/">{CONTINENTS[x["cont"]]}</a> <span aria-hidden="true">/</span> <a href="../../{country_path(x)}">{esc(x["country"])}</a> <span aria-hidden="true">/</span> <span aria-current="page">{esc(x["name"])}</span>
  </nav>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-scene">
      <picture>
        <source type="image/avif" srcset="{srcset('avif')}" sizes="100vw">
        <source type="image/webp" srcset="{srcset('webp')}" sizes="100vw">
        <img srcset="{srcset('jpg')}" sizes="100vw" src="../../img/{hero}-1024.jpg" width="1600" height="533" alt="{esc(f'The {x["name"]} skyline in ink and watercolour, as the game paints it')}" fetchpriority="high" style="object-position: {round(x['landmark_col'] * 100)}% 100%">
      </picture>
      <h1 id="hero-title" class="hero-title"><span>{esc(x["name"])}</span> <span class="small">paper plane game</span></h1>
    </div>
    <div class="wrap hero-copy">
      <div>
        <span class="eyebrow">City {x["n"]} of {total} &middot; {esc(x["country"])} &middot; {CONTINENTS[lv["continent"]]}</span>
        <p class="hero-tag">{esc(wish)}</p>
        <p class="lede">{esc(b["preflight.goal"])}</p>
      </div>
      <ul class="badges">
        <li>{play("../../", "city", x["id"])}</li>
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="history-title">
    <div class="wrap">
      <span class="eyebrow">The city</span>
      <h2 id="history-title">{esc(a["historyTitle"])}</h2>
      <p class="lede">{esc(a["history"])}</p>
      <p class="mine-line">&ldquo;{esc(a["historyIdLine"])}&rdquo;</p>
      <span class="eyebrow">The landmark</span>
      <h2 id="landmark-title">{esc(a["landmarkTitle"])}</h2>
      <p>{esc(a["landmark"])}</p>
    </div>
  </section>

  <section class="section alt" aria-labelledby="keepers-title">
    <div class="wrap">
      <span class="eyebrow">Two keepers</span>
      <h2 id="keepers-title">Who keeps the wish in {esc(x["name"])}.</h2>
      <p class="lede">An Elite wakes first; the Boss guards the wish itself. Hit their weak points for a BONK!, land the last blow for a KO!, and each one grins and takes a bow.</p>
      <ul class="keeper-grid pair">
{keeper_card(x, "elite")}
{keeper_card(x, "boss")}
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="journal-title">
    <div class="wrap">
      <span class="eyebrow">The journal</span>
      <h2 id="journal-title">{esc(b["clear"])}</h2>
      <ul class="journal">{journal}
      </ul>
      <p>{" ".join(route)}</p>
      <ul class="badges">
        <li>{play("../../", "city", x["id"] + "_end")}</li>
      </ul>
    </div>
  </section>

  <section class="section alt" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">{total} cities</span>
      <h2 id="more-title">Fly on.</h2>
      <ul class="city-links">{others}
      </ul>
    </div>
  </section>
</main>

''' + foot('../../')
    return page, n_words, index


def hub(cities):
    cards = ''.join(f'''
        <li class="keeper-card">
          <div class="keepers">
            {pic('../', f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
          </div>
          <h3><a href="{x["id"]}/">{esc(x["name"])}</a></h3>
          <p class="sub">{esc(x["country"])} &middot; {esc(x["atlas"]["landmarkTitle"])}</p>
          <p>{esc(x["beats"]["elite.name"])} and {esc(the(x["beats"]["boss.name"]))}</p>
        </li>''' for x in cities)
    desc = f'The {len(cities)} cities of Paper Skyline, from Paris to Toronto, each with its painting, its history and its two keepers.'
    return head('../', f'Cities | Paper Skyline', desc, '/cities/', 'brand/og-image-1200x630.jpg', False) + f'''
<main id="main">
  <section class="section" aria-labelledby="cities-title">
    <div class="wrap">
      <span class="eyebrow">{len(cities)} cities</span>
      <h1 id="cities-title">Where the plane flies.</h1>
      <p class="lede">{esc(desc)}</p>
      <ul class="keeper-grid">{cards}
      </ul>
    </div>
  </section>
</main>

''' + foot('../')


def city_card(x, c, href):
    keeper = lambda role: pic(c, f'keeper-{x["slug"]}-{role}', 'png', x['beats'][f'{role}.name'],
                              *keeper_size(x['slug'], role), ' loading="lazy" decoding="async"')
    return f'''
        <li class="keeper-card">
          <div class="keepers">
            {pic(c, f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
            {keeper('elite')}
            {keeper('boss')}
          </div>
          <h3><a href="{href}">{esc(x["name"])}</a></h3>
          <p class="sub">{esc(x["atlas"]["landmarkTitle"])}</p>
          <p>{esc(x["beats"]["elite.name"])} and {esc(the(x["beats"]["boss.name"]))}</p>
        </li>'''


def crumbs_html(c, trail):
    sep = ' <span aria-hidden="true">/</span> '
    xs = [f'<a href="{c}{h}">{esc(n)}</a>' for n, h in trail[:-1]] + [f'<span aria-current="page">{esc(trail[-1][0])}</span>']
    return f'  <nav class="wrap crumbs" aria-label="Breadcrumb">\n    {sep.join(xs)}\n  </nav>\n'


def page_ld(path, title, desc, trail, about=None):
    url = f'{ORIGIN}/{path}'
    page = {'@type': 'WebPage', '@id': url, 'url': url, 'name': title, 'description': desc, 'inLanguage': 'en',
            'breadcrumb': {'@id': f'{url}#breadcrumb'}, 'mentions': {'@id': f'{ORIGIN}/#game'}}
    if about:
        page['about'] = about
    return {'@context': 'https://schema.org', '@graph': [page, {
        '@type': 'BreadcrumbList', '@id': f'{url}#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': n, 'item': f'{ORIGIN}/{h}'}
            for i, (n, h) in enumerate(trail, 1)]}, GAME_LD]}


def links(c, items):
    return ''.join(f'\n        <li><a href="{c}{h}">{esc(n)}</a></li>' for n, h in items)


def country_page(code, cs, atlas, conts):
    k, x0 = atlas['countries'][code], cs[0]
    c, path, cont = '../../../', country_path(x0), x0['cont']
    n_words = words(k['intro'], k['idLine'], *k['facts'])
    index = n_words >= MIN_WORDS
    title = f'{k["name"]} paper plane game | Paper Skyline'
    desc = (f'Fly a paper plane over {joined([x["name"] for x in cs])} in Paper Skyline, '
            f'and meet the keepers of {country_in(code, k["name"])}.')
    trail = [('Home', ''), (CONTINENTS[cont], f'world/{cont}/'), (k['name'], path)]
    facts = ''.join(f'\n        <li>{esc(f)}</li>' for f in k['facts'])
    cards = ''.join(city_card(x, c, f'{c}cities/{x["id"]}/') for x in cs)
    near = [(n, h) for n, h in conts[cont] if h != path]
    more = (f'''
      <h3>More of {CONTINENTS[cont]}</h3>
      <ul class="city-links">{links(c, near)}
      </ul>''' if near else '')
    about = {'@type': 'Country', 'name': k['name']}
    outline = pic(c, f'country-{code.lower()}-320', 'png', f"The outline of {country_in(code, k['name'])} from the game's Atlas", 320, 320)
    page = head(c, title, desc, f'/{path}', f'img/og-{x0["slug"]}.jpg', index,
                page_ld(path, title, desc, trail, about)) + f'''
<main id="main">
{crumbs_html(c, trail)}  <section class="section country-head" aria-labelledby="country-title">
    <div class="wrap">
      <div>
        <span class="eyebrow">{CONTINENTS[cont]}</span>
        <h1 id="country-title">{esc(k["name"])}</h1>
        <p class="lede">{esc(k["intro"])}</p>
        <p class="mine-line">&ldquo;{esc(k["idLine"])}&rdquo;</p>
        <ul class="journal">{facts}
        </ul>
      </div>
      {outline}
    </div>
  </section>

  <section class="section alt" aria-labelledby="cities-title">
    <div class="wrap">
      <span class="eyebrow">{len(cs)} {"city" if len(cs) == 1 else "cities"} in the game</span>
      <h2 id="cities-title">Fly over {esc(country_in(code, k["name"]))}.</h2>
      <ul class="keeper-grid">{cards}
      </ul>
      <ul class="badges more">
        <li>{play(c, "country", code.lower())}</li>
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">The world</span>
      <h2 id="more-title">Fly on.</h2>{more}
      <h3>Every continent</h3>
      <ul class="city-links">{links(c, [(CONTINENTS[k2], f'world/{k2}/') for k2 in conts])}
      </ul>
    </div>
  </section>
</main>

''' + foot(c)
    return path, page, n_words, index


def continent_page(cont, cs, conts, total):
    c, path = '../../', f'world/{cont}/'
    name = CONTINENTS[cont]
    title = f'{name} in Paper Skyline | paper plane game'
    countries = sorted({x['country'] for x in cs})
    desc = (f'{len(cs)} of the {total} cities in Paper Skyline are in {name}, across {len(countries)} '
            f'{"country" if len(countries) == 1 else "countries"}: {joined([x["name"] for x in cs])}.')
    trail = [('Home', ''), (name, path)]
    cards = ''.join(city_card(x, c, f'{c}cities/{x["id"]}/') for x in cs)
    page = head(c, title, desc, f'/{path}', f'img/og-{cs[0]["slug"]}.jpg', False,
                page_ld(path, title, desc, trail, {'@type': 'Continent', 'name': name})) + f'''
<main id="main">
{crumbs_html(c, trail)}  <section class="section" aria-labelledby="cont-title">
    <div class="wrap">
      <span class="eyebrow">{len(cs)} {"city" if len(cs) == 1 else "cities"} &middot; {len(countries)} {"country" if len(countries) == 1 else "countries"}</span>
      <h1 id="cont-title">{name}</h1>
      <p class="lede">{esc(desc)}</p>
      <ul class="city-links">{links(c, conts[cont])}
      </ul>
      <ul class="keeper-grid">{cards}
      </ul>
    </div>
  </section>

  <section class="section alt" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">The world</span>
      <h2 id="more-title">Fly on.</h2>
      <ul class="city-links">{links(c, [(CONTINENTS[k], f'world/{k}/') for k in conts if k != cont])}
      </ul>
    </div>
  </section>
</main>

''' + foot(c)
    return path, page


def world_page(by_cont, conts, total):
    c, path = '../', 'world/'
    title = 'The world of Paper Skyline | paper plane game'
    desc = f'Every city in Paper Skyline by continent and country: {total} cities, from Paris to Toronto.'
    trail = [('Home', ''), ('World', path)]
    blocks = ''.join(f'''
      <h2><a href="{c}world/{k}/">{CONTINENTS[k]}</a></h2>
      <ul class="city-links">{links(c, [(x['name'] if x['name'] == x['country'] else f'{x["name"]}, {x["country"]}', f'cities/{x["id"]}/')
                                             for x in by_cont[k]])}
      </ul>''' for k in conts)
    page = head(c, title, desc, f'/{path}', 'brand/og-image-1200x630.jpg', False,
                page_ld(path, title, desc, trail)) + f'''
<main id="main">
{crumbs_html(c, trail)}  <section class="section world" aria-labelledby="world-title">
    <div class="wrap">
      <span class="eyebrow">{total} cities</span>
      <h1 id="world-title">Where the plane flies.</h1>
      <p class="lede">{esc(desc)}</p>{blocks}
    </div>
  </section>
</main>

''' + foot(c)
    return path, page


def write(path, page):
    os.makedirs(os.path.join(SITE, path), exist_ok=True)
    open(os.path.join(SITE, path, 'index.html'), 'w', encoding='utf-8').write(page)


def sitemap(name, urls):
    rows = ''.join(f'  <url><loc>{ORIGIN}/{u}</loc></url>\n' for u in urls)
    open(os.path.join(SITE, name), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{rows}</urlset>\n')


def main():
    cities, atlas = load()
    by_id = {x['id']: x for x in cities}
    urls = []
    for x in cities:
        page, n, index = city_page(x, by_id, len(cities))
        write(f'cities/{x["id"]}/', page)
        print(f'{x["id"]:16} {n:4} words  {"index" if index else "noindex"}')
        if index:
            urls.append(f'cities/{x["id"]}/')
    write('cities/', hub(cities))
    sitemap('sitemap-cities.xml', urls)

    by_cont, by_code = {}, {}
    for x in cities:
        by_cont.setdefault(x['cont'], []).append(x)
        by_code.setdefault(x['code'], []).append(x)
    order = [k for k in CONTINENTS if k in by_cont]
    conts = {k: sorted({(x['country'], country_path(x)) for x in by_cont[k]}) for k in order}
    urls = []
    for code, cs in by_code.items():
        path, page, n, index = country_page(code, cs, atlas, conts)
        write(path, page)
        print(f'{path:36} {n:4} words  {"index" if index else "noindex"}')
        if index:
            urls.append(path)
    for k in order:
        write(*continent_page(k, by_cont[k], conts, len(cities)))
    write(*world_page(by_cont, order, len(cities)))
    sitemap('sitemap-world.xml', urls)


if __name__ == '__main__':
    main()
