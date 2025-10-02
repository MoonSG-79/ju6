
from PyQt5 import QtWidgets

class UniverseTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        h = QtWidgets.QHBoxLayout(self)

        left = QtWidgets.QVBoxLayout(); right = QtWidgets.QVBoxLayout()

        self.lst_themes = QtWidgets.QListWidget()
        self.btn_add_theme = QtWidgets.QPushButton("Add Theme")
        self.btn_del_theme = QtWidgets.QPushButton("Delete Theme")
        left.addWidget(self.lst_themes); left.addWidget(self.btn_add_theme); left.addWidget(self.btn_del_theme)

        self.lst_symbols = QtWidgets.QListWidget()
        self.btn_add_symbol = QtWidgets.QPushButton("Add Symbol")
        self.btn_del_symbol = QtWidgets.QPushButton("Delete Symbol")
        right.addWidget(self.lst_symbols); right.addWidget(self.btn_add_symbol); right.addWidget(self.btn_del_symbol)

        h.addLayout(left, 1); h.addLayout(right, 2)
