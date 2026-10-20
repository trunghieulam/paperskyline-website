#!/usr/bin/env python3
"""Writes cities/<id>/, world/<continent>/<country>/ and their hubs and sitemaps from the game's own data,
in English at the root and in each other language under /<lang>/.
Usage: tools/cities.py [path to game-paper-flights]   (default: ../game-paper-flights next to this repo)
Facts come from the city graph (kg.py, built into tools/.tmp/), the Atlas text and the game's locale packs;
the only text written here is the page furniture in tools/i18n.py.
"""
import base64
import copy
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import unicodedata

from art import CITIES, IDS, NAMES
from i18n import DISCORD, T

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, '..', 'game-paper-flights'))
PACKS = os.path.join(GAME, 'Assets/Content/Locale/packs')
# The City Writer's verified extra text; WEB_TEXT points a preview build at an unmerged branch's checkout
TEXT = os.environ.get('WEB_TEXT', os.path.join(GAME, 'design/web-text'))
ORIGIN = 'https://paperskyline.org'
LANGS = ['en', 'zh-Hans', 'id']
# The #96 rule: index a page only with this much verified text of its own, plus its own image.
# Chinese counts Han characters; 450 is the usual 1.5 characters per English word.
MIN_WORDS = {'en': 300, 'zh-Hans': 450, 'id': 300}
# #97 votes; the Turnstile widget and the Worker accept paperskyline.org only.
VOTE_API = 'https://paperskyline-stats.paperskyline-stats.workers.dev/v1'
TURNSTILE_KEY = '0x4AAAAAAFbTIz8qnpCl2WLo'
TURNSTILE = 'https://challenges.cloudflare.com'
DISCORD_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z"/></svg>'


def kg(sql):
    db = os.path.join(SITE, 'tools', '.tmp', 'kg.sqlite')
    os.makedirs(os.path.dirname(db), exist_ok=True)
    out = subprocess.run(['python3', 'design-studio/tools/kg/kg.py', '--db', db, 'sql', sql, '--json', '--limit', '0'],
                         cwd=GAME, capture_output=True, text=True, check=True).stdout
    data = json.loads(out[out.index('{'):])
    return [dict(zip(data['columns'], r)) for r in data['rows']]


def esc(s):
    return html.escape(s, quote=True)


def words(lang, *parts):
    text = ' '.join(re.sub(r'<[^>]+>', ' ', p) for p in parts)
    if lang == 'zh-Hans':
        return len(re.findall(r'[㐀-鿿]', text)) + len(re.findall(r"[A-Za-z0-9'’-]+", text))
    return len(re.findall(r"[\w'’-]+", text))


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
        looks = kg(f"SELECT n.key, n.label, n.props FROM edges e JOIN nodes n ON n.key=e.dst "
                   f"WHERE e.src='level:{cid}' AND e.kind='grants_look'")
        a = atlas['cities'][cid]
        country = atlas['countries'][a['country']]['name']
        cities.append(dict(n=n, id=cid, slug=slug, name=NAMES.get(slug, level['name']), level=level, beats=beats,
                           landmark_col=bg.get('landmarkColumn', .5), coords=place.get('coords'), relics=relics, keepers=keepers,
                           parents=parents, children=children, looks=looks, atlas=a,
                           code=a['country'], cont=level['continent'], country=country,
                           country_path=f'world/{level["continent"]}/{slugify(country)}/'))
    return cities, atlas


def localize(cities, atlas, lang):
    """The same cities with every visible string from the game's <lang> packs; a missing key fails the build."""
    if lang == 'en':
        return cities, atlas
    pack = lambda f: json.load(open(os.path.join(PACKS, lang, f), encoding='utf-8'))
    ui, story = pack(f'{lang}.json'), pack(f'v1-story.{lang}.json')['cities']
    # A dash joining two names (斯托克顿—达灵顿) is a range, which the site sets as an en dash; the no-em-dash rule stands
    at = json.loads(re.sub(r'(?<=\S)—(?=\S)', '–', open(os.path.join(PACKS, lang, f'atlas-stories.{lang}.json'), encoding='utf-8').read()))
    out = []
    for x in cities:
        s, y = story[x['id']], copy.deepcopy(x)
        b = {'preflight.wish': s['preflight']['wish'], 'preflight.goal': s['preflight']['goal'], 'clear': s['clear']}
        b.update({f'journal[{i}]': j for i, j in enumerate(s['journal'])})
        for role in ('elite', 'boss'):
            b.update({f'{role}.{k}': v for k, v in s[role].items() if isinstance(v, str)})
        y['beats'] = b
        y['relics'] = {x['keepers'][role]: (s[role]['relic']['name'], s[role]['relic']['effect'])
                       for role in ('elite', 'boss') if x['keepers'][role] in x['relics']}
        y['looks'] = [dict(l, label=ui[f'look.{l["key"].split(":", 1)[1]}.name']) for l in x['looks']]
        y['name'] = ui[f'city.{x["id"]}.name']
        y['atlas'] = at['cities'][x['id']]
        y['country'] = at['countries'][x['code']]['name']
        out.append(y)
    return out, at


