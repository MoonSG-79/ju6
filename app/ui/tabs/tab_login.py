
from PyQt5 import QtWidgets
from app.services.kiwoom_api import KiwoomAPI

class LoginTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.api = KiwoomAPI()
        layout = QtWidgets.QFormLayout(self)

        self.lbl_mode = QtWidgets.QLabel(f"Mode: {self.api.mode}")
        self.chk_paper = QtWidgets.QCheckBox("Paper Trading"); self.chk_paper.setChecked(True)
        self.ed_acc = QtWidgets.QLineEdit("")
        self.ed_pw = QtWidgets.QLineEdit(); self.ed_pw.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_login = QtWidgets.QPushButton("Login (Kiwoom)")
        self.lbl_status = QtWidgets.QLabel("Not logged in")

        layout.addRow(self.lbl_mode)
        layout.addRow(self.chk_paper)
        layout.addRow("Account No", self.ed_acc)
        layout.addRow("Password", self.ed_pw)
        layout.addRow(self.btn_login)
        layout.addRow(self.lbl_status)

        self.btn_login.clicked.connect(self.login)

    def login(self):
        ok = self.api.login(self.ed_acc.text(), self.ed_pw.text(), self.chk_paper.isChecked())
        if ok:
            accs = self.api.get_accounts()
            self.lbl_status.setText("Logged in. Accounts: " + ", ".join(accs) if accs else "Logged in.")
        else:
            self.lbl_status.setText("Login failed")
