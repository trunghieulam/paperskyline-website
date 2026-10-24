#!/usr/bin/env python3
"""Exports the site's images from the game's shipped art. Reads the game repo, writes img/ and brand/.
Usage: tools/art.py [path to game-paper-flights]   (default: ../game-paper-flights next to this repo)
Opaque paintings fall back to JPEG, cut-out keepers to PNG; AVIF and WebP carry the weight.
"""
import hashlib
import json
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, '..', 'game-paper-flights'))
IMG = os.path.join(SITE, 'img')
NAVY = (29, 31, 79)

# (slug, (elite kit, module), (boss kit, module)): the shipped cities' keepers in campaign order, idle state
CITIES = [
    ('paris', ('paris-elite', 'paris_horse_state1'), ('paris-boss-stryge', 'paris_stryge_state1')),
    ('new-york', ('new-york-elite', 'nyc_taxi_state1'), ('new-york-boss', 'nyc_boss_state1')),
    ('tokyo', ('tokyo-elite', 'tokyo_neko_state1'), ('tokyo-boss', 'tokyo_kabuki_state1')),
    ('cairo', ('cairo-elite', 'cairo_camel_state1'), ('cairo-boss', 'cairo_sphinx_state1')),
    ('rio', ('rio-elite', 'rio_cablecar_state1'), ('rio-boss-v2', 'rio_dancer_state1')),
    ('london', ('london-elite-raven', 'london_raven_state1'), ('london-boss-giant', 'london_giant_state1')),
    ('sydney', ('sydney-elite-cockatoo', 'sydney_cockatoo_state1'), ('sydney-boss-lyrebird', 'sydney_lyrebird_state1')),
    ('beijing', ('beijing-elite-lion', 'beijing_lion_state1'), ('beijing-boss-xiezhi', 'beijing_xiezhi_state1')),
    ('rome', ('rome-elite-lion', 'rome_lion_state1'), ('rome-boss-gladiator', 'rome_gladiator_state1')),
    ('san-francisco', ('sf-elite-gripman', 'sf_gripman_state1'), ('sf-boss-grizzly', 'sf_grizzly_state1')),
    ('bangkok', ('bangkok-elite-fighting-fish', 'bangkok_fish_state1'),
     ('bangkok-boss-war-elephant', 'bangkok_elephant_state1')),
    ('istanbul', ('istanbul-elite-gull', 'istanbul_gull_state1'), ('istanbul-boss-karagoz', 'istanbul_karagoz_state1')),
    ('barcelona', ('barcelona-elite-gegant', 'barcelona_gegant_state1'),
     ('barcelona-boss-salamander', 'barcelona_salamander_state1')),
    ('hong-kong', ('hong-kong-elite-neon-master', 'hong_kong_neon_state1'),
     ('hong-kong-boss-pirate', 'hong_kong_pirate_state1')),
    ('toronto', ('toronto-elite-moose', 'toronto_moose_state1'), ('toronto-boss-raccoon', 'toronto_raccoon_state1')),
    ('ho-chi-minh-city', ('ho-chi-minh-city-elite-courier', 'hcmc_courier_state1'),
     ('ho-chi-minh-city-boss-cyclo', 'hcmc_cyclo_state1')),
    ('amsterdam', ('amsterdam-elite-heron', 'amsterdam_heron_state1'), ('amsterdam-boss-windmill', 'amsterdam_windmill_state1')),
    ('singapore', ('singapore-elite-hornbill', 'singapore_hornbill_state1'),
     ('singapore-boss-harbour-elder', 'singapore_harbour_elder_state1')),
    ('dubai', ('dubai-elite-oryx', 'dubai_oryx_state1'), ('dubai-boss-pearl-diver', 'dubai_pearl_diver_state1')),
    ('berlin', ('berlin-elite-bear-dj', 'berlin_bear_dj_state1'),
     ('berlin-boss-traffic-light-man', 'berlin_traffic_light_man_state1')),
    ('athens', ('athens-elite-bronze-griffin', 'athens_bronze_griffin_state1'),
     ('athens-boss-erechtheion-serpent', 'athens_erechtheion_serpent_state1')),
]
# Display names and city ids where the art slug is not the city's
NAMES = {'rio': 'Rio de Janeiro'}
IDS = {'rio': 'rio-de-janeiro'}
# The share cards' Chinese face: Noto Sans SC Black (OFL), fetched once into tools/.tmp and checked
CJK = ('https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/SubsetOTF/SC/NotoSansSC-Black.otf',
       'ccb496022356b7dd14d117538a472ae40feff8f6e8f3fe8bffc5616785d2f3f9')
