#!/usr/bin/python
import json
from lib import Factory, sync_to_csv
import sys

factory = Factory()
j = json.loads(str(open(sys.argv[1], 'rb').read()))
data = []
for transaction_id, trade in j['result']['closed'].iteritems():
    if trade['status'] != 'closed':
        continue
    if trade['descr']['pair'] != 'ETHEUR':
        continue
    if trade['descr']['type'] != 'sell':
        continue

    data.append(factory.from_kraken(transaction_id, trade))

sync_to_csv(sys.argv[2], data)
