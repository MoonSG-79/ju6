
from typing import Tuple
import pandas as pd
from sqlalchemy import select
from app.core.db import get_session, RationaleItem, RationaleWeight
from app.services.condition_engine import load_df
from app.core.indicators import ema, sma, rsi, macd, obv, volume_spike

def _eval_volume_spike(df): return volume_spike(df["vol"], 20, 2.0)
def _eval_short_ma_gc(df):
    s = ema(df["close"], 5); l = ema(df["close"], 20)
    return ((s.shift(1) <= l.shift(1)) & (s > l)).fillna(False)
def _eval_long_green(df):
    body = (df["close"] - df["open"]).abs()
    atr = (df["high"] - df["low"]).rolling(14).mean()
    return ((df["close"] > df["open"]) & (body > 1.5*atr)).fillna(False)
def _eval_prev_high_break(df):
    rh = df["high"].rolling(390).max().shift(1)
    return (df["high"] > rh).fillna(False)
def _eval_prev_low_hold(df):
    rl = df["low"].rolling(390).min().shift(1)
    return (df["low"] >= rl).fillna(False)
def _eval_gap_up_support(df):
    prev_close = df["close"].shift(1)
    gap = (df["open"] - prev_close) / (prev_close.replace(0,1e-9)) * 100.0
    return ((gap > 1.0) & (df["low"] > prev_close)).fillna(False)
def _eval_rsi_oversold_bounce(df):
    r = rsi(df["close"])
    return ((r.shift(1) < 30) & (r >= 30)).fillna(False)
def _eval_rsi_overbought(df):
    r = rsi(df["close"]); return (r > 70).fillna(False)
def _eval_macd_gc(df):
    m, s, _ = macd(df["close"]); return ((m.shift(1) <= s.shift(1)) & (m > s)).fillna(False)
def _eval_macd_dc(df):
    m, s, _ = macd(df["close"]); return ((m.shift(1) >= s.shift(1)) & (m < s)).fillna(False)
def _eval_obv_up(df):
    o = obv(df["close"], df["vol"]); return (o.diff() > 0).fillna(False)
def _eval_obv_down(df):
    o = obv(df["close"], df["vol"]); return (o.diff() < 0).fillna(False)
def _eval_pullback_bounce(df):
    e20 = ema(df["close"], 20); return ((df["close"].shift(1) <= e20.shift(1)) & (df["close"] > e20)).fillna(False)
def _eval_lower_high(df):
    s20 = sma(df["close"], 20); rolling_max = df["high"].rolling(20).max()
    return ((s20.diff() < 0) & (df["close"] < s20) & (rolling_max.diff() < 0)).fillna(False)
def _eval_fib_retracement(df):
    low20 = df["low"].rolling(20).min(); high20 = df["high"].rolling(20).max()
    rng = (high20 - low20).replace(0, 1e-9); ratio = (df["close"] - low20) / rng
    return ((ratio > 0.382) & (ratio < 0.618)).fillna(False)
def _eval_ma_support(df):
    s20 = sma(df["close"], 20); return (df["low"] >= s20*0.995).fillna(False)
def _eval_news_theme(df): return _eval_volume_spike(df)
def _eval_ask_wall_clear(df):
    return pd.Series([False]*len(df), index=df.index)
def _eval_downtrend_break(df):
    s50 = sma(df["close"], 50); return ((df["close"].shift(1) <= s50.shift(1)) & (df["close"] > s50)).fillna(False)
def _eval_psych_levels(df):
    c = df["close"]; nearest = (c/1000.0).round()*1000.0
    return ((abs(c - nearest) / nearest) < 0.002).fillna(False)

EVAL_MAP = {
    "거래량 급증": _eval_volume_spike,
    "단기이평 골든크로스": _eval_short_ma_gc,
    "장대양봉 출현": _eval_long_green,
    "전일 고점 돌파": _eval_prev_high_break,
    "전일 저점 지지": _eval_prev_low_hold,
    "시초가 갭상승 + 지지": _eval_gap_up_support,
    "RSI 과매도 반등": _eval_rsi_oversold_bounce,
    "RSI 과매수": _eval_rsi_overbought,
    "MACD 골든크로스": _eval_macd_gc,
    "MACD 데드크로스": _eval_macd_dc,
    "OBV 상승 전환": _eval_obv_up,
    "OBV 하락 전환": _eval_obv_down,
    "눌림목 반등": _eval_pullback_bounce,
    "고점 하락 패턴": _eval_lower_high,
    "피보나치 되돌림": _eval_fib_retracement,
    "이평선 지지 여부": _eval_ma_support,
    "장중 뉴스/테마 급등": _eval_news_theme,
    "상위 매도벽 해소": _eval_ask_wall_clear,
    "하락 추세선 돌파": _eval_downtrend_break,
    "심리적 가격대": _eval_psych_levels,
}

def compute_human_score(symbol: str, tf: str, profile: str = "scalp") -> Tuple[float, pd.Series]:
    with get_session() as s:
        rows = s.execute(select(RationaleItem.id, RationaleItem.name, RationaleWeight.weight)
                         .join(RationaleWeight, RationaleWeight.item_id==RationaleItem.id)
                         .where(RationaleWeight.profile==profile)
                         .order_by(RationaleItem.idx)).all()
    if not rows:
        return 0.0, pd.Series(dtype=float)

    df_price = load_df(symbol, tf)
    if df_price.empty:
        return 0.0, pd.Series(dtype=float)

    score_sum = 0.0; weight_sum = 0.0; detail = {}
    for item_id, name, weight in rows:
        func = EVAL_MAP.get(name)
        if func is None or not weight or weight <= 0: continue
        series = func(df_price)
        val = bool(series.iloc[-1]) if len(series) else False
        detail[name] = 1.0 if val else 0.0
        score_sum += (1.0 if val else 0.0) * float(weight)
        weight_sum += float(weight)

    final = 0.0 if weight_sum == 0 else (score_sum / weight_sum) * 100.0
    return round(final, 2), pd.Series(detail)
