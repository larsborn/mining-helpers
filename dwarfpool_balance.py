#!/usr/bin/python
import requests
import sys
import re

eth_amount = re.compile('(\d+\.\d+) ETH')

wallet = sys.argv[1]
url = 'http://dwarfpool.com/eth/address/?wallet=%s' % wallet
data = re.sub('<[^<]+?>', ' ', requests.get(url).content).replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
matches = eth_amount.findall(data)
mapping = {'current': 0, 'already_paid': 1, 'uncofirmed': 2, 'one_percent_fee': 3, 'earning_in_last_24': 4}
print(matches[mapping[sys.argv[2]]])
