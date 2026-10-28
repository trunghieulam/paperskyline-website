#!/usr/bin/env python3
"""Stamps <lastmod> on every sitemap row: the day the page's <main> text last changed in git, or today if it has
changed since HEAD. Nav, footer and CSP restamps don't count, so Google can keep trusting the dates.
Usage: tools/lastmod.py [--check]   (cities.py and news.py run it after writing their sitemaps)
"""
import datetime
import html
import os
import re
import subprocess
import sys

SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ORIGIN = 'https://paperskyline.org'


def sitemaps():
    index = open(os.path.join(SITE, 'sitemap.xml'), encoding='utf-8').read()
    return re.findall(rf'<loc>{ORIGIN}/(sitemap-[a-z-]+\.xml)</loc>', index)


def page_file(loc):
    p = loc.removeprefix(ORIGIN + '/')
    return p + 'index.html' if p == '' or p.endswith('/') else p


def text(s):
    m = re.search(r'<main[^>]*>(.*)</main>', s, re.S)
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1) if m else s)).split())


def git(*args):
    return subprocess.run(['git', *args], cwd=SITE, capture_output=True, text=True, check=True).stdout


def dates(files):
    """file -> the day its <main> text last changed."""
    history = {f: [] for f in files}
    for block in git('log', '--format=%x00%H %cs', '--name-only', '--', *files).split('\0')[1:]:
        head, *names = block.strip().split('\n')
        sha, day = head.split()
        for f in names:
            if f in history:
                history[f].append((sha, day))
    cat = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=SITE, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def blob(sha, f):
        cat.stdin.write(f'{sha}:{f}\n'.encode())
        cat.stdin.flush()
        meta = cat.stdout.readline().split()
        if meta[-1] == b'missing':
            return ''
        data = cat.stdout.read(int(meta[2]))
        cat.stdout.read(1)
        return text(data.decode('utf-8'))

    today, out = datetime.date.today().isoformat(), {}
    for f in files:
        now = text(open(os.path.join(SITE, f), encoding='utf-8').read())
        commits = history[f]
        if not commits or blob(commits[0][0], f) != now:
            out[f] = today
            continue
        out[f] = commits[-1][1]
        for (_, day), (older, _) in zip(commits, commits[1:]):
            if blob(older, f) != now:
                out[f] = day
                break
    cat.stdin.close()
    cat.wait()
    return out


def rows(sm):
    return re.findall(r'<url>.*?</url>', open(os.path.join(SITE, sm), encoding='utf-8').read(), re.S)


def run(check=False):
    """Rewrites the sitemaps' lastmod, or with check=True only reports stale ones; returns 1 if any were stale."""
    maps = {sm: rows(sm) for sm in sitemaps()}
    files = sorted({page_file(re.search(r'<loc>([^<]+)', r).group(1)) for rs in maps.values() for r in rs})
    want = dates(files)
    bad = 0
    for sm, rs in maps.items():
        s = open(os.path.join(SITE, sm), encoding='utf-8').read()
        for r in rs:
            day = want[page_file(re.search(r'<loc>([^<]+)', r).group(1))]
            have = re.search(r'<lastmod>([^<]*)</lastmod>', r)
            if have and have.group(1) == day:
                continue
            if check:
                print(f'FAIL {sm}: {re.search(r"<loc>([^<]+)", r).group(1)} lastmod {have.group(1) if have else "missing"}, '
                      f'its text last changed {day} (run tools/lastmod.py)')
                bad = 1
                continue
            new = (r.replace(have.group(0), f'<lastmod>{day}</lastmod>') if have
                   else r.replace('</loc>', f'</loc><lastmod>{day}</lastmod>', 1))
            s = s.replace(r, new, 1)
        if not check:
            open(os.path.join(SITE, sm), 'w', encoding='utf-8').write(s)
    return bad


if __name__ == '__main__':
    sys.exit(run('--check' in sys.argv))
