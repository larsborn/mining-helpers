from lib import ZabbixSender
import sys
import krakenex

kraken_api_key_file_name = sys.argv[1]
currency = sys.argv[2]

api = krakenex.API()
api.load_key(kraken_api_key_file_name)

print(float(api.query_private('Balance', {})['result']['X%s' % currency]))
