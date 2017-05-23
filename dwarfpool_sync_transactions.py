#!/usr/bin/python
import requests
import sys
from bs4 import BeautifulSoup
from lib import Factory, sync_to_csv

csv_filename = sys.argv[1]

factory = Factory()

data = []
for wallet in sys.argv[2:]:
    url = 'http://dwarfpool.com/eth/address/?wallet=%s' % wallet
    html_doc = requests.get(url).content
    soup = BeautifulSoup(html_doc, 'html.parser')

    tbody = soup.find_all('tbody')[0]
    tds = tbody.find_all('td')
    for i in range(0, len(tds), 3):
        data.append(factory.from_triple(tds[i:i + 3], wallet))

sync_to_csv(csv_filename, data)
