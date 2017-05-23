#!/usr/bin/python
import os
import requests
import sys
import csv
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

csv_filename = sys.argv[1]


class Transaction(object):
    def __init__(self, transaction_id, target_address, timestamp, amount):
        self.transaction_id = transaction_id
        self.target_address = target_address
        self.timestamp = timestamp
        self.amount = amount

    def __repr__(self):
        return '<Transaction %s; %s; %s; %s>' % (self.transaction_id, self.target_address, self.timestamp, self.amount)

    def __eq__(self, other):
        return self.transaction_id == other.transaction_id \
               and self.target_address == other.target_address \
               and self.timestamp == other.timestamp \
               and self.amount == other.amount


data = []
for wallet in sys.argv[2:]:
    url = 'http://dwarfpool.com/eth/address/?wallet=%s' % wallet
    html_doc = requests.get(url).content
    soup = BeautifulSoup(html_doc, 'html.parser')

    tbody = soup.find_all('tbody')[0]
    tds = tbody.find_all('td')
    for i in range(0, len(tds), 3):
        data.append(Transaction(tds[i + 2].get_text(), wallet, parse_date(tds[i].get_text()), tds[i + 1].get_text()))

if os.path.exists(csv_filename):
    for row in csv.reader(open(csv_filename, 'rb')):
        transaction = Transaction(row[0], row[1], parse_date(row[2]), row[3])
        if transaction not in data:
            data.append(transaction)

data = sorted(data, key=lambda elem: elem.timestamp)

fp = csv.writer(open(csv_filename, 'wb'))
for transaction in data:
    fp.writerow([transaction.transaction_id, transaction.target_address, transaction.timestamp, transaction.amount])
