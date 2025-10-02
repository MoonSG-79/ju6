
import pandas as pd
from typing import Dict, Callable
from sqlalchemy import select
from app.core.db import get_session, Candle
from app.core.indicators import rsi, macd, obv, sma, ema, golden_cross, volume_spike

ConditionFunc = Callable[[pd.DataFrame], pd.Series]

def _to_df(rows):
    df = pd.DataFrame([{
        "ts": r.ts, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "vol": r.vol
    } for r in rows]).sort_values("ts").reset_index(drop=True)
    return df

def load_df(symbol: str, tf: str) -> pd.DataFrame:
    with get_session() as s:
        rows = s.execute(select(Candle).where(Candle.symbol==symbol, Candle.tf==tf).order_by(Candle.ts)).scalars().all()
    return _to_df(rows)

def cond_volume_spike(df: pd.DataFrame) -> pd.Series:
    return volume_spike(df["vol"], 20, 2.0)

def cond_short_golden(df: pd.DataFrame) -> pd.Series:
    short = ema(df["close"], 5); long = ema(df["close"], 20)
    return golden_cross(short, long)

def cond_day_cross(df: pd.DataFrame) -> pd.Series:
    short = sma(df["close"], 10); long = sma(df["close"], 60)
    return golden_cross(short, long)

def cond_mid_trend(df: pd.DataFrame) -> pd.Series:
    m, s, _ = macd(df["close"])
    return (m > s)

def build_presets() -> Dict[str, Dict[str, ConditionFunc]]:
    return {
        "scalp": {"volume_spike": cond_volume_spike, "short_gc": cond_short_golden},
        "day":   {"day_gc": cond_day_cross},
        "mid":   {"mid_trend": cond_mid_trend},
    }

def evaluate(symbol: str, tf: str, preset: str = "scalp") -> pd.Series:
    df = load_df(symbol, tf)
    conds = build_presets().get(preset, {})
    if df.empty or not conds: return pd.Series([], dtype=bool)
    signals = None
    for name, fn in conds.items():
        s = fn(df).fillna(False)
        signals = s if signals is None else (signals & s)
    return signals if signals is not None else pd.Series([False]*len(df))
