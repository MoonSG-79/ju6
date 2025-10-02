
import pandas as pd
import numpy as np

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=1).mean()

def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(gain, index=close.index).rolling(period).mean()
    roll_down = pd.Series(loss, index=close.index).rolling(period).mean()
    rs = roll_up / (roll_down + 1e-9)
    r = 100.0 - (100.0 / (1.0 + rs))
    return r

def macd(close: pd.Series, fast=12, slow=26, signal=9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    dir = np.sign(close.diff().fillna(0.0))
    return (dir * volume).fillna(0.0).cumsum()

def golden_cross(short: pd.Series, long: pd.Series) -> pd.Series:
    prev = (short.shift(1) <= long.shift(1)) & (short > long)
    return prev.fillna(False)

def volume_spike(vol: pd.Series, window: int = 20, k: float = 2.0) -> pd.Series:
    ma = vol.rolling(window).mean()
    sd = vol.rolling(window).std()
    return (vol > (ma + k*sd)).fillna(False)
