#!/usr/bin/env python3.6

# Scrape the list of SP500 stocks from wikipedia.org
# https://en.wikipedia.org/wiki/List_of_chief_executive_officers

import csv

from lxml import html
import requests

p = requests.get('https://en.wikipedia.org/wiki/List_of_chief_executive_officers')
tree = html.fromstring(p.content)

table = tree.xpath('//table')[0]
headers = [t.xpath('string()') for t in table.xpath('.//th')]

with open('ceos.csv', 'w') as csvfile:
    ceoswriter = csv.writer(csvfile)
    ceoswriter.writerow(headers)

    rows = table.xpath('.//tr')
    for row in rows:
        cells = row.xpath('.//td')
        ceoswriter.writerow([cell.xpath('string()').strip() for cell in cells])