STORE = 'docs/store/google-play/1.9.0/en-US'
# The V-D216 2.0 launch set: icons, the header mark and the plane-less wordmark
BRAND = 'design/art-source/branding-2-0/export'
# The 1.9.0 store frames carry a caption band above the game; content starts at y 192
STORE_CROP = (0, 192, 1920, 1080)


def game(*p):
    return os.path.join(GAME, *p)


def cjk_font():
    path = os.path.join(SITE, 'tools', '.tmp', os.path.basename(CJK[0]))
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(CJK[0], path)
    if hashlib.sha256(open(path, 'rb').read()).hexdigest() != CJK[1]:
        sys.exit(f'{path}: unexpected checksum; delete it and re-run')
    return path


def sprite(kit, mid):
    d = game('Assets/Art/Encounters', kit)
    m = {x['id']: x for x in json.load(open(os.path.join(d, 'modules.json')))['modules']}[mid]
    x, y, w, h = m['sheet_rect']
    return Image.open(os.path.join(d, kit + '.png')).convert('RGBA').crop((x, y, x + w, y + h))


def fit(im, w=None, h=None):
    """Resize in premultiplied alpha so the sheet's grey matte never halos onto the dark theme."""
    if w is None:
        w = round(im.width * h / im.height)
    if h is None:
        h = round(im.height * w / im.width)
    if im.mode == 'RGBA':
        return im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
    return im.resize((w, h), Image.LANCZOS)


def save(im, name, fallback):
    base = os.path.join(IMG, name)
    im.save(base + '.avif', quality=55, speed=4)
    im.save(base + '.webp', quality=78, method=6)
    if fallback == 'jpg':
        im.convert('RGB').save(base + '.jpg', quality=76, optimize=True, progressive=True)
    else:
        im.save(base + '.png', optimize=True)
    print(name, im.size, {e: os.path.getsize(base + '.' + e) for e in ('avif', 'webp', fallback)})


def painting(slug):
    folder = ''.join(w.capitalize() for w in slug.split('-'))
    return Image.open(game('Assets/Art/Cities', folder, slug + '-background.png')).convert('RGB')


def hero_src():
    return painting('paris')


def hero():
    src = hero_src()
    for w in (640, 1024, 1600):
        save(fit(src, w), f'hero-paris-{w}', 'jpg')


def keepers():
    for slug, elite, boss in CITIES:
        for role, (kit, mid) in (('elite', elite), ('boss', boss)):
            k = sprite(kit, mid)
            k = fit(k, h=280) if k.width * 280 <= k.height * 300 else fit(k, w=300)
            save(k, f'keeper-{slug}-{role}', 'png')


def skies():
    for slug, _, _ in CITIES:
        save(fit(painting(slug), 720), f'sky-{slug}', 'jpg')


# img/shot-paris-* (business.html) is a frozen 1.3 export; its source capture is gone
# The 1.9.0 Paper Pop set, caption band cropped, 1920:888
SHOTS = ['wish', 'workshop', 'keepers', 'daily', 'looks']


def shots():
    # The game moved its store captures to paper-skyline-local-media; without them keep the committed exports
    if not os.path.exists(game(STORE, f'01-{SHOTS[0]}-en-US.jpg')):
        return print(f'{STORE} absent: shot-* kept as committed')
    for slug in SHOTS:
        src = Image.open(game(STORE, f'0{SHOTS.index(slug) + 1}-{slug}-en-US.jpg')).convert('RGB').crop(STORE_CROP)
        for w in (800, 1600):
            save(fit(src, w), f'shot-{slug}-{w}', 'jpg')


# The press kit (#214): the six 1.9.6 App Store iPhone frames, the 2.0 residents, and full-size downloads in press/
PRESS_SHOTS = 'docs/store/app-store/screenshots/iphone'
RESIDENTS = ['emile', 'imani', 'hana']


def press():
    out = os.path.join(SITE, 'press')
    os.makedirs(out, exist_ok=True)
    for f in sorted(os.listdir(game(PRESS_SHOTS))):
        if not f.endswith('.png'):
            continue
        src = Image.open(game(PRESS_SHOTS, f)).convert('RGB')
        slug = f[3:-4]
        for w in (800, 1600):
            save(fit(src, w), f'press-{slug}-{w}', 'jpg')
        # Downloads sit outside img/ and its weight budget: press wants the full frame
        src.save(os.path.join(out, f'paper-skyline-{slug}.jpg'), quality=88, optimize=True, progressive=True)
    for n in RESIDENTS:
        save(fit(Image.open(game(f'design/art-source/{n}-portrait-rig/{n}-c-portrait.png')).convert('RGB'), 360),
             f'resident-{n}', 'jpg')
    for name in ('logo-stacked-full', 'logo-title-full'):
        Image.open(game(BRAND, name + '.png')).save(os.path.join(out, f'paper-skyline-{name[5:-5]}-logo.png'), optimize=True)


