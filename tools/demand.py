#!/usr/bin/env python3
"""Monthly city demand from a Search Console Performance export (#95): per-city impressions and planned-city signals.
Usage: tools/demand.py <export .zip or folder> [--game path] [--month YYYY-MM]
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import unicodedata
import zipfile

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HISTORY = os.path.join(SITE, 'tools', '.tmp', 'demand')
LANGS = ['zh-Hans', 'id']
# A planned city is a signal at this many impressions in the export's 28 days, or in the top TOP two months running.
MIN_IMPRESSIONS = 100
TOP = 5
CJK = re.compile(r'[㐀-鿿豈-﫿]')


def norm(s):
    s = ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))
    return re.sub(r'[\s\-_.,/\'’]+', ' ', s.casefold()).strip()


def cities_from_graph(game):
    """Every present-era city with its names; shipped means on the site (art.CITIES), the rest are planned."""
    sys.path.insert(0, os.path.dirname(__file__))
    import cities as site
    from art import CITIES, IDS
    site.GAME = game
    shipped = {IDS.get(slug, slug) for slug, _, _ in CITIES}
    packs = {l: json.load(open(os.path.join(game, 'Assets/Content/Locale/packs', l, f'{l}.json'), encoding='utf-8')) for l in LANGS}
    rows = site.kg("SELECT id, label, json_extract(props,'$.country') AS country FROM nodes "
                   "WHERE kind='level' AND json_extract(props,'$.era')='present'")
    return [dict(id=r['id'], name=r['label'], country=r['country'], shipped=r['id'] in shipped,
                 names=[r['label']] + [p[k] for p in packs.values() if (k := f'city.{r["id"]}.name') in p])
            for r in rows]


def matcher(cities):
    """A query -> city ids function; the longest name wins, so "new york" never also counts York."""
    pats = sorted({(norm(n), c['id']) for c in cities for n in c['names'] if norm(n)}, key=lambda p: -len(p[0]))
    rx = [(re.compile(re.escape(n) if CJK.search(n) else rf'(?<!\w){re.escape(n)}(?!\w)'), cid) for n, cid in pats]

    def match(q):
        q, taken, hits = norm(q), [], set()
        for r, cid in rx:
            for m in r.finditer(q):
                if not any(m.start() < e and s < m.end() for s, e in taken):
                    taken.append(m.span())
                    hits.add(cid)
        return hits
    return match


def read_export(path):
    """{table name: rows} from the export zip or its unzipped folder; numbers parsed, BOM tolerated."""
    if os.path.isdir(path):
        files = {}
        for f in os.listdir(path):
            if f.endswith('.csv'):
                with open(os.path.join(path, f), encoding='utf-8-sig') as fh:
                    files[f] = fh.read()
    else:
        with zipfile.ZipFile(path) as z:
            files = {os.path.basename(f): z.read(f).decode('utf-8-sig') for f in z.namelist() if f.endswith('.csv')}
    num = lambda v: float(v.replace(',', '').rstrip('%') or 0)
    out = {}
    for f, text in files.items():
        rows = list(csv.DictReader(io.StringIO(text)))
        for r in rows:
            for k in ('Clicks', 'Impressions', 'CTR', 'Position'):
                if k in r:
                    r[k] = num(r[k])
        out[f.removesuffix('.csv')] = rows
    for need in ('Queries', 'Pages'):
        if need not in out:
            sys.exit(f'demand.py: {path} has no {need}.csv; export Performance > Search results with Queries and Pages')
    return out


def tally(export, cities):
    match, by = matcher(cities), {c['id']: dict(c, q_impr=0, q_clicks=0, pos_w=0.0, p_impr=0, queries=[]) for c in cities}
    unmatched = []
    for r in export['Queries']:
        hits = match(r['Top queries'])
        if not hits:
            unmatched.append(r)
        for cid in hits:
            c = by[cid]
            c['q_impr'] += r['Impressions']; c['q_clicks'] += r['Clicks']; c['pos_w'] += r['Position'] * r['Impressions']
            c['queries'].append(r['Top queries'])
    for r in export['Pages']:
        m = re.match(r'https?://[^/]+/(?:(?:zh-Hans|id)/)?cities/([a-z0-9-]+)/', r['Top pages'])
        if m and m.group(1) in by:
            by[m.group(1)]['p_impr'] += r['Impressions']
    for c in by.values():
        c['impr'] = max(c['q_impr'], c['p_impr'])
        c['pos'] = c['pos_w'] / c['q_impr'] if c['q_impr'] else None
    return sorted(by.values(), key=lambda c: (-c['impr'], c['name'])), unmatched


def month_of(export, given):
    if given:
        return given
    dates = [r['Date'] for r in export.get('Dates', []) if r.get('Date')]
    return max(dates)[:7] if dates else datetime.date.today().strftime('%Y-%m')


def previous(month):
    y, m = map(int, month.split('-'))
    return f'{y - (m == 1)}-{(m - 2) % 12 + 1:02d}'


def signals(rows, month, history=HISTORY):
    """Planned cities passing the rule, with the reason; saves this month's planned top for next month."""
    planned = [c for c in rows if not c['shipped'] and c['impr'] > 0]
    top = [c['id'] for c in planned[:TOP]]
    try:
        with open(os.path.join(history, f'{previous(month)}.json'), encoding='utf-8') as f:
            before = json.load(f)['top']
    except FileNotFoundError:
        before = None
    os.makedirs(history, exist_ok=True)
    with open(os.path.join(history, f'{month}.json'), 'w', encoding='utf-8') as f:
        json.dump({'month': month, 'top': top, 'impressions': {c['id']: c['impr'] for c in planned}}, f, indent=1)
    out = []
    for c in planned:
        why = [f'{c["impr"]:.0f} impressions'] if c['impr'] >= MIN_IMPRESSIONS else []
        if before is not None and c['id'] in top and c['id'] in before:
            why.append(f'top {TOP} in {previous(month)} and {month}')
        if why:
            out.append((c, why))
    return out, before is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('export')
    ap.add_argument('--game', default=os.path.join(SITE, '..', 'game-paper-flights'))
    ap.add_argument('--month', help='YYYY-MM the export covers (default: its last date, else this month)')
    a = ap.parse_args()
    export = read_export(a.export)
    rows, unmatched = tally(export, cities_from_graph(os.path.abspath(a.game)))
    month = month_of(export, a.month)
    print(f'# City demand, {month} (Search Console, {sum(r["Impressions"] for r in export["Queries"]):.0f} query impressions)')
    print(f'{"city":22} {"status":8} {"impr":>6} {"query":>6} {"page":>6} {"clicks":>6} {"pos":>5}')
    for c in rows:
        if c['impr']:
            pos = f'{c["pos"]:.1f}' if c['pos'] is not None else '-'
            print(f'{c["name"][:22]:22} {"shipped" if c["shipped"] else "planned":8} {c["impr"]:6.0f} {c["q_impr"]:6.0f} '
                  f'{c["p_impr"]:6.0f} {c["q_clicks"]:6.0f} {pos:>5}')
    found, had_history = signals(rows, month)
    print(f'\n## Planned-city signals ({MIN_IMPRESSIONS}+ impressions, or top {TOP} two months running'
          f'{"" if had_history else "; no previous month saved yet"})')
    print('\n'.join(f'- {c["name"]} ({c["country"]}): {", ".join(why)}' for c, why in found) or '- none')
    print('\n## Top queries naming no known city')
    print('\n'.join(f'- {r["Top queries"]}: {r["Impressions"]:.0f}' for r in sorted(unmatched, key=lambda r: -r['Impressions'])[:15]) or '- none')
    if export.get('Countries'):
        print('\n## Top searcher countries')
        print('\n'.join(f'- {r["Country"]}: {r["Impressions"]:.0f}' for r in sorted(export['Countries'], key=lambda r: -r['Impressions'])[:10]))


if __name__ == '__main__':
    main()
