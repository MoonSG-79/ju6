
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, UniqueConstraint, Text, Boolean, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import DateTime
from .config import DB_PATH
from datetime import datetime

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    future=True,
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous = NORMAL;")
    cur.execute("PRAGMA temp_store = MEMORY;")
    cur.execute("PRAGMA cache_size = -64000;")
    cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    account_id = Column(String, primary_key=True)
    is_paper = Column(Boolean, default=True)
    acc_alias = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Theme(Base):
    __tablename__ = "themes"
    theme_id = Column(Integer, primary_key=True, autoincrement=True)
    theme_name = Column(String, unique=True)

class ThemeSymbol(Base):
    __tablename__ = "theme_symbols"
    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_id = Column(Integer)
    symbol = Column(String)
    __table_args__ = (UniqueConstraint('theme_id', 'symbol', name='uq_theme_symbol'),)

class Candle(Base):
    __tablename__ = "candles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    tf = Column(String, index=True)  # timeframe: 1m,3m,15m,60m,1d
    ts = Column(BigInteger, index=True)  # epoch ms
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)
    __table_args__ = (UniqueConstraint('symbol','tf','ts', name='uq_candle'),)

class InvestorFlow(Base):
    __tablename__ = "investor_flows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    ts = Column(BigInteger, index=True)  # epoch ms
    foreigner = Column(Float, default=0.0)
    institution = Column(Float, default=0.0)
    retail = Column(Float, default=0.0)
    __table_args__ = (UniqueConstraint('symbol','ts', name='uq_flow'),)

class RationaleItem(Base):
    __tablename__ = "rationale_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    note = Column(Text)
    idx = Column(Integer)

class RationaleWeight(Base):
    __tablename__ = "rationale_weights"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile = Column(String)  # scalp/day/mid
    item_id = Column(Integer)
    weight = Column(Float)
    __table_args__ = (UniqueConstraint('profile','item_id', name='uq_profile_item'),)

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True)
    symbol = Column(String)
    side = Column(String)  # BUY/SELL
    qty = Column(Integer)
    price = Column(Float)
    status = Column(String)  # NEW/FILLED/CANCELED
    ts = Column(BigInteger)

class Trade(Base):
    __tablename__ = "trades"
    trade_id = Column(String, primary_key=True)
    order_id = Column(String)
    symbol = Column(String)
    qty = Column(Integer)
    price = Column(Float)
    pnl = Column(Float, default=0.0)
    ts = Column(BigInteger)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(Text)

def create_all():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
