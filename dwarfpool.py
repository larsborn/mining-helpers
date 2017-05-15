#!/usr/bin/python
import requests
import json
import sys

a_wallet = sys.argv[1]
a_worker = sys.argv[2]
a_field = sys.argv[3]

url = 'http://dwarfpool.com/eth/api?wallet=%s&email=mail@example.com' % a_wallet
r = requests.get(url)
j = json.loads(r.content)
if 'error' in j.keys() and j['error']:
    print j['error_code']
    exit()

for worker, fields in j['workers'].iteritems():
    if worker in a_worker:
        if a_field in fields.keys():
            print(fields[a_field])
            exit()
