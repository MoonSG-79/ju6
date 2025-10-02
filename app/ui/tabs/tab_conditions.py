
from PyQt5 import QtWidgets
from app.services.kiwoom_api import KiwoomAPI

class ConditionsTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.api = KiwoomAPI()
        v = QtWidgets.QVBoxLayout(self)

        self.grp = QtWidgets.QGroupBox("Presets (engine-side)")
        h = QtWidgets.QHBoxLayout(self.grp)
        self.rb_scalp = QtWidgets.QRadioButton("Scalp (1~3m)")
        self.rb_day   = QtWidgets.QRadioButton("Day Trade (3~15m)")
        self.rb_mid   = QtWidgets.QRadioButton("Mid Trade (15~60m + Daily)")
        self.rb_scalp.setChecked(True)
        for rb in [self.rb_scalp, self.rb_day, self.rb_mid]: h.addWidget(rb)
        v.addWidget(self.grp)

        g2 = QtWidgets.QGroupBox("Kiwoom Conditions")
        g2v = QtWidgets.QVBoxLayout(g2)
        self.btn_fetch = QtWidgets.QPushButton("Load Conditions (GetConditionLoad)")
        self.lst = QtWidgets.QListWidget()
        self.btn_sub = QtWidgets.QPushButton("Subscribe Real-time (SendCondition)")
        self.lst_realtime = QtWidgets.QListWidget()
        g2v.addWidget(self.btn_fetch); g2v.addWidget(self.lst); g2v.addWidget(self.btn_sub)
        g2v.addWidget(QtWidgets.QLabel("Realtime Hits")); g2v.addWidget(self.lst_realtime)
        v.addWidget(g2)

        self.btn_fetch.clicked.connect(self.fetch)
        self.btn_sub.clicked.connect(self.subscribe)

        self.api.on_real_condition(self._on_real_cond)

    def fetch(self):
        self.lst.clear()
        for c in self.api.fetch_condition_list(): self.lst.addItem(c)

    def subscribe(self):
        it = self.lst.currentItem()
        if not it:
            QtWidgets.QMessageBox.warning(self, "Warn", "Pick a condition."); return
        codes = self.api.subscribe_condition(it.text())
        QtWidgets.QMessageBox.information(self, "Subscribed", f"Initial: {', '.join(codes) if codes else '(none)'}")

    def _on_real_cond(self, code, rtype, cond_name, cond_idx):
        self.lst_realtime.addItem(f"{rtype} {code} @ {cond_name}")
        self.lst_realtime.scrollToBottom()
