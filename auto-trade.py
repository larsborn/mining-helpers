from lib import ZabbixSender
import sys
import krakenex

kraken_api_key_file_name = sys.argv[1]
source_currency = sys.argv[2]
target_currency = sys.argv[3]

api = krakenex.API()
api.load_key(kraken_api_key_file_name)
zabbix = ZabbixSender('/usr/bin/zabbix_sender', '/etc/zabbix/zabbix_agentd.conf')

eth = float(api.query_private('Balance', {})['result']['X%s' % source_currency])
if eth < 1e-06:
    exit()
zabbix.send_item('amount.%s.order' % source_currency.lower(), eth)
trade = api.query_private('AddOrder', {
    'pair': 'X%sZ%s' % (source_currency, target_currency),
    'type': 'sell',
    'ordertype': 'market',
    'volume': '%s' % eth,
    'trading_agreement': 'agree'
})
if 'error' in trade.keys() and len(trade['error']) > 0:
    order = 'KRAKEN API ERROR: %s' % '\n'.join(trade['error'])
else:
    order = trade['result']['descr']['txid']
zabbix.send_item('id.%s.order' % source_currency.lower(), order)
