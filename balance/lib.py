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