
from PyQt5 import QtWidgets
from app.ui.tabs.tab_login import LoginTab
from app.ui.tabs.tab_conditions import ConditionsTab
from app.ui.tabs.tab_universe import UniverseTab
from app.ui.tabs.tab_data import DataTab
from app.ui.tabs.tab_rationale import RationaleTab
from app.ui.tabs.tab_ai import AITab
from app.ui.tabs.tab_trading import TradingTab
from app.ui.tabs.tab_settlement import SettlementTab

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Trading Bot (Kiwoom)")
        self.resize(1280, 840)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(LoginTab(), "Login")
        tabs.addTab(ConditionsTab(), "Conditions")
        tabs.addTab(UniverseTab(), "Universe")
        tabs.addTab(DataTab(), "Data")
        tabs.addTab(RationaleTab(), "Rationale")
        tabs.addTab(AITab(), "AI")
        tabs.addTab(TradingTab(), "Trading")
        tabs.addTab(SettlementTab(), "Settlement")

        self.setCentralWidget(tabs)
