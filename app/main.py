
from PyQt5 import QtWidgets
import sys
from app.ui.main_window import MainWindow
from app.core.db import create_all

def main():
    create_all()
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
