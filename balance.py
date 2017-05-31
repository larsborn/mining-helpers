import csv
import requests
import configparser
import krakenex
import datetime
from dateutil.parser import parse as parse_date
from itertools import islice,groupby

config = configparser.ConfigParser()
config.read('config.ini')
bankurl = config['DEFAULT']['bankurl']
exchangeurl = config['DEFAULT']['exchangeurl']
poolurl = config['DEFAULT']['poolurl']

class mined(object):
    def __init__(self, row):
        self.tid    = row[0]
        self.wallet = row[1]
        self.time   = parse_date(row[2])
        self.amount = float(row[3])
    
    def __repr__(self):
        return '<Mined %s; %s; %s; %s>' % (
            self.tid, self.wallet, self.time, self.amount
        )

    def __eq__(self, other):
        return self.tid == other.tid

class trade(object):
    def __init__(self, row):
        self.tid            = row[0]
        self.amount_eth     = float(row[1])
        self.time           = parse_date(row[2])
        self.amount_euro    = float(row[3])
        self.fee            = float(row[4])
    
    def __repr__(self):
        return '<Trade %s; %s; %s; %s; %s>' % (
            self.tid, self.amount_eth, self.time, self.amount_euro, self.fee
        )

    def __eq__(self, other):
        return self.tid == other.tid
        
class deposit(object):
    def __init__(self, row):
        self.tid            = row[0]
        self.amount         = float(row[1])
        self.time           = parse_date(row[2])
    
    def __repr__(self):
        return '<Deposit %s; %s; %s>' % (
            self.tid, self.amount, self.time
        )

    def __eq__(self, other):
        return self.tid == other.tid

class withdrawal(object):
    def __init__(self, row):
        self.tid            = row[0]
        self.amount         = float(row[1])
        self.time           = parse_date(row[2])
    
    def __repr__(self):
        return '<Withdrawal %s; %s; %s>' % (
            self.tid, self.amount, self.time
        )

    def __eq__(self, other):
        return self.tid == other.tid
        
class SEPA(object):
    def __init__(self, row):
        self.time           = parse_date(row[1]).replace(hour=23, minute=59)
        self.tid            = row[4]
        if row[3] == "Überweisung":
            self.withdrawal = True
        else:
            self.withdrawal = False
        self.amount         = float(row[5].replace(',', '.'))
    
    def __repr__(self):
        return '<SEPA %s; %s; %s;>' % (
            self.tid, self.time, self.amount
        )

    def __eq__(self, other):
        return self.tid == other.tid
        
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
        
response = requests.get(poolurl)
lines = csv.reader(response.text.splitlines() , delimiter=',')
for line in lines:
    t = mined(line)
    mines.append(t)
        
response = requests.get(bankurl)
lines = csv.reader(response.text.splitlines() , delimiter=';')
for line in islice(lines, 7, None):
    t = SEPA(line)
    sepas.append(t)

result = trades + mines + sepas + withdrawals + deposits
result.sort(key=lambda x: x.time, reverse=False)


tradePresent = False
income = 0
eurobalance = 0
girobalance = 0
missing = 0
untraded = 0
eurofees = 0
ethfees = 0
missingtrades = 0
missingincome = 0
for res in result:
    if type(res) == SEPA:
        if tradePresent and res.withdrawal == False:
            tradePresent = False
            girobalance += res.amount
            print("[%s]\tGot %f € via SEPA. Giro Balance is %f €. Fees were %f €" % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount, girobalance,eurobalance-res.amount))
            eurofees +=eurobalance-res.amount
            eurobalance = 0
        elif res.withdrawal == True:
            girobalance += res.amount
            print("[%s]\t%f € were withdrawn from Giro. Giro Balance is %f €." % (res.time.strftime("%Y-%m-%d %H:%M:%S"), -res.amount, girobalance))
        else:
            girobalance += res.amount
            print("[%s]\tGot %f € via SEPA. Giro Balance is %f €. Fee is unknown due to missing trade." % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount, girobalance))
            print("\t\t\tWARNING: There was no matching Trade. Balance was %f ETH." % income)
            untraded += income
            missingtrades+=1
            income = 0
    elif type(res) == deposit:
        print("[%s]\tdeposit of %f ETH on Kraken." % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount))
    elif type(res) == withdrawal:
        print("[%s]\tWithdrawal of %f € from Kraken." % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount))
    elif type(res) == mined:
        income += res.amount
        print("[%s]\tMined %f ETH. Balance is %f ETH" % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount, income))
    elif type(res) == trade:
        if income >0 and abs((1-(res.amount_eth / income))*100) >1:
            print("[%s]\tTraded %f ETH for %f €. ETH transaction fee is unknown, Marketplace Fee was %f €" % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount_eth, res.amount_euro, res.fee))
            print("\t\t\tWARNING: Balance was %f ETH but only %f ETH were traded." %(income,res.amount_eth))
            missing += income-res.amount_eth
            missingtrades+=1
        elif income == 0:
            print("[%s]\tTraded %f ETH for %f €. ETH transaction fee is unknown, Marketplace Fee was %f €" % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount_eth, res.amount_euro, res.fee))
            print("\t\t\tWARNING: ETH Balance was 0 but ETH was traded. Some income is probably missing.")
            missingincome += 1
        else:
            print("[%s]\tTraded %f ETH for %f €. Transaction fee was %f ETH, Marketplace Fee was %f €" % (res.time.strftime("%Y-%m-%d %H:%M:%S"), res.amount_eth, res.amount_euro, -(res.amount_eth-income),res.fee)) 
            ethfees += -(res.amount_eth-income)
        tradePresent = True
        eurofees += res.fee
        eurobalance += res.amount_euro
        income = 0
    #print(res)
print("--------------------------------------------------------------------------")
print("Kraken: %f ETH, Kraken: %f €, Giro: %f €, Sum: %f €" % (income,eurobalance,girobalance,eurobalance+girobalance))
print("Fees: %f ETH, %f €" % (ethfees,eurofees))
print("%f ETH got lost, %f ETH were untraded but probably withdrawn.\nAt least %i Trades seem to be missing. Also %i trades were carried out without balance." % (missing,untraded,missingtrades,missingincome))