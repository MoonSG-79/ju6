
from typing import List, Callable, Optional
import time, random, uuid
from dataclasses import dataclass

@dataclass
class OrderResult:
    order_id: str
    status: str   # NEW/FILLED/CANCELED
    price: float

# ---------- Mock Impl (safe fallback) ----------
class _MockKiwoom:
    def __init__(self):
        self.logged_in = False
        self.is_paper = True
        self.accounts = ["000000-01"]
        self.conds = ["Scalp_VolSpike", "Day_Cross", "Mid_Trend"]
        self._real_callbacks: List[Callable[[str,str,str,int], None]] = []

    def login(self, account_no: str, password: str="", is_paper: bool=True) -> bool:
        time.sleep(0.1)
        self.logged_in = True
        self.is_paper = is_paper
        if account_no and account_no not in self.accounts:
            self.accounts.append(account_no)
        return True

    def get_accounts(self) -> List[str]: return self.accounts
    def fetch_condition_list(self) -> List[str]: return list(self.conds)

    def subscribe_condition(self, cond_name: str) -> List[str]:
        sample = ["A005930","A000660","A035720","A251270","A091990","A214330"]
        random.shuffle(sample)
        for code in sample[:2]:
            for cb in self._real_callbacks: cb(code, "I", cond_name, 0)
        return sample[:random.randint(2, 5)]

    def on_real_condition(self, cb: Callable[[str,str,str,int], None]): self._real_callbacks.append(cb)

    # --- extras for UI demo ---
    def get_orderbook(self, symbol: str):
        mid = random.uniform(10000, 50000)
        asks = [(round(mid + i*10,2), random.randint(1,50)*10) for i in range(5,0,-1)]
        bids = [(round(mid - i*10,2), random.randint(1,50)*10) for i in range(1,6)]
        return {"asks": asks, "bids": bids, "mid": round(mid,2)}

    def place_order(self, symbol: str, side: str, qty: int, price: Optional[float]=None) -> OrderResult:
        mid = self.get_orderbook(symbol)["mid"]
        fill_price = price or mid
        return OrderResult(order_id=str(uuid.uuid4()), status="FILLED", price=float(fill_price))

# ---------- Real KHOpenAPI wrapper (minimal) ----------
try:
    from PyQt5.QAxContainer import QAxWidget
    from PyQt5 import QtCore
except Exception:
    QAxWidget = None
    QtCore = None

class _RealKiwoom:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.logged_in = False
        self._real_callbacks: List[Callable[[str,str,str,int], None]] = []
        # Connect events
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveConditionVer.connect(self._on_receive_condition_ver)
        self.ocx.OnReceiveTrCondition.connect(self._on_receive_tr_condition)
        self.ocx.OnReceiveRealCondition.connect(self._on_receive_real_condition)

    def on_real_condition(self, cb: Callable[[str,str,str,int], None]): self._real_callbacks.append(cb)

    def login(self, account_no: str="", password: str="", is_paper: bool=True) -> bool:
        self.ocx.dynamicCall("CommConnect()")
        t0 = time.time()
        while not self.logged_in and time.time() - t0 < 30:
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50); time.sleep(0.05)
        return self.logged_in
    def _on_event_connect(self, err_code): self.logged_in = (err_code == 0)

    def get_accounts(self) -> List[str]:
        v = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        return [x for x in v.strip().split(';') if x] if v else []

    def fetch_condition_list(self) -> List[str]:
        self.ocx.dynamicCall("GetConditionLoad()")
        t0 = time.time()
        while not hasattr(self, "_cond_list") and time.time() - t0 < 10:
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50); time.sleep(0.05)
        return getattr(self, "_cond_list", [])

    def _on_receive_condition_ver(self, ret, msg):
        s = self.ocx.dynamicCall("GetConditionNameList()")
        lst = []
        if s:
            for item in s.split(';'):
                if '^' in item:
                    idx, name = item.split('^'); lst.append(name)
        self._cond_list = lst

    def subscribe_condition(self, cond_name: str) -> List[str]:
        names = self.fetch_condition_list()
        idx = names.index(cond_name) if cond_name in names else 0
        self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", "9000", cond_name, idx, 1)
        t0 = time.time()
        while not hasattr(self, "_last_codes") and time.time() - t0 < 5:
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50); time.sleep(0.05)
        codes = getattr(self, "_last_codes", [])
        if hasattr(self, "_last_codes"): delattr(self, "_last_codes")
        return codes

    def _on_receive_tr_condition(self, scr_no, code_list, cond_name, idx, next_):
        codes = [c for c in code_list.split(';') if c]; self._last_codes = codes

    def _on_receive_real_condition(self, code, rtype, cond_name, cond_idx):
        for cb in self._real_callbacks:
            try: cb(code, rtype, cond_name, cond_idx)
            except Exception: pass

    # Minimal place_order stub (user should map to SendOrder in production)
    def place_order(self, symbol: str, side: str, qty: int, price: Optional[float]=None) -> OrderResult:
        # For safety here we just simulate a fill; replace with SendOrder(...) mapping.
        return OrderResult(order_id=str(uuid.uuid4()), status="FILLED", price=float(price or 0.0))

# ---------- Facade ----------
class KiwoomAPI:
    def __init__(self):
        if QAxWidget is None:
            self.mode = "mock"; self._impl = _MockKiwoom()
        else:
            self.mode = "real"; self._impl = _RealKiwoom()
        self.on_real_condition = self._impl.on_real_condition

    def login(self, account_no: str="", password: str="", is_paper: bool=True) -> bool:
        return self._impl.login(account_no, password, is_paper)

    def get_accounts(self) -> List[str]:
        return self._impl.get_accounts()

    def fetch_condition_list(self) -> List[str]:
        return self._impl.fetch_condition_list()

    def subscribe_condition(self, cond_name: str) -> List[str]:
        return self._impl.subscribe_condition(cond_name)

    # used by TradeEngine
    def place_order(self, symbol: str, side: str, qty: int, price: Optional[float]=None) -> OrderResult:
        return self._impl.place_order(symbol, side, qty, price)

    # UI-only in mock
    def get_orderbook(self, symbol: str):
        if hasattr(self._impl, "get_orderbook"):
            return self._impl.get_orderbook(symbol)
        return {"asks": [], "bids": [], "mid": 0.0}
