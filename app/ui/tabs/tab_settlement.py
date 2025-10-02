
from PyQt5 import QtWidgets
from app.services.settlement_service import daily_pnl

class SettlementTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        v = QtWidgets.QVBoxLayout(self)
        self.btn_refresh = QtWidgets.QPushButton("Refresh Settlement")
        self.table = QtWidgets.QTableWidget()
        v.addWidget(self.btn_refresh); v.addWidget(self.table)
        self.btn_refresh.clicked.connect(self.refresh)

    def refresh(self):
        df = daily_pnl()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date","Symbol","Qty","PnL"])
        for i, row in df.reset_index(drop=True).iterrows():
            self.table.setItem(i,0, QtWidgets.QTableWidgetItem(str(row["date"])))
            self.table.setItem(i,1, QtWidgets.QTableWidgetItem(str(row["symbol"])))
            self.table.setItem(i,2, QtWidgets.QTableWidgetItem(str(row["qty"])))
            self.table.setItem(i,3, QtWidgets.QTableWidgetItem(str(round(row["pnl"],2))))