def extra(kind, key, lang):
    """The "## heading" sections of design/web-text/<kind>/<key>.<lang>.md as (heading, [paragraphs]), or []."""
    f = os.path.join(TEXT, kind, f'{key}.{lang}.md')
    if not os.path.exists(f):
        return []
    out = []
    for block in re.split(r'\n\s*\n', open(f, encoding='utf-8').read().strip()):
        block = ' '.join(block.split())
        if re.search(r'\]\(|^[-*>#]|\*\*', re.sub(r'^## ', '', block)):
            sys.exit(f'{f}: only "## heading" and plain paragraphs are rendered: {block[:60]}')
        if block.startswith('## '):
            out.append((block[3:], []))
        elif out:
            out[-1][1].append(block)
        else:
            sys.exit(f'{f}: text before the first "## heading"')
    return out


def extra_html(secs, id_):
    """One section holding every extra heading and its paragraphs."""
    if not secs:
        return ''
    body = ''.join(f'\n      <h2 id="{id_}-{i}">{esc(h)}</h2>' + ''.join(f'\n      <p>{esc(p)}</p>' for p in ps)
                   for i, (h, ps) in enumerate(secs, 1))
    return f'''  <section class="section extra" aria-labelledby="{id_}-1">
    <div class="wrap">{body}
    </div>
  </section>

'''


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip('-')


def prefix(lang):
    return '' if lang == 'en' else f'{lang}/'


def hreflang(c, rel, lang, t, langs=LANGS):
    """The alternate links for <head> and the visible language switcher, for the page at <lang>/<rel>."""
    alts = ''.join(f'<link rel="alternate" hreflang="{l}" href="{ORIGIN}/{prefix(l)}{rel}">\n' for l in langs)
    alts += f'<link rel="alternate" hreflang="x-default" href="{ORIGIN}/{rel}">\n'
    xs = [f'<span aria-current="true">{T[l]["name"]}</span>' if l == lang else
          f'<a href="{c}{prefix(l)}{rel}" hreflang="{l}" lang="{l}">{T[l]["name"]}</a>' for l in langs]
    switch = f'    <nav class="langs" aria-label="{t["langs"]}">{" ".join(xs)}</nav>\n'
    return alts, switch


