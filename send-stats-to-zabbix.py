#!/usr/bin/python
import json
import re
import requests
from lib import ClaymoreMinerStats, ZabbixSender

r = requests.get('http://localhost:3333')
stats = ClaymoreMinerStats(json.loads(re.search("\{[^\}]*\}", str(r.content)).group(0)))
s = ZabbixSender('C:\\zabbix_sender.exe', 'C:\\zabbix_agentd.conf')
s.send_item('total_hashrate', stats.total_hashrate)
s.send_item('total_shares', stats.total_shares)
s.send_item('total_rejected_shares', stats.total_rejected_shares)
s.send_item('total_incorrect_shares', stats.incorrect_shares)
