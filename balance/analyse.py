import configparser
from sqlalchemy.orm import sessionmaker
from lib import *
import pprint
import csv

pp = pprint.PrettyPrinter(indent=4)

config = configparser.ConfigParser()
config.read('config.ini')
db_conn = config['DEFAULT']['db_conn']

db = create_engine(db_conn)
db.echo = False 
Base.metadata.create_all(db)
Session = sessionmaker(bind=db)
session = Session()

sepas = session.query(SEPA).order_by(SEPA.time).all()
mines = session.query(mined).order_by(mined.time).all() 
trades = session.query(trade).order_by(trade.time).all()
deposits = session.query(deposit).order_by(deposit.time).all()
withdrawals = session.query(withdrawal).order_by(withdrawal.time).all()

sepas.sort(key=lambda x: x.time, reverse=False)
mines.sort(key=lambda x: x.time, reverse=False)
trades.sort(key=lambda x: x.time, reverse=False)
deposits.sort(key=lambda x: x.time, reverse=False)
withdrawals.sort(key=lambda x: x.time, reverse=False)

usepas = []
umines = []
utrades = []
udeposits = []
uwithdrawals =[]

balance = []

lastW = trades[0].time
lastT = deposits[0].time
lastD = mines[0].time

for s in sepas:
    if s.withdrawal == False:
        w = next((x for x in withdrawals if x.tid in s.tid), None)
        if not w == None:
            uwithdrawals.append(w)
            t = [x for x in trades if x.time >=lastW and x.time < s.time]
            utrades += t
            tl = []
            for td in t:
                d = [x for x in deposits if x.time >=lastT and x.time < td.time]
                udeposits += d
                dl = []
                for dp in d:
                    m = next((x for x in mines if x.time >=lastD and x.time < dp.time), None)
                    umines.append(m)
                    lastD = dp.time
                    dl.append({'d':dp, 'mine':m})
                lastT = td.time
                tl.append({'t':td, 'deposits': dl})
            lastW =s.time
            balance.append({'sepa':s,'withdrawal':{'w':w,'trades': tl}})
            usepas.append(s)
    else:
        balance.append({'sepa':s})
        usepas.append(s)



mines = list(set(mines)-set(umines))
deposits = list(set(deposits)-set(udeposits))
trades = list(set(trades)-set(utrades))
withdrawals = list(set(withdrawals)-set(uwithdrawals))

trades.sort(key=lambda x: x.time, reverse=False)
deposits.sort(key=lambda x: x.time, reverse=False)
mines.sort(key=lambda x: x.time, reverse=False)

obalance = []

if len(trades) > 0:
    lastT = deposits[0].time
    lastD = mines[0].time
    for td in trades:
        d = [x for x in deposits if x.time >=lastT and x.time < td.time]
        udeposits += d
        dl = []
        for dp in d:
            m = next((x for x in mines if x.time >=lastD and x.time < dp.time), None)
            if  m == None:
                print("----------------")
                print("didn't find a matching mine for deposit:")
                pp.pprint(dp)
                print("in")
                pp.pprint(mines)
                print("Parameters were time between %s and %s" %(lastD, dp.time))
                print("----------------")
            umines.append(m)
            lastD = dp.time
            dl.append({'d':dp, 'mine':m})
        lastT = td.time
        obalance.append({'trade':td, 'deposits': dl})
        
mines = list(set(mines)-set(umines))
deposits = list(set(deposits)-set(udeposits))

deposits.sort(key=lambda x: x.time, reverse=False)
mines.sort(key=lambda x: x.time, reverse=False) 

ebalance = []
if len(deposits) > 0:
    lastD = mines[0].time

    for dp in deposits:
            m = next((x for x in mines if x.time >=lastD and x.time < dp.time), None)
            if  m == None:
                print("----------------")
                print("didn't find a matching mine for deposit:")
                pp.pprint(dp)
                print("in")
                pp.pprint(mines)
                print("Parameters were time between %s and %s" %(lastD, dp.time))
                print("----------------")
            umines.append(m)
            lastD = dp.time
            ebalance.append({'deposit':dp, 'mine':m})
        
mines = list(set(mines)-set(umines))
sepas = list(set(sepas)-set(usepas))
              