def head(c, t, lang, title, desc, rel, image, index, ld=None, langs=LANGS, csp=None):
    ld = f'<script type="application/ld+json">\n{json.dumps(ld, ensure_ascii=False, indent=1)}\n</script>\n' if ld else ''
    robots = '' if index else '<meta name="robots" content="noindex,follow">\n'
    alts, switch = hreflang(c, rel, lang, t, langs)
    csp = f'<meta http-equiv="Content-Security-Policy" content="{csp}">\n' if csp else ''
    path = f'/{prefix(lang)}{rel}'
    nav = ''.join(f'\n      <a href="{c}{h}">{n}</a>' for n, h in zip(t['nav'], [prefix(lang), 'business.html', 'support.html', 'privacy.html', 'terms.html']))
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{csp}<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{ORIGIN}{path}">
{alts}<meta property="og:type" content="website">
<meta property="og:site_name" content="Paper Skyline">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:image" content="{ORIGIN}/{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{t["og_locale"]}">
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
<a class="skip" href="#main">{t["skip"]}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{c}{prefix(lang)}">
      <picture><source type="image/avif" srcset="{c}img/mark-96.avif"><source type="image/webp" srcset="{c}img/mark-96.webp"><img src="{c}img/mark-96.png" width="96" height="96" alt=""></picture>
      Paper Skyline
    </a>
    <nav class="site-nav" aria-label="Site">{nav}
    </nav>
  </div>
</header>
''', switch


def foot(c, t, lang):
    nav = ''.join(f'\n      <a href="{c}{h}">{n}</a>' for n, h in zip(t['foot_nav'], [prefix(lang), 'business.html', 'support.html', 'privacy.html', 'terms.html']))
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div>
      <a class="brand" href="{c}{prefix(lang)}">
        <picture><source type="image/avif" srcset="{c}img/mark-96.avif"><source type="image/webp" srcset="{c}img/mark-96.webp"><img src="{c}img/mark-96.png" width="96" height="96" alt=""></picture>
        Paper Skyline
      </a>
      <p>{t["tagline"]}</p>
      <p>{discord(t)}</p>
      <p>&copy; 2026 THLab &middot; paperskyline.org</p>
      <p class="fine">{t["trademark"]}</p>
    </div>
    <nav class="site-nav" aria-label="Footer">{nav}
    </nav>
  </div>
</footer>
</body>
</html>
'''


def discord(t, cls='discord'):
    return f'<a class="{cls}" href="{DISCORD}">{DISCORD_SVG}{t["discord"]}</a>'


def og(slug, lang):
    """The share card with the city's name in the page's language, where art.py made one."""
    local = f'img/og-{slug}-{lang.lower()}.jpg'
    return local if lang != 'en' and os.path.exists(os.path.join(SITE, local)) else f'img/og-{slug}.jpg'


def pic(c, name, ext, alt, w, h, extra=''):
    return (f'<picture><source type="image/avif" srcset="{c}img/{name}.avif">'
            f'<source type="image/webp" srcset="{c}img/{name}.webp">'
            f'<img src="{c}img/{name}.{ext}" width="{w}" height="{h}" alt="{esc(alt)}"{extra}></picture>')


def play(c, lang, medium, campaign):
    # Play Console splits installs by medium, so each language gets its own: city, city_zh_hans, city_id
    medium += '' if lang == 'en' else '_' + lang.lower().replace('-', '_')
    alt = '' if lang == 'en' else ' lang="en"'
    return ('<a class="store-link" href="https://play.google.com/store/apps/details?id=paperskyline.org&amp;referrer='
            f'utm_source%3Dsite%26utm_medium%3D{medium}%26utm_campaign%3D{campaign.replace("-", "_")}">\n'
            f'          <img src="{c}brand/google-play-badge.png" width="646" height="250" alt="Get it on Google Play"{alt}>\n'
            '        </a>')


def names(t, ids, by_id, base='../'):
    xs = [f'<a href="{base}{i}/">{esc(by_id[i]["name"])}</a>' for i in ids if i in by_id]
    return t['join'](xs) if xs else ''


def route(t, x, by_id, base='../'):
    """Where the plane reaches the city from and where clearing it leads: the city's ties on the map."""
    out = [t['route_from'].format(name=esc(x['name']), cities=names(t, x['parents'], by_id, base)) if x['parents']
           else t['route_start'].format(name=esc(x['name']))]
    nxt = [i for i in x['children'] if i in by_id]
    if nxt:
        out.append(t['route_next'].format(cities=names(t, nxt, by_id, base)))
    return out


def keeper_size(slug, role):
    from PIL import Image
    return Image.open(os.path.join(SITE, 'img', f'keeper-{slug}-{role}.png')).size


def keeper_card(c, t, x, role):
    b = x['beats']
    name, sub = b[f'{role}.name'], b[f'{role}.subtitle']
    w, h = keeper_size(x['slug'], role)
    relic = x['relics'].get(x['keepers'][role])
    relic_html = (f'\n          <p class="relic"><b>{esc(t["relic"].format(relic=relic[0]))}</b>{t["sp"]}{esc(relic[1])}</p>'
                  if relic else '')
    return f'''        <li class="keeper-card">
          <div class="keepers">
            {pic(c, f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
            {pic(c, f'keeper-{x["slug"]}-{role}', 'png', t['keeper_alt'](name, sub), w, h, ' loading="lazy" decoding="async"')}
          </div>
          <span class="eyebrow">{t[role]}</span>
          <h3>{esc(name)}</h3>
          <p class="sub">{esc(sub)}</p>
          <p>{esc(b[f"{role}.legend"])}</p>
          <p>{t["sp"].join(esc(b[f"{role}.{k}"]) for k in ("wake", "crack", "break"))}</p>
          <blockquote class="mine"><p>&ldquo;{esc(b[f"{role}.mine"])}&rdquo;</p></blockquote>{relic_html}
        </li>'''


GAME_LD = {'@type': ['VideoGame', 'MobileApplication'], '@id': f'{ORIGIN}/#game', 'name': 'Paper Skyline',
           'applicationCategory': 'GameApplication', 'operatingSystem': 'Android', 'gamePlatform': 'Android',
           'installUrl': 'https://play.google.com/store/apps/details?id=paperskyline.org', 'url': f'{ORIGIN}/',
           'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}}


def crumbs_html(c, t, trail, switch):
    sep = ' <span aria-hidden="true">/</span> '
    xs = [f'<a href="{c}{h}">{esc(n)}</a>' for n, h in trail[:-1]] + [f'<span aria-current="page">{esc(trail[-1][0])}</span>']
    return (f'  <div class="wrap topbar">\n    <nav class="crumbs" aria-label="{t["crumbs"]}">\n      {sep.join(xs)}\n    </nav>\n'
            f'{switch}  </div>\n')


def page_ld(lang, rel, title, desc, trail, about=None, image=None):
    url = f'{ORIGIN}/{prefix(lang)}{rel}'
    page = {'@type': 'WebPage', '@id': url, 'url': url, 'name': title, 'description': desc, 'inLanguage': lang}
    if image:
        page['primaryImageOfPage'] = {'@type': 'ImageObject', 'url': f'{ORIGIN}/{image}', 'width': 1200, 'height': 630}
    if about:
        page['about'] = about
    page.update({'mentions': {'@id': f'{ORIGIN}/#game'}, 'breadcrumb': {'@id': f'{url}#breadcrumb'}})
    return {'@context': 'https://schema.org', '@graph': [page, {
        '@type': 'BreadcrumbList', '@id': f'{url}#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': n, 'item': f'{ORIGIN}/{h}'}
            for i, (n, h) in enumerate(trail, 1)]}, GAME_LD]}


