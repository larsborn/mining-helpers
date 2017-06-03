import csv
import requests
import configparser
import krakenex
import datetime
from lib import *
from sqlalchemy.orm import sessionmaker
from itertools import islice,groupby
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read('config.ini')
bankurl = config['DEFAULT']['bankurl']
exchangeurl = config['DEFAULT']['exchangeurl']
poolurl = config['DEFAULT']['poolurl']
db_conn = config['DEFAULT']['db_conn']
wallet = config['DEFAULT']['wallet']
  
trades      = []
mines       = []
sepas       = []
withdrawals = []
deposits    = []

k = krakenex.API()
k.load_key('kraken.key')
th = k.query_private('TradesHistory', {})
for tr in th['result']['trades']:
    if th['result']['trades'][tr]['type'] == "sell" and th['result']['trades'][tr]['pair'] == "XETHZEUR":
        t =trade([  th['result']['trades'][tr]['ordertxid'],
                    th['result']['trades'][tr]['vol'],
                    datetime.datetime.fromtimestamp(th['result']['trades'][tr]['time']).strftime('%Y-%m-%d %H:%M:%S'),
                    th['result']['trades'][tr]['cost'],
                    th['result']['trades'][tr]['fee']])
        trades.append(t)
        
trades.sort(key=lambda x: x.time, reverse=False)
tmptrades = []
for key, group in groupby(trades, lambda x: x.tid):
    sum_eth  = 0
    sum_euro = 0 
    sum_fee  = 0
    time = ""
    for thing in group:
        sum_eth  += thing.amount_eth
        sum_euro += thing.amount_euro
        sum_fee  += thing.fee
        time      = thing.time
    t =trade([key,sum_eth,time.strftime('%Y-%m-%d %H:%M:%S'),sum_euro,sum_fee])
    tmptrades.append(t)
trades = tmptrades 
        
d = k.query_private('Ledgers', {'type':'withdrawal', 'asset':'ZEUR'})
for dl in d['result']['ledger']:
    t = withdrawal([d['result']['ledger'][dl]['refid'], d['result']['ledger'][dl]['amount'], datetime.datetime.fromtimestamp(d['result']['ledger'][dl]['time']).strftime('%Y-%m-%d %H:%M:%S')])
    withdrawals.append(t)
    
d = k.query_private('Ledgers', {'type':'deposit', 'asset':'XETH'})
for dl in d['result']['ledger']:
    t = deposit([d['result']['ledger'][dl]['refid'], d['result']['ledger'][dl]['amount'], datetime.datetime.fromtimestamp(d['result']['ledger'][dl]['time']).strftime('%Y-%m-%d %H:%M:%S')])
    deposits.append(t)
        
url = 'http://dwarfpool.com/eth/address/?wallet=%s' % wallet
html_doc = requests.get(url).content
soup = BeautifulSoup(html_doc, 'html.parser')

tbodys = soup.find_all('tbody')
if len(tbodys) > 0:
    tbody = tbodys[0]
    tds = tbody.find_all('td')
    for i in range(0, len(tds), 3):
        t = mined([tds[i+2].get_text(),wallet,tds[i].get_text(),tds[i+1].get_text()])
        mines.append(t)
        
response = requests.get(bankurl)
lines = csv.reader(response.text.splitlines() , delimiter=';')
for line in islice(lines, 7, None):
    t = SEPA(line)
    sepas.append(t)

result = trades + mines + sepas + withdrawals + deposits
result.sort(key=lambda x: x.time, reverse=False)



db = create_engine(db_conn)
db.echo = False 
Base.metadata.create_all(db)
Session = sessionmaker(bind=db)
session = Session()

def insert_if_new(session, t):
    q = session.query(type(t)).filter(type(t).tid==t.tid)
    if len(q.all()) == 0:
        print("New Record with id %s for %s" % (t.tid, type(t).__table__))
        session.add(t)
    else:
        print("Record with id %s already exists in %s" % (t.tid, type(t).__table__))

for res in result:
    insert_if_new(session, res)
session.commit()