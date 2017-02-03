#!/usr/bin/env python3.6

# Scrape the list of SP500 stocks from wikipedia.org
# https://en.wikipedia.org/wiki/List_of_S%26P_500_companies

from lxml import html
import requests

p = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
tree = html.fromstring(p.content)

table = tree.xpath('//table')[0]
headers = [t.xpath('string()') for t in table.xpath('.//th')]
print(','.join(headers))

rows = table.xpath('.//tr')
for row in rows:
    cells = row.xpath('.//td')
    print(','.join([cell.xpath('string()') for cell in cells]))