def city_page(x, by_id, total, lang):
    t, p = T[lang], prefix(lang)
    c = '../../' + '../' * (lang != 'en')
    a, b, lv = x['atlas'], x['beats'], x['level']
    wish = re.sub(r'^[^#]*#\{n\}[:：]\s*', '', b['preflight.wish'])
    wish = wish[0].upper() + wish[1:]
    elite, boss = b['elite.name'], b['boss.name']
    hero = 'hero-paris' if x['slug'] == 'paris' else f'city-{x["slug"]}'
    srcset = lambda e: ', '.join(f'{c}img/{hero}-{w}.{e} {w}w' for w in (640, 1024, 1600))
    ties = route(t, x, by_id)
    for look in x['looks']:
        kind = t['kinds'].get(json.loads(look['props']).get('lookKind'), t['kinds']['style'])
        ties.append(t['route_look'].format(look=esc(look['label']), kind=kind))
    journal = ''.join(f'\n          <li>{esc(b[k])}</li>' for k in ('journal[0]', 'journal[1]') if k in b)
    body = [wish, b['preflight.goal'], a['historyTitle'], a['history'], a['historyIdLine'], a['landmarkTitle'],
            a['landmark'], b['clear'], *(b[k] for k in ('journal[0]', 'journal[1]') if k in b)]
    for role in ('elite', 'boss'):
        body += [b[f'{role}.{k}'] for k in ('name', 'subtitle', 'legend', 'wake', 'crack', 'break', 'mine')]
    body += [f'{r[0]} {r[1]}' for r in x['relics'].values()]
    secs = extra('cities', x['id'], lang)
    body += [h for h, _ in secs] + [p for _, ps in secs for p in ps]
    n_words = words(lang, *body)
    index = n_words >= MIN_WORDS[lang]
    rel = f'cities/{x["id"]}/'
    title = t['city_title'].format(name=x['name'])
    desc = t['city_desc'].format(place=t['place'](x['name'], x['country']), elite=t['the'](elite), boss=t['the'](boss))
    others = ''.join(f'\n        <li><a href="../{o["id"]}/">{esc(o["name"])}</a></li>'
                     for o in by_id.values() if o['id'] != x['id'])
    cont = t['continents'][x['cont']]
    trail = [(t['home'], p), (cont, f'{p}world/{x["cont"]}/'), (x['country'], p + x['country_path']), (x['name'], p + rel)]
    place = {'@type': 'City', 'name': x['name'], 'containedInPlace': {'@type': 'Country', 'name': x['country']}}
    if x['coords']:
        place['geo'] = {'@type': 'GeoCoordinates', 'latitude': x['coords']['lat'], 'longitude': x['coords']['lon']}
    image = og(x["slug"], lang)
    top, switch = head(c, t, lang, title, desc, rel, image, index, page_ld(lang, rel, title, desc, trail, place, image))
    page = top + f'''
<main id="main">
{crumbs_html(c, t, trail, switch)}  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-scene">
      <picture>
        <source type="image/avif" srcset="{srcset('avif')}" sizes="100vw">
        <source type="image/webp" srcset="{srcset('webp')}" sizes="100vw">
        <img srcset="{srcset('jpg')}" sizes="100vw" src="{c}img/{hero}-1024.jpg" width="1600" height="533" alt="{esc(t['hero_alt'].format(name=x['name']))}" fetchpriority="high" style="object-position: {round(x['landmark_col'] * 100)}% 100%">
      </picture>
      <h1 id="hero-title" class="hero-title"><span>{esc(x["name"])}</span> <span class="small">{t["h1_small"]}</span></h1>
    </div>
    <div class="wrap hero-copy">
      <div>
        <span class="eyebrow">{t["city_eb"].format(n=x["n"], total=total)} &middot; {esc(x["country"])} &middot; {cont}</span>
        <p class="hero-tag">{esc(wish)}</p>
        <p class="lede">{esc(b["preflight.goal"])}</p>
      </div>
      <ul class="badges">
        <li>{play(c, lang, "city", x["id"])}</li>
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="history-title">
    <div class="wrap">
      <span class="eyebrow">{t["the_city"]}</span>
      <h2 id="history-title">{esc(a["historyTitle"])}</h2>
      <p class="lede">{esc(a["history"])}</p>
      <p class="mine-line">&ldquo;{esc(a["historyIdLine"])}&rdquo;</p>
      <span class="eyebrow">{t["the_landmark"]}</span>
      <h2 id="landmark-title">{esc(a["landmarkTitle"])}</h2>
      <p>{esc(a["landmark"])}</p>
    </div>
  </section>

{extra_html(secs, "about")}  <section class="section alt" aria-labelledby="keepers-title">
    <div class="wrap">
      <span class="eyebrow">{t["two_keepers"]}</span>
      <h2 id="keepers-title">{t["keepers_h2"].format(name=esc(x["name"]))}</h2>
      <p class="lede">{t["keepers_lede"]}</p>
      <ul class="keeper-grid pair">
{keeper_card(c, t, x, "elite")}
{keeper_card(c, t, x, "boss")}
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="journal-title">
    <div class="wrap">
      <span class="eyebrow">{t["the_journal"]}</span>
      <h2 id="journal-title">{esc(b["clear"])}</h2>
      <ul class="journal">{journal}
      </ul>
      <p>{t["sp"].join(ties)}</p>
      <ul class="badges">
        <li>{play(c, lang, "city", x["id"] + "_end")}</li>
      </ul>
    </div>
  </section>

  <section class="section alt" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">{t["n_cities"](total)}</span>
      <h2 id="more-title">{t["fly_on"]}</h2>
      <ul class="city-links">{others}
      </ul>
    </div>
  </section>
</main>

''' + foot(c, t, lang)
    return page, n_words, index


def hub(cities, lang):
    t = T[lang]
    c = '../' + '../' * (lang != 'en')
    cards = ''.join(f'''
        <li class="keeper-card">
          <div class="keepers">
            {pic(c, f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
          </div>
          <h3><a href="{x["id"]}/">{esc(x["name"])}</a></h3>
          <p class="sub">{esc(x["country"])} &middot; {esc(x["atlas"]["landmarkTitle"])}</p>
          <p>{esc(t["join"]([x["beats"]["elite.name"], t["the"](x["beats"]["boss.name"])]))}</p>
        </li>''' for x in cities)
    desc = t['hub_desc'].format(n=len(cities), first=cities[0]['name'], last=cities[-1]['name'])
    top, switch = head(c, t, lang, t['hub_title'], desc, 'cities/', 'brand/og-image-1200x630.jpg', False)
    return top + f'''
<main id="main">
  <div class="wrap topbar">
{switch}  </div>
  <section class="section" aria-labelledby="cities-title">
    <div class="wrap">
      <span class="eyebrow">{t["n_cities"](len(cities))}</span>
      <h1 id="cities-title">{t["hub_h1"]}</h1>
      <p class="lede">{esc(desc)}</p>
      <ul class="keeper-grid">{cards}
      </ul>
    </div>
  </section>
</main>

''' + foot(c, t, lang)


