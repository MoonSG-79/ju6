
from datetime import datetime
import numpy as np
import pandas as pd
from typing import List
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select
from app.core.db import get_session, Candle, InvestorFlow
from app.core.utils import get_logger

log = get_logger("data_manager")

TF_MINUTES = {"1m":1, "3m":3, "15m":15, "60m":60, "1d": 60*24}

def _gen_dummy_ohlcv(start_ts: int, periods: int, tf: str, seed: int = 42):
    np.random.seed(seed)
    dt = TF_MINUTES[tf]
    ts = np.array([start_ts + i*dt*60*1000 for i in range(periods)], dtype=np.int64)
    price = np.cumsum(np.random.normal(0, 1, size=periods)) + 100.0
    price = np.maximum(price, 1.0)
    open_ = price + np.random.normal(0, 0.5, size=periods)
    close = price + np.random.normal(0, 0.5, size=periods)
    high = np.maximum(open_, close) + np.abs(np.random.normal(0, 0.3, size=periods))
    low  = np.minimum(open_, close) - np.abs(np.random.normal(0, 0.3, size=periods))
    vol  = np.random.randint(1000, 5000, size=periods)
    df = pd.DataFrame({"ts": ts, "open":open_, "high":high, "low":low, "close":close, "vol":vol})
    return df

def _bulk_upsert_candles(df: pd.DataFrame, symbol: str, tf: str, chunk: int = 20000):
    if df.empty: return 0
    df = df.copy(); df["symbol"] = symbol; df["tf"] = tf
    keys = ["symbol","tf","ts","open","high","low","close","vol"]
    total = 0
    with get_session() as s:
        for i in range(0, len(df), chunk):
            part = df.iloc[i:i+chunk][keys]
            stmt = sqlite_insert(Candle.__table__).values(part.to_dict("records")).prefix_with("OR IGNORE")
            s.execute(stmt); s.commit(); total += len(part)
    return total

def initial_load(symbols: List[str], tfs: List[str] = ["1m","3m","15m","60m","1d"], years: int = 2):
    now = int(datetime.utcnow().timestamp()*1000)
    trading_minutes_per_year = 252 * 390
    caps = {"1m":200_000, "3m":150_000, "15m":80_000, "60m":40_000, "1d":1_200}

    for sym in symbols:
        for tf in tfs:
            step = TF_MINUTES[tf]
            periods = max(200, (trading_minutes_per_year*years)//step)
            periods = min(periods, caps.get(tf, periods))
            start_ts = now - periods*step*60*1000
            df = _gen_dummy_ohlcv(start_ts, periods, tf, seed=abs(hash(sym+tf))%(2**32))
            _bulk_upsert_candles(df, sym, tf, chunk=20000)

        # Investor flows: cap 500 days
        periods = min(252*years, 500)
        ts0 = now - periods*24*60*60*1000
        flows = pd.DataFrame({
            "symbol": sym,
            "ts": [ts0 + i*24*60*60*1000 for i in range(periods)],
            "foreigner": np.random.randint(-500,500, size=periods),
            "institution": np.random.randint(-500,500, size=periods),
            "retail": np.random.randint(-500,500, size=periods)
        })
        with get_session() as s:
            for i in range(0, len(flows), 5000):
                part = flows.iloc[i:i+5000]
                stmt = sqlite_insert(InvestorFlow.__table__).values(part.to_dict("records")).prefix_with("OR IGNORE")
                s.execute(stmt); s.commit()
    log.info(f"Initial load completed for {len(symbols)} symbols.")

def update_data(symbols: List[str], tfs: List[str] = ["1m","3m","15m","60m","1d"]):
    add_bars = 300
    for sym in symbols:
        for tf in tfs:
            step = TF_MINUTES[tf]
            with get_session() as s:
                last_ts = s.execute(select(Candle.ts).where(Candle.symbol==sym, Candle.tf==tf).order_by(Candle.ts.desc())).scalars().first()
            if not last_ts: continue
            df = _gen_dummy_ohlcv(last_ts + step*60*1000, add_bars, tf, seed=abs(hash(sym+tf+"upd"))%(2**32))
            _bulk_upsert_candles(df, sym, tf, chunk=20000)
    log.info(f"Update completed for {len(symbols)} symbols.")
