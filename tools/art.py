#!/usr/bin/env python3
"""Exports the site's images from the game's shipped art. Reads the game repo, writes img/ and brand/.
Usage: tools/art.py [path to game-paper-flights]   (default: ../game-paper-flights next to this repo)
Opaque paintings fall back to JPEG, cut-out keepers to PNG; AVIF and WebP carry the weight.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, '..', 'game-paper-flights'))
IMG = os.path.join(SITE, 'img')
INK = (42, 38, 34)

# (slug, background, preflight, (elite kit, module), (boss kit, module)) — keepers as compose.py ships them
CITIES = [
    ('paris', 'Paris/paris-background.png', 'paris',
     ('paris-elite', 'paris_horse_state1'), ('paris-boss-mime', 'paris_mime_state1')),
    ('new-york', 'NewYork/new-york-background.png', 'new-york',
     ('new-york-elite', 'nyc_taxi_state1'), ('new-york-boss', 'nyc_boss_state1')),
    ('tokyo', 'Tokyo/tokyo-background.png', 'tokyo',
     ('tokyo-elite', 'tokyo_neko_state1'), ('tokyo-boss', 'tokyo_kabuki_state1')),
    ('cairo', 'Cairo/cairo-background.png', 'cairo',
     ('cairo-elite', 'cairo_camel_state1'), ('cairo-boss', 'cairo_sphinx_state1')),
    ('rio', 'Rio/rio-background.png', 'rio-de-janeiro',
     ('rio-elite', 'rio_cablecar_state1'), ('rio-boss-v2', 'rio_dancer_state1')),
]


def game(*p):
    return os.path.join(GAME, *p)


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


def hero():
    src = Image.open(game('Assets/Resources/Preflight/paris.png')).convert('RGB')
    for w in (640, 1024, 1672):
        save(fit(src, w), f'hero-paris-{w}', 'jpg')


def cities():
    for slug, bg, _, elite, boss in CITIES:
        src = Image.open(game('Assets/Art/Cities', bg)).convert('RGB')
        # 3:2 window on the landmark (~60% across per the city standard), trimming the top of the sky
        top = src.height * 28 // 100
        h = src.height - top
        w = h * 3 // 2
        x = max(0, min(src.width - w, int(src.width * .6) - w // 2))
        save(fit(src.crop((x, top, x + w, src.height)), 480), f'city-{slug}', 'jpg')
        for role, (kit, mid) in (('elite', elite), ('boss', boss)):
            k = sprite(kit, mid)
            k = fit(k, h=280) if k.width * 280 <= k.height * 300 else fit(k, w=300)
            save(k, f'keeper-{slug}-{role}', 'png')


def og():
    W, H = 1200, 630
    src = Image.open(game('Assets/Resources/Preflight/paris.png')).convert('RGBA')
    s = max(W / src.width, H / src.height)
    bg = fit(src, round(src.width * s), round(src.height * s))
    card = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H))
    font = ImageFont.truetype(game('Assets/Fonts/Caveat-Bold.ttf'), 132)
    text = Image.new('RGBA', card.size, (0, 0, 0, 0))
    ImageDraw.Draw(text).text((48, 36), 'Paper Skyline', font=font, fill=(246, 239, 217, 255),
                              stroke_width=10, stroke_fill=(246, 239, 217, 255))
    glow = text.filter(ImageFilter.GaussianBlur(10))
    card.alpha_composite(glow)
    card.alpha_composite(text)
    ImageDraw.Draw(card).text((48, 36), 'Paper Skyline', font=font, fill=INK + (255,))
    x = 690
    for slug, *_, (kit, mid) in CITIES:
        k = fit(sprite(kit, mid), h=190)
        shadow = Image.new('RGBA', k.size, (0, 0, 0, 0))
        shadow.putalpha(k.getchannel('A').point(lambda a: a * 110 // 255))
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        y = H - 40 - k.height
        card.alpha_composite(shadow, (x + 3, y + 4))
        card.alpha_composite(k, (x, y))
        x += k.width - 8
    card.convert('RGB').save(os.path.join(SITE, 'brand/og-image-1200x630.jpg'), quality=84, optimize=True,
                             progressive=True)


def icons():
    src = Image.open(game('Assets/Branding/app-icon.png')).convert('RGB')
    src.save(os.path.join(SITE, 'brand/app-icon-1024.png'), optimize=True)
    fit(src, 180).save(os.path.join(SITE, 'apple-touch-icon.png'), optimize=True)


def main():
    os.makedirs(IMG, exist_ok=True)
    hero()
    cities()
    og()
    icons()


if __name__ == '__main__':
    main()
