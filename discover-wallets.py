#!/usr/bin/python
from lib import ZabbixSender
import json
import glob
import re

eth_wallet = re.compile('[a-f0-9]{40}')

wallets = []
for filename in glob.iglob('C://Users//**//*.bat', recursive=True):
    data = open(filename, 'r').read()
    wallets += eth_wallet.findall(data)
wallets = list(set(wallets))

list = [{'{#WALLET}': wallet} for wallet in wallets]

s = ZabbixSender('C:\\zabbix_sender.exe', 'C:\\zabbix_agentd.conf')
s.send_item('wallets', json.dumps({'data': list}))
