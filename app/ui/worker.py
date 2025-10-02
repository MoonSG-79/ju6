
from PyQt5 import QtCore

class Worker(QtCore.QThread):
    progress = QtCore.pyqtSignal(str)
    done = QtCore.pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__(); self.fn=fn; self.args=args; self.kwargs=kwargs

    def run(self):
        try:
            self.progress.emit("Started..."); self.fn(*self.args, **self.kwargs); self.done.emit("Finished.")
        except Exception as e:
            self.done.emit(f"Error: {e}")