def home(cities, lang):
    """/<lang>/: the home page in the listing's own words, then every city; English keeps the hand-written index.html."""
    t, h, p, c = T[lang], T[lang]['homepage'], prefix(lang), '../'
    srcset = lambda e: ', '.join(f'{c}img/hero-paris-{w}.{e} {w}w' for w in (640, 1024, 1600))
    cards = ''.join(f'''
        <div class="card">
          <h3>{esc(n)}</h3>
          <p>{esc(d)}</p>
        </div>''' for n, d in h['cards']).replace('{n}', str(len(cities)))
    tiles = ''.join(city_card(x, c, t, f'cities/{x["id"]}/') for x in cities)
    url = f'{ORIGIN}/{p}'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': h['title'], 'description': h['desc'], 'inLanguage': lang,
         'about': {'@id': f'{ORIGIN}/#game'}}, GAME_LD]}
    top, switch = head(c, t, lang, h['title'], h['desc'], '', 'brand/og-image-1200x630.jpg', True, ld)
    return top + f'''
<main id="main">
  <div class="wrap topbar">
{switch}  </div>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-scene">
      <picture>
        <source type="image/avif" srcset="{srcset('avif')}" sizes="100vw">
        <source type="image/webp" srcset="{srcset('webp')}" sizes="100vw">
        <img srcset="{srcset('jpg')}" sizes="100vw" src="{c}img/hero-paris-1024.jpg" width="1600" height="533" alt="{esc(h['alt'])}" fetchpriority="high">
      </picture>
      <h1 id="hero-title" class="hero-title" lang="en"><span>Paper</span> <span>Skyline</span></h1>
    </div>
    <div class="wrap hero-copy">
      <div>
        <span class="eyebrow">{h["eyebrow"]}</span>
        <p class="hero-tag">{esc(h["tag"])}</p>
        <p class="lede">{esc(h["lede"])}</p>
      </div>
      <ul class="badges">
        <li>{play(c, lang, "home", "badge")}</li>
        <li>{discord(t, "discord join")}</li>
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="play-title">
    <div class="wrap">
      <span class="eyebrow">{h["play_eb"]}</span>
      <h2 id="play-title">{h["play_h2"]}</h2>
      <div class="plainly">{cards}
      </div>
    </div>
  </section>

  <section class="section alt" aria-labelledby="cities-title">
    <div class="wrap">
      <span class="eyebrow">{t["n_cities"](len(cities))}</span>
      <h2 id="cities-title">{t["hub_h1"]}</h2>
      <ul class="city-links">
        <li><a href="world/">{h["by_cont"]}</a></li>
        <li><a href="cities/">{h["all_cities"]}</a></li>
      </ul>
      <ul class="keeper-grid">{tiles}
      </ul>
      <ul class="badges more">
        <li>{play(c, lang, "home", "cities")}</li>
      </ul>
    </div>
  </section>
</main>

''' + foot(c, t, lang)


def city_card(x, c, t, href):
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
          <p>{esc(t["join"]([x["beats"]["elite.name"], t["the"](x["beats"]["boss.name"])]))}</p>
        </li>'''


def city_row(x, c, t, href, by_id, total):
    """A country page's section for one of its cities: the painting and keepers beside its postcard and map ties."""
    keeper = lambda role: pic(c, f'keeper-{x["slug"]}-{role}', 'png', x['beats'][f'{role}.name'],
                              *keeper_size(x['slug'], role), ' loading="lazy" decoding="async"')
    keepers = t['keepers_line'].format(keepers=esc(t['join']([x['beats']['elite.name'], t['the'](x['beats']['boss.name'])])))
    ties = t['sp'].join(route(t, x, by_id, href.rsplit('/', 2)[0] + '/'))
    return f'''
        <li class="city-row">
          <div class="keepers">
            {pic(c, f'sky-{x["slug"]}', 'jpg', '', 720, 240, ' loading="lazy" decoding="async"').replace('<picture>', '<picture class="sky">', 1)}
            {keeper('elite')}
            {keeper('boss')}
          </div>
          <div>
            <span class="eyebrow">{t["city_eb"].format(n=x["n"], total=total)}</span>
            <h3 id="city-{x["id"]}"><a href="{href}">{esc(x["name"])}</a></h3>
            <p class="sub">{esc(x["atlas"]["landmarkTitle"])}</p>
            <blockquote class="mine"><p>&ldquo;{esc(x["atlas"]["postcard"])}&rdquo;</p></blockquote>
            <p>{esc(x["atlas"]["landmarkIdLine"])}{t["sp"]}{keepers}</p>
            <p>{ties}</p>
            <p><a href="{href}">{esc(t["city_more"].format(name=x["name"]))}</a></p>
          </div>
        </li>'''


def wish_more(c, t, lang):
    return '' if lang != 'en' else f'''
      <h3>{t["wish_h3"]}</h3>
      <ul class="city-links">{links(c, [(t["wish_link"], 'wish/')])}
      </ul>'''


def links(c, items):
    return ''.join(f'\n        <li><a href="{c}{h}">{esc(n)}</a></li>' for n, h in items)


def country_page(code, cs, atlas, conts, by_id, lang):
    t, p = T[lang], prefix(lang)
    k, x0 = atlas['countries'][code], cs[0]
    c, rel, cont = '../../../' + '../' * (lang != 'en'), x0['country_path'], x0['cont']
    secs = extra('countries', code, lang)
    # The postcard and landmark line appear on no other page, so they count; the route repeats the city page's
    own = [s for x in cs for s in (x['atlas']['postcard'], x['atlas']['landmarkIdLine'])]
    n_words = words(lang, k['intro'], k['idLine'], *k['facts'], *own, *(h for h, _ in secs), *(p for _, ps in secs for p in ps))
    index = n_words >= MIN_WORDS[lang]
    title = t['country_title'].format(name=k['name'])
    desc = t['country_desc'].format(cities=t['join']([x['name'] for x in cs]), country=t['country_in'](code, k['name']))
    trail = [(t['home'], p), (t['continents'][cont], f'{p}world/{cont}/'), (k['name'], p + rel)]
    facts = ''.join(f'\n        <li>{esc(f)}</li>' for f in k['facts'])
    rows = ''.join(city_row(x, c, t, f'{c}{p}cities/{x["id"]}/', by_id, len(by_id)) for x in cs)
    near = [(n, p + h) for n, h in conts[cont] if h != rel]
    more = (f'''
      <h3>{t["more_of"].format(cont=t["continents"][cont])}</h3>
      <ul class="city-links">{links(c, near)}
      </ul>''' if near else '')
    outline = pic(c, f'country-{code.lower()}-320', 'png', t['outline_alt'].format(country=t['country_in'](code, k['name'])), 320, 320)
    top, switch = head(c, t, lang, title, desc, rel, og(x0["slug"], lang), index,
                       page_ld(lang, rel, title, desc, trail, {'@type': 'Country', 'name': k['name']}))
    page = top + f'''