def og(src=None, title=None, ks=None, out='brand/og-image-1200x630.jpg', font=None):
    W, H = 1200, 630
    src = (src or hero_src()).convert('RGBA')
    s = max(W / src.width, H / src.height)
    bg = fit(src, round(src.width * s), round(src.height * s))
    card = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H))
    if title is None:
        card.alpha_composite(fit(Image.open(game(BRAND, 'title/wordmark.png')).convert('RGBA'), h=340), (28, 16))
    else:
        font = font or ImageFont.truetype(game('Assets/Fonts/Baloo2-ExtraBold.ttf'), 128)
        ImageDraw.Draw(card).text((52, 44), title, font=font, fill=NAVY + (180,),
                                  stroke_width=12, stroke_fill=NAVY + (180,))
        ImageDraw.Draw(card).text((44, 34), title, font=font, fill=NAVY + (255,),
                                  stroke_width=12, stroke_fill=(255, 255, 255, 255))
    ks = ks or [sprite(kit, mid) for _, _, (kit, mid) in CITIES[:4:3] + CITIES[1:2]]
    ks = [fit(k, h=230) if k.width * 230 <= k.height * 420 else fit(k, w=420) for k in ks]
    x = W - 36 - sum(k.width - 8 for k in ks)
    for k in ks:
        shadow = Image.new('RGBA', k.size, (0, 0, 0, 0))
        shadow.putalpha(k.getchannel('A').point(lambda a: a * 110 // 255))
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        y = H - 40 - k.height
        card.alpha_composite(shadow, (x + 3, y + 4))
        card.alpha_composite(k, (x, y))
        x += k.width - 8
    card.convert('RGB').save(os.path.join(SITE, out), quality=84, optimize=True, progressive=True)


def cities():
    """The city pages (tools/cities.py): each painting at hero sizes, and a share card with its keepers,
    plus one per language whose pack names the city differently."""
    packs = {lang: json.load(open(game('Assets/Content/Locale/packs', lang, f'{lang}.json'), encoding='utf-8'))
             for lang in ('zh-Hans', 'id')}
    fonts = {'zh-Hans': ImageFont.truetype(cjk_font(), 112)}
    for slug, elite, boss in CITIES:
        src = painting(slug)
        if slug != 'paris':
            for w in (640, 1024, 1600):
                save(fit(src, w), f'city-{slug}-{w}', 'jpg')
        name = NAMES.get(slug, slug.replace('-', ' ').title())
        ks = [sprite(*elite), sprite(*boss)]
        og(src, name, ks, f'img/og-{slug}.jpg')
        for lang, ui in packs.items():
            local = ui[f'city.{IDS.get(slug, slug)}.name']
            if local != name:
                og(src, local, ks, f'img/og-{slug}-{lang.lower()}.jpg', fonts.get(lang))


def countries():
    d = game('Assets/Resources/Atlas/Countries')
    for f in sorted(os.listdir(d)):
        if f.endswith('.png'):
            save(fit(Image.open(os.path.join(d, f)).convert('RGBA'), 320), f[:-4] + '-320', 'png')


def icons():
    src = Image.open(game(BRAND, 'icon/app-icon-1024.png')).convert('RGB')
    # JPEG: the painted icon is ~1.4 MB as PNG, and nothing here needs its (absent) alpha
    src.save(os.path.join(SITE, 'brand/app-icon-1024.jpg'), quality=85, optimize=True, progressive=True)
    for name, out in (('apple-touch-icon-180.png', 'apple-touch-icon.png'), ('favicon-32.png', 'favicon-32.png')):
        Image.open(game(BRAND, 'web', name)).save(os.path.join(SITE, out), optimize=True)
    with open(game(BRAND, 'web/favicon.ico'), 'rb') as f, open(os.path.join(SITE, 'favicon.ico'), 'wb') as o:
        o.write(f.read())
    save(Image.open(game(BRAND, 'web/header-mark-128.png')).convert('RGBA'), 'mark-128', 'png')
    word = Image.open(game(BRAND, 'title/wordmark.png')).convert('RGBA')
    for w in (480, 960):
        save(fit(word, w), f'wordmark-{w}', 'png')
        # The PNG is only the no-AVIF/WebP fallback; a 256-colour palette cuts it to a sixth
        fit(word, w).quantize(256, method=Image.Quantize.FASTOCTREE).save(os.path.join(IMG, f'wordmark-{w}.png'), optimize=True)


def main():
    os.makedirs(IMG, exist_ok=True)
    hero()
    keepers()
    skies()
    shots()
    press()
    og()
    cities()
    countries()
    icons()


if __name__ == '__main__':
    main()
