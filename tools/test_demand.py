#!/usr/bin/env python3
"""tools/demand.py on a sample Performance export with Search Console's real CSV headers. Run: python3 tools/test_demand.py"""
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(__file__))
import demand

CITIES = [
    dict(id='new-york', name='New York', country='US', shipped=True, names=['New York', '纽约', 'New York']),
    dict(id='york', name='York', country='GB', shipped=False, names=['York', '约克', 'York']),
    dict(id='sao-paulo', name='São Paulo', country='BR', shipped=False, names=['São Paulo', '圣保罗', 'São Paulo']),
    dict(id='lisbon', name='Lisbon', country='PT', shipped=False, names=['Lisbon', '里斯本', 'Lisboa']),
    dict(id='tokyo', name='Tokyo', country='JP', shipped=True, names=['Tokyo', '东京', 'Tokyo']),
]
EXPORT = {
    'Queries.csv': '﻿Top queries,Clicks,Impressions,CTR,Position\n'
                   'new york paper plane game,3,40,7.5%,6.2\n'
                   'paper plane over york,0,12,0%,18\n'
                   'sao paulo plane game,1,90,1.11%,9\n'
                   '纸飞机 圣保罗,0,20,0%,11\n'
                   'lisboa avião de papel,2,130,1.54%,4.5\n'
                   'paper plane upgrade game,5,300,1.67%,8\n',
    'Pages.csv': 'Top pages,Clicks,Impressions,CTR,Position\n'
                 'https://paperskyline.org/cities/tokyo/,4,70,5.71%,7\n'
                 'https://paperskyline.org/zh-Hans/cities/tokyo/,1,15,6.67%,5\n'
                 'https://paperskyline.org/world/asia/japan/,0,9,0%,21\n',
    'Countries.csv': 'Country,Clicks,Impressions,CTR,Position\nBrazil,1,110,0.91%,9\nPortugal,2,130,1.54%,4.5\n',
    'Dates.csv': 'Date,Clicks,Impressions,CTR,Position\n2026-11-01,1,20,5%,8\n2026-11-28,2,30,6.67%,7\n',
    'Filters.csv': 'Filter,Value\nSearch type,Web\nDate,Last 28 days\n',
}


class Demand(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.zip = os.path.join(self.tmp, 'paperskyline.org-Performance-on-Search-2026-11-29.zip')
        with zipfile.ZipFile(self.zip, 'w') as z:
            for f, text in EXPORT.items():
                z.writestr(f, text)
        self.export = demand.read_export(self.zip)
        self.rows, self.unmatched = demand.tally(self.export, CITIES)
        self.by = {c['id']: c for c in self.rows}

    def test_longest_name_wins(self):
        self.assertEqual(self.by['new-york']['q_impr'], 40)
        self.assertEqual(self.by['york']['q_impr'], 12)

    def test_accents_han_and_local_names(self):
        self.assertEqual(self.by['sao-paulo']['q_impr'], 110)
        self.assertEqual(self.by['lisbon']['q_impr'], 130)

    def test_pages_count_every_language(self):
        self.assertEqual(self.by['tokyo']['p_impr'], 85)
        self.assertEqual(self.by['tokyo']['impr'], 85)

    def test_unmatched_and_month(self):
        self.assertEqual([r['Top queries'] for r in self.unmatched], ['paper plane upgrade game'])
        self.assertEqual(demand.month_of(self.export, None), '2026-11')
        self.assertEqual(demand.previous('2026-01'), '2025-12')

    def test_signals(self):
        hist = os.path.join(self.tmp, 'history')
        found, had = demand.signals(self.rows, '2026-10', hist)
        self.assertFalse(had)
        self.assertEqual({c['id'] for c, _ in found}, {'sao-paulo', 'lisbon'})
        found, had = demand.signals(self.rows, '2026-11', hist)
        self.assertTrue(had)
        why = {c['id']: w for c, w in found}
        self.assertEqual(set(why), {'sao-paulo', 'lisbon', 'york'})
        self.assertEqual(why['york'], ['top 5 in 2026-10 and 2026-11'])


if __name__ == '__main__':
    unittest.main()