<main id="main">
{crumbs_html(c, t, trail, switch)}  <section class="section country-head" aria-labelledby="country-title">
    <div class="wrap">
      <div>
        <span class="eyebrow">{t["continents"][cont]}</span>
        <h1 id="country-title">{esc(k["name"])}</h1>
        <p class="lede">{esc(k["intro"])}</p>
        <p class="mine-line">&ldquo;{esc(k["idLine"])}&rdquo;</p>
        <ul class="journal">{facts}
        </ul>
      </div>
      {outline}
    </div>
  </section>

{extra_html(secs, "about")}  <section class="section alt" aria-labelledby="cities-title">
    <div class="wrap">
      <span class="eyebrow">{t["in_game"](len(cs))}</span>
      <h2 id="cities-title">{esc(t["fly_over"].format(country=t["country_in"](code, k["name"])))}</h2>
      <ul class="city-rows">{rows}
      </ul>
      <ul class="badges more">
        <li>{play(c, lang, "country", code.lower())}</li>
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">{t["the_world"]}</span>
      <h2 id="more-title">{t["fly_on"]}</h2>{more}
      <h3>{t["every_cont"]}</h3>
      <ul class="city-links">{links(c, [(t["continents"][k2], f'{p}world/{k2}/') for k2 in conts])}
      </ul>{wish_more(c, t, lang)}
    </div>
  </section>
</main>

''' + foot(c, t, lang)
    return p + rel, page, n_words, index


def later_html(t, cont, later):
    """The planned cities of one continent as plain chips: named on the map, no page of their own yet."""
    xs = [n for k, n in later if k == cont]
    return (f'''
      <h3>{t["planned_h3"].format(cont=t["continents"][cont])}</h3>
      <ul class="city-links later">{''.join(f'<li><span>{esc(n)}</span></li>' for n in xs)}
      </ul>''' if xs else '')


def continent_page(cont, cs, conts, total, later, lang):
    t, p = T[lang], prefix(lang)
    c, rel = '../../' + '../' * (lang != 'en'), f'world/{cont}/'
    name = t['continents'][cont]
    title = t['cont_title'].format(cont=name)
    countries = sorted({x['country'] for x in cs})
    desc = t['cont_desc'].format(n=len(cs), total=total, cont=name, countries=t['n_countries'](len(countries)),
                                 cities=t['join']([x['name'] for x in cs]))
    trail = [(t['home'], p), (name, p + rel)]
    cards = ''.join(city_card(x, c, t, f'{c}{p}cities/{x["id"]}/') for x in cs)
    top, switch = head(c, t, lang, title, desc, rel, og(cs[0]["slug"], lang), True,
                       page_ld(lang, rel, title, desc, trail, {'@type': 'Continent', 'name': name}))
    page = top + f'''
<main id="main">
{crumbs_html(c, t, trail, switch)}  <section class="section" aria-labelledby="cont-title">
    <div class="wrap">
      <span class="eyebrow">{t["n_cities"](len(cs))} &middot; {t["n_countries"](len(countries))}</span>
      <h1 id="cont-title">{name}</h1>
      <p class="lede">{esc(desc)}</p>
      <ul class="city-links">{links(c, [(n, p + h) for n, h in conts[cont]])}
      </ul>
      <ul class="keeper-grid">{cards}
      </ul>
    </div>
  </section>

  <section class="section alt" aria-labelledby="more-title">
    <div class="wrap">
      <span class="eyebrow">{t["the_world"]}</span>
      <h2 id="more-title">{t["fly_on"]}</h2>{later_html(t, cont, later)}
      <h3>{t["every_cont"]}</h3>
      <ul class="city-links">{links(c, [(t["continents"][k], f'{p}world/{k}/') for k in conts if k != cont])}
      </ul>{wish_more(c, t, lang)}
    </div>
  </section>
