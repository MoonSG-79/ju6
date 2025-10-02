
import time, uuid
from typing import Optional, Dict, List, Tuple
from sqlalchemy import select
from app.core.db import get_session, Order, Trade, Candle
from app.core.utils import get_logger

log = get_logger("trade_engine")

class TradeEngine:
    def __init__(self, broker):
        self.broker = broker
        self.running = False
        self.positions: Dict[str, Dict] = {}
        self.take_profits: List[Tuple[float, float]] = []  # (gain_pct, sell_ratio)

    def start(self): self.running = True; log.info("Auto trading started.")
    def stop(self):  self.running = False; log.info("Auto trading stopped.")

    def set_take_profits(self, steps): self.take_profits = sorted(steps, key=lambda x: x[0])

    def _last_price(self, symbol: str) -> Optional[float]:
        with get_session() as s:
            return s.execute(select(Candle.close).where(Candle.symbol==symbol, Candle.tf=="1m").order_by(Candle.ts.desc())).scalars().first()

    def place_order(self, symbol: str, side: str, qty: int, price: Optional[float]=None):
        res = self.broker.place_order(symbol, side, qty, price)
        with get_session() as s:
            s.merge(Order(order_id=res.order_id, symbol=symbol, side=side, qty=qty, price=res.price, status=res.status, ts=int(time.time()*1000)))
            if res.status == "FILLED":
                if side.upper() == "BUY":
                    pos = self.positions.get(symbol, {"qty":0,"avg":0.0,"trail":None,"sold_levels":set()})
                    new_qty = pos["qty"] + qty
                    new_avg = (pos["avg"]*pos["qty"] + res.price*qty)/max(1, new_qty)
                    pos.update({"qty":new_qty, "avg":new_avg})
                    self.positions[symbol] = pos
                    s.merge(Trade(trade_id=str(uuid.uuid4()), order_id=res.order_id, symbol=symbol, qty=qty, price=res.price, pnl=0.0, ts=int(time.time()*1000)))
                else:
                    pos = self.positions.get(symbol, {"qty":0,"avg":0.0,"trail":None,"sold_levels":set()})
                    new_qty = pos["qty"] - qty
                    pnl = (res.price - pos["avg"]) * qty
                    pos.update({"qty":max(0,new_qty)})
                    if pos["qty"] == 0:
                        pos["avg"] = 0.0; pos["sold_levels"] = set(); pos["trail"] = None
                    self.positions[symbol] = pos
                    s.merge(Trade(trade_id=str(uuid.uuid4()), order_id=res.order_id, symbol=symbol, qty=-qty, price=res.price, pnl=pnl, ts=int(time.time()*1000)))
            s.commit()
        log.info(f"Order {res.order_id} {side} {symbol} x{qty} @ {res.price} -> {res.status}")
        return res

    def apply_stop_loss(self, symbol: str, stop_pct: float):
        pos = self.positions.get(symbol)
        if not pos or pos["qty"] <= 0: return
        last = self._last_price(symbol)
        if last is None: return
        if (last - pos["avg"]) / pos["avg"] * 100.0 <= -abs(stop_pct):
            self.place_order(symbol, "SELL", pos["qty"])

    def apply_trailing_stop(self, symbol: str, trail_pct: float):
        pos = self.positions.get(symbol)
        if not pos or pos["qty"] <= 0: return
        last = self._last_price(symbol)
        if last is None: return
        high = pos.get("trail")
        if high is None or last > high: pos["trail"] = last
        drawdown = (last - pos["trail"]) / pos["trail"] * 100.0 if pos["trail"] else 0.0
        if drawdown <= -abs(trail_pct): self.place_order(symbol, "SELL", pos["qty"])

    def apply_take_profits(self, symbol: str):
        pos = self.positions.get(symbol)
        if not pos or pos["qty"] <= 0 or not self.take_profits: return
        last = self._last_price(symbol)
        if last is None: return
        gain = (last - pos["avg"]) / pos["avg"] * 100.0
        for lvl, ratio in self.take_profits:
            if gain >= lvl and lvl not in pos.get("sold_levels", set()):
                qty_to_sell = max(1, int(pos["qty"] * ratio))
                self.place_order(symbol, "SELL", qty_to_sell)
                pos.setdefault("sold_levels", set()).add(lvl)

    def decide(self, human_score: float, ai_score: float, buy_th: int, sell_th: int):
        final = (human_score + ai_score) / 2.0
        if final >= buy_th:  return "BUY", final
        if final <= sell_th: return "SELL", final
        return "HOLD", final
