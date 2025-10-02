
import pandas as pd
from sqlalchemy import select
from app.core.db import get_session, Trade

def daily_pnl():
    with get_session() as s:
        rows = s.execute(select(Trade)).scalars().all()
        if not rows:
            return pd.DataFrame(columns=["date","symbol","qty","pnl"])
        df = pd.DataFrame([{"ts": r.ts, "symbol": r.symbol, "qty": r.qty, "price": r.price, "pnl": r.pnl} for r in rows])
        df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.date
        agg = df.groupby(["date","symbol"], as_index=False).agg({"qty":"sum","pnl":"sum"})
        return agg[["date","symbol","qty","pnl"]].sort_values(["date","symbol"])
