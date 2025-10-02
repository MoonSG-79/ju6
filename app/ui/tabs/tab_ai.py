
from PyQt5 import QtWidgets
from app.services.ai_assessor import ai_score

class AITab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        v = QtWidgets.QVBoxLayout(self)
        self.combo = QtWidgets.QComboBox(); self.combo.addItems(["Conservative","Normal","Aggressive"])
        self.btn_test = QtWidgets.QPushButton("Test AI Score")
        self.lbl = QtWidgets.QLabel("AI Score: -")
        v.addWidget(self.combo); v.addWidget(self.btn_test); v.addWidget(self.lbl)
        self.btn_test.clicked.connect(self.calc)

    def calc(self):
        features = {"volatility":0.02, "spread":0.15, "momentum":0.6, "trend":0.55}
        score = ai_score(features, human_score=75, mode=self.combo.currentText())
        self.lbl.setText(f"AI Score: {score}")