</main>

''' + foot(c, t, lang)
    return p + rel, page


def world_page(by_cont, conts, cities, later, lang):
    t, p = T[lang], prefix(lang)
    c, rel = '../' + '../' * (lang != 'en'), 'world/'
    title = t['world_title']
    desc = t['world_desc'].format(total=len(cities), first=cities[0]['name'], last=cities[-1]['name'])
    trail = [(t['home'], p), (t['world'], p + rel)]
    blocks = ''.join(f'''
      <h2><a href="{c}{p}world/{k}/">{t["continents"][k]}</a></h2>
      <ul class="city-links">{links(c, [(t['place'](x['name'], x['country']), f'{p}cities/{x["id"]}/') for x in by_cont[k]])}
      </ul>{later_html(t, k, later)}''' for k in conts)
    top, switch = head(c, t, lang, title, desc, rel, 'brand/og-image-1200x630.jpg', True,
                       page_ld(lang, rel, title, desc, trail))
    page = top + f'''
<main id="main">
{crumbs_html(c, t, trail, switch)}  <section class="section world" aria-labelledby="world-title">
    <div class="wrap">
      <span class="eyebrow">{t["n_cities"](len(cities))}</span>
      <h1 id="world-title">{t["hub_h1"]}</h1>
      <p class="lede">{esc(desc)}</p>{blocks}{wish_more(c, t, lang)}
    </div>
  </section>
</main>

''' + foot(c, t, lang)
    return p + rel, page


def planned():
    """The cities the game plans but no build carries yet, in campaign order: the ones a vote can still move."""
    return kg("SELECT l.id, l.label AS name, json_extract(l.props,'$.continent') AS cont, c.label AS country "
              "FROM nodes l LEFT JOIN nodes c ON c.key = 'country:' || json_extract(l.props,'$.country') "
              "WHERE l.kind='level' AND json_extract(l.props,'$.era')='present' "
              "AND coalesce(json_extract(l.props,'$.pack'), '') = '' ORDER BY l.ord")


def wish_row(x, t):
    n = f'n-{x["id"]}'
    return (f'\n        <li data-city="{x["id"]}" data-name="{esc(x["name"])}">'
            f'<span class="wish-name">{esc(t["place"](x["name"], x["country"]) if x["country"] else x["name"])}</span> '
            f'<span class="wish-count" id="{n}" data-count></span> '
            f'<button type="button" aria-label="I want {esc(x["name"])}" aria-describedby="{n}" hidden>I want it</button></li>')


def wish_page(wishes):
    """English only, noindex and in no sitemap: the planned cities, each with a vote button that vote.js reveals."""
    t, c, rel = T['en'], '../', 'wish/'
    js = open(os.path.join(SITE, 'tools', 'vote.js'), encoding='utf-8').read().strip()
    sha = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    csp = f"script-src 'sha256-{sha}' {TURNSTILE}; frame-src {TURNSTILE}; connect-src {VOTE_API.rsplit('/v1', 1)[0]}"
    title, desc = t['wish_title'], t['wish_desc'].format(n=len(wishes), first=wishes[0]['name'], last=wishes[-1]['name'])
    trail = [(t['home'], ''), (t['world'], 'world/'), (t['wish_link'], rel)]
    blocks = ''.join(f'''
      <h2>{t["continents"][k]}</h2>
      <ul class="wish-list">{"".join(wish_row(x, t) for x in wishes if x["cont"] == k)}
      </ul>''' for k in t['continents'] if any(x['cont'] == k for x in wishes))
    top, switch = head(c, t, 'en', title, desc, rel, 'brand/og-image-1200x630.jpg', False,
                       page_ld('en', rel, title, desc, trail), langs=['en'], csp=csp)
    page = top + f'''
<main id="main">
{crumbs_html(c, t, trail, switch)}  <section class="section world" aria-labelledby="wish-title">
    <div class="wrap" data-vote-api="{VOTE_API}" data-vote-key="{TURNSTILE_KEY}">
      <span class="eyebrow">{t["wish_eb"](len(wishes))}</span>
      <h1 id="wish-title">{t["wish_h1"]}</h1>
      <p class="lede">{t["wish_lede"]}</p>
      <noscript><p>{t["wish_nojs"]}</p></noscript>{blocks}
    </div>
  </section>
  <div class="vote-bar"><p role="status" data-vote-status></p><div data-vote-check></div></div>
</main>
<script>{js}</script>
<script src="{TURNSTILE}/turnstile/v0/api.js?render=explicit&amp;onload=psVoteCheck" async defer></script>

