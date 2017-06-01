from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from dateutil.parser import parse as parse_date
Base = declarative_base()

class mined(Base):
    __tablename__ = 'mines'
    tid     = Column(String(70), primary_key=True)
    wallet  = Column(String(50))
    time    = Column(DateTime)
    amount  = Column(Float)
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
        if type(other) == type(None):
            return False
        return self.tid == other.tid

    def __hash__(self):
        return hash(self.tid)

class trade(Base):
    __tablename__ = 'trades'
    tid         = Column(String(50), primary_key=True)
    time        = Column(DateTime)
    amount_eth  = Column(Float)
    amount_euro = Column(Float)
    fee = Column(Float)
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
        if type(other) == type(None):
            return False
        return self.tid == other.tid
        
    def __hash__(self):
        return hash(self.tid)
        
class deposit(Base):
    __tablename__ = 'deposits'
    tid     = Column(String(50), primary_key=True)
    time    = Column(DateTime)
    amount  = Column(Float)
    def __init__(self, row):
        self.tid            = row[0]
        self.amount         = float(row[1])
        self.time           = parse_date(row[2])
    
    def __repr__(self):
        return '<Deposit %s; %s; %s>' % (
            self.tid, self.amount, self.time
        )

    def __eq__(self, other):
        if type(other) == type(None):
            return False
        return self.tid == other.tid
        
    def __hash__(self):
        return hash(self.tid)

class withdrawal(Base):
    __tablename__ = 'withdrawals'
    tid     = Column(String(50), primary_key=True)
    time    = Column(DateTime)
    amount  = Column(Float)
    def __init__(self, row):
        self.tid            = row[0]
        self.amount         = float(row[1])
        self.time           = parse_date(row[2])
    
    def __repr__(self):
        return '<Withdrawal %s; %s; %s>' % (
            self.tid, self.amount, self.time
        )

    def __eq__(self, other):
        if type(other) == type(None):
            return False
        return self.tid == other.tid
        
    def __hash__(self):
        return hash(self.tid)
        
class SEPA(Base):
    __tablename__ = 'sepas'
    tid         = Column(String(50), primary_key=True)
    time        = Column(DateTime)
    withdrawal  = Column(Boolean)
    amount      = Column(Float)
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
        if type(other) == type(None):
            return False
        return self.tid == other.tid
        
    def __hash__(self):
        return hash(self.tid)
        
class journal(object):
    def __init__(self, filename):
        self.f = open(filename, 'w')
        
    def symmetric(self, time1, time2, desc, amount, account1, account2, currency):
        if not time2 == None:
            self.f.write('%s=%s %s\n' % (time1.strftime('%Y/%m/%d'), time2.strftime('%Y/%m/%d'), desc))
        else:
            self.f.write('%s %s\n' % (time1.strftime('%Y/%m/%d'), desc))
        self.f.write('\t%s  %s%f\n' % (account1, currency, -amount))
        self.f.write('\t%s  %s%f\n' % (account2, currency, amount))
        self.f.write('\n')
    
    def symmetricFee(self, time1, time2, desc, amount1, amount2, account1, account2, currency, feeaccount, feetype = "auto", feeamount = 0):
        if not time2 == None:
            self.f.write('%s=%s %s\n' % (time1.strftime('%Y/%m/%d'), time2.strftime('%Y/%m/%d'), desc))
        else:
            self.f.write('%s %s\n' % (time1.strftime('%Y/%m/%d'), desc))
        self.f.write('\t%s  %s%f\n' % (account1, currency, amount1))
        self.f.write('\t%s  %s%f\n' % (account2, currency, amount2))
        if feetype == "auto":
            self.f.write('\t%s\n' % (feeaccount))
        else:
            self.f.write('\t%s  %s%f\n' % (feeaccount, currency, feeamount))
        self.f.write('\n')
    
    def asymmetric(self, time1, time2, desc, amount1, amount2, account1, account2, currency1, currency2):
        if not time2 == None:
            self.f.write('%s=%s %s\n' % (time1.strftime('%Y/%m/%d'), time2.strftime('%Y/%m/%d'), desc))
        else:
            self.f.write('%s %s\n' % (time1.strftime('%Y/%m/%d'), desc))
        self.f.write('\t%s  %s%f\n' % (account1, currency1, amount1))
        self.f.write('\t%s  %s%f\n' % (account2, currency2, amount2))
        self.f.write('\n')
        
    def asymmetricFee(self, time1, time2, desc, amount1, amount2, account1, account2, currency1, currency2, feeaccount, feetype = "auto", feeamount = 0, feecurrency = ""):
        if not time2 == None:
            self.f.write('%s=%s %s\n' % (time1.strftime('%Y/%m/%d'), time2.strftime('%Y/%m/%d'), desc))
        else:
            self.f.write('%s %s\n' % (time1.strftime('%Y/%m/%d'), desc))
        self.f.write('\t%s  %s%f\n' % (account1, currency1, amount1))
        self.f.write('\t%s  %s%f\n' % (account2, currency2, amount2))
        if feetype == "auto":
            self.f.write('\t%s\n' % (feeaccount))
        else:
            self.f.write('\t%s  %s%f\n' % (feeaccount, feecurrency, feeamount))
        self.f.write('\n')