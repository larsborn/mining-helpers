from lib import ZabbixSender, KrakenApi
from os import environ

zabbix = ZabbixSender('/usr/bin/zabbix_sender', '/etc/zabbix/zabbix_agentd.conf')
api = KrakenApi(environ['CLIKRAKEN_BINARY'])
eth = api.get_balance('ETH')
if eth < 1e-06:
    exit()
zabbix.send_item('amount.eth.order', eth)
trade = api.sell_for_market_price('XETHZEUR', eth)
zabbix.send_item('id.eth.order', trade)