''' + foot(c, t, 'en')
    return rel, page


def write(path, page):
    os.makedirs(os.path.join(SITE, path), exist_ok=True)
    open(os.path.join(SITE, path, 'index.html'), 'w', encoding='utf-8').write(page)


def sitemap(name, urls):
    rows = ''.join(f'  <url><loc>{ORIGIN}/{u}</loc></url>\n' for u in urls)
    open(os.path.join(SITE, name), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{rows}</urlset>\n')


def build(cities, atlas, lang, planned_rows):
    """Writes one language's pages; returns the indexable city and country paths."""
    p = prefix(lang)
    ui = json.load(open(os.path.join(PACKS, lang, f'{lang}.json'), encoding='utf-8')) if lang != 'en' else {}
    later = [(r['cont'], ui.get(f'city.{r["id"]}.name', r['name'])) for r in planned_rows]
    by_id = {x['id']: x for x in cities}
    city_urls, world_urls = [], []
    for x in cities:
        page, n, index = city_page(x, by_id, len(cities), lang)
        write(f'{p}cities/{x["id"]}/', page)
        print(f'{lang:8} {x["id"]:16} {n:4} words  {"index" if index else "noindex"}')
        if index:
            city_urls.append(f'{p}cities/{x["id"]}/')
    write(f'{p}cities/', hub(cities, lang))
    if lang != 'en':
        write(p, home(cities, lang))

    by_cont, by_code = {}, {}
    for x in cities:
        by_cont.setdefault(x['cont'], []).append(x)
        by_code.setdefault(x['code'], []).append(x)
    order = [k for k in T['en']['continents'] if k in by_cont]
    conts = {k: sorted({(x['country'], x['country_path']) for x in by_cont[k]}) for k in order}
    for code, cs in by_code.items():
        path, page, n, index = country_page(code, cs, atlas, conts, by_id, lang)
        write(path, page)
        print(f'{lang:8} {path:44} {n:4} words  {"index" if index else "noindex"}')
        if index:
            world_urls.append(path)
    for k in order:
        path, page = continent_page(k, by_cont[k], conts, len(cities), later, lang)
        write(path, page)
        world_urls.append(path)
    path, page = world_page(by_cont, order, cities, later, lang)
    write(path, page)
    world_urls.insert(0, path)
    return city_urls, world_urls


NUMS = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
        'seventeen eighteen nineteen').split() + [f'{t}{"-" + u if u else ""}' for t in ('twenty', 'thirty', 'forty', 'fifty')
                                                   for u in [''] + 'one two three four five six seven eight nine'.split()]


def stamp(cities):
    """Keeps the hand-written pages current: the Discord invite everywhere, the city count on index and support."""
    num = '|'.join(sorted(NUMS, key=len, reverse=True))
    n = len(cities)
    for f in sorted(os.listdir(SITE)):
        if not f.endswith('.html'):
            continue
        path = os.path.join(SITE, f)
        s = open(path, encoding='utf-8').read()
        new = re.sub(r'https://discord\.gg/[A-Za-z0-9]+', DISCORD, s)
        if f == 'index.html':
            new = re.sub(rf'\b({num})(?= (painted )?cities)', NUMS[n], new)
            new = re.sub(rf'\b({num}) cities, ({num}) keepers', f'{NUMS[n].capitalize()} cities, {NUMS[2 * n]} keepers', new, flags=re.I)
        if f == 'support.html':
            listed = T['en']['join']([x['name'] for x in cities])
            new = re.sub(r'(<summary>Which cities can I fly\?</summary>\s*<p>)[^<]*(</p>)', rf'\g<1>{NUMS[n].capitalize()}: {listed}.\2', new)
        if new != s:
            open(path, 'w', encoding='utf-8').write(new)
            print(f'stamped  {f}')


STATS = 'https://paperskyline-stats.paperskyline-stats.workers.dev'
PAGE_DIRS = ['cities', 'world', 'devlog', 'wish', 'zh-Hans', 'id']


def csp_for(page):
    """script-src lists exactly the page's inline scripts plus any origins it already allowed; connect-src self and the Worker."""
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">\n', page)
    dirs = dict(d.strip().split(' ', 1) for d in m.group(1).split(';')) if m else {}
    hashes = [f"'sha256-{base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()}'"
              for s in re.findall(r'<script>(.*?)</script>', page, re.S)]
    dirs['script-src'] = ' '.join(hashes + [x for x in dirs.get('script-src', '').split() if not x.startswith("'sha256-")])
    dirs['connect-src'] = ' '.join(["'self'"] + [x for x in dirs.pop('connect-src', STATS).split() if x != "'self'"])
    meta = f'<meta http-equiv="Content-Security-Policy" content="{"; ".join(f"{k} {v}" for k, v in dirs.items())}">\n'
    if m:
        return page.replace(m.group(0), meta)
    return page.replace('<meta name="viewport" content="width=device-width, initial-scale=1">\n',
                        '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + meta, 1)


def stamp_geo():
    """Every page carries tools/geo.js (the not-available banner) before </body>, and a CSP that allows its scripts."""
    js = open(os.path.join(SITE, 'tools', 'geo.js'), encoding='utf-8').read().strip()
    files = [f for f in os.listdir(SITE) if f.endswith('.html')]
    for d in PAGE_DIRS:
        files += [os.path.relpath(os.path.join(r, f), SITE) for r, _, fs in os.walk(os.path.join(SITE, d)) for f in fs if f.endswith('.html')]
    for f in sorted(files):
        path = os.path.join(SITE, f)
        s = open(path, encoding='utf-8').read()
        new = re.sub(r'<script>\(function \(\) \{\n  var main = document\.getElementById[^<]*</script>\n', '', s)
        new = csp_for(new.replace('</body>', f'<script>{js}</script>\n</body>', 1))
        if new != s:
            open(path, 'w', encoding='utf-8').write(new)


def main():
    cities, atlas = load()
    stamp(cities)
    rows = planned()
    for lang in LANGS:
        city_urls, world_urls = build(*localize(cities, atlas, lang), lang, rows)
        if lang == 'en':
            sitemap('sitemap-cities.xml', city_urls)
            sitemap('sitemap-world.xml', world_urls)
        else:
            sitemap(f'sitemap-{lang.lower()}.xml', [prefix(lang)] + city_urls + world_urls)
    write(*wish_page(rows))
    stamp_geo()


if __name__ == '__main__':
    main()
