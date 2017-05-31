import csv
import requests
import configparser
from dateutil.parser import parse as parse_date
from itertools import islice

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
        
trades  = []
mines   = []
sepas   = []        
response = requests.get(exchangeurl)
lines = csv.reader(response.text.splitlines() , delimiter=',')
for line in lines:
    t = trade(line)
    trades.append(t)
trades.sort(key=lambda x: x.time, reverse=False)
        
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

result = trades + mines + sepas
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