#pp.pprint(balance)
#print("-------------")
#pp.pprint(obalance)
#print("-------------")
#pp.pprint(ebalance)
#print("-------------")
#pp.pprint(mines)
#pp.pprint(sepas)
#print("-------------")

ETH_P = 0
ETH_PtoE_Fee = 0
ETH_E = 0
EUR_Trade_Fee = 0
EUR_E = 0
EUR_EtoB_Fee = 0
EUR_B = 0
j = journal('analyse.journal')

for s in balance:
    if s['sepa'].withdrawal == False:
        EUR_E += s['withdrawal']['w'].amount - 0.09
        EUR_EtoB_Fee += 0.09
        for t in s['withdrawal']['trades']:
            ETH_E -= t['t'].amount_eth
            EUR_Trade_Fee += t['t'].fee
            EUR_E -= t['t'].fee
            EUR_E += t['t'].amount_euro
            for d in t['deposits']:
                ETH_E += d['d'].amount
                ETH_PtoE_Fee += d['mine'].amount-d['d'].amount
                ETH_P -= d['mine'].amount
                j.symmetricFee(d['d'].time, d['mine'].time, d['mine'].tid, -d['mine'].amount, d['d'].amount, "Income:Gutemine", "Assets:Kraken ETH", "ETH", "Fees:ETH Transfer")
            j.asymmetricFee(t['t'].time, None, t['t'].tid, -t['t'].amount_eth, t['t'].amount_euro-t['t'].fee, "Assets:Kraken ETH", "Assets:Kraken EUR", "ETH", "EUR", "Fees:Trade", "manual", t['t'].fee, "EUR")
        EUR_B += s['sepa'].amount
        j.symmetricFee(s['withdrawal']['w'].time, s['sepa'].time, s['sepa'].tid, s['withdrawal']['w'].amount - 0.09, s['sepa'].amount, "Assets:Kraken EUR", "Assets:ING DiBa", "EUR", "Fees:EUR Transfer")
    else:
        EUR_B += s['sepa'].amount
        if "Strom" in s['sepa'].tid:
            j.symmetric(s['sepa'].time, None, s['sepa'].tid, -s['sepa'].amount, "Assets:ING DiBa", "Expenses:Power", "EUR")
        elif "Hardware" in s['sepa'].tid:
            j.symmetric(s['sepa'].time, None, s['sepa'].tid, -s['sepa'].amount, "Assets:Investment", "Expenses:Hardware", "EUR")
        else:
            j.symmetric(s['sepa'].time, None, s['sepa'].tid, -s['sepa'].amount, "Assets", "Expenses", "EUR")
    
for t in obalance:
    ETH_E -= t['trade'].amount_eth
    EUR_Trade_Fee += t['trade'].fee
    EUR_E -= t['trade'].fee
    EUR_E += t['trade'].amount_euro
    for d in t['deposits']:
        ETH_E += d['d'].amount
        ETH_PtoE_Fee += d['mine'].amount-d['d'].amount
        ETH_P -= d['mine'].amount
        j.symmetricFee(d['d'].time, d['mine'].time, d['mine'].tid, -d['mine'].amount, d['d'].amount, "Income:Gutemine", "Assets:Kraken ETH", "ETH", "Fees:ETH Transfer")
    j.asymmetricFee(t['trade'].time, None, t['trade'].tid, -t['trade'].amount_eth, t['trade'].amount_euro-t['trade'].fee, "Assets:Kraken ETH", "Assets:Kraken EUR", "ETH", "EUR", "Fees:Trade", "manual", t['trade'].fee, "EUR")
    
for d in ebalance:
    ETH_E += d['deposit'].amount
    ETH_PtoE_Fee += d['mine'].amount-d['d'].amount
    ETH_P -= d['mine'].amount
    j.symmetricFee(d['deposit'].time, d['mine'].time, d['mine'].tid, -d['mine'].amount, d['deposit'].amount, "Income:Gutemine", "Assets:Kraken ETH", "ETH", "Fees:ETH Transfer")

print("Pool\t\tExchange\tExchange\tBank")
print("%f ETH\t%f ETH\t%f €\t%f €" % (ETH_P, ETH_E, EUR_E, EUR_B))
print("Tx Fees\t\tTrade Fees\tWithdrawal Fees")
print("%f ETH\t%f €\t%f €" % (ETH_PtoE_Fee, EUR_Trade_Fee, EUR_EtoB_Fee))