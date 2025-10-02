
from PyQt5 import QtWidgets, QtCore
from app.services.trade_engine import TradeEngine
from app.services.kiwoom_api import KiwoomAPI
from app.services.ai_assessor import ai_score
from app.services.rationale_service import compute_human_score

def parse_tp_steps(text: str):
    steps = []
    if not text.strip(): return steps
    for part in text.split(","):
        if "@" not in part: continue
        lvl, ratio = part.split("@", 1)
        try: steps.append((float(lvl.strip()), float(ratio.strip())))
        except: pass
    return steps

class TradingTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        grid = QtWidgets.QGridLayout(self)

        self.buy_view  = QtWidgets.QTableWidget(5, 2)
        self.sell_view = QtWidgets.QTableWidget(5, 2)
        self.buy_view.setHorizontalHeaderLabels(["Bid Price","Bid Qty"])
        self.sell_view.setHorizontalHeaderLabels(["Ask Price","Ask Qty"])

        grid.addWidget(QtWidgets.QLabel("Buy Realtime"), 0, 0)
        grid.addWidget(QtWidgets.QLabel("Sell Realtime"), 0, 1)
        grid.addWidget(self.buy_view, 1, 0)
        grid.addWidget(self.sell_view, 1, 1)

        form = QtWidgets.QFormLayout()
        self.ed_symbol = QtWidgets.QLineEdit("A005930")
        self.cmb_profile = QtWidgets.QComboBox(); self.cmb_profile.addItems(["scalp","day","mid"])
        self.cmb_ai = QtWidgets.QComboBox(); self.cmb_ai.addItems(["Conservative","Normal","Aggressive"])
        self.spn_buy_th  = QtWidgets.QSpinBox(); self.spn_buy_th.setRange(0,100); self.spn_buy_th.setValue(70)
        self.spn_sell_th = QtWidgets.QSpinBox(); self.spn_sell_th.setRange(0,100); self.spn_sell_th.setValue(40)
        self.dsb_stop = QtWidgets.QDoubleSpinBox(); self.dsb_stop.setSuffix(" %"); self.dsb_stop.setDecimals(2); self.dsb_stop.setValue(3.0)
        self.dsb_trail = QtWidgets.QDoubleSpinBox(); self.dsb_trail.setSuffix(" %"); self.dsb_trail.setDecimals(2); self.dsb_trail.setValue(2.0)
        self.spn_qty = QtWidgets.QSpinBox(); self.spn_qty.setRange(1,100000); self.spn_qty.setValue(10)
        self.ed_tp = QtWidgets.QLineEdit("2@0.3,4@0.3,6@0.4")
        self.chk_auto_stops = QtWidgets.QCheckBox("Auto Apply Stop/Trail/TP"); self.chk_auto_stops.setChecked(True)

        form.addRow("Symbol", self.ed_symbol)
        form.addRow("Profile", self.cmb_profile)
        form.addRow("AI Mode", self.cmb_ai)
        form.addRow("Buy Threshold", self.spn_buy_th)
        form.addRow("Sell Threshold", self.spn_sell_th)
        form.addRow("Stop Loss", self.dsb_stop)
        form.addRow("Trailing Stop", self.dsb_trail)
        form.addRow("Qty", self.spn_qty)
        form.addRow("TP Steps (gain@ratio)", self.ed_tp)
        form.addRow(self.chk_auto_stops)

        btns = QtWidgets.QHBoxLayout()
        self.btn_start = QtWidgets.QPushButton("Start Auto Trading")
        self.btn_stop  = QtWidgets.QPushButton("Stop")
        self.btn_eval  = QtWidgets.QPushButton("Evaluate Now")
        self.btn_apply_tp = QtWidgets.QPushButton("Apply TP Steps")
        self.lbl_info  = QtWidgets.QLabel("Decision: -")
        for w in [self.btn_start, self.btn_stop, self.btn_eval, self.btn_apply_tp, self.lbl_info]:
            btns.addWidget(w)

        grid.addLayout(form, 2, 0, 1, 2)
        grid.addLayout(btns, 3, 0, 1, 2)

        self.api = KiwoomAPI()
        self.engine = TradeEngine(self.api)

        self.btn_start.clicked.connect(self.engine.start)
        self.btn_stop.clicked.connect(self.engine.stop)
        self.btn_eval.clicked.connect(self.evaluate_once)
        self.btn_apply_tp.clicked.connect(self.apply_tp_steps)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.heartbeat)
        self.timer.start(1500)

    def refresh_orderbook(self):
        ob = self.api.get_orderbook(self.ed_symbol.text().strip())
        asks = ob.get("asks", []); bids = ob.get("bids", [])
        self.sell_view.setRowCount(len(asks)); self.buy_view.setRowCount(len(bids))
        for i,(p,q) in enumerate(asks):
            self.sell_view.setItem(i,0, QtWidgets.QTableWidgetItem(str(p)))
            self.sell_view.setItem(i,1, QtWidgets.QTableWidgetItem(str(q)))
        for i,(p,q) in enumerate(bids):
            self.buy_view.setItem(i,0, QtWidgets.QTableWidgetItem(str(p)))
            self.buy_view.setItem(i,1, QtWidgets.QTableWidgetItem(str(q)))

    def evaluate_once(self):
        sym = self.ed_symbol.text().strip()
        profile = self.cmb_profile.currentText()
        human, _ = compute_human_score(sym, "1m", profile=profile)
        features = {"volatility":0.02, "spread":0.15, "momentum":0.6, "trend":0.55}
        ai = ai_score(features, human_score=human, mode=self.cmb_ai.currentText())
        action, final = self.engine.decide(human, ai, self.spn_buy_th.value(), self.spn_sell_th.value())
        self.lbl_info.setText(f"Human {human} | AI {ai} -> {action} {final:.2f}")
        if action == "BUY":
            self.engine.place_order(sym, "BUY", self.spn_qty.value())
        elif action == "SELL":
            self.engine.place_order(sym, "SELL", self.spn_qty.value())

    def apply_tp_steps(self):
        steps = parse_tp_steps(self.ed_tp.text())
        self.engine.set_take_profits(steps)

    def heartbeat(self):
        self.refresh_orderbook()
        if not self.chk_auto_stops.isChecked(): return
        sym = self.ed_symbol.text().strip()
        self.engine.apply_stop_loss(sym, self.dsb_stop.value())
        self.engine.apply_trailing_stop(sym, self.dsb_trail.value())
        self.engine.apply_take_profits(sym)
