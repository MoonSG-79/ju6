
from PyQt5 import QtWidgets
from app.services.data_manager import initial_load, update_data
from app.core.db import create_all
from app.ui.worker import Worker

class DataTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        v = QtWidgets.QVBoxLayout(self)
        self.btn_init = QtWidgets.QPushButton("Initial Load (2Y trading mins, capped)")
        self.btn_update = QtWidgets.QPushButton("Update Data (+300 bars/TF)")
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True)

        form = QtWidgets.QFormLayout()
        self.ed_symbols = QtWidgets.QLineEdit("A005930,A000660,A035720")
        self.ed_years = QtWidgets.QSpinBox(); self.ed_years.setRange(1,5); self.ed_years.setValue(2)
        form.addRow("Symbols (comma)", self.ed_symbols)
        form.addRow("Years", self.ed_years)

        v.addLayout(form)
        v.addWidget(self.btn_init); v.addWidget(self.btn_update); v.addWidget(self.log)

        self.btn_init.clicked.connect(self.do_init)
        self.btn_update.clicked.connect(self.do_update)
        create_all()

        self.worker = None

    def _attach_worker(self, worker: Worker):
        worker.progress.connect(self.log.appendPlainText)
        worker.done.connect(self.log.appendPlainText)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker; worker.start()

    def do_init(self):
        symbols = [s.strip() for s in self.ed_symbols.text().split(",") if s.strip()]
        years = int(self.ed_years.value())
        w = Worker(initial_load, symbols, years=years)
        self._attach_worker(w)

    def do_update(self):
        symbols = [s.strip() for s in self.ed_symbols.text().split(",") if s.strip()]
        w = Worker(update_data, symbols)
        self._attach_worker(w)
