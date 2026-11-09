#!/usr/bin/env python3
"""Tells Bing and the other IndexNow engines which pages changed. Run only after the push to main is live.
Usage: tools/indexnow.py [--since REV] [URL or /path …] [--send]   (without --send it prints what it would send)
URLs given first lead the list; --since adds every sitemap page whose file changed between REV and HEAD.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORIGIN = 'https://paperskyline.org'
ENDPOINT = 'https://api.indexnow.org/indexnow'
UA = {'User-Agent': 'paperskyline-indexnow'}


def key():
    keys = [os.path.basename(f)[:-4] for f in glob.glob(os.path.join(SITE, '*.txt'))
            if re.fullmatch(r'[0-9a-f]{32}\.txt', os.path.basename(f))]
    if len(keys) != 1:
        sys.exit(f'expected one <32 hex>.txt key file at the site root, found {len(keys)}')
    k = keys[0]
    if open(os.path.join(SITE, k + '.txt'), encoding='utf-8').read().strip() != k:
        sys.exit(f'{k}.txt does not hold its own key')
    return k


def sitemap_urls():
    urls = set()
    for sm in glob.glob(os.path.join(SITE, 'sitemap-*.xml')):
        urls.update(re.findall(r'<loc>([^<]+)</loc>', open(sm, encoding='utf-8').read()))
    return urls


def url_for(path):
    path = path.removeprefix('./')
    if path == 'index.html':
        return ORIGIN + '/'
    return ORIGIN + '/' + (path[:-len('index.html')] if path.endswith('/index.html') else path)


def changed_since(rev):
    out = subprocess.run(['git', '-C', SITE, 'diff', '--name-only', f'{rev}..HEAD'], capture_output=True, text=True, check=True).stdout
    return [url_for(f) for f in out.split() if f.endswith('.html')]


def live(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA, method='HEAD'), timeout=20) as r:
            return r.status == 200
    except urllib.error.URLError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--since')
    ap.add_argument('--send', action='store_true')
    a = ap.parse_args()
    k, indexable = key(), sitemap_urls()
    wanted = [u if u.startswith('http') else ORIGIN + '/' + u.lstrip('/') for u in a.urls]
    wanted += changed_since(a.since) if a.since else []
    urls, skipped = [], []
    for u in dict.fromkeys(wanted):
        (urls if u in indexable else skipped).append(u)
    for u in skipped:
        print(f'skip (not in a sitemap): {u}')
    if not urls:
        sys.exit('no URLs to send')
    body = {'host': 'paperskyline.org', 'key': k, 'keyLocation': f'{ORIGIN}/{k}.txt', 'urlList': urls[:10000]}
    print(json.dumps(body, indent=1))
    if not a.send:
        print('dry run: add --send to submit')
        return
    # IndexNow fetches the key from the live site, and pinging a page that 404s wastes the crawl.
    down = [u for u in [body['keyLocation']] + urls if not live(u)]
    if down:
        sys.exit('not live yet, nothing sent:\n  ' + '\n  '.join(down))
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method='POST',
                                 headers={**UA, 'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f'IndexNow: HTTP {r.status} for {len(urls)} URLs')
    except urllib.error.HTTPError as e:
        sys.exit(f'IndexNow: HTTP {e.code} {e.read().decode(errors="replace")[:300]}')


if __name__ == '__main__':
    main()